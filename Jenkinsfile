// ============================================================================
// JUNIOR GUIDE: What is this file?
// ----------------------------------------------------------------------------
// This is a Declarative Jenkins Pipeline (Jenkinsfile).
// Jenkins reads it and runs your CI/CD work step by step.
//
// Flow: GitHub -> Jenkins -> Docker Hub, then redeploy + verify on the host.
//
// Our pipeline has 8 stages:
//   1. Checkout      -> download code from GitHub (credentials, branch main)
//   2. Build         -> compile backend (Maven Wrapper) + frontend (npm)
//   3. Docker Build  -> build backend + frontend images, tag :build-N
//   4. Login Docker Hub -> docker login with Jenkins credentials (masked)
//   5. Tag Images    -> also tag both images :latest
//   6. Push Images   -> push :build-N + :latest, then pull back as proof
//   7. Deploy/Verify -> docker compose up -d --build, wait for db healthy,
//                       curl backend :8080 + frontend :4200
//   8. Push          -> push a build tag back to GitHub (tags only, no loop)
//
// It also "listens" for GitHub pushes via triggers (webhook + polling).
//
// ONE-TIME SETUP (Jenkins UI):
//   - Credential `146958092` = GitHub user + PAT (classic, `repo` scope).
//   - Credential `dockerhub-credentials` = Docker Hub user `twelvy1400` +
//     PAT (Read + Write scope). NEVER paste tokens into code or chat — if a
//     token was ever exposed, revoke it on Docker Hub first, then store only
//     the fresh value here.
//     Create: Manage Jenkins > Credentials > Add "Username with password".
//   - Credential `mysql-root-password` = DB root password (Secret text).
//     Must match the password the mysql_data volume was initialized with
//     (local `.env` uses the same value; `.env` itself is gitignored and
//     never reaches the agent — this credential fills the gap).
//   - The agent must have Docker engine + Compose v2, agent user in `docker`.
//   - Docker files must be on GitHub `main` (they are committed in this repo).
// SECRETS POLICY: no literal secret appears in this file — only credential
// IDs. All secrets travel via `withCredentials` (Jenkins masks them in logs).
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
//     nginx:alpine (frontend runtime), mysql:8.0 (database).
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
    // pushes do), and stage 8 pushes Git TAGS only (not `main`) to avoid a loop.
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
        DOCKERHUB_NAMESPACE = 'twelvy1400'
        // JUNIOR: Jenkins Credentials ID for Docker Hub.
        // Create it once: Jenkins > Manage Jenkins > Credentials >
        // Add "Username with password" (username = twelvy1400,
        // password = Docker Hub PAT with Read+Write scope),
        // ID = exactly `dockerhub-credentials`.
        DOCKERHUB_CREDENTIALS_ID = 'dockerhub-credentials'
        // JUNIOR: Jenkins Credentials ID for the MySQL root password.
        // Create it once: Jenkins > Manage Jenkins > Credentials >
        // Add "Secret text" (secret = DB root password, same value as local
        // `.env`), ID = exactly `mysql-root-password`.
        // Why: `.env` is gitignored, so a fresh agent checkout has no DB
        // password — Compose would silently fall back to its default. This
        // credential injects the real one as an env var (shell env beats
        // compose defaults), keeping the secret out of the repo AND the logs.
        MYSQL_ROOT_PASSWORD_CREDENTIALS_ID = 'mysql-root-password'
        // Immutable tag per build, e.g. build-42. `:latest` is added in stage 5.
        IMAGE_TAG = "build-${BUILD_NUMBER}"
    }

    stages {

        // ====================================================================
        // STAGE 1/8: CHECKOUT
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
        // STAGE 2/8: BUILD
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
        // STAGE 3/8: DOCKER BUILD
        // Goal: build both production images, tagged immutably (:build-N).
        // Dockerfiles (already validated locally):
        //   backend:  maven:3.9-eclipse-temurin-17-alpine -> eclipse-temurin:17-jre-alpine
        //   frontend: node:22-alpine -> nginx:alpine (serves dist/frontend/browser)
        // ====================================================================
        stage('Docker Build') {
            steps {
                sh '''
                    echo "=== Building backend image ==="
                    docker build ./backend -t "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG"
                    docker image inspect "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG" > /dev/null
                    echo "=== Building frontend image ==="
                    docker build ./frontend -t "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG"
                    docker image inspect "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG" > /dev/null
                    echo "=== Built images ==="
                    docker images | grep "$DOCKERHUB_NAMESPACE" || true
                '''
            }
        }

        // ====================================================================
        // STAGE 4/8: LOGIN DOCKER HUB
        // Goal: authenticate to Docker Hub WITHOUT leaking the secret.
        // `--password-stdin` keeps the PAT out of `ps` output; Jenkins masks
        // DH_PASS in logs. Never `docker login -p <secret>` and never echo it.
        // ====================================================================
        stage('Login Docker Hub') {
            steps {
                echo '=== Stage: Login Docker Hub (credential ID: dockerhub-credentials) ==='
                // try/catch: if `withCredentials` itself throws (entry missing
                // / invisible / wrong kind), the stage would otherwise die with
                // the error buried in Console Output. Catch it and print the
                // exact remediation. `sh` failures (exit code) already explain
                // themselves, so those are rethrown untouched.
                script {
                    try {
                // `withCredentials` safely injects Docker Hub user + token as
                // env vars. Jenkins masks them in logs. Never hardcode tokens!
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh '''
                        if echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin; then
                          echo "=== Docker Hub login OK ==="
                        else
                          echo "ERROR: 'docker login' failed (exit $?)."
                          echo "Checklist:"
                          echo "  1. Jenkins credential 'dockerhub-credentials' must be kind 'Username with password', username 'twelvy1400'."
                          echo "  2. Its password must be a VALID Docker Hub PAT (Read+Write). A revoked/expired/Read-only token fails here."
                          echo "  3. Regenerate the PAT on Docker Hub > Account Settings > Security, update the credential, rebuild."
                          exit 1
                        fi
                    '''
                }
                    } catch (err) {
                        def msg = err.getMessage() ?: ''
                        if (msg.contains('exit code')) { throw err }
                        echo "ERROR: Jenkins could not load credential 'dockerhub-credentials'."
                        echo "Jenkins said: ${msg}"
                        echo "Remediation (pick the one that matches):"
                        echo "  A. NOT FOUND: create it at Dashboard > Manage Jenkins > Credentials > 'Stores scoped to Jenkins' > global > Add Credentials (Kind 'Username with password', ID exactly 'dockerhub-credentials')."
                        echo "     WRONG PLACES that builds cannot see: your personal page (top-right username > Credentials), or inside a Folder's Credentials when the job is at root."
                        echo "  B. WRONG KIND: the Kind column must read 'Username with password'. A 'Secret text' entry with the same ID is rejected by this stage — recreate it with the right kind."
                        throw err
                    }
                }
            }
        }

        // ====================================================================
        // STAGE 5/8: TAG IMAGES
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
        // STAGE 6/8: PUSH IMAGES
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
                    echo "=== Pushing backend ==="
                    docker push "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG"
                    docker push "$DOCKERHUB_NAMESPACE/backend:latest"
                    echo "=== Pushing frontend ==="
                    docker push "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG"
                    docker push "$DOCKERHUB_NAMESPACE/frontend:latest"
                    echo "=== Registry proof: pull immutable tags back ==="
                    docker pull "$DOCKERHUB_NAMESPACE/backend:$IMAGE_TAG"
                    docker pull "$DOCKERHUB_NAMESPACE/frontend:$IMAGE_TAG"
                '''
            }
        }

        // ====================================================================
        // STAGE 7/8: DEPLOY / VERIFY
        // Goal: redeploy the full stack on this host from the repo state and
        // prove it works end to end:
        //   db healthy -> backend answers :8080 -> frontend serves :4200.
        // docker-compose.yml already wires:
        //   backend depends_on db (service_healthy), frontend depends_on backend,
        //   named volume mysql_data, dedicated network app-net, no published
        //   DB port, secrets via ${VAR:-default}.
        // SECRET FLOW: `.env` is gitignored so the agent has none — the DB
        // password below comes from the `mysql-root-password` credential,
        // injected as a shell env var. Compose resolves shell env BEFORE
        // `.env`/defaults, so both the containers AND the mysqladmin
        // healthcheck get the real password, and Jenkins masks it in logs.
        // ====================================================================
        stage('Deploy / Verify') {
            steps {
                // `withCredentials` (string binding) exposes the DB password
                // ONLY as a masked env var for these steps. Never echo it.
                // NOTE: literal ID (no ${VAR} interpolation) on purpose.
                withCredentials([string(
                    credentialsId: 'mysql-root-password',
                    variable: 'MYSQL_ROOT_PASSWORD'
                )]) {
                sh '''
                    echo "=== Deploy: (re)create full stack ==="
                    docker compose up -d --build
                    docker compose ps

                    echo "=== Verify 1/3: db becomes healthy (max ~120s) ==="
                    for i in $(seq 1 24); do
                      STATUS=$(docker inspect app-db --format '{{.State.Health.Status}}')
                      echo "db health: $STATUS (attempt $i/24)"
                      if [ "$STATUS" = "healthy" ]; then break; fi
                      sleep 5
                    done
                    STATUS=$(docker inspect app-db --format '{{.State.Health.Status}}')
                    if [ "$STATUS" != "healthy" ]; then
                      echo "ERROR: db never became healthy."
                      docker compose logs --tail=50 db || true
                      exit 1
                    fi

                    echo "=== Verify 2/3: backend answers on :8080 (max ~120s) ==="
                    for i in $(seq 1 24); do
                      CODE=$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://localhost:8080/entreprise/all || echo 000)
                      echo "backend /entreprise/all: HTTP $CODE (attempt $i/24)"
                      if [ "$CODE" = "200" ]; then break; fi
                      sleep 5
                    done
                    CODE=$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://localhost:8080/entreprise/all || echo 000)
                    if [ "$CODE" != "200" ]; then
                      echo "ERROR: backend never answered 200."
                      docker compose logs --tail=50 backend || true
                      exit 1
                    fi
                    curl -s -m 10 http://localhost:8080/entreprise/all
                    echo

                    echo "=== Verify 3/3: frontend serves on :4200 (incl. SPA fallback) ==="
                    CODE=$(curl -s -m 10 -o /dev/null -w '%{http_code}' http://localhost:4200/ || echo 000)
                    echo "frontend /: HTTP $CODE"
                    if [ "$CODE" != "200" ]; then
                      echo "ERROR: frontend did not serve 200."
                      docker compose logs --tail=50 frontend || true
                      exit 1
                    fi
                    CODE=$(curl -s -m 10 -o /dev/null -w '%{http_code}' http://localhost:4200/entreprise || echo 000)
                    echo "frontend /entreprise (SPA fallback): HTTP $CODE"
                    if [ "$CODE" != "200" ]; then
                      echo "ERROR: SPA fallback route did not serve 200."
                      docker compose logs --tail=50 frontend || true
                      exit 1
                    fi

                    echo "=== Stack status ==="
                    docker compose ps
                '''
                } // withCredentials: MYSQL_ROOT_PASSWORD leaves scope here
            }
        }

        // ====================================================================
        // STAGE 8/8: PUSH (back to GitHub)
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
            // Archive the backend jar so you can download it from Jenkins UI.
            archiveArtifacts artifacts: 'backend/target/*.jar', allowEmptyArchive: true, fingerprint: true
            // Always log out so no registry session lingers on a shared agent.
            sh 'docker logout || true'
        }
        success {
            echo 'Checkout + Build + Docker Build + Login + Tag + Push + Deploy/Verify + Push succeeded!'
        }
        failure {
            echo 'Pipeline failed - check stage logs above.'
            // Dump recent stack logs to pinpoint db/backend/frontend failures.
            sh 'docker compose logs --tail=50 || true'
        }
    }
}
