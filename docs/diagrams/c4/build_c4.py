#!/usr/bin/env python3
"""Build the C4 diagrams for Gestion des projets (context, containers, backend components, Kubernetes).

    python docs/diagrams/c4/build_c4.py            # SVG + PNG (needs Chromium)
    python docs/diagrams/c4/build_c4.py --svg-only

Every element comes from the code at the commit it ships with: docker-compose.yml
(services, ports, volumes, profiles), Jenkinsfile (stages), monitoring/ (Prometheus,
Grafana), k8s/ (Deployments, Services) and backend/src (controllers, services,
repositories). Drawing kit: c4lib.py (shared with the other project diagrams).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c4lib import MONO, Canvas, build  # noqa: E402

STACK = ["springboot", "angular", "mysql", "jenkins", "sonarqubeserver", "prometheus", "grafana", "kubernetes"]
W = 2200


def context(theme: str) -> str:
    c = Canvas(W, 1180, theme)
    t = c.t
    c.header("C4 MODEL  ·  LEVEL 1  ·  SYSTEM CONTEXT", "Gestion des projets",
             "A small CRUD app, delivered and watched like a production service.", STACK)
    c.person(80, 230, 380, 150, "Developer", ["Pushes code, reads the quality", "gate and the dashboards"])
    c.person(80, 720, 380, 150, "Project manager", ["Manages companies, teams,", "projects and their details"])

    c.card(700, 400, 760, 520, t["ana"], "SOFTWARE SYSTEM", "Gestion des projets", "Spring Boot · Angular · MySQL",
           ["CRUD for companies, teams, projects and", "project details (25 REST routes).", "",
            "19 backend and 20 frontend tests; both", "coverage reports gated by SonarQube.", "",
            "Runs on Docker Compose or Kubernetes", "(minikube); Prometheus, Grafana and", "Alertmanager watch the API."],
           icons=("springboot", "angular", "mysql"), title_size=30, line_size=17)

    c.card(1620, 200, 500, 170, t["ext"], "EXTERNAL SYSTEM", "GitHub", "source repository",
           ["a push triggers the pipeline;", "Jenkins pushes a build-N tag"], icons=("github",))
    c.card(1620, 450, 500, 170, t["ext"], "EXTERNAL SYSTEM", "Jenkins", "Jenkinsfile · 10 stages",
           ["build, test, analyse, gate,", "image, push, deploy and verify"], icons=("jenkins",))
    c.card(1620, 700, 500, 170, t["ext"], "EXTERNAL SYSTEM", "Docker Hub", "twelvy1400/gestion-projets-*",
           ["backend and frontend images,", ":build-N and :latest"], icons=("docker",))

    c.arrow([(460, 285), (1617, 285)], halo=True)
    c.label(1040, 285, ["git push"])
    c.arrow([(1870, 370), (1870, 447)], halo=True)
    c.label(1870, 409, ["webhook / poll"])
    c.arrow([(1617, 535), (1463, 535)], halo=True)
    c.label(1540, 535, ["builds, tests,", "deploys"])
    c.arrow([(1870, 620), (1870, 697)], halo=True)
    c.label(1870, 659, ["pushes images"])
    c.arrow([(1617, 785), (1463, 785)], halo=True)
    c.label(1540, 785, ["Pulled by", "Kubernetes"])
    c.arrow([(270, 380), (270, 480), (697, 480)], halo=True)
    c.label(500, 480, ["Reads gate, dashboards"], tech="SonarQube · Grafana")
    c.arrow([(460, 795), (697, 795)], halo=True)
    c.label(578, 795, ["Uses the app"], tech="browser")

    c.legend(1120, "github.com/adriansalvadorekomo/DevOps-AppGestionDesProjets", items=[("person", "person", "Person"), ("card", "ops", "Software system"), ("card", "ext", "External system"), ("rel", "line", "Uses")])
    return c.svg("Gestion des projets — C4 Level 1, system context",
                 "A developer pushes to GitHub, which triggers the Jenkins pipeline; Jenkins builds, tests, analyses "
                 "and deploys the system and pushes its images to Docker Hub. A project manager uses the app in a "
                 "browser; the developer reads the SonarQube gate and the Grafana dashboards.")


def container(theme: str) -> str:
    WC = 2400
    c = Canvas(WC, 1980, theme)
    t = c.t
    c.header("C4 MODEL  ·  LEVEL 2  ·  CONTAINER DIAGRAM", "Gestion des projets — the compose stack",
             "The app, its metrics, alerts and quality gate in one docker-compose.yml; Jenkins drives it.", STACK)
    X = [90, 650, 1210]
    CW = 440
    cx = [x + CW / 2 for x in X]
    RA, RB, RC = 500, 880, 1240

    c.person(140, 230, 340, 120, "Project manager", ["Manages companies, teams", "and projects"])
    c.boundary(40, 420, 1680, 1060, t["ops"], "DOCKER COMPOSE", "network app-net", icons=("docker",), tab="right")

    # application
    c.card(X[0], RA, CW, 200, t["ops"], "CONTAINER · WEB APP", "Frontend", "Angular 22 · nginx · :4200 → 80",
           ["nginx serves the SPA and", "proxies /api/ to the backend"], icons=("angular", "nginx"))
    c.card(X[1], RA, CW, 200, t["ops"], "CONTAINER · REST API", "Backend", "Spring Boot 4.1 · Java 17 · :8080",
           ["4 controllers, 25 routes, JPA;", "Actuator health and metrics"], icons=("springboot",))
    c.card(X[2], RA, CW, 200, t["gold"], "DATA STORE", "MySQL 8.0", "db · volume mysql_data",
           ["companies, teams, projects,", "details; teams ↔ projects table"], icons=("mysql",), shape="cylinder")
    c.arrow([(310, 350), (310, 497)], halo=True)
    c.label(310, 455, ["Uses"], tech="browser · :4200")
    c.arrow([(X[0] + CW, 600), (X[1] - 3, 600)], halo=True)
    c.label(590, 600, ["/api/*"], tech="HTTP")
    c.arrow([(X[1] + CW, 600), (X[2] - 3, 600)], halo=True)
    c.label(1150, 600, ["Reads, writes"], tech="JDBC")

    # monitoring profile
    c.boundary(70, 800, 1620, 350, t["dlv"], "PROFILE · MONITORING", "--profile monitoring")
    c.card(X[0], RB, CW, 200, t["dlv"], "CONTAINER · DASHBOARD", "Grafana", "grafana 13.2 · :3000",
           ["Provisioned dashboard: traffic,", "latency, errors, DB pool, JVM"], icons=("grafana",))
    c.card(X[1], RB, CW, 200, t["dlv"], "CONTAINER · METRICS", "Prometheus", "prometheus 3.16 · :9090",
           ["Scrapes every 15 s; evaluates", "4 rules: down, 5xx, p95, heap"], icons=("prometheus",))
    c.card(X[2], RB, CW, 200, t["dlv"], "CONTAINER · ALERTING", "Alertmanager", "alertmanager 0.35 · :9093",
           ["critical → on-call, warning → team;", "BackendDown mutes its warnings"], icons=("prometheus",))
    c.arrow([(cx[1], RB - 3), (cx[1], RA + 203)], halo=True)
    c.label(cx[1], 745, ["Scrapes"], tech="/actuator/prometheus")
    c.arrow([(X[0] + CW, 980), (X[1] - 3, 980)], halo=True)
    c.label(590, 980, ["Queries"], tech="PromQL")
    c.arrow([(X[1] + CW, 980), (X[2] - 3, 980)], halo=True)
    c.label(1150, 980, ["Fires"], tech="alerts")

    # code quality
    c.card(X[1], RC, CW, 180, t["gold"], "DATA STORE", "PostgreSQL 15", "sonardb · volume sonardb_data",
           ["analysis history"], icons=("postgresql",), shape="cylinder")
    c.card(X[2], RC, CW, 190, t["ok"], "CONTAINER · QUALITY GATE", "SonarQube", "sonarqube 9.9 LTS · :9000",
           ["backend: JaCoCo coverage", "frontend: vitest lcov coverage"], icons=("sonarqubeserver",))
    c.arrow([(X[2], 1330), (X[1] + CW + 3, 1330)], halo=True)
    c.label(1150, 1330, ["Stores"], tech="JDBC")

    # outside: Jenkins and Docker Hub
    c.card(1860, RA, 400, 200, t["ext"], "EXTERNAL · CI/CD", "Jenkins", "Jenkinsfile · 10 stages",
           ["build, test, analyse, gate,", "image, push, deploy, verify"], icons=("jenkins",))
    c.card(1860, RC, 400, 190, t["ext"], "EXTERNAL · REGISTRY", "Docker Hub", "twelvy1400/gestion-projets-*",
           ["backend and frontend images", ":build-N and :latest"], icons=("docker",))
    c.arrow([(2060, RA + 200), (2060, RC - 3)], halo=True)
    c.label(2060, 970, ["Pushes images"])
    c.arrow([(1857, 560), (1723, 560)], dashed=True, halo=True)
    c.label(1790, 515, ["Deploys,", "verifies"])
    c.arrow([(1857, 650), (1790, 650), (1790, 1330), (X[2] + CW + 3, 1330)], halo=True)
    c.label(1790, 1000, ["Sends analyses,", "polls both gates"], tech="sonar-token")

    # the developer, below the stack
    c.person(560, 1580, 380, 120, "Developer", ["Pushes code; reads the gate,", "dashboards and alerts"])
    c.arrow([(560, 1640), (310, 1640), (310, RB + 203)], halo=True)
    c.label(310, 1300, ["Reads dashboards"], tech=":3000")
    c.arrow([(940, 1625), (cx[2], 1625), (cx[2], RC + 193)], halo=True)
    c.label(cx[2], 1530, ["Reads the gate"], tech=":9000")
    c.arrow([(940, 1675), (2330, 1675), (2330, 600), (2263, 600)], halo=True)
    c.label(2330, 1120, ["git push"], tech="webhook")

    c.text(60, 1790, "Host ports: 4200, 8080, 9000. Monitoring binds 3000, 9090 and 9093 to 127.0.0.1.",
           14.5, 400, t["muted"], MONO)
    c.text(60, 1818, "deploy-verify.sh: db healthy, API 200, SPA and fallback, /api proxy, /actuator/health UP.",
           14.5, 400, t["muted"], MONO)
    c.legend(1915, "docker-compose.yml · Jenkinsfile · monitoring/", items=[("person", "person", "Person"), ("card", "ops", "Container"), ("card", "ok", "Quality gate"), ("store", "gold", "Data store"), ("card", "ext", "External system"), ("boundary", "ops", "Deployment boundary"), ("rel", "line", "Uses"), ("rel_dashed", "line", "Deploys")])
    return c.svg("Gestion des projets — C4 Level 2, containers",
                 "In Docker Compose, a project manager uses the Angular frontend; nginx serves it and proxies /api/ to "
                 "the Spring Boot backend, which reads and writes MySQL. In the monitoring profile Prometheus scrapes "
                 "the backend's actuator metrics, Grafana queries Prometheus and Prometheus fires alerts to "
                 "Alertmanager, which routes them by severity. SonarQube, backed by PostgreSQL, is the quality gate: "
                 "Jenkins sends the backend and frontend analyses and polls both gates. Jenkins, triggered by a git "
                 "push, deploys and verifies the stack and pushes the images to Docker Hub. The developer reads "
                 "Grafana and SonarQube.")


def component(theme: str) -> str:
    c = Canvas(W, 1600, theme)
    t = c.t
    c.header("C4 MODEL  ·  LEVEL 3  ·  COMPONENT DIAGRAM", "Gestion des projets — inside the backend",
             "Four domains, three layers each; Actuator exposes health and metrics.", STACK)
    c.card(820, 180, 560, 110, t["ext"], "CONTAINER · OUTSIDE THIS ONE", "Frontend (nginx)", "/api/* → backend:8080", [],
           icons=("nginx",), title_size=19)
    c.boundary(40, 340, 2140, 830, t["ops"], "CONTAINER", "Backend · Spring Boot 4.1", icons=("springboot",))

    cols = [
        ("EntrepriseController", "/entreprise · 5 routes", ["add, update, delete,", "get/{id}, all"],
         "EntrepriseServiceImpl", ["CRUD through", "the repository"],
         "EntrepriseRepository", "JpaRepository", ["table entreprises"]),
        ("EquipeController", "/equipe · 8 routes", ["CRUD, by-entreprise,", "assign-entreprise / -projet"],
         "EquipeServiceImpl", ["assigns a team to a", "company or a project"],
         "EquipeRepository", "+ findByEntrepriseId", ["table equipes; join table", "equipes_projets"]),
        ("ProjetController", "/projet · 5 routes", ["add, update, delete,", "get/{id}, all"],
         "ProjetServiceImpl", ["CRUD through", "the repository"],
         "ProjetRepository", "JpaRepository", ["table projets"]),
        ("ProjetDetailleController", "/projet-detaille · 7 routes", ["CRUD, by-projet,", "assign-projet"],
         "ProjetDetailleServiceImpl", ["assigns a detail", "to a project"],
         "ProjetDetailleRepository", "+ findByProjetId", ["table projets_detailles"]),
    ]
    xs = [70, 500, 930, 1360]
    cw = 380
    for x, (ctl, route, cl, svc, sl, repo, rtech, rl) in zip(xs, cols, strict=True):
        cx = x + cw / 2
        c.card(x, 420, cw, 180, t["ops"], "COMPONENT · CONTROLLER", ctl, route, cl, title_size=18)
        c.card(x, 670, cw, 180, t["ops"], "COMPONENT · SERVICE", svc, "@Service", sl, title_size=18)
        c.card(x, 920, cw, 180, t["gold"], "COMPONENT · REPOSITORY", repo, rtech, rl, title_size=18)
        c.arrow([(cx, 600), (cx, 667)])
        c.arrow([(cx, 850), (cx, 917)])
        c.arrow([(cx, 1100), (cx, 1227)])
    # bus from the frontend to the four controllers
    c.arrow([(1100, 290), (1100, 375)], head=False)
    c.arrow([(260, 375), (1550, 375)], head=False)
    for x in xs:
        c.arrow([(x + cw / 2, 375), (x + cw / 2, 417)])
    c.label(1100, 330, ["HTTP + JSON"])
    # cross-domain repository use
    c.arrow([(560, 850), (560, 885), (400, 885), (400, 917)], dashed=True)
    c.arrow([(820, 850), (820, 885), (980, 885), (980, 917)], dashed=True)
    c.arrow([(1380, 850), (1380, 885), (1260, 885), (1260, 917)], dashed=True)

    # actuator column
    c.card(1790, 420, 370, 180, t["dlv"], "COMPONENT · METRICS", "Micrometer", "Prometheus registry",
           ["http_server_requests,", "hikaricp, jvm_*"], title_size=18, icons=("prometheus",))
    c.card(1790, 670, 370, 180, t["dlv"], "COMPONENT · SPRING BOOT", "Actuator", "/actuator/health · /prometheus",
           ["readiness includes the DB;", "liveness stays independent"], title_size=18)
    c.arrow([(1975, 670), (1975, 603)])
    c.label(1975, 636, ["Renders"])

    c.card(70, 1230, 1670, 150, t["gold"], "DATA STORE · OUTSIDE THIS CONTAINER", "MySQL 8.0", "jdbc:mysql://db:3306",
           [], icons=("mysql",), shape="cylinder")
    c.card(1790, 1230, 370, 150, t["dlv"], "CONTAINER · OUTSIDE", "Prometheus", "scrapes every 15 s", [],
           icons=("prometheus",), title_size=19)
    c.arrow([(1975, 1227), (1975, 853)], halo=True)
    c.label(1975, 1140, ["GET /actuator/prometheus"])
    c.legend(1535, "backend/src/main/java/tn/esprit/backend", items=[("card", "ext", "Other container"), ("card", "ops", "Component"), ("store", "gold", "Database"), ("boundary", "ops", "Container boundary"), ("rel", "line", "Calls"), ("rel_dashed", "line", "Reads another domain")])
    return c.svg("Gestion des projets — C4 Level 3, backend components",
                 "Each of the four domains has a REST controller, a service and a Spring Data repository on MySQL. "
                 "EquipeServiceImpl also reads the company and project repositories to assign a team; "
                 "ProjetDetailleServiceImpl reads the project repository. Actuator and Micrometer expose health and "
                 "Prometheus metrics.")


def deployment(theme: str) -> str:
    c = Canvas(W, 1510, theme)
    t = c.t
    c.header("C4 MODEL  ·  DEPLOYMENT  ·  KUBERNETES", "Gestion des projets — on minikube",
             "kubectl apply -k k8s/ : two Deployments, one StatefulSet, three Services.", STACK)
    c.person(180, 236, 340, 120, "Project manager", ["Opens the NodePort"])
    c.card(800, 200, 560, 120, t["ext"], "EXTERNAL · REGISTRY", "Docker Hub", "twelvy1400/gestion-projets-*:latest",
           [], icons=("docker",), title_size=19)
    c.boundary(40, 420, 2120, 920, t["ops"], "MINIKUBE · NAMESPACE", "gestion-projets", icons=("kubernetes",),
               tab="right")

    colx = [90, 790, 1490]
    w = 580
    svc = [("SERVICE · NODEPORT", "frontend", ":80 → nodePort 30080"),
           ("SERVICE · CLUSTERIP", "backend", ":8080"),
           ("SERVICE · HEADLESS", "db", ":3306 · governs the StatefulSet")]
    dep = [("DEPLOYMENT · 2 REPLICAS", "frontend", "gestion-projets-frontend",
            ["nginx: Angular build + /api/ proxy", "probes: GET / (readiness, liveness)",
             "requests 20m / 32Mi · limit 128Mi"], ("angular", "nginx")),
           ("DEPLOYMENT · 2 REPLICAS", "backend", "gestion-projets-backend · maxUnavailable 0",
            ["probes: /actuator/health/{liveness,", "readiness}; startup up to 3 min",
             "requests 100m / 384Mi · limit 640Mi"], ("springboot",)),
           ("STATEFULSET · 1 REPLICA", "db", "mysql:8.0 · pod db-0",
            ["readiness: mysqladmin ping (app user)", "liveness: TCP :3306",
             "requests 100m / 384Mi · limit 768Mi"], ("mysql",))]
    for x, (eb, title, tech) in zip(colx, svc, strict=True):
        c.card(x, 500, w, 130, t["person"], eb, title, tech, [], title_size=20)
    for x, (eb, title, tech, lines, icons) in zip(colx, dep, strict=True):
        c.card(x, 720, w, 210, t["ops"], eb, title, tech, lines, icons=icons, title_size=20)
        c.arrow([(x + w / 2, 630), (x + w / 2, 717)])
    c.label(380, 674, ["selects pods"])
    c.arrow([(670, 870), (735, 870), (735, 565), (787, 565)], halo=True)
    c.label(735, 760, ["/api/ →", "backend:8080"])
    c.arrow([(1370, 870), (1435, 870), (1435, 565), (1487, 565)], halo=True)
    c.label(1435, 760, ["JDBC as", "gestion"])

    c.card(790, 1030, 580, 190, t["ext"], "CONFIG · KUSTOMIZE GENERATORS", "app-config · app-secrets", "kubectl apply -k k8s/",
           ["MYSQL_DATABASE, MYSQL_USER (ConfigMap)", "both passwords (Secret, from the", "git-ignored k8s/secrets.env)"],
           title_size=20)
    c.arrow([(1080, 1027), (1080, 933)], dashed=True)
    c.arrow([(1370, 1125), (1430, 1125), (1430, 990), (1600, 990), (1600, 933)], dashed=True)
    c.label(1080, 980, ["env"])
    c.label(1430, 1060, ["env"])
    c.card(1490, 1030, 580, 190, t["gold"], "PVC · FROM volumeClaimTemplates", "data-db-0", "1Gi · ReadWriteOnce",
           ["/var/lib/mysql of db-0; kept when", "the pod is replaced"], shape="cylinder", title_size=20)
    c.arrow([(1900, 930), (1900, 1027)])

    c.arrow([(350, 356), (350, 497)], halo=True)
    c.label(350, 465, ["minikube service frontend"], tech="NodePort 30080")
    c.arrow([(1080, 320), (1080, 417)], dashed=True, halo=True)
    c.label(1080, 370, ["Pulled by the kubelet"])

    c.text(90, 1262, "Pods only receive traffic once ready: the backend waits for MySQL through its readiness group.",
           15, 400, t["muted"], MONO)
    c.text(90, 1294, "Rolling updates keep both backend replicas serving (maxUnavailable 0, maxSurge 1).",
           15, 400, t["muted"], MONO)
    c.legend(1445, "k8s/ · namespace.yaml · mysql.yaml · backend.yaml · frontend.yaml · kustomization.yaml",
             items=[("person", "person", "Person"), ("card", "ops", "Service or Deployment"), ("card", "ext", "Config or external"), ("store", "gold", "Persistent volume"), ("boundary", "ops", "Namespace"), ("rel", "line", "Routes / uses"), ("rel_dashed", "line", "Configures / pulls")])
    return c.svg("Gestion des projets — deployment on Kubernetes (minikube)",
                 "In the gestion-projets namespace, a NodePort Service exposes two nginx frontend pods, which proxy "
                 "/api/ to the backend ClusterIP Service and its two Spring Boot pods; those reach MySQL through the "
                 "db Service. MySQL keeps its data on a 1Gi PersistentVolumeClaim. A ConfigMap and a Secret, generated "
                 "by kustomize, provide the database name and password. Images come from Docker Hub.")


if __name__ == "__main__":
    build(HERE, (("context", context, (W, 1180)), ("container", container, (2400, 1980)),
                 ("component", component, (W, 1600)), ("deployment", deployment, (W, 1510))))
