"""Generate dashboards/backend.json (run: python monitoring/grafana/build_dashboard.py).

Every panel reads Micrometer metrics scraped from /actuator/prometheus.
"""

import json
import pathlib

DS = {"type": "prometheus", "uid": "prometheus"}
API = 'job="backend", uri!~"/actuator.*"'
_id = iter(range(1, 100))


def target(expr, legend="", ref="A"):
    return {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref}


def stat(title, expr, x, unit="none", decimals=None, thresholds=None, desc="", mappings=None):
    p = {
        "id": next(_id), "type": "stat", "title": title, "description": desc, "datasource": DS,
        "gridPos": {"x": x, "y": 0, "w": 4, "h": 4},
        "targets": [target(expr)],
        "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "value",
                    "graphMode": "area", "textMode": "value"},
        "fieldConfig": {"defaults": {"unit": unit, "thresholds": thresholds or {
            "mode": "absolute", "steps": [{"color": "green", "value": None}]}}, "overrides": []},
    }
    if decimals is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimals
    if mappings:
        p["fieldConfig"]["defaults"]["mappings"] = mappings
    return p


def series(title, targets, x, y, w=12, h=8, unit="none", desc="", stack=False):
    return {
        "id": next(_id), "type": "timeseries", "title": title, "description": desc, "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [target(e, lg, chr(65 + i)) for i, (e, lg) in enumerate(targets)],
        "options": {"legend": {"displayMode": "list", "placement": "bottom"},
                    "tooltip": {"mode": "multi", "sort": "desc"}},
        "fieldConfig": {"defaults": {"unit": unit, "custom": {
            "lineWidth": 2, "fillOpacity": 12, "showPoints": "never",
            "stacking": {"mode": "normal" if stack else "none"}}}, "overrides": []},
    }


def row(title, y):
    return {"id": next(_id), "type": "row", "title": title, "collapsed": False,
            "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": []}


red = lambda warn, crit: {"mode": "absolute", "steps": [  # noqa: E731
    {"color": "green", "value": None}, {"color": "orange", "value": warn}, {"color": "red", "value": crit}]}

panels = [
    stat("Backend up", 'up{job="backend"}', 0, thresholds={"mode": "absolute", "steps": [
        {"color": "red", "value": None}, {"color": "green", "value": 1}]},
         desc="UP when Prometheus scraped /actuator/prometheus on the last attempt.",
         mappings=[{"type": "value", "options": {
             "0": {"text": "DOWN", "color": "red"}, "1": {"text": "UP", "color": "green"}}}]),
    stat("Requests / s", f"sum(rate(http_server_requests_seconds_count{{{API}}}[1m]))", 4, "reqps", 2),
    stat("p95 latency", f"histogram_quantile(0.95, sum by (le) (rate(http_server_requests_seconds_bucket{{{API}}}[5m])))",
         8, "s", 3, red(0.25, 0.5)),
    # "or vector(0)": with no 5xx at all the numerator has no series; show 0 %, not "No data".
    stat("5xx share", f'(sum(rate(http_server_requests_seconds_count{{{API}, status=~"5.."}}[5m])) or vector(0)) '
         f"/ clamp_min(sum(rate(http_server_requests_seconds_count{{{API}}}[5m])), 1e-9)", 12, "percentunit", 1,
         red(0.01, 0.05)),
    stat("Heap used", 'sum(jvm_memory_used_bytes{job="backend", area="heap"}) '
         '/ sum(jvm_memory_max_bytes{job="backend", area="heap"} > 0)', 16, "percentunit", 0, red(0.75, 0.9)),
    stat("Uptime", 'process_uptime_seconds{job="backend"}', 20, "s", 0),
    row("API traffic", 4),
    series("Requests / s by endpoint", [(f"sum by (method, uri) (rate(http_server_requests_seconds_count{{{API}}}[1m]))",
                                         "{{method}} {{uri}}")], 0, 5, unit="reqps", stack=True),
    series("Latency by endpoint (p95)", [(
        f"histogram_quantile(0.95, sum by (le, uri) (rate(http_server_requests_seconds_bucket{{{API}}}[5m])))",
        "{{uri}}")], 12, 5, unit="s"),
    series("Responses by status", [(f"sum by (status) (rate(http_server_requests_seconds_count{{{API}}}[1m]))",
                                    "{{status}}")], 0, 13, unit="reqps", stack=True),
    series("Database connections (HikariCP)", [
        ('sum(hikaricp_connections_active{job="backend"})', "active"),
        ('sum(hikaricp_connections_idle{job="backend"})', "idle"),
        ('sum(hikaricp_connections_pending{job="backend"})', "waiting")], 12, 13),
    row("JVM", 21),
    series("Heap and non-heap", [
        ('sum by (area) (jvm_memory_used_bytes{job="backend"})', "used {{area}}"),
        ('sum(jvm_memory_max_bytes{job="backend", area="heap"} > 0)', "heap max")], 0, 22, w=8, unit="bytes"),
    series("CPU", [('process_cpu_usage{job="backend"}', "process"), ('system_cpu_usage{job="backend"}', "system")],
           8, 22, w=8, unit="percentunit"),
    series("GC pause time / s", [('sum by (gc) (rate(jvm_gc_pause_seconds_sum{job="backend"}[1m]))', "{{gc}}")],
           16, 22, w=8, unit="s"),
]

dashboard = {
    "uid": "gestion-projets-backend",
    "title": "Gestion des projets · backend",
    "description": "Spring Boot API: traffic, latency, errors, database pool and JVM (Micrometer → Prometheus).",
    "tags": ["spring-boot", "prometheus", "devops"],
    "timezone": "browser",
    "schemaVersion": 41,
    "version": 1,
    "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"},
    "panels": panels,
    "templating": {"list": []},
    "annotations": {"list": []},
}

out = pathlib.Path(__file__).parent / "dashboards" / "backend.json"
out.write_text(json.dumps(dashboard, indent=2) + "\n")
print("wrote", out.relative_to(pathlib.Path.cwd()) if out.is_relative_to(pathlib.Path.cwd()) else out)
