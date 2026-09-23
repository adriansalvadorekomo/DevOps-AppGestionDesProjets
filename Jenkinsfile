// ============================================================================
// JUNIOR GUIDE: What is this file?
// ----------------------------------------------------------------------------
// This is a Declarative Jenkins Pipeline (Jenkinsfile).
// Jenkins reads it and runs your CI/CD work step by step.
//
// Our pipeline has ONLY 2 stages:
//   1. Build -> download code from GitHub, compile backend + frontend
//   2. Push  -> push a build tag back to GitHub
//
// It also "listens" for GitHub pushes via triggers (webhook + polling).
//
// Versions pinned here match your machines (checked 2026-09-22):
//   - Maven 3.9.16        (local `mvn -version` + system Maven)
//   - JDK 21              (dev default java 21.0.2, Jenkins controller 21.0.12.1)
//   - Node v26.2.0        (dev mise default; system v26.8.1)
//   - npm 11.13.0 expected by frontend/package.json ("packageManager")
//     NOTE: local `npm -v` reports 12.0.2 (anomaly) -> pipeline logs versions
//     and uses `npm ci` so you can see what the Jenkins agent really has.
// ============================================================================

pipeline {

    // JUNIOR: Where should this run?
    // `agent any` = run on any available Jenkins agent (your Jenkins server).
    agent any

    // JUNIOR: Which tools should Jenkins prepare for us?
    // NOTE: we use NO `tools` block on purpose.
    // - Your Jenkins has zero Maven/JDK installs configured and no NodeJS
    //   plugin, so any `tools { maven... }` fails compilation.
    // - Instead: Maven comes from the repo's Maven Wrapper (backend/mvnw,
    //   pinned to 3.9.16), Java 21 from `environment` below, Node from system.
    // Nothing to configure in `Manage Jenkins > Tools`.

    // JUNIOR: How does Jenkins "listen whenever someone pushes"?
    // 1. githubPush() = Jenkins listens for GitHub webhook events.
    //    You must add webhook in GitHub repo settings:
    //    https://github.com/adriansalvadorekomo/DevOps-AppGestionDesProjets/settings/hooks
    //    Payload URL: http://<your-jenkins>:8090/github-webhook/
    //    Event: "Just the push event".
    //    And check "GitHub hook trigger for GITScm polling" in the job config.
    // 2. pollSCM() = fallback: Jenkins checks GitHub every 2 min if webhook fails.
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
    }

    stages {

        // ====================================================================
        // STAGE 1/2: BUILD
        // Goal: get code with GitHub credentials, then compile everything.
        // ====================================================================
        stage('Build') {
            steps {
                // STEP 1: Checkout code USING your GitHub credentials.
                // `checkout scm` alone uses the job config; explicit `git`
                // below guarantees the credentialsId is used.
                git branch: "${GIT_BRANCH}",
                    credentialsId: "${GITHUB_CREDENTIALS_ID}",
                    url: "${GIT_REPO_URL}"

                // STEP 2: Print versions so juniors can debug "works on my
                // machine but not Jenkins" issues.
                // NOTE: no system `mvn` on this Jenkins — backend builds via
                // Maven Wrapper (backend/mvnw), so we version-check the wrapper.
                sh '''
                    echo "=== Jenkins agent versions ==="
                    java -version
                    node -v
                    npm -v
                '''

                // STEP 3: Build backend (Spring Boot + Maven Wrapper).
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

                // STEP 4: Build frontend (Angular + npm).
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

                // STEP 5: Show what we built (helps juniors see outputs).
                sh '''
                    echo "=== Build outputs ==="
                    ls -lh backend/target/*.jar || echo "no jar found"
                    ls -lh frontend/dist || echo "no frontend dist found"
                '''
            }
        }

        // ====================================================================
        // STAGE 2/2: PUSH (back to GitHub)
        // Goal: tag this successful build and push the TAG to GitHub.
        // We push TAGS ONLY (not the `main` branch) to avoid an infinite loop:
        // pushing `main` would trigger githubPush() again -> new build -> push...
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
        }
        success {
            echo 'Build + Push succeeded!'
        }
        failure {
            echo 'Build or Push failed - check stage logs above.'
        }
    }
}
