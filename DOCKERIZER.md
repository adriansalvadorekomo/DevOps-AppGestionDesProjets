# DOCKERIZER — Learn to Dockerize This Project From Scratch

> Read this top to bottom once, then use it as revision notes.
> Every example comes from THIS repo (Spring Boot backend + Angular frontend + MySQL).
> Goal: understand the **reasoning**, so you can reproduce it on any project —
> and explain it in an interview without notes.

**What you need:** Docker Engine + Compose v2 (`docker --version`, `docker compose version`),
this repo, and the ability to run `curl`. No Jenkins needed for this guide.

---

## 1. Start With the Architecture

Without Docker, the app looks like this:

```text
User (browser)
  │
  ▼
Frontend (ng serve :4200)
  │
  ▼
Backend (java -jar :8080)
  │
  ▼
Database (mysqld :3306)
```

Three processes on one machine, talking over `localhost`, database files on your disk.
It works — until a teammate has a different Java version, or the server has no Node,
or someone deletes the database files.

With Docker, the same three pieces become **three containers** on one **private network**,
and the data lives in a **volume** outside any container:

> 🖼️ **Interactive diagram:** [`docs/docker-stack-architecture.html`](docs/docker-stack-architecture.html)
> — open it in a browser: symmetric topology, pan/zoom, guided Request-path and
> Data-durability views, PNG/SVG export.
>
> ```text
> User ──► Frontend ──► Backend ──► Database
>            :4200        :8080       :3306 (internal, as db:3306)
>              │                         │
>              └──── app-net ────────────┘
>                              │
>                     mysql_data (volume)
> ```

### The 6 concepts (short, practical)

| Concept | One-sentence version | This project |
|---|---|---|
| **Image** | A frozen, shareable template: app + runtime + config, built from a Dockerfile. Read-only. | `twelvy1400/backend:build-31` (358MB), `twelvy1400/frontend:build-31` (95.2MB) |
| **Container** | A *running* image: a process with its own filesystem and network identity. Disposable. | `app-db`, `app-backend`, `app-frontend` (`docker compose ps`) |
| **Dockerfile** | The recipe that builds an image, step by step. | `backend/Dockerfile`, `frontend/Dockerfile` |
| **Docker Compose** | One YAML file that builds/starts/wires several containers together. | `docker-compose.yml` at repo root |
| **Volume** | Storage that lives *outside* containers, so data survives restarts/deletes. | `mysql_data` → `/var/lib/mysql` |
| **Network** | A private LAN for your containers, with automatic DNS: service names work as hostnames. | `app-net` (bridge) |

### Why service names instead of `localhost`?

