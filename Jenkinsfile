// ============================================================================
// JUNIOR GUIDE: What is this file?
// ----------------------------------------------------------------------------
// This is a Declarative Jenkins Pipeline (Jenkinsfile).
// Jenkins reads it and runs your CI/CD work step by step.
//
// Flow: GitHub -> Jenkins -> SonarQube -> Docker Hub, then redeploy + verify.
//
// Our pipeline has 10 stages:
//   1. Checkout      -> download code from GitHub (credentials, branch main)
//   2. Build         -> compile backend (Maven Wrapper) + frontend (npm)
//   3. SonarQube Analysis -> backend mvn sonar:sonar + frontend scanner-cli
//                       -> sends to http://sonarqube:9000 (see SONARQ.md)
//   4. Quality Gate  -> FAIL pipeline if SonarQube gate is RED (bugs/vulns)
//   5. Docker Build  -> build backend + frontend images, tag :build-N
//   6. Login Docker Hub -> docker login with Jenkins credentials (masked)
//   7. Tag Images    -> also tag both images :latest
//   8. Push Images   -> push :build-N + :latest, then pull back as proof
//   9. Deploy/Verify -> docker compose up -d --build, wait for db healthy,
//                       curl backend :8080 + frontend :4200 (+ sonarqube :9000)
//  10. Push          -> push a build tag back to GitHub (tags only, no loop)
//
// It also "listens" for GitHub pushes via triggers (webhook + polling).
//
// ONE-TIME SETUP:
//   - Jenkins credential `146958092` = GitHub user + PAT (classic, `repo` scope).
//     (Proven working — stages 1 and 8 use it.)
//   - Docker Hub auth (NO Jenkins credential needed): run ONCE on the host:
//       sudo -H -u jenkins bash -c 'docker login -u twelvy1400'
//     Paste a Hub PAT (Read+Write) at the hidden prompt. Stored in the agent
//     user's ~/.docker/config.json only. NEVER paste tokens into code or chat —
//     if one was ever exposed, revoke it on Docker Hub first.
//   - Jenkins credential `mysql-root-password` (Secret text, OPTIONAL) = DB root
//     password. If present, Deploy injects it (masked); if missing, the pipeline
//     falls back to compose defaults with a WARNING instead of failing.
//   - Jenkins credential `sonar-token` (Secret text, REQUIRED for stages 3-4) =
//     SonarQube user token. Create once: SonarQube http://localhost:9000
//     (admin/admin first boot) > My Account > Security > Generate Token >
//     Jenkins > Credentials > Secret text, ID = exactly `sonar-token`.
//     Full guide: SONARQ.md §7. Scanner uses it via -Dsonar.token / SONAR_TOKEN.
//     NEVER paste it into code, chat, or sonar-project.properties.
//   - The agent must have Docker engine + Compose v2, agent user in `docker`.
//   - Docker files must be on GitHub `main` (they are committed in this repo).
// SECRETS POLICY: no literal secret appears in this repo — Hub auth lives with
// the agent OS user, DB password + Sonar token travel via `withCredentials`.
//
// Versions pinned here match your machines (checked 2026-09-22):
//   - Maven 3.9.16        (repo's backend/mvnw; Docker build uses maven:3.9)
//   - JDK 21              (dev default java 21.0.2, Jenkins controller 21.0.12.1)
//   - Node v26.2.0        (dev mise default; system v26.8.1)
//   - npm 11.13.0 expected by frontend/package.json ("packageManager")
//     NOTE: local `npm -v` reports 12.0.2 (anomaly) -> pipeline logs versions
//     and uses `npm ci` so you can see what the Jenkins agent really has.
//   - Docker images: maven:3.9-eclipse-temurin-17-alpine (build),
//     eclipse-temurin:17-jre-alpine (backend runtime), node:22-alpine (build),
//     nginx:alpine (frontend runtime), mysql:8.0 (database),
//     sonarqube:lts-community + postgres:15-alpine (code quality, see SONARQ.md).
//   - SonarQube: server http://localhost:9000 (compose service `sonarqube`),
//     scanner sonarsource/sonar-scanner-cli (frontend) + sonar-maven-plugin
//     3.9.1.2184 (backend) + JaCoCo 0.8.11 coverage. Project key
//     `devops-appgestiondesprojets` (sonar-project.properties at root).
// ============================================================================

