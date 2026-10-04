# SONARQ — Learn Code Analysis With SonarQube From Scratch

> Read this top to bottom once, then use it as revision notes.
> Every example comes from THIS repo (Spring Boot backend + Angular frontend + SonarQube LTS).
> Goal: understand the **reasoning**, so you can reproduce it on any project —
> and explain it in an interview without notes.

**What you need:** Docker Engine + Compose v2, this repo, `curl`, and a running
`sonarqube` service (`docker compose up -d sonardb sonarqube`). No Jenkins needed for §1–§6.

Companion: [`DOCKERIZER.md`](DOCKERIZER.md) (containers) → this file (code quality) → `Jenkinsfile` (pipeline).

---

## 1. Start With the Architecture

Without SonarQube, quality is an opinion ("looks fine to me"):

```text
Developer
   │
   ▼
Code (backend/src, frontend/src) ──► Build (mvn / npm) ──► Ship it?
```

With SonarQube, quality is a measurement:

```text
Jenkins / your laptop
   │  STEP 1: scanner sends sources + coverage
   ▼
SonarQube (:9000) ──computes──► bugs / vulnerabilities / smells / duplication / coverage
   │  STEP 2: Quality Gate says PASS or FAIL
   ▼
Pipeline continues (Docker Build) or STOPS (red gate)
   │
   ▼
SonarDB (postgres:15) holds history: "are we getting better or worse?"
```

Our Compose wiring:

```text
Scanner ──► sonarqube:9000 ──► sonardb:5432
  (mvn sonar:sonar / scanner-cli)    (postgres, internal only)
              │                              │
              └────────── app-net ───────────┘
              │                              │
   sonarqube_data/logs/extensions      sonardb_data (volume)
Browser ──► http://localhost:9000 (published port)
```

### The 6 concepts (short, practical)

| Concept | One-sentence version | This project |
|---|---|---|
| **Server** | The web app that stores rules, shows issues, enforces gates. | `app-sonarqube` (`sonarqube:lts-community`), UI `:9000` |
| **Database** | Where server keeps analysis history (not your app data). | `app-sonardb` (`postgres:15-alpine`), volume `sonardb_data` |
| **Scanner** | CLI/Maven plugin that ships your code + coverage to the server. | `sonar-maven-plugin` 3.9.1.2184 (backend) + `sonarsource/sonar-scanner-cli` (frontend) |
| **Project Key** | Unique ID of your codebase in SonarQube. | `devops-appgestiondesprojets` (`sonar-project.properties`) |
| **Token** | Password the scanner uses instead of your login. Like a PAT. | Jenkins credential `sonar-token` (Secret text), env `SONAR_TOKEN` |
| **Quality Gate** | PASS/FAIL rule: "is this code shippable?" | Default "Sonar way": no new bugs/vulns, coverage on new code |

### Why service names instead of `localhost`? (same rule as DOCKERIZER §7)