Inside a container, **`localhost` means that same container** — not your laptop, not the
neighbor container. So the backend reaches the database at `db:3306` (Compose DNS resolves
`db` to the database container's IP), never `localhost:3306`.

⚠️ **Interview-grade nuance this project teaches:** our Angular frontend runs *in the
browser*, not in the container. Browser code can't resolve Docker DNS, so the frontend
services call `http://localhost:8080/...` — and that works because we **publish** the
backend port to the host (`8080:8080`). Rule of thumb: container→container = service
names; browser→container = published `localhost` ports.

---

## 2. Dockerize the Backend Step by Step

Stack facts we read from the repo (never assume — always inspect):
`pom.xml` → Java 17, Spring Boot, `mysql-connector-j`; `application.properties` →
port **8080** (default), JDBC to `localhost:3306/test_db`; entry point = fat jar
(`backend/target/backend-1.0.0.jar`, 50MB) run with `java -jar`.

Our `backend/Dockerfile`:

```dockerfile
FROM maven:3.9-eclipse-temurin-17-alpine AS build   # 1. build env: Maven + JDK 17
WORKDIR /app                                        # 2. working dir inside image
COPY pom.xml ./                                     # 3a. manifest first (cache!)
COPY src ./src                                      # 3b. then source
RUN mvn -B clean package -DskipTests                # 4. compile → target/*.jar

FROM eclipse-temurin:17-jre-alpine                  # 5. tiny runtime: JRE only
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar         # 6. only the artifact crosses over
EXPOSE 8080                                         # 7. documentation (+ tooling)
ENTRYPOINT ["java", "-jar", "app.jar"]              # 8. how the container starts
```

How each decision was made:

* **Base image:** `pom.xml` says Java 17 → smallest image that *runs* Java 17 is
  `eclipse-temurin:17-jre-alpine` (JRE, not JDK — we don't compile at runtime).
  The build stage needs Maven too → `maven:3.9-eclipse-temurin-17-alpine`.
* **Files copied first:** `pom.xml` before `src/` — dependencies change rarely, source
  changes constantly (see §11 layer caching).
* **Port:** 8080, because Spring Boot's default is 8080 and nothing overrides `server.port`.
* **Start command:** `java -jar app.jar` — exactly what you'd run locally after `mvn package`.
* **Env vars:** none baked in. The DB URL/user/password arrive at *runtime* from Compose
  (`SPRING_DATASOURCE_URL=jdbc:mysql://db:3306/...` — note `db`, not `localhost`),
  which Spring Boot maps over `application.properties` automatically.

### Instruction cheat card: What → Why → Misuse

| Instruction | What it does | Why we need it here | Misuse symptom |
|---|---|---|---|
| `FROM` | Sets the starting image (and names the stage with `AS`). | Pins exact build/runtime environments; `AS build` lets stage 2 copy from stage 1. | Wrong Java major → `UnsupportedClassVersionError` at startup. |
| `WORKDIR` | Creates + `cd`s into a directory; all following paths are relative to it. | Avoids absolute-path soup; every `COPY`/`RUN` below just works. | Omitting it litters files at `/` and breaks relative `COPY --from` paths. |
| `COPY` | Copies files from build context (or `--from=stage`) into the image. | Ships manifest, source, then only the jar — nothing else crosses stages. | `COPY . .` first line → cache busted on every edit; secrets (`.env`) baked into history. |
| `RUN` | Executes a command **at build time**, saving the result as a layer. | Compiles the jar once, so containers start in seconds. | Long `RUN` chains re-execute on any cache miss; failed `RUN` = failed build. |
| `ENV` | Bakes an env var into the image. | **Deliberately NOT used here** — DB credentials differ per environment and must stay out of images (see §11 Security). Runtime env comes from Compose instead. | Baking passwords → visible forever in `docker history` + Hub. |
| `EXPOSE` | Documents which port the app listens on (metadata + tooling hint). | Signals 8080 to humans and tooling. | Believing it *publishes* the port — it doesn't; only Compose `ports:` / `-p` does (§5, §13). |
| `CMD` | Default command, easily overridden (`docker run img echo hi`). | Used in frontend (`CMD ["nginx", ...]`) where overriding is harmless. | — |
| `ENTRYPOINT` | The container's fixed main process (keeps PID 1, gets signals properly). | Backend must *always* boot Spring — `ENTRYPOINT ["java","-jar","app.jar"]`. | Shell form (`ENTRYPOINT java -jar app.jar`) breaks signal handling → slow `docker stop`. Always use JSON-array form. |

---

## 3. Dockerize the Frontend Step by Step

Stack facts: Angular 22 (`package.json`, `packageManager npm@11`), `ng build` →
`dist/frontend/browser/` (verified with `ls`), dev server `:4200`, runtime needs **no Node**
— just static files + a web server.

```dockerfile
FROM node:22-alpine AS build              # Stage 1: build env (Node 22 runs npm 11 + ng)
WORKDIR /app
COPY package.json package-lock.json ./    # manifest first (cache!)
RUN npm ci                                # clean, lockfile-exact install
COPY . .                                  # then source
RUN npm run build                         # → dist/frontend/browser/

FROM nginx:alpine                          # Stage 2: production runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf      # SPA fallback (below)
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Build environment ↓ Production runtime (the key idea)

> 🖼️ **Interactive diagram:** [`docs/multistage-builds-dataflow.html`](docs/multistage-builds-dataflow.html)
> — both pipelines side by side: Source → Build → Artifact → Runtime → Serve.
>
> ```text
> Stage 1 (node:22-alpine — thrown away after build)
>   Source Code → npm ci → ng build → static files (ours: 300K!)
>
> Stage 2 (nginx:alpine — the shipped 95.2MB image)
>   Minimal web server + COPY only the static files → serve on :80
> ```

**Why the final image shrinks dramatically:** the finished image contains zero Node,
zero `node_modules`, zero TypeScript toolchain — just nginx + 300K of HTML/JS/CSS.
Measure it yourself: `du -sh frontend/dist/frontend/browser` (300K) vs
`docker images ... frontend` (95.2MB — almost all nginx+Alpine, see `docker history` in §12).

### `nginx.conf` — the line that saves Angular routing

```nginx
location / { try_files $uri $uri/ /index.html; }
```

*What → Why → Misuse:* an SPA has one real file (`index.html`); routes like `/entreprise`
exist only in the browser's router. Without this fallback, refreshing on any route returns
nginx **404**. Beginner mistake #1 in containerized SPAs.

---

## 4. `.dockerignore`

`COPY . .` sends your whole folder to the Docker daemon as the **build context**.
`.dockerignore` filters it — same idea as `.gitignore`, but for builds.

What we exclude and why:

| Entry | Why |
|---|---|
| `node_modules/` / `target/` | **Huge**, and *regenerated inside* the image (`npm ci` / `mvn package`). Sending them wastes minutes and can poison the build with host-OS binaries. |
| `dist/` | Stale build output; the image builds its own. |
| `.angular/` | Local incremental-build cache. Useless remotely, slows context transfer. |
| `.git/` | History is often hundreds of MB and can leak branch/tag info. |
| `.env` | ⛔ Secrets must never enter build context (they'd persist in image layers). |
| `coverage/`, `*.log`, `.DS_Store`, IDE files | Dead weight in context transfer. |

Unnecessary files hurt **four** ways: bigger context → slower uploads to the daemon,
more cache invalidation → slower rebuilds, bigger images, and secret leakage.
Check it: `du -sh frontend/node_modules` on your machine, then imagine uploading that on every build.

---

## 5. Docker Compose Step by Step

From three manual `docker run` commands to one file:

```text
docker compose
      │
      ├── db       (mysql:8.0, internal only)
      ├── backend  (build ./backend, :8080)
      └── frontend (build ./frontend, :4200→:80)
```

Per-key **What → Why this project needs it** (quoting our `docker-compose.yml`):

* **`services:`** — declares the three containers. Names (`db`, `backend`, `frontend`) become DNS hostnames on `app-net`.
* **`build: ./backend`** — build the image from that Dockerfile at deploy time (reproducible from source; Jenkins does the same). `db` uses **`image: mysql:8.0`** instead — no Dockerfile needed for off-the-shelf software.
* **`ports: ["8080:8080"]`** — `HOST:CONTAINER`. Publishes backend to your browser (remember §1: browser needs `localhost:8080`). `db` has **no** `ports:` — unreachable from outside, only via `db:3306` internally. `frontend` maps `"4200:80"` (keeps the README's `localhost:4200` habit while nginx listens on 80 inside).
* **`environment:`** — runtime config with safe defaults: `${MYSQL_ROOT_PASSWORD:-root}` means "use env/`.env` value, else `root`". Backend gets `SPRING_DATASOURCE_URL=jdbc:mysql://db:3306/...` — **service name, not localhost**. (We don't use `env_file:`; Compose auto-loads the gitignored `.env` file, and real shell env beats both — that's how Jenkins injects secrets with no `.env` present.)
* **`depends_on: db: {condition: service_healthy}`** — start backend only after `db` passes its healthcheck (§6). Frontend uses `service_started` on backend (enough: nginx serves static files regardless).
* **`healthcheck:`** — `mysqladmin ping` every 10s; `start_period: 30s` gives MySQL time to initialize before counting failures.
* **`volumes: [mysql_data:/var/lib/mysql]`** — named volume holding real database files (§8).
* **`networks: [app-net]`** — one private bridge for all three; nothing else on the host can snoop.
* **`restart: unless-stopped`** — containers come back after a host reboot.
* **`container_name:`** — stable names (`app-db`…) so logs/inspect commands are predictable.

---

## 6. Startup Order

Required order:

```text
Database
   ↓  healthy (accepting connections)
Backend
   ↓  ready (Tomcat up)
Frontend
```

### `depends_on` ≠ ready

Plain `depends_on: [db]` only orders **container start**. MySQL's container starts in
~2s but needs ~20s before accepting connections — Spring Boot would crash on first
query with `Communications link failure`, restart, crash… Our fix (already in the file):

```yaml
depends_on:
  db:
    condition: service_healthy   # NOT service_started!
```

> **Container started ≠ Application ready.** Memorize this — it explains half of all
> "works locally, fails in Docker" mysteries. `service_healthy` makes Compose wait for
> the `mysqladmin ping` healthcheck to succeed before starting the backend.

---

## 7. Networking

Compose runs an embedded DNS server on `app-net`: every service name resolves to that
container's current IP (even across restarts — never hardcode IPs).

```text
backend  →  db:3306        ✅ (Compose DNS)
frontend →  backend:8080   (only relevant server-side; our Angular calls from the browser → §1)
```

Why `localhost:3306` inside the backend container is **wrong**:

```text
localhost = the current container
backend's localhost → the backend container itself → nothing listens on 3306 there → connection refused
```

Symptoms you'll recognize: `Connection refused` / `Communications link failure` only
inside Docker while local runs work. Fix: replace `localhost` with the service name
(here via `SPRING_DATASOURCE_URL`, keeping `application.properties` untouched for local dev).

---

## 8. Persistent Database

Containers are cattle: `docker compose down` deletes them, and their internal filesystem
goes with them — including MySQL's data dir. A **named volume** is storage *outside* the
container lifecycle:

```text
docker compose down
        │
        ✕  app-db container deleted (nobody cares)

mysql_data volume survives
        │
        ▼
next `up` → same tables, same rows
```

We watched this for real: a test row survived full rebuilds because only containers
were recreated — the volume never moved.

| Storage | Lives where | Dies when | Use for |
|---|---|---|---|
| Container filesystem | Inside container | Container deleted | Throwaway (caches, temp) |
| **Named volume** (`mysql_data:/var/lib/mysql`) | Managed by Docker | Only `docker compose down -v` / `docker volume rm` | **Databases** — Junior default choice |
| Bind mount (`./data:/var/lib/mysql`) | Your host folder | Never (it's your files) | Dev convenience (live code reload), not prod DBs |

⚠️ Destructive commands (memorize): `docker compose down -v` **deletes volumes** = your
database is gone. Plain `docker compose down` / `restart` keeps data.

---

## 9. Essential Docker Commands

Format: **command → what → when**. (⚠️ = destructive — think twice.)

**Images & containers**

```bash
docker build ./backend -t myapp/backend:1.0
→ Build an image from a Dockerfile (-t names it)
→ After editing Dockerfile/source; in CI on every push

docker images / docker images | grep myapp
→ List local images + sizes
→ "Did my build work? Why is disk full?"

docker ps  → Running containers (names, ports, status)
→ First check whenever "the app doesn't respond"
docker ps -a → Also exited ones (with exit codes!)
→ "It crashed — what was the exit code?"

docker run --rm -p 8080:8080 myapp/backend:1.0
→ One-off container from an image (--rm cleans up after)
→ Smoke-test an image without Compose

docker exec -it app-backend sh
→ Open a shell INSIDE a running container
→ Inspect files/env, run mysqladmin/curl from inside

docker logs app-backend / docker logs -f app-db / docker logs --tail=50 app-db
→ Read (follow / tail) a container's stdout
→ 90% of debugging starts here

docker inspect app-db --format '{{.State.Health.Status}}'
→ Full JSON config/state of a container
→ Health status, IPs, mounts, env — the "x-ray" command

docker stop app-backend / docker rm app-backend / docker rmi myapp/backend:1.0
→ Stop / delete container / delete image
→ Cleanup; ⚠️ rm/rmi delete things (containers must be stopped first)

docker volume ls / docker network ls / docker system df
→ Volumes, networks, disk usage
→ "Where is my data? What's eating 3GB?" (see §12)
```

**Compose (your daily driver — prefer these over raw `docker`):**

```bash
docker compose up -d --build
→ (Re)build images + start whole stack detached
→ The one command that (re)deploys everything, locally and in CI

docker compose ps / docker compose logs / docker compose logs -f backend
→ Status / all logs / follow one service
→ The debugging trio (§10)

docker compose exec backend sh
→ Shell into the backend container
→ Debug from inside (§10 step 4)

docker compose down          → Stop + delete containers/network (KEEPS volumes = data safe)
docker compose down -v       → ⚠️ Also DELETES volumes = database wiped. Only for a true reset.
docker compose build         → Rebuild images without starting
docker compose restart backend → Restart one service
docker compose config        → Render + validate compose file (catches YAML/env mistakes before up)
```

---

## 10. Debugging Workflow

When the app doesn't work, go in order — don't skip steps:

```text
1. Running?          docker compose ps
   ↓  Up? healthy? restarting loop? exited (code?)
2. What failed?      docker compose logs --tail=50
   ↓  ERROR? Exception? refused? denied? port conflict?
3. Zoom to service   docker compose logs backend
   ↓  backend:  Hibernate errors? Tomcat up on 8080? link failure = DB unreachable
   ↓  db:       "Access denied" = wrong password; InnoDB errors = corrupt volume
   ↓  frontend: nginx emerg = bad nginx.conf; refresh 404 = missing try_files (§3)
4. Enter container   docker compose exec app-backend sh
   ↓  env SPRING_* right? DNS db:3306 ok? files in /app?
5. Check outside     curl localhost:8080/... and localhost:4200/
   ↓  distinguishes "container broken" from "wrong expectation"
6. Rebuild           docker compose up -d --build
   ↓  Dockerfile/compose/.env changes NEVER apply live — rebuild is mandatory
```

Golden rule: **read the logs before changing anything.** Most fixes in §16 were found at step 2.

---

## 11. Image Optimization

Golden rule:

> **Use the smallest image that correctly satisfies the application's requirements.**

### Small base images

```text
Alpine (musl libc, ~5MB base) → tiny; occasionally breaks native-compiled deps
Slim   (glibc, Debian-based)  → bigger; safest compatibility
Full                          → only when you truly need the toolchain at runtime
```

We use `-alpine` everywhere (Maven build, JRE runtime, Node build, nginx) because our
stacks are pure-JVM / static-files — no native compilation pitfalls. MySQL has **no**
Alpine variant, so `mysql:8.0` (1.1GB) is the honest minimum there: smallest *compatible* wins over smallest absolute.

### Layer caching (the `COPY` order trick)

```dockerfile
COPY package.json package-lock.json ./   # changes rarely…
RUN npm ci                               # …so this layer is reused for weeks
COPY . .                                 # changes constantly — only rebuilds from here down
RUN npm run build
```

Mental model: Docker caches **each instruction's result** and reuses it while inputs are
identical. Copy the *stable* files first, volatile source last — otherwise one changed
`.ts` file reinstalls 200MB of `node_modules`. Same logic in backend (`pom.xml` before `src/`).

### Multi-stage builds

> 🖼️ See both pipelines side by side in [`docs/multistage-builds-dataflow.html`](docs/multistage-builds-dataflow.html).
>
> ```text
> Builder image (Maven+JDK / Node — fat, discarded)
>                     ↓  compile / build
> COPY ONLY artifacts (app.jar / static files)
>                     ↓
> Small runtime image (JRE / nginx — what actually ships)
> ```

Our proof (§12): the shipped backend holds just the 50MB jar on a 259MB JRE — no Maven,
no source. The frontend holds 300K of static files on nginx — no Node, no `node_modules`.

### Production dependencies

`npm ci` in the build stage installs devDeps too — fine, because that stage is discarded.
What matters is the **final** stage: only production artifacts enter it. Same for Maven:
tests are skipped (`-DskipTests`) and only the packaged jar crosses over.

### Build context

`.dockerignore` (§4) keeps `node_modules/`, `target/`, `.git/` out of the context —
faster uploads, fewer cache busts, no leaked secrets.

### Layer count

Combine *logically related* RUN steps (`apt-get update && install && rm -rf /var/lib/apt/lists/*`
in one layer, or it bloats). But don't golf layers at the cost of readability — a clear
Dockerfile beats a 3-line clever one you'll misread at 2 AM.

### Security checklist

* Never `COPY .env` / never `ENV` secrets into images (`docker history` never forgets).
* Pin base images (`:17-jre-alpine`, `:8.0`) — floating tags rebuild differently tomorrow.
* No unneeded packages in runtime stages.
* Non-root users when practical (noted as future hardening in our backend Dockerfile).

---

## 12. Measure the Optimization (real numbers from THIS project)

Never claim "optimized" without measuring. Commands:

```bash
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}'  # final sizes
docker history IMAGE --format '{{.Size}} {{.CreatedBy}}'     # where the bytes live, per layer
docker image inspect IMAGE | grep -E 'Architecture|Os|Size'  # metadata
docker system df                                             # disk: images, volumes, build cache
```

Measured 2026-09-29 on this machine:

| What | Size | Meaning |
|---|---|---|
| `twelvy1400/frontend:*` | **95.2MB** | nginx:alpine + our files |
| `frontend/dist/frontend/browser` (the app itself) | **300K** | our real code is 0.3% of the image — the rest is the server |
| `twelvy1400/backend:*` | **358MB** | JRE + jar |
| `backend-1.0.0.jar` | **50MB** | the artifact (`COPY` layer shows 52.4MB in history) |
| `eclipse-temurin:17-jre-alpine` (base) | **259MB** | unavoidable JVM cost; 142MB JDK layer + 38.7MB Alpine packages in history |
| `mysql:8.0` | **1.1GB** | no Alpine variant exists — accepted, documented |

How to compare optimizations yourself: build variants and diff —
`docker build -f Dockerfile -t app:after .` vs a deliberately naive one
(single-stage, `COPY . .` first, full `node:22`/`maven` runtime), then compare
`docker images` + `docker history`. The recipe matters more than any single number.

Side observation from `docker system df`: every pushed `:build-N` tag shares layers
(images total 2.3GB, only 34% reclaimable) — tags are cheap pointers, which is exactly
why the `latest` + `build-N` tagging strategy (§15) costs almost nothing.

---

## 13. Common Junior Mistakes (and WHY each hurts)

* **Using `localhost` between containers** → each container's localhost is itself; you get
  `Connection refused` while local runs work. Use service names (§7; browser exception §1).
* **Copying `node_modules`/`target` into the image** → slow contexts, stale/host-OS
  binaries, giant layers. Let the Dockerfile install fresh (§4, §11).
* **Copying `.env` into an image** → secrets baked into layers forever, visible via
  `docker history`, pushed to registries. Runtime env only (§11).
* **Huge base images "to be safe"** (full `node`, full `maven` as runtime) → 3–10× image
  size, slower pulls/deploys, bigger attack surface. Smallest *compatible* wins.
* **No `.dockerignore`** → everything above, plus cache busts on every stray file change.
* **Database without a volume** → first `down` wipes all data. Named volume, always (§8).
* **Confusing `EXPOSE` with port mapping** → `EXPOSE` documents; only `ports:` publishes.
  "Container runs but I can't reach it" = missing `ports:` 9 times out of 10.
* **Thinking `depends_on` = ready** → it orders *starts*. Need `condition: service_healthy`
  + `healthcheck`, or Spring boots into a dead database (§6).
* **Rebuilding everything for one service change** → `docker compose up -d --build backend`
  rebuilds just backend; layer cache handles the rest.
* **Secrets in `docker-compose.yml`** → it's committed to git. Use `${VAR:-default}` +
  gitignored `.env` + injected env (shell env wins) — exactly our file's pattern.
* **`:latest` everywhere without understanding** → `:latest` moves; you can't roll back or
  reproduce. Our strategy: immutable `:build-N` + floating `:latest` (§15).

---

## 14. Mental Model (memorize this)

> 🖼️ **Interactive diagrams (open in a browser):**
> [`docs/docker-stack-architecture.html`](docs/docker-stack-architecture.html) — the system at rest ·
> [`docs/dockerize-process-workflow.html`](docs/dockerize-process-workflow.html) — the process over time ·
> [`docs/multistage-builds-dataflow.html`](docs/multistage-builds-dataflow.html) — how artifacts flow
>
> ```text
> Dockerfile ──builds──► Image ──runs as──► Container
>
> docker-compose.yml ──orchestrates──► Frontend + Backend + Database
>                                              │
>                                   Volume + Network (app-net)
> ```

Complete workflow:

```text
Code
 ↓  write Dockerfile (base → deps → source → artifact → runtime)
docker build
 ↓
Image  (measure: images / history)
 ↓  describe the system (docker-compose.yml)
Docker Compose  (up -d --build)
 ↓
Containers + Network + Volume
 ↓  verify (ps → logs → curl :8080/:4200)
Application running
```

Say it in an interview like this: *"I containerized a 3-tier app: multi-stage builds so
only artifacts ship, Compose with health-gated startup order, service-name networking,
a named volume for MySQL, secrets via environment — then measured: 95MB frontend,
358MB backend."*

---

## 15. Jenkins Preparation (what comes next — no implementation here)

Our Docker design maps 1:1 onto CI/CD stages (already reflected in this repo's `Jenkinsfile`):

```text
Git Push
   ↓  webhook / pollSCM triggers
Jenkins
   ↓  Checkout (git)
Build  (mvnw package · npm ci + ng build — fail fast BEFORE Docker)
   ↓
Test  (skipped here with -DskipTests — add when tests exist)
   ↓
Docker Build  (the Dockerfiles from §2–3)
   ↓
Push  (agent login → tag :build-N + :latest → push → pull-back proof)
   ↓
Deploy  (compose up -d --build + §10 verify loop on THIS host)
```

Docker commands from this tutorial you'll meet again inside Jenkins stages:
`docker build`, `docker tag`, `docker push`/`pull`, `docker login`,
`docker compose up -d --build`, `docker compose ps`/`logs`, `curl` health checks.
Design decisions that pay off in CI: Dockerfiles build from a clean checkout (no host
toolchain needed on agents), Compose defaults let deploys run with zero secrets files,
and immutable `:build-N` tags make every deployment traceable and rollback-able.

---

## 16. Troubleshooting — Real Incidents From THIS Project (tips)

Each entry: **symptom → diagnosis → fix**. These all actually happened here; learn the pattern.

### 16.1 `permission denied ... /var/run/docker.sock` in CI

*Symptom:* every `docker` step fails instantly.
*Diagnosis:* socket is `root:docker` mode 660; check the agent user: `id jenkins` showed
no `docker` group, while `getent group docker` existed. It's host permissions, never Dockerfile code.
*Fix (host, needs sudo):* `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`
(restart required — group membership applies to new processes only). Verify: `id jenkins`.

### 16.2 `Could not find credentials entry with ID '...'` (with silent stage log)

*Symptom:* stage dies at `withCredentials` with an empty step log; real error hides in full Console Output.
*Diagnosis:* entry missing/invisible (wrong store scope — personal page or folder instead of
global), wrong Kind, or pasted ID with invisible whitespace.
*Fix:* global store + exact ID + correct Kind; verify with the Script Console snippet listing
visible credential IDs. **Defensive pattern we added:** `echo` marker *before* `withCredentials`
+ `try/catch` that prints remediation — a stage must never fail silently.

### 16.3 Registry `i/o timeout` on `docker build`/`push`

*Symptom:* `failed to resolve source metadata ... dial tcp ...:443: i/o timeout` (ours: `eclipse-temurin` layer).
*Diagnosis:* transient Hub/ISP blip — proven by an immediate manual `docker pull` succeeding in 6s.
*Fix:* `retry 3` wrapper with backoff around registry-touching commands (added to our
Docker Build + Push stages). Momentary blips cost seconds, not builds.

### 16.4 Silent `docker login` failure

*Symptom:* stage red, no useful output.
*Diagnosis:* secret masking + bare pipes swallow errors.
*Fix:* `if echo "$PASS" | docker login ...; then OK; else` print a checklist (kind? user?
PAT valid+Read/Write?) and `exit 1`. Never `docker login -p <secret>` (leaks via `ps`).

### 16.5 Backend crash-loops against the DB on first deploy

*Symptom:* `Communications link failure`, container restarts repeatedly, then "magically" fine.
*Diagnosis:* container started ≠ app ready (§6) — Spring queried before MySQL accepted connections.
*Fix:* `healthcheck` + `depends_on: {condition: service_healthy}` (already in our compose).

### 16.6 Angular 404 on page refresh (but home page works)

*Symptom:* `/` loads, `/entreprise` refresh → nginx 404.
*Diagnosis:* SPA routes exist only in the browser; nginx looks for a real file.
*Fix:* `try_files $uri $uri/ /index.html;` in `nginx.conf` (§3).

### 16.7 Wrong `COPY` path for the frontend build output

*Symptom:* `COPY failed: no source files found`.
*Diagnosis:* Angular's application builder outputs `dist/frontend/browser/`, not `dist/`.
*Fix:* verify with `ls -R frontend/dist` (or a local `npm run build`) and match the Dockerfile path exactly.

### 16.8 Backend can't reach DB: `localhost` in JDBC URL

*Symptom:* works with local MySQL, `Connection refused` in Compose.
*Diagnosis:* `localhost` inside the container (§7).
*Fix:* override at runtime via `SPRING_DATASOURCE_URL=jdbc:mysql://db:3306/...`, keep
`application.properties` as-is for local dev. Same pattern for any service-to-service URL.

### 16.9 Fresh checkout has no `.env` (CI) — or stale secrets locally

*Symptom:* works on your machine, wrong DB password in CI (silent default) — or vice versa.
*Diagnosis:* `.env` is gitignored by design; Compose precedence is **shell env > `.env` > default**.
*Fix:* Jenkins injects `MYSQL_ROOT_PASSWORD` from its credential (wins automatically);
locally keep `.env` aligned with the volume's original password (changing it needs
`down -v` = data loss, §8). Never commit `.env` (`.env.example` documents the keys).

### 16.10 Token/secret posted in chat, logs, or code

*Symptom:* someone (maybe you) pastes a PAT where others can see it.
*Fix:* treat it as compromised **immediately**: revoke → regenerate → update the *one*
place that stores it (agent login / credential vault). Secrets live in exactly one
secure place each, never in two, never in chat.

### The meta-lesson (interview-worthy)

> Reproduce first, blame code last. Every incident above was solved by the same loop:
> read the exact error → locate which layer it belongs to (host / registry / Compose /
> app) → verify with one command (`id`, `docker pull`, `curl`, `docker logs`) →
> fix that layer only. `docker compose ps` + `docker compose logs` before theories.

---

## 17. SonarQube (code quality) — Next Step

Full guide moved to [`SONARQ.md`](SONARQ.md) (same What → Why → Misuse style).

Short version: `docker-compose.yml` now also runs `sonarqube:lts-community` (:9000)
+ `sonardb: postgres:15-alpine` (SonarQube 9.9+ dropped MySQL, so `app-db` can't be
reused). Scanners (`sonar-maven-plugin` backend + `scanner-cli` frontend, config in
`sonar-project.properties`) send sources + JaCoCo/LCOV coverage; Jenkins stages
`SonarQube Analysis` → `Quality Gate` fail the build on RED before any Docker push.
Host prereq: `sysctl -w vm.max_map_count=262144`. Token via Jenkins `sonar-token`.