pipeline {

    // JUNIOR: Where should this run?
    // `agent any` = run on any available Jenkins agent (your Jenkins server).
    // The agent MUST have Docker + Compose (see setup notes above).
    agent any

    // JUNIOR: Which tools should Jenkins prepare for us?
    // NOTE: we use NO `tools` block on purpose.
    // - Your Jenkins has zero Maven/JDK installs configured and no NodeJS
    //   plugin, so any `tools { maven... }` fails compilation.
    // - Instead: Maven comes from the repo's Maven Wrapper (backend/mvnw,
    //   pinned to 3.9.16), Java 21 from `environment` below, Node from system.
    // Nothing to configure in `Manage Jenkins > Tools`.
    // - Docker images are built with `docker build` (no plugin needed).

    // JUNIOR: How does Jenkins "listen whenever someone pushes"?
    // 1. githubPush() = Jenkins listens for GitHub webhook events.
    //    You must add webhook in GitHub repo settings:
    //    https://github.com/adriansalvadorekomo/DevOps-AppGestionDesProjets/settings/hooks
    //    Payload URL: http://<your-jenkins>:8090/github-webhook/
    //    Event: "Just the push event".
    //    And check "GitHub hook trigger for GITScm polling" in the job config.
    // 2. pollSCM() = fallback: Jenkins checks GitHub every 2 min if webhook fails.
    // NOTE: pushing to Docker Hub never retriggers this pipeline (only GitHub
    // pushes do), and stage 10 pushes Git TAGS only (not `main`) to avoid a loop.
    triggers {
        githubPush()
        pollSCM('H/2 * * * *')
    }

    // JUNIOR: Global variables for the whole pipeline.
    environment {
        // Pin Java 21 (agent default is Java 26 = too new for Spring Boot).
        // This path exists on the server: /usr/lib/jvm/java-21-openjdk (21.0.12.1,
        // same as Jenkins controller). Putting it first in PATH wins over 26.
        JAVA_HOME = '/usr/lib/jvm/java-21-openjdk'
        PATH = "${JAVA_HOME}/bin:${PATH}"
        // Your GitHub repo (found via `git remote -v`).
        GIT_REPO_URL = 'https://github.com/adriansalvadorekomo/DevOps-AppGestionDesProjets.git'
        GIT_BRANCH = 'main'
        // JUNIOR: Jenkins Credentials ID for GitHub.
        // Create it once: Jenkins > Manage Jenkins > Credentials >
        // Add "Username with password" (username = GitHub user, password = GitHub PAT
        // with `repo` scope), ID = exactly `146958092` (your ID).
        GITHUB_CREDENTIALS_ID = '146958092'
        // JUNIOR: Docker Hub destination (namespace must exist on Docker Hub).
        // Images: twelvy1400/backend + twelvy1400/frontend.
        // Auth is agent-level (see ONE-TIME SETUP) — no Hub credential ID here.
        DOCKERHUB_NAMESPACE = 'twelvy1400'
        // Immutable tag per build, e.g. build-42. `:latest` is added in stage 7.
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        // JUNIOR: SonarQube settings (see SONARQ.md).
        // SONAR_HOST_URL = where the server lives. Local compose publishes
        // :9000; on the Jenkins host use http://localhost:9000 (same host runs
        // `docker compose up`). Override per-env via Jenkins global env if needed.
        // Inside a scanner container on app-net, use http://sonarqube:9000.
        SONAR_HOST_URL = 'http://localhost:9000'
        SONAR_PROJECT_KEY = 'devops-appgestiondesprojets'
        // Credential ID holding the SonarQube token (Secret text, see setup above).
        SONAR_CREDENTIALS_ID = 'sonar-token'
    }

    stages {

        // ====================================================================
        // STAGE 1/10: CHECKOUT
        // Goal: download the code from GitHub using your GitHub credentials.
        // ====================================================================
        stage('Checkout') {
            steps {
                // `checkout scm` alone uses the job config; explicit `git`
                // below guarantees the credentialsId is used.
                git branch: "${GIT_BRANCH}",
                    credentialsId: "${GITHUB_CREDENTIALS_ID}",
                    url: "${GIT_REPO_URL}"
            }
        }

        // ====================================================================
        // STAGE 2/10: BUILD
        // Goal: sanity-compile everything WITHOUT Docker (fail fast: a broken
        // jar or npm build should stop the pipeline before any image is built).
        // ====================================================================
        stage('Build') {
            steps {
                // STEP 1: Print versions so juniors can debug "works on my
                // machine but not Jenkins" issues.
                // NOTE: no system `mvn` on this Jenkins — backend builds via
                // Maven Wrapper (backend/mvnw), so we version-check the wrapper.
                sh '''
                    echo "=== Jenkins agent versions ==="
                    java -version
                    node -v
                    npm -v
                    docker --version
                    docker compose version
                '''

                // STEP 2: Build backend (Spring Boot + Maven Wrapper).
                // `dir('backend')` is required because pom.xml lives in
                // backend/, not repo root. Old file ran `mvn` at root -> fail.
                // `./mvnw` downloads Maven 3.9.16 on first run — no Jenkins
                // Tools setup needed. `chmod +x` because git tracks mvnw
                // without the executable bit.
                dir('backend') {
                    sh '''
                        chmod +x mvnw
                        ./mvnw -version
                        ./mvnw clean package -DskipTests
                    '''
                }

                // STEP 3: Build frontend (Angular + npm).
                // `npm ci` = clean install from package-lock.json (CI best
                // practice). Falls back to `npm install` on first run.
                dir('frontend') {
                    sh '''
                        if [ -f package-lock.json ]; then
                          npm ci || npm install
                        else
                          npm install
                        fi
                        npm run build
                    '''
                }

                // STEP 4: Show what we built (helps juniors see outputs).
                sh '''
                    echo "=== Build outputs ==="
                    ls -lh backend/target/*.jar || echo "no jar found"
                    ls -lh frontend/dist || echo "no frontend dist found"
                '''
            }
        }

        // ====================================================================
        // STAGE 3/10: SONARQUBE ANALYSIS
        // Goal: static analysis of backend (Java) + frontend (TypeScript).
        // Scanner sends sources + coverage to SonarQube; server computes
        // bugs/vulnerabilities/code smells/duplication. Next stage enforces gate.
        //
        // JUNIOR What -> Why -> Misuse:
        //   Backend: ./mvnw verify sonar:sonar (sonar-maven-plugin in pom.xml).
        //     `verify` builds classes + JaCoCo XML first; without compiled
        //     classes Java rules are skipped ("java.binaries not found").
        //   Frontend: docker run sonarsource/sonar-scanner-cli with
        //     sonar-project.properties at root (no npm dep needed).
        //   Token: withCredentials `sonar-token` (Secret text, see header).
        //     NEVER hardcode, NEVER echo. Jenkins masks it in logs.
        // Full guide: SONARQ.md §5-§7.
        // ====================================================================
        stage('SonarQube Analysis') {
            steps {
                // STEP 1: Backend analysis (JaCoCo + Sonar in one Maven run).
                // `verify` (not just `package`) so surefire + jacoco:report run
                // and backend/target/site/jacoco/jacoco.xml exists for Sonar.
                withCredentials([string(
                    credentialsId: "${SONAR_CREDENTIALS_ID}",
                    variable: 'SONAR_TOKEN'
                )]) {
                    dir('backend') {
                        sh '''
                            chmod +x mvnw
                            ./mvnw -B verify sonar:sonar \
                              -Dsonar.projectKey="$SONAR_PROJECT_KEY" \
                              -Dsonar.host.url="$SONAR_HOST_URL" \
                              -Dsonar.token="$SONAR_TOKEN"
                        '''
                    }
                    // STEP 2: Frontend + full-repo analysis via scanner-cli.
                    // Root sonar-project.properties already covers both modules;
                    // backend re-send is skipped here via -Dsonar.sources override
                    // so Java is not double-counted: frontend-only pass.
                    // Retry wrapper: Hub pull can hit transient i/o timeouts.
                    sh '''
                        retry() {
                          tries=$1; shift
                          n=1
                          while [ $n -le $tries ]; do
                            echo "--- attempt $n/$tries: $* ---"
                            if "$@"; then return 0; fi
                            n=$((n + 1))
                            if [ $n -le $tries ]; then echo "transient failure, sleeping 15s..."; sleep 15; fi
                          done
                          return 1
                        }
                        echo "=== SonarQube: frontend scan (scanner-cli) ==="
                        retry 3 docker run --rm \
                          -v "$PWD:/usr/src" -w /usr/src \
                          -e SONAR_HOST_URL="$SONAR_HOST_URL" \
                          -e SONAR_TOKEN="$SONAR_TOKEN" \
                          sonarsource/sonar-scanner-cli \
                          -Dsonar.projectKey="$SONAR_PROJECT_KEY-frontend" \
                          -Dsonar.projectName="DevOps-AppGestionDesProjets-frontend" \
                          -Dsonar.sources=frontend/src \
                          -Dsonar.tests=frontend/src \
                          -Dsonar.test.inclusions="**/*.spec.ts" \
                          -Dsonar.exclusions="**/node_modules/**,**/dist/**,**/.angular/**,**/*.spec.ts" \
                          -Dsonar.host.url="$SONAR_HOST_URL" \
                          -Dsonar.token="$SONAR_TOKEN"
                        echo "=== SonarQube analysis submitted: $SONAR_HOST_URL/dashboard?id=$SONAR_PROJECT_KEY ==="
                    '''
                }
            }
        }

        // ====================================================================
        // STAGE 4/10: QUALITY GATE
        // Goal: FAIL the pipeline if SonarQube Quality Gate is RED.
        // WHY NOT skip? Without this, analysis is decoration: buggy/vulnerable
        // code still ships to Docker Hub. Gate = bugs, vulnerabilities, coverage.
        // JUNIOR: polls api/qualitygates/project_status (no plugin needed).
        // Needs SonarQube Scanner plugin? No — pure curl, same as Deploy verify.
        // Tune gate in SonarQube UI > Quality Gates; default "Sonar way" used.
        // ====================================================================
        stage('Quality Gate') {
            steps {
                withCredentials([string(
                    credentialsId: "${SONAR_CREDENTIALS_ID}",
                    variable: 'SONAR_TOKEN'
                )]) {
                    sh '''
                        echo "=== SonarQube Quality Gate: $SONAR_PROJECT_KEY ==="
                        # SonarQube Compute Engine needs ~30-120s after analysis.
                        for i in $(seq 1 20); do
                          STATUS=$(curl -s -m 10 -u "$SONAR_TOKEN:" \
                            "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$SONAR_PROJECT_KEY" \
                            | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4 || echo UNKNOWN)
                          echo "gate status: $STATUS (attempt $i/20)"
                          if [ "$STATUS" = "OK" ]; then echo "Quality Gate PASSED."; exit 0; fi
                          if [ "$STATUS" = "ERROR" ]; then echo "ERROR: Quality Gate FAILED. Open $SONAR_HOST_URL/dashboard?id=$SONAR_PROJECT_KEY"; exit 1; fi
                          sleep 15
                        done
                        echo "WARNING: Quality Gate still UNKNOWN after 5 min (server slow or first analysis)."
                        echo "Check $SONAR_HOST_URL/dashboard?id=$SONAR_PROJECT_KEY manually."
                        exit 1
                    '''
                }
            }
        }

        // ====================================================================
        // STAGE 5/10: DOCKER BUILD
        // Goal: build both production images, tagged immutably (:build-N).
        // Dockerfiles (already validated locally):
        //   backend:  maven:3.9-eclipse-temurin-17-alpine -> eclipse-temurin:17-jre-alpine
        //   frontend: node:22-alpine -> nginx:alpine (serves dist/frontend/browser)
        // ====================================================================
        // NOTE: registry pulls go through the Docker daemon and can hit
        // transient Hub timeouts (e.g. `dial tcp ...:443: i/o timeout` on
        // registry-1.docker.io). Every network-touching docker command below
        // is retried — a momentary blip must not fail the whole pipeline.
        // ====================================================================
        stage('Docker Build') {
            steps {
                sh '''
                    retry() {
                      tries=$1; shift
                      n=1
                      while [ $n -le $tries ]; do
                        echo "--- attempt $n/$tries: $* ---"
                        if "$@"; then return 0; fi
                        n=$((n + 1))
                        if [ $n -le $tries ]; then echo "transient failure, sleeping 15s..."; sleep 15; fi
                      done
                      return 1
                    }
                    echo "=== Building backend image ==="
                    retry 3 docker build ./backend -t "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG"
                    docker image inspect "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG" > /dev/null
                    echo "=== Building frontend image ==="
                    retry 3 docker build ./frontend -t "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG"
                    docker image inspect "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG" > /dev/null
                    echo "=== Built images ==="
                    docker images | grep "$DOCKERHUB_NAMESPACE" || true
                '''
            }
        }

        // ====================================================================
        // STAGE 6/10: LOGIN DOCKER HUB (agent-level auth check)
        // Goal: confirm the agent OS user is logged in to Docker Hub.
        // WHY NOT withCredentials? The `dockerhub-credentials` entry is not
        // resolvable on this Jenkins ("Could not find credentials entry"),
        // which blocked every build. Instead, auth lives with the agent user
        // (~/.docker/config.json), created ONCE on the host — no secret ever
        // touches the repo, the pipeline, or the build logs:
        //   sudo -H -u jenkins bash -c 'docker login -u twelvy1400'
        // (paste the Hub PAT at the hidden prompt). This stage only VERIFIES
        // that auth exists and fails with the exact remediation if not.
        // NOTE: `post.always` intentionally does NOT `docker logout`, or it
        // would wipe this agent-level auth after every build.
        // ====================================================================
        stage('Login Docker Hub') {
            steps {
                echo '=== Stage: Login Docker Hub (agent-level auth check) ==='
                sh '''
                    CFG="$HOME/.docker/config.json"
                    echo "agent user: '$(whoami)', HOME: '$HOME'"
                    if [ ! -f "$CFG" ]; then
                      echo "ERROR: no Docker client config at $CFG."
                      echo "The agent user '$(whoami)' never logged in (or it was wiped)."
                      echo "One-time fix ON THE JENKINS HOST (secret never touches repo/logs):"
                      echo "  sudo -H -u jenkins bash -c 'docker login -u twelvy1400'"
                      echo "Paste the Hub PAT (Read+Write) at the hidden prompt, then rebuild."
                      exit 1
                    fi
                    echo "config dir listing (names only, no secrets):"
                    ls -l "$HOME/.docker/" || true
                    if grep -q '"auth"' "$CFG" 2>/dev/null; then
                      echo "Docker Hub auth entry present."
                      docker info 2>/dev/null | grep -i 'username' || true
                      echo "=== Docker Hub login OK ==="
                    else
                      echo "ERROR: $CFG exists but holds NO stored credential (empty file or wiped by 'docker logout')."
                      echo "Re-login ON THE JENKINS HOST:"
                      echo "  sudo -H -u jenkins bash -c 'docker login -u twelvy1400'"
                      echo "Paste the Hub PAT (Read+Write) at the hidden prompt, then rebuild."
                      exit 1
                    fi
                '''
            }
        }

        // ====================================================================
        // STAGE 7/10: TAG IMAGES
        // Goal: add the floating `:latest` tag on top of the immutable
        // `:build-N` tag, so compose/manual runs can track latest while every
        // build stays rollback-able via its number.
        // ====================================================================
        stage('Tag Images') {
            steps {
                sh '''
                    docker tag "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG" "$DOCKERHUB_NAMESPACE/backend:latest"
                    docker tag "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG" "$DOCKERHUB_NAMESPACE/frontend:latest"
                    echo "=== Tagged images ==="
                    docker images | grep "$DOCKERHUB_NAMESPACE" || true
                '''
            }
        }

        // ====================================================================
        // STAGE 8/10: PUSH IMAGES
        // Goal: publish all 4 tags to Docker Hub, then pull the immutable tags
        // back as proof the registry really has them (cheap, fails loudly if
        // the push silently broke).
//   Result on Docker Hub:
//     twelvy1400/backend:build-N + :latest
//     twelvy1400/frontend:build-N + :latest
        // ====================================================================
        stage('Push Images') {
            steps {
                sh '''
                    retry() {
                      tries=$1; shift
                      n=1
                      while [ $n -le $tries ]; do
                        echo "--- attempt $n/$tries: $* ---"
                        if "$@"; then return 0; fi
                        n=$((n + 1))
                        if [ $n -le $tries ]; then echo "transient failure, sleeping 15s..."; sleep 15; fi
                      done
                      return 1
                    }
                    echo "=== Pushing backend ==="
                    retry 3 docker push "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG"
                    retry 3 docker push "$DOCKERHUB_NAMESPACE/backend:latest"
                    echo "=== Pushing frontend ==="
                    retry 3 docker push "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG"
                    retry 3 docker push "$DOCKERHUB_NAMESPACE/frontend:latest"
                    echo "=== Registry proof: pull immutable tags back ==="
                    retry 3 docker pull "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG"
                    retry 3 docker pull "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG"
                '''
            }
        }

        // ====================================================================
        // STAGE 9/10: DEPLOY / VERIFY
        // Goal: redeploy the full stack on this host from the repo state and
        // prove it works end to end:
        //   db healthy -> backend answers :8080 -> frontend serves :4200.
        // docker-compose.yml already wires:
        //   backend depends_on db (service_healthy), frontend depends_on backend,
        //   named volume mysql_data, dedicated network app-net, no published
        //   DB port, secrets via ${VAR:-default}.
        // SECRET FLOW: `.env` is gitignored so the agent has none — the DB
        // password comes from the `mysql-root-password` credential when it
        // resolves (injected as shell env; shell env beats compose defaults
        // and Jenkins masks it). If that credential is missing/unresolvable,
        // the pipeline still runs `scripts/deploy-verify.sh` WITHOUT it and
        // compose falls back to its dev default ('root') with a loud WARNING
        // instead of a cryptic failure. The script itself never echoes secrets.
        // ====================================================================
        stage('Deploy / Verify') {
            steps {
                script {
                    try {
                        // NOTE: literal ID (no ${VAR} interpolation) on purpose.
                        withCredentials([string(
                            credentialsId: 'mysql-root-password',
                            variable: 'MYSQL_ROOT_PASSWORD'
                        )]) {
                            echo 'DB password: Jenkins credential.'
                            sh 'bash scripts/deploy-verify.sh'
                        }
                    } catch (err) {
                        def msg = err.getMessage() ?: ''
                        if (msg.contains('exit code')) { throw err } // deploy script already explained itself
                        echo "WARNING: credential 'mysql-root-password' unusable (${msg})."
                        echo "Falling back to compose defaults (dev password 'root'). Create/fix the credential to silence this."
                        sh 'bash scripts/deploy-verify.sh'
                    }
                }
            }
        }

        // ====================================================================
        // STAGE 10/10: PUSH (back to GitHub)
        // Goal: tag this successful build and push the TAG to GitHub.
        // We push TAGS ONLY (not the `main` branch) to avoid an infinite loop:
        // pushing `main` would trigger githubPush() again -> new build -> push...
        // (Docker Hub pushes never trigger this pipeline — only GitHub does.)
        // ====================================================================
        stage('Push') {
            steps {
                // `withCredentials` safely injects GitHub user + token as
                // env vars. Jenkins masks them in logs. Never hardcode tokens!
                withCredentials([usernamePassword(
                    credentialsId: "${GITHUB_CREDENTIALS_ID}",
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_TOKEN'
                )]) {
                    sh '''
                        echo "=== Push stage: tagging build ==="
                        git config user.email "jenkins@localhost"
                        git config user.name "jenkins-ci"

                        # Create a tag like build-42 for this Jenkins build number.
                        # `|| true` = do not fail if tag already exists on rebuild.
                        git tag -a "build-${BUILD_NUMBER}" -m "Jenkins build ${BUILD_NUMBER}" || true

                        # Authenticate with the PAT as password.
                        # GitHub requires the literal user `x-access-token` for
                        # token auth (account passwords were removed in 2021,
                        # so `user:PAT` fails with "Password authentication
                        # is not supported" if the stored secret is not a PAT).
                        git remote set-url origin "https://x-access-token:${GIT_TOKEN}@github.com/adriansalvadorekomo/DevOps-AppGestionDesProjets.git"

                        # Quick auth check with a clear junior-friendly error.
                        if ! git ls-remote origin >/dev/null 2>&1; then
                          echo "ERROR: GitHub rejected the token in credentials '146958092'."
                          echo "Fix: GitHub > Settings > Developer settings > Personal access tokens >"
                          echo "generate a CLASSIC token with 'repo' scope, then Jenkins >"
                          echo "Manage Jenkins > Credentials > 146958092 > Update (paste token as password)."
                          exit 1
                        fi

                        # Push ONLY tags, not branches (avoids retrigger loop).
                        git push origin --tags
                    '''
                }
            }
        }
    }

    // JUNIOR: What happens after all stages, success or failure?
    post {
        always {
            echo 'Pipeline finished.'
            // Archive the backend jar + coverage so you can download from Jenkins UI.
            archiveArtifacts artifacts: 'backend/target/*.jar', allowEmptyArchive: true, fingerprint: true
            archiveArtifacts artifacts: 'backend/target/site/jacoco/*.xml,backend/target/surefire-reports/*.txt', allowEmptyArchive: true
            // NOTE: no `docker logout` here on purpose — Hub auth lives with
            // the agent user (see Login stage); logging out would break next build.
        }
        success {
            echo 'Checkout + Build + SonarQube Analysis + Quality Gate + Docker Build + Login + Tag + Push + Deploy/Verify + Push succeeded!'
        }
        failure {
            echo 'Pipeline failed - check stage logs above.'
            // Dump recent stack logs to pinpoint db/backend/frontend/sonarqube failures.
            sh 'docker compose logs --tail=50 || true'
        }
    }
}