Inside a scanner container, **`localhost` means that same container** — not SonarQube.
So a scanner on `app-net` reaches the server at `http://sonarqube:9000`
(Compose DNS resolves `sonarqube` to the server container's IP), never `localhost:9000`.

⚠️ **Interview-grade nuance:** Jenkins `sh` steps run ON the agent (not in a container),
so they use `http://localhost:9000` (published port). Scanner *containers*
(`docker run ... scanner-cli`) use `http://sonarqube:9000` (service name).
Rule of thumb: container→container = service names; host/agent→container = published `localhost` ports.
Our `Jenkinsfile` sets `SONAR_HOST_URL=http://localhost:9000` for agent steps.

---

## 2. SonarQube via Docker Compose Step by Step

Stack facts we read from the repo (never assume — always inspect):
`docker-compose.yml` → app DB is `mysql:8.0`; SonarQube docs → MySQL unsupported since 9.9;
therefore a **dedicated Postgres** is mandatory, not optional.

Our two new services in `docker-compose.yml`:

```yaml
sonardb:
  image: postgres:15-alpine          # 1. smallest Postgres that SonarQube supports
  environment:                        # 2. SONAR_JDBC_* with safe defaults
    POSTGRES_USER: ${SONAR_JDBC_USERNAME:-sonar}
    POSTGRES_PASSWORD: ${SONAR_JDBC_PASSWORD:-sonar}
    POSTGRES_DB: ${SONAR_JDBC_DATABASE:-sonar}
  volumes: [sonardb_data:/var/lib/postgresql/data]  # 3. history survives restarts
  # No ports: reachable internally as sonardb:5432 only.

sonarqube:
  image: sonarqube:lts-community     # 4. LTS = stable rules, free Community
  depends_on: {sonardb: {condition: service_healthy}}  # 5. wait for DB ready
  environment:
    SONAR_JDBC_URL: jdbc:postgresql://sonardb:5432/${SONAR_JDBC_DATABASE:-sonar}
    # NOTE: service name `sonardb`, NOT localhost (§1).
  ports: ["9000:9000"]               # 6. UI for browser + agent scanners
  volumes:                           # 7. data/logs/extensions survive restarts
    - sonarqube_data:/opt/sonarqube/data
    - sonarqube_logs:/opt/sonarqube/logs
    - sonarqube_extensions:/opt/sonarqube/extensions
```

How each decision was made:

* **Base image:** `sonarqube:lts-community` — pinned LTS, free, covers Java + TS.
  Floating `latest` would change rules mid-semester; pin it like `mysql:8.0`.
* **Why Postgres 15 Alpine:** smallest image SonarQube still supports.
  Reusing `app-db` (MySQL) fails at boot with `MySQL is no longer supported`.
* **Volumes:** three for SonarQube (data = issues, extensions = plugins, logs = debug)
  + one for Postgres. Without them, first `down -v` wipes all quality history.
* **Healthcheck:** `curl .../api/system/status | grep UP` with `start_period: 120s` —
  first boot downloads plugins and takes 1–2 min. Don't shorten it.

### Host prereq (Elasticsearch inside SonarQube needs it)

```bash
sysctl -w vm.max_map_count=262144
# Persist: echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

*What → Why → Misuse:* Elasticsearch (bundled search engine) mmaps many files;
the kernel default (65530) kills it with exit 78. Symptom: `sonarqube` exits instantly,
logs say `max virtual memory areas vm.max_map_count [65530] is too low`.

### Instruction cheat card: What → Why → Misuse (SonarQube edition)

| Key | What it does | Why we need it here | Misuse symptom |
|---|---|---|---|
| `image: sonarqube:lts-community` | Starts the analysis server. | Pinned LTS = reproducible rules. | `:latest` → new rules fail old code overnight. |
| `SONAR_JDBC_URL` | Tells server where its DB lives. | Must use `sonardb:5432` (Compose DNS). | `localhost:5432` → `Connection refused` inside container. |
| `depends_on: service_healthy` | Waits for Postgres `pg_isready`. | Server crashes if DB isn't accepting connections. | `service_started` → crash-loop on first `up`. |
| `ports: 9000:9000` | Publishes UI. | Browser + Jenkins agent need `localhost:9000`. | Missing → "server runs but I can't open it". |
| `volumes:` | Persists data/logs/plugins. | History + installed analyzers survive restarts. | No volume → re-analyze everything after each `down -v`. |
| Token via env | Scanner auth (`SONAR_TOKEN`). | Keeps secret out of images and git. | Baking token → visible in `docker history` + Hub. |

---

## 3. `sonar-project.properties` Line by Line

`sonar-project.properties` at repo root = the scanner's instruction sheet.
Quoting ours:

* **`sonar.projectKey=devops-appgestiondesprojets`** — unique ID in SonarQube.
  Shown in URL (`/dashboard?id=...`) and Jenkins logs. Lowercase, no spaces.
* **`sonar.sources=backend/src,frontend/src`** — real code only.
  Build outputs (`target/`, `dist/`) are never sources.
* **`sonar.tests=backend/src/test,frontend/src`** + `test.inclusions` — tells SonarQube
  "these are tests, don't count them as duplication".
* **`sonar.exclusions=**/node_modules/**,**/target/**,**/dist/**,**/.angular/**`** —
  generated/huge/cached dirs. Scanning them wastes minutes and creates false bugs.
* **`sonar.java.binaries=backend/target/classes`** — compiled `.class` files.
  Java rules NEED bytecode (null-deref, injection). Without it: warning
  `Java analysis requires compiled classes` and half the rules silently skip.
* **`sonar.coverage.jacoco.xmlReportPaths=backend/target/site/jacoco/jacoco.xml`** —
  where JaCoCo writes coverage (see §4). Missing file → 0% coverage, not "no tests".
* **`sonar.typescript.lcov.reportPaths=frontend/coverage/lcov.info`** —
  where vitest writes coverage. Warns (doesn't fail) if absent on first run.
* **`sonar.sourceEncoding=UTF-8`** — avoids `unrecognized character` noise on French comments.

---

## 4. Backend Analysis (Java 17 + Maven)

What we added to `backend/pom.xml`:

```xml
<jacoco.version>0.8.11</jacoco.version>
<sonar-maven-plugin.version>3.9.1.2184</sonar-maven-plugin.version>
<!-- plugins: jacoco:prepare-agent + report, sonar:sonar -->
```

*What → Why → Misuse:*

* **JaCoCo `prepare-agent`** instruments tests at runtime. Without it, `mvn verify`
  runs tests but writes no coverage file → SonarQube shows 0%.
* **JaCoCo `report` (phase `verify`)** builds `target/site/jacoco/jacoco.xml`.
  Must run `verify` (not just `package`): `package` skips the report goal.
* **`sonar-maven-plugin`** sends `backend/src` + `jacoco.xml` to the server.
  Command used in Jenkins (never locally with a hardcoded token):

```bash
cd backend
./mvnw -B verify sonar:sonar \
  -Dsonar.projectKey=devops-appgestiondesprojets \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token="$SONAR_TOKEN"
```

Check it: `ls backend/target/site/jacoco/jacoco.xml` (exists after `verify`),
`ls backend/target/classes` (exists — proves `java.binaries` path is valid).

---

## 5. Frontend Analysis (Angular 22 + TypeScript)

No `package.json` change needed — the standalone scanner does the work:

```bash
docker run --rm -v "$PWD:/usr/src" -w /usr/src \
  -e SONAR_HOST_URL=http://sonarqube:9000 -e SONAR_TOKEN="$SONAR_TOKEN" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.projectKey=devops-appgestiondesprojets-frontend \
  -Dsonar.sources=frontend/src \
  -Dsonar.exclusions="**/node_modules/**,**/dist/**,**/.angular/**"
```

*What → Why → Misuse:* scanner-cli is a Docker image (like `nginx:alpine`):
no Node install, no Jenkins plugin, version pinned by Hub tag. We run it with
`-v $PWD:/usr/src` so it sees the checked-out code, and `--network` implicitly
via Compose defaults when run on the same host (or explicit `--network app-net`
if resolving `sonarqube` hostname from inside).

Coverage (phase 2, optional today): `npm run test -- --coverage` writes
`frontend/coverage/lcov.info` via vitest; scanner picks it up automatically
through `sonar.typescript.lcov.reportPaths`. First pipeline runs without it —
bugs/smells still report, coverage appears once tests run.

---

## 6. Jenkins Pipeline (stages 3–4 of 10)

Our `Jenkinsfile` inserts analysis **after Build, before Docker Build** —
broken quality blocks image push (fail fast, same philosophy as Build):

```text
Git Push
   ↓  webhook / pollSCM
Checkout (git, credential 146958092)
   ↓
Build (mvnw package · npm ci + ng build)
   ↓
SonarQube Analysis (backend mvn sonar:sonar + frontend scanner-cli, credential sonar-token)
   ↓
Quality Gate (curl api/qualitygates/project_status → OK or ERROR, abort on ERROR)
   ↓
Docker Build → Login → Tag → Push → Deploy/Verify → Push tags
```

Per-key **What → Why this project needs it**:

* **`SONAR_HOST_URL=http://localhost:9000`** — agent runs on the same host as Compose,
  so published port. Scanner containers use the same var (override to
  `http://sonarqube:9000` if DNS-resolving from inside a custom network).
* **`withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')])`** —
  same pattern as `mysql-root-password`: secret lives in Jenkins vault, travels as
  masked env, never in code/logs/chat. Missing credential → stage fails with
  remediation echo (defensive pattern from DOCKERIZER §16.2).
* **`retry 3` around `docker run scanner-cli`** — Hub pulls hit transient
  `i/o timeout` (same incident as Docker Build §16.3). Momentary blips cost seconds.
* **`archiveArtifacts: backend/target/site/jacoco/*.xml`** — coverage downloadable
  from Jenkins UI alongside the jar (audit trail for TP grading).

### ONE-TIME SETUP (do once on Jenkins host + SonarQube UI)

```text
1. docker compose up -d sonardb sonarqube   (wait 60-120s, check /api/system/status → UP)
2. Open http://localhost:9000 (admin/admin → change password)
3. My Account > Security > Generate Token (User Token) → copy once
4. Jenkins > Manage > Credentials > Secret text, ID = exactly `sonar-token`, paste token
5. Rebuild. Stage logs show "ANALYSIS SUCCESSFUL" + dashboard link.
```

---

## 7. Essential SonarQube Commands

Format: **command → what → when**.

```bash
docker compose up -d sonardb sonarqube
→ Start only quality services (faster than full stack)
→ First install, or after reboot

docker compose ps / docker compose logs sonarqube / docker compose logs -f sonardb
→ Status / server logs / follow DB logs
→ The debugging trio (same as DOCKERIZER §9)

curl -s http://localhost:9000/api/system/status
→ {"status":"UP"} means ready for analysis
→ Gate before running any scanner; Jenkins Quality Gate polls this API family

docker compose exec sonarqube ls /opt/sonarqube/logs
→ Server log files (ce.log = background tasks, es.log = search engine)
→ "Analysis submitted but never finishes" → read ce.log

docker inspect app-sonarqube --format '{{.State.Health.Status}}'
→ healthy / starting / unhealthy
→ Distinguishes "still booting" from "crashed"

# Backend local analysis (server must be UP, token exported, never committed):
cd backend && ./mvnw -B verify sonar:sonar -Dsonar.host.url=http://localhost:9000 -Dsonar.token="$SONAR_TOKEN"
→ Full backend scan with coverage
→ Before pushing, to catch red gate early

docker compose down          → Stop quality + app (KEEPS volumes = history safe)
docker compose down -v        → ⚠️ DELETES volumes = SonarQube history + app DB wiped. Only for true reset.
```

---

## 8. Debugging Workflow

When analysis doesn't work, go in order — don't skip steps:

```text
1. Server UP?       curl localhost:9000/api/system/status → UP?
   ↓  DOWN/000? → docker compose ps (restarting? exited?) → logs sonarqube
2. Token OK?       401 Unauthorized = wrong/revoked/missing sonar-token.
   ↓  Regenerate in UI, update Jenkins credential, rebuild.
3. Project key?    404 Component not found = typo in -Dsonar.projectKey.
   ↓  Must match sonar-project.properties / SONAR_PROJECT_KEY exactly.
4. Java classes?   "java.binaries not found" → run `verify` not `package`,
   ↓  check backend/target/classes exists.
5. Coverage 0%?    jacoco.xml / lcov.info missing → run verify / test --coverage first.
   ↓  Scanner warns, doesn't fail — coverage appears next run.
6. Gate UNKNOWN?   Compute Engine still working (first analysis slow).
   ↓  Wait 2 min, refresh dashboard. Quality Gate stage retries 20×15s.
```

Golden rule: **read `ce.log` before changing config.** Most "analysis stuck"
cases are visible there, not in Jenkins.

---

## 9. Troubleshooting — Real Incidents You Will Hit

### 9.1 `max virtual memory areas vm.max_map_count [65530] is too low` (exit 78)

*Symptom:* `app-sonarqube` exits instantly, `docker compose ps` shows `Exited (78)`.
*Diagnosis:* bundled Elasticsearch needs ≥262144 mmap areas; host default is 65530.
*Fix (host, needs sudo):* `sudo sysctl -w vm.max_map_count=262144` + persist in
`/etc/sysctl.conf`. Verify: `sysctl vm.max_map_count`. Restart: `docker compose up -d sonarqube`.

### 9.2 `401 Unauthorized` from scanner

*Symptom:* `Not authorized. Please check sonar.token` in analysis log.
*Diagnosis:* token wrong (typo), revoked in UI, or Jenkins credential ID mismatch
(`sonar-token` vs `sonar_token` — Jenkins IDs are exact).
*Fix:* regenerate token in SonarQube UI → Jenkins Credentials → update `sonar-token` →
rebuild. Verify with `curl -u "$SONAR_TOKEN:" http://localhost:9000/api/authentication/validate`
→ `{"valid":true}`. **Defensive pattern:** stage echoes remediation, never the token.

### 9.3 `Java analysis requires compiled classes` / `java.binaries not found`

*Symptom:* analysis succeeds but Java issues ≈ 0, warning in `ce.log`.
*Diagnosis:* scanner ran before `mvn compile`/`verify`, or `sonar.java.binaries`
points at a missing dir (e.g. `target/classes` vs `backend/target/classes` from root).
*Fix:* always `./mvnw verify sonar:sonar` in one Maven invocation (our Jenkinsfile does);
verify `ls backend/target/classes` exists. Same class of bug as DOCKERIZER §16.7
(wrong `COPY` path for `dist/`).

### 9.4 `MySQL is no longer supported` at SonarQube boot

*Symptom:* server log says `Unsupported database: mysql`, exits.
*Diagnosis:* someone pointed `SONAR_JDBC_URL` at `app-db` (MySQL).
*Fix:* use `jdbc:postgresql://sonardb:5432/sonar` (already in our compose).
Never cross-wire app DB and Sonar DB (§2).

### 9.5 Token/secret posted in chat, logs, or code

*Symptom:* someone pastes `sonar-token` where others can see it.
*Fix:* treat as compromised **immediately**: SonarQube UI → revoke → regenerate →
update the *one* place storing it (Jenkins `sonar-token`). Same rule as
DOCKERIZER §16.10: secrets live in exactly one secure place each, never in two.

### The meta-lesson (interview-worthy)

> Reproduce first, blame rules last. Every incident above was solved by the same loop:
> read the exact error → locate which layer (host / server / scanner / token) →
> verify with one command (`curl status`, `validate`, `ls classes`, `logs`) →
> fix that layer only.

---

## 10. Mental Model (memorize this)

```text
sonar-project.properties ──configures──► Scanner ──ships──► SonarQube ──stores in──► sonardb
     (what to scan)            (mvn / cli)      (bugs/vulns/smells)       (postgres)
                                                        │
                                                  Quality Gate
                                                  PASS → ship / FAIL → fix
```

Say it in an interview like this: *"I added SonarQube LTS + Postgres to Compose,
configured one properties file for Java + TypeScript with JaCoCo/LCOV coverage,
and gated the Jenkins pipeline: backend via sonar-maven-plugin, frontend via
scanner-cli Docker image, token via Jenkins credentials — red gate fails the build
before any Docker push."*

---

## 11. Measure the Quality (numbers from YOUR project after first run)

Never claim "clean code" without measuring. After first green run, fill this in:

| Metric | Where | Healthy |
|---|---|---|
| Bugs / Vulnerabilities | Dashboard → Issues | 0 new on new code |
| Code smells / Debt | Dashboard → Maintainability | Decreasing trend |
| Duplication | Dashboard → Duplications | < 3% |
| Coverage (backend) | `backend/target/site/jacoco/jacoco.xml` → Dashboard | Rising; gate on new code |
| Coverage (frontend) | `frontend/coverage/lcov.info` → Dashboard | Rising; gate on new code |

How to compare yourself: run analysis on `main`, note the numbers, fix one rule
(e.g. `Sonar way` blocker), re-run, diff the dashboard. The trend matters more
than any single number — same philosophy as DOCKERIZER §12 image sizes.
