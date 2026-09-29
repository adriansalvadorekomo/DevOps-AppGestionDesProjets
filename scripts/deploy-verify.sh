#!/usr/bin/env bash
# Deploy + verify the full stack: db healthy -> backend :8080 -> frontend :4200.
#
# DB password resolution (Compose precedence: shell env > .env file > default):
#   - Local dev:  reads `.env` (gitignored) or falls back to compose defaults.
#   - Jenkins:    stage 'Deploy / Verify' injects MYSQL_ROOT_PASSWORD from the
#                 `mysql-root-password` credential; if that credential is
#                 missing, the pipeline runs this script WITHOUT it and the
#                 same compose defaults apply (dev password 'root').
# Never echo secrets. Exit non-zero on any verification failure.
set -u

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
