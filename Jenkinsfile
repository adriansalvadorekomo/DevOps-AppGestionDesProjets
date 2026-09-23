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
    // IMPORTANT: These NAMES must exactly match:
    //   Jenkins > Manage Jenkins > Tools > Maven / JDK / NodeJS
    // If a name is wrong, the build fails with "tool not found".
    tools {
        maven 'Maven 3.9.16'    // matches your local Maven 3.9.16
        jdk 'openjdk 21.0.2'    // matches dev JDK 21.0.2; controller runs 21.0.12.1 (compatible).
                                // Backend pom.xml needs Java 17+, so JDK 21 is fine.
        nodejs 'NodeJS-26.2.0'  // must match your Jenkins NodeJS install name.
                                // Create it in Jenkins Tools if missing, version 26.2.0
                                // to mirror dev. Angular 22 officially supports
                                // Node 20+, so Node 20/22 LTS also works and is safer.
    }

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
                // machine but not Jenkins" issues. Compare with local:
                // java 21.0.2, mvn 3.9.16, node v26.2.0.
                sh '''
                    echo "=== Jenkins agent versions ==="
                    java -version
                    mvn -version
                    node -v
                    npm -v
                '''

                // STEP 3: Build backend (Spring Boot + Maven).
                // `dir('backend')` is required because pom.xml lives in
                // backend/, not repo root. Old file ran `mvn` at root -> fail.
                dir('backend') {
                    sh 'mvn clean package -DskipTests'
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

                        # Rewrite origin URL with token so `git push` is authenticated.
                        git remote set-url origin "https://${GIT_USER}:${GIT_TOKEN}@github.com/adriansalvadorekomo/DevOps-AppGestionDesProjets.git"

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
