"""Draw the C4 diagrams of Gestion des projets (docs/diagrams/c4/*.svg).

Four views, each in a light and a dark theme:
  c4-context     C4 level 1: who uses the system, what delivers it
  c4-container   C4 level 2: the compose stack (app, metrics, alerts, quality gate)
  c4-component   C4 level 3: inside the Spring Boot backend
  c4-deployment  deployment view: the Kubernetes manifests on minikube

Every element comes from the files at the commit it ships with: docker-compose.yml,
Jenkinsfile, scripts/, monitoring/, k8s/ and backend/src. Drawing kit: c4kit.py (same
engine as the Episteme diagrams).

    uv run --no-project --with fonttools --with brotli python docs/diagrams/c4/build_c4.py [--png]
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c4kit import Box, Canvas, View, build  # noqa: E402

READOUT = [("TESTS", "28 + 20"), ("LINE COVERAGE", "98.4% · 98.5%"), ("QUALITY GATES", "2 · SonarQube")]
COL = [32, 360, 688, 1016]  # four columns, 224 wide, 104 apart
W = 224


# ── C4 level 1 · context ───────────────────────────────────────────────────
def context_view(cv: Canvas):
    dev = Box(32, 200, 192, 112)
    pm = Box(32, 416, 192, 112)
    system = Box(368, 184, 528, 384)
    github = Box(1040, 184, 208, 96)
    jenkins = Box(1040, 328, 208, 96)
    hub = Box(1040, 472, 208, 96)

    cv.arrow([(dev.cx, dev.y), (dev.cx, 168), (github.cx, 168), (github.cx, github.y)])
    cv.label([("git push", False)], 632, 172)
    cv.arrow([(dev.r, 264), (system.x, 264)])
    cv.label([("reads the gate,", False), ("dashboards", False), ("Sonar · Grafana", True)], 296, 214)
    cv.arrow([(pm.r, 472), (system.x, 472)])
    cv.label([("uses", False), ("browser", True)], 296, 438)
    cv.arrow([(github.cx, github.b), (github.cx, jenkins.y)])
    cv.label([("webhook", False)], github.cx + 12, 308, "start")
    cv.arrow([(jenkins.x, 376), (system.r, 376)])
    cv.label([("builds, tests,", False), ("deploys", False)], 968, 336)
    cv.arrow([(jenkins.cx, jenkins.b), (jenkins.cx, hub.y)])
    cv.label([("pushes images", False)], jenkins.cx + 12, 452, "start")
    cv.arrow([(system.r, 520), (hub.x, 520)])
    cv.label([("pulled by", False), ("Kubernetes", True)], 968, 486)

    cv.node(dev, "person", "Person", "Developer", None, ["Pushes code, reads", "the gate and dashboards"], ["user"])
    cv.node(pm, "person", "Person", "Project manager", None, ["Manages companies,", "teams and projects"], ["user"])
    cv.node(system, "container", "Software system", "Gestion des projets", "Spring Boot · Angular · MySQL",
            ["CRUD for companies, teams, projects and their", "details: 25 REST routes behind an Angular app.", "",
             "28 backend and 20 frontend tests; both coverage", "reports are gated by SonarQube in Jenkins.", "",
             "Runs on Docker Compose or Kubernetes (minikube);", "Prometheus, Grafana and Alertmanager watch",
             "the API."],
            ["springboot", "angular", "mysql", "kubernetes"], focal=True)
    cv.node(github, "external", "External", "GitHub", None, ["Source; build-N tags"], ["github"])
    cv.node(jenkins, "external", "External", "Jenkins", None, ["Jenkinsfile, 10 stages"], ["jenkins"])
    cv.node(hub, "external", "External", "Docker Hub", None, ["gestion-projets-*"], ["docker"])

    cv.readout(READOUT, 1248, 96)
    cv.legend(616, [("person", "person"), ("focal", "the system"), ("external", "external system"),
                    ("call", "uses")])


# ── C4 level 2 · containers ────────────────────────────────────────────────
def container_view(cv: Canvas):
    ra, rb, rc = 344, 552, 768
    pm = Box(32, 168, 232, 96)
    frontend = Box(COL[0], ra, W, 128)
    backend = Box(COL[1], ra, W, 128)
    mysql = Box(COL[2], ra, W, 128)
    grafana = Box(COL[0], rb, W, 128)
    prom = Box(COL[1], rb, W, 128)
    am = Box(COL[2], rb, W, 128)
    sonar = Box(COL[1], rc, W, 128)
    sonardb = Box(COL[2], rc, W, 128)
    jenkins = Box(COL[3], ra, W, 128)
    hub = Box(COL[3], rb, W, 128)
    dev = Box(COL[1], 1024, W, 96)

    cv.zone(Box(16, 312, 928, 680), "GESTION DES PROJETS", "docker compose · app-net", at="bottom", lx=588)
    cv.zone(Box(24, 520, 912, 192), "MONITORING", "opt-in profile", at="bottom", lx=280)

    cv.arrow([(frontend.cx, pm.b), (frontend.cx, frontend.y)])
    cv.label([("uses", False), ("browser · :4200", True)], frontend.cx + 12, 300, "start")
    cv.arrow([(frontend.r, 392), (backend.x, 392)])
    cv.label([("/api/*", False), ("nginx proxy", True)], 308, 356)
    cv.arrow([(backend.r, 392), (mysql.x, 392)])
    cv.label([("reads, writes", False), ("JDBC", True)], 636, 356)
    cv.arrow([(prom.cx, prom.y), (prom.cx, backend.b)])
    cv.label([("scrapes, 15 s", False), ("/actuator/prometheus", True)], prom.cx + 12, 500, "start")
    cv.arrow([(grafana.r, 600), (prom.x, 600)])
    cv.label([("queries", False), ("PromQL", True)], 308, 564)
    cv.arrow([(prom.r, 600), (am.x, 600)])
    cv.label([("fires alerts", False)], 636, 584)
    cv.arrow([(sonar.r, 832), (sonardb.x, 832)])
    cv.label([("stores", False), ("JDBC", True)], 636, 796)
    # Jenkins, outside the stack
    cv.arrow([(jenkins.x, 392), (948, 392)], dashed=True)
    cv.label([("deploys", False)], 980, 376)
    cv.arrow([(jenkins.cx, jenkins.b), (jenkins.cx, hub.y)])
    cv.label([("pushes images", False), (":build-N, :latest", True)], jenkins.cx + 12, 500, "start")
    cv.arrow([(jenkins.x, 448), (980, 448), (980, 736), (548, 736), (548, sonar.y)])
    cv.label([("analyses, polls both gates", False), ("sonar-token", True)], 760, 726)
    # the developer, under the stack
    cv.arrow([(dev.x, 1072), (grafana.cx, 1072), (grafana.cx, grafana.b)])
    cv.label([("reads dashboards", False), (":3000", True)], grafana.cx + 12, 952, "start")
    cv.arrow([(dev.cx, dev.y), (dev.cx, sonar.b)])
    cv.label([("reads the gate", False), (":9000", True)], dev.cx + 12, 952, "start")
    cv.arrow([(dev.r, 1072), (1262, 1072), (1262, 408), (jenkins.r, 408)])
    cv.label([("git push", False), ("webhook", True)], 900, 1060)

    cv.node(pm, "person", "Person", "Project manager", None, ["Companies, teams, projects"], ["user"])
    cv.node(frontend, "container", "Container", "Frontend", "Angular 22 · nginx · :4200",
            ["SPA; nginx proxies /api/", "to the backend"], ["angular", "nginx"])
    cv.node(backend, "container", "Container", "Backend", "Spring Boot 4.1 · :8080",
            ["4 controllers, 25 routes;", "Actuator health, metrics"], ["springboot"])
    cv.node(mysql, "store", "Data store", "MySQL 8.0", "db · volume mysql_data",
            ["Companies, teams, projects,", "details, teams ↔ projects"], ["mysql"])
    cv.node(grafana, "container", "Container", "Grafana", "Grafana 13.2 · :3000",
            ["Provisioned dashboard:", "traffic, errors, JVM"], ["grafana"])
    cv.node(prom, "container", "Container", "Prometheus", "Prometheus 3.16 · :9090",
            ["Scrapes every 15 s;", "4 alert rules"], ["prometheus"])
    cv.node(am, "container", "Container", "Alertmanager", "Alertmanager 0.35 · :9093",
            ["critical → on-call;", "BackendDown mutes warnings"], ["prometheus"])
    cv.node(sonar, "container", "Container", "SonarQube", "SonarQube 26.11 · :9000",
            ["Gates the backend (JaCoCo)", "and the frontend (lcov)"], ["sonarqubeserver"], focal=True)
    cv.node(sonardb, "store", "Data store", "PostgreSQL 15", "sonardb · volume", ["Analysis history"], ["postgresql"])
    cv.node(jenkins, "external", "External", "Jenkins", "Jenkinsfile · 10 stages",
            ["Build, test, analyse,", "gate, push, deploy"], ["jenkins"])
    cv.node(hub, "external", "External", "Docker Hub", "gestion-projets-*",
            ["backend and frontend", ":build-N and :latest"], ["docker"])
    cv.node(dev, "person", "Person", "Developer", None, ["Pushes code, reads results"], ["user"])

    cv.readout(READOUT, 1248, 96)
    cv.legend(1152, [("person", "person"), ("container", "container"), ("focal", "the quality gate"),
                     ("store", "data store"), ("external", "external"), ("call", "call / read / write"),
                     ("occasional", "deploys")])


# ── C4 level 3 · components of the backend ─────────────────────────────────
def component_view(cv: Canvas):
    cols = [32, 280, 528, 776, 1024]  # five columns, 224 wide, 24 apart
    w = 224
    r1, r2, r3 = 328, 504, 680
    frontend = Box(528, 168, 224, 88)
    domains = [("Entreprise", "/entreprise · 5 routes", ["add, update, delete,", "get/{id}, all"],
                ["CRUD through", "the repository"], ["table entreprises"]),
               ("Equipe", "/equipe · 8 routes", ["CRUD, by-entreprise,", "assign to company, project"],
                ["Assigns a team to a", "company or a project"], ["table equipes, join", "table equipes_projets"]),
               ("Projet", "/projet · 5 routes", ["add, update, delete,", "get/{id}, all"],
                ["CRUD through", "the repository"], ["table projets"]),
               ("ProjetDetaille", "/projet-detaille", ["7 routes: CRUD, by-projet,", "assign-projet"],
                ["Assigns a detail", "to a project"], ["table projets_detailles"])]
    micrometer = Box(cols[4], r1, w, 128)
    actuator = Box(cols[4], r2, w, 128)
    mysql = Box(32, 880, 968, 88)
    prom = Box(cols[4], 880, w, 88)

    cv.zone(Box(16, 304, 1248, 528), "BACKEND", "container", at="bottom", lx=920)

    cv.arrow([(frontend.cx, frontend.b), (frontend.cx, 288)], head=False)
    cv.arrow([(cols[0] + w / 2, 288), (cols[3] + w / 2, 288)], head=False)
    for x in cols[:4]:
        cx = x + w / 2
        cv.arrow([(cx, 288), (cx, r1)])
        cv.arrow([(cx, r1 + 128), (cx, r2)])
        cv.arrow([(cx, r2 + 128), (cx, r3)])
        cv.arrow([(cx, r3 + 128), (cx, mysql.y)])
    cv.label([("HTTP + JSON", False)], frontend.cx + 12, 276, "start")
    # services that also read another domain's repository
    cv.arrow([(300, r2 + 128), (300, 656), (236, 656), (236, r3)], dashed=True)
    cv.arrow([(484, r2 + 128), (484, 656), (548, 656), (548, r3)], dashed=True)
    cv.arrow([(796, r2 + 128), (796, 656), (732, 656), (732, r3)], dashed=True)
    # observability
    cv.arrow([(actuator.cx, actuator.y), (actuator.cx, micrometer.b)])
    cv.label([("renders", False)], actuator.cx + 12, 484, "start")
    cv.arrow([(prom.cx, prom.y), (prom.cx, actuator.b)])
    cv.label([("scrapes", False)], prom.cx + 12, 858, "start")

    cv.node(frontend, "external", "Container · outside", "Frontend (nginx)", "/api/* → backend:8080", [], ["nginx"])
    for x, (name, route, ctl, svc, repo) in zip(cols[:4], domains, strict=True):
        cv.node(Box(x, r1, w, 128), "container", "Controller", name, route, ctl)
        cv.node(Box(x, r2, w, 128), "container", "Service", name, f"{name}ServiceImpl", svc)
        cv.node(Box(x, r3, w, 128), "container", "Repository", name, "Spring Data JPA", repo)
    cv.node(micrometer, "container", "Component", "Micrometer", "Prometheus registry",
            ["http_server_requests,", "hikaricp, jvm_*"], ["prometheus"])
    cv.node(actuator, "container", "Component", "Actuator", "/actuator/health",
            ["Readiness includes MySQL;", "liveness does not"], ["springboot"], focal=True)
    cv.node(mysql, "store", "Data store · outside", "MySQL 8.0", "jdbc:mysql://db:3306 · app user gestion", [],
            ["mysql"])
    cv.node(prom, "external", "Container · outside", "Prometheus", "every 15 s", [], ["prometheus"])

    cv.readout([("REST ROUTES", "25"), ("BACKEND TESTS", "28 · 98.4%"), ("FRONTEND TESTS", "20 · 98.5%")],
               1248, 96)
    cv.legend(1000, [("container", "component"), ("focal", "the health gate: no DB, no traffic"),
                     ("store", "data store"), ("external", "outside the backend"), ("call", "call"),
                     ("occasional", "reads another domain")])


# ── deployment · Kubernetes ────────────────────────────────────────────────
def deployment_view(cv: Canvas):
    cols = [64, 480, 896]  # three columns, 320 wide, 96 apart
    w = 320
    pm = Box(64, 168, 240, 96)
    hub = Box(480, 168, 320, 96)
    svc = [Box(x, 344, w, 88) for x in cols]
    wl = [Box(x, 496, w, 152) for x in cols]
    config = Box(cols[1], 720, w, 128)
    pvc = Box(cols[2], 720, w, 128)

    cv.zone(Box(32, 312, 1216, 616), "GESTION-PROJETS", "namespace · minikube", at="bottom")

    cv.arrow([(svc[0].cx, pm.b), (svc[0].cx, svc[0].y)])
    cv.label([("minikube service", False), ("NodePort 30080", True)], svc[0].cx + 12, 296, "start")
    cv.arrow([(hub.cx, hub.b), (hub.cx, 312)], dashed=True)
    cv.label([("pulled by the kubelet", False)], hub.cx + 12, 296, "start")
    for s, d in zip(svc, wl, strict=True):
        cv.arrow([(s.cx, s.b), (s.cx, d.y)])
    cv.label([("selects pods", False)], svc[0].cx + 12, 472, "start")
    cv.arrow([(wl[0].r, 560), (432, 560), (432, 388), (svc[1].x, 388)])
    cv.label([("/api/", False), (":8080", True)], 432, 466)
    cv.arrow([(wl[1].r, 560), (848, 560), (848, 388), (svc[2].x, 388)])
    cv.label([("JDBC", False), ("as gestion", True)], 848, 466)
    cv.arrow([(config.cx, config.y), (config.cx, wl[1].b)], dashed=True)
    cv.label([("env", False)], config.cx + 12, 692, "start")
    cv.arrow([(config.r, 760), (848, 760), (848, 680), (1000, 680), (1000, wl[2].b)], dashed=True)
    cv.label([("env", False)], 924, 668)
    cv.arrow([(1120, wl[2].b), (1120, pvc.y)])
    cv.label([("mounts", False)], 1132, 692, "start")
    cv.note("verified: MySQL down → backend NotReady, 0 restarts, back on its own", 64, 900)

    cv.node(pm, "person", "Person", "Project manager", None, ["Opens the NodePort"], ["user"])
    cv.node(hub, "external", "External", "Docker Hub", "twelvy1400/gestion-projets-*", [], ["docker"])
    cv.node(svc[0], "container", "Service · NodePort", "frontend", ":80 → nodePort 30080", [])
    cv.node(svc[1], "container", "Service · ClusterIP", "backend", ":8080", [])
    cv.node(svc[2], "container", "Service · headless", "db", ":3306 · governs db-0", [])
    cv.node(wl[0], "container", "Deployment · 2 replicas", "frontend", "gestion-projets-frontend",
            ["nginx: SPA + /api/ proxy", "probes: GET /", "requests 20m / 32Mi · limit 128Mi"], ["angular", "nginx"])
    cv.node(wl[1], "container", "Deployment · 2 replicas", "backend", "gestion-projets-backend",
            ["readiness includes MySQL, liveness not", "startup probe: up to 3 min",
             "maxUnavailable 0 · 384Mi / 640Mi"], ["springboot"], focal=True)
    cv.node(wl[2], "container", "StatefulSet · 1 replica", "db", "mysql:8.0 · pod db-0",
            ["app user gestion, never root", "readiness: mysqladmin ping", "requests 100m / 384Mi · limit 768Mi"],
            ["mysql"])
    cv.node(config, "external", "Kustomize generators", "app-config · app-secrets", "kubectl apply -k k8s/",
            ["DB name and user; both passwords", "from the git-ignored secrets.env"])
    cv.node(pvc, "store", "PVC · claim template", "data-db-0", "1Gi · ReadWriteOnce",
            ["/var/lib/mysql of db-0;", "kept when the pod is replaced"])

    cv.readout([("WORKLOADS", "2 Deployments · 1 StatefulSet"), ("PODS", "2 · 2 · 1"), ("VERIFIED ON", "minikube")],
               1248, 96)
    cv.legend(952, [("person", "person"), ("container", "Kubernetes object"), ("focal", "the readiness gate"),
                    ("store", "volume"), ("external", "config or external"), ("call", "routes / uses"),
                    ("occasional", "configures / pulls")])


VIEWS = [
    View("context", context_view, 1280, 664, "c4 model · level 1 · context", "Gestion des projets",
         "a CRUD app delivered and watched like a production service",
         "Gestion des projets — C4 context view",
         "C4 context diagram: a developer pushes to GitHub, which triggers Jenkins; Jenkins builds, tests, deploys "
         "the system and pushes its images to Docker Hub, from which Kubernetes pulls them. A project manager uses "
         "the app in a browser; the developer reads the SonarQube gate and the Grafana dashboards."),
    View("container", container_view, 1280, 1200, "c4 model · level 2 · containers", "The compose stack",
         "app, metrics, alerts and quality gate in one docker-compose.yml",
         "Gestion des projets — C4 container view",
         "C4 container diagram: the project manager uses the Angular frontend; nginx serves it and proxies /api/ to "
         "the Spring Boot backend, which reads and writes MySQL. In the monitoring profile Prometheus scrapes the "
         "backend's actuator metrics, Grafana queries Prometheus and Prometheus fires alerts to Alertmanager. "
         "SonarQube, backed by PostgreSQL, is the quality gate: Jenkins sends both analyses and polls both gates. "
         "Jenkins deploys the stack and pushes the images to Docker Hub; the developer pushes code and reads "
         "Grafana and SonarQube."),
    View("component", component_view, 1280, 1048, "c4 model · level 3 · backend components", "Inside the backend",
         "four domains, three layers each; Actuator decides if a pod gets traffic",
         "Gestion des projets — C4 component view of the backend",
         "C4 component diagram of the backend: requests from the nginx frontend reach four REST controllers, each "
         "calling its service and its Spring Data repository on MySQL; the team and project-detail services also "
         "read other domains' repositories. Micrometer keeps the metrics that Actuator exposes at "
         "/actuator/prometheus for Prometheus; Actuator's readiness group includes the database."),
    View("deployment", deployment_view, 1280, 1000, "deployment · kubernetes", "On minikube",
         "kubectl apply -k k8s/ : two Deployments, one StatefulSet, three Services",
         "Gestion des projets — deployment on Kubernetes",
         "Deployment diagram: in the gestion-projets namespace a NodePort Service exposes two nginx frontend pods, "
         "which proxy /api/ to the backend ClusterIP Service and its two Spring Boot pods; those connect as the "
         "application user to MySQL, a one-replica StatefulSet behind a headless Service, whose data lives on a "
         "claim from its volume template. Kustomize generates the ConfigMap and the Secret; the kubelet pulls the "
         "images from Docker Hub."),
]

if __name__ == "__main__":
    build(HERE, "DevOps-AppGestionDesProjets", VIEWS)
