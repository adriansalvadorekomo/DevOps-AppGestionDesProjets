#!/usr/bin/env bash
# Wait for the SonarQube quality gate of every project key given; fail if any is red.
#   SONAR_HOST_URL=http://localhost:9000 SONAR_TOKEN=... scripts/quality-gate.sh KEY [KEY...]
# Jenkins runs it for the backend and the frontend projects (stage "Quality Gate").
set -u
: "${SONAR_HOST_URL:?SONAR_HOST_URL is required}" "${SONAR_TOKEN:?SONAR_TOKEN is required}"
[ "$#" -ge 1 ] || { echo "usage: $0 PROJECT_KEY [PROJECT_KEY...]"; exit 2; }

gate() {
  key=$1
  # The Compute Engine needs 30-120 s after an analysis before the status exists.
  for i in $(seq 1 20); do
    status=$(curl -s -m 10 -u "$SONAR_TOKEN:" \
      "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$key" \
      | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "[$key] gate status: ${status:-UNKNOWN} (attempt $i/20)"
    case "$status" in
      OK) echo "[$key] quality gate PASSED"; return 0 ;;
      ERROR) echo "[$key] quality gate FAILED: $SONAR_HOST_URL/dashboard?id=$key"; return 1 ;;
    esac
    sleep 15
  done
  echo "[$key] quality gate still unknown after 5 minutes: $SONAR_HOST_URL/dashboard?id=$key"
  return 1
}

failed=0
for key in "$@"; do
  gate "$key" || failed=1
done
exit "$failed"
