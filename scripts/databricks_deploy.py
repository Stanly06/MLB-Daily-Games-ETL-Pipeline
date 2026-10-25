"""Continuous deployment to Databricks (run by GitHub Actions; standard library only).

1. Pulls the workspace Git folder of this repository to the latest `main` (Repos API), so every job
   run uses the code that is on GitHub.
2. Creates or updates the setup job and the daily job (Jobs API 2.2 `reset`) from
   `resources/jobs/mlb_performance_daily.job.json`, pointing every task at that Git folder.
3. Prints the status of the latest daily-job runs.

It never starts a backfill. Environment: DATABRICKS_HOST, DATABRICKS_TOKEN (repository secrets),
optional MLB_GIT_FOLDER_NAME (default: MLB-Daily-Games-ETL-Pipeline).

    python scripts/databricks_deploy.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = os.environ["DATABRICKS_HOST"].rstrip("/")
TOKEN = os.environ["DATABRICKS_TOKEN"]
REPO_URL = "https://github.com/Stanly06/MLB-Daily-Games-ETL-Pipeline"
FOLDER_NAME = os.environ.get("MLB_GIT_FOLDER_NAME", "MLB-Daily-Games-ETL-Pipeline")
ROOT = Path(__file__).resolve().parents[1]


def api(method, path, body=None, query=None, allow_missing=False):
    url = f"{HOST}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        if allow_missing and e.code == 404:
            return None
        sys.exit(f"::error::{method} {path} -> HTTP {e.code}: {e.read().decode()[:500]}")


def main():
    me = api("GET", "/api/2.0/preview/scim/v2/Me")["userName"]
    folder = f"/Users/{me}/{FOLDER_NAME}"
    print(f"Workspace user: {me}\nGit folder: {folder}")

    # 1. Git folder -> latest main (create it if it does not exist yet)
    status = api("GET", "/api/2.0/workspace/get-status", query={"path": folder}, allow_missing=True)
    if status and status.get("object_type") == "REPO":
        repo = {"id": status["object_id"]}
        print("Git folder found")
    elif status:
        sys.exit(f"::error::{folder} exists but is not a Git folder ({status.get('object_type')})")
    else:
        repo = api("POST", "/api/2.0/repos", {"url": REPO_URL, "provider": "gitHub", "path": folder})
        print(f"Created Git folder {folder}")
    updated = api("PATCH", f"/api/2.0/repos/{repo['id']}", {"branch": "main"})
    print(f"Git folder on main @ {updated.get('head_commit_id', '?')[:7]}")

    # 2. Jobs from the repository definition
    def notebook(rel):
        return f"{folder}/src/{rel}"

    daily = json.loads((ROOT / "resources/jobs/mlb_performance_daily.job.json").read_text())
    for t in daily["tasks"]:
        t["notebook_task"]["notebook_path"] = notebook(t["notebook_task"]["notebook_path"].split("/src/", 1)[1])
    daily["email_notifications"] = {"on_failure": [me], "on_duration_warning_threshold_exceeded": [me],
                                    "no_alert_for_skipped_runs": True}
    setup = {
        "name": "mlb_performance_intelligence_setup",
        "description": "One-time setup: catalog mlb_intelligence, schemas, Volumes and metadata tables.",
        "tags": daily.get("tags", {}), "max_concurrent_runs": 1,
        "tasks": [
            {"task_key": "create_catalog_schemas", "notebook_task": {"notebook_path": notebook("setup/00_Create_Catalog_Schemas"), "source": "WORKSPACE"}},
            {"task_key": "create_metadata_tables", "depends_on": [{"task_key": "create_catalog_schemas"}],
             "notebook_task": {"notebook_path": notebook("setup/01_Create_Metadata_Tables"), "source": "WORKSPACE"}},
        ],
    }
    ids = {}
    for spec in (setup, daily):
        found = api("GET", "/api/2.2/jobs/list", query={"name": spec["name"]}).get("jobs", [])
        if found:
            ids[spec["name"]] = found[0]["job_id"]
            api("POST", "/api/2.2/jobs/reset", {"job_id": found[0]["job_id"], "new_settings": spec})
            action = "updated"
        else:
            ids[spec["name"]] = api("POST", "/api/2.2/jobs/create", spec)["job_id"]
            action = "created"
        print(f"{spec['name']}: {action} ({len(spec['tasks'])} tasks) -> {HOST}/jobs/{ids[spec['name']]}")

    # 3. Latest runs of the daily job
    runs = api("GET", "/api/2.2/jobs/runs/list", query={"job_id": ids[daily["name"]], "limit": 5}).get("runs", [])
    for r in runs:
        st = r.get("state", {})
        params = {p["name"]: p.get("value") for p in r.get("job_parameters", []) if p.get("name") == "mode"}
        print(f"run {r['run_id']} · {st.get('life_cycle_state')} · {st.get('result_state', '-')} · mode={params.get('mode', 'daily')} · {r.get('run_page_url', '')}")
    if not runs:
        print("No runs yet.")

    # 4. Self-healing: if the daily job has never succeeded and nothing is running, start one backfill
    #    (already extracted files are skipped, so it only fills what is missing in Silver/Gold).
    history = api("GET", "/api/2.2/jobs/runs/list", query={"job_id": ids[daily["name"]], "limit": 25}).get("runs", [])
    active = [r for r in history if r.get("state", {}).get("life_cycle_state") in ("QUEUED", "PENDING", "RUNNING", "TERMINATING", "BLOCKED")]
    ever_ok = any(r.get("state", {}).get("result_state") == "SUCCESS" for r in history)
    if not ever_ok and not active and os.environ.get("MLB_AUTO_BACKFILL", "true") == "true":
        new = api("POST", "/api/2.2/jobs/run-now", {"job_id": ids[daily["name"]], "job_parameters": {"mode": "backfill"}})
        print(f"\nNo successful run yet: started backfill run {new['run_id']} -> {HOST}/jobs/{ids[daily['name']]}/runs/{new['run_id']}")
    elif active:
        print(f"\nA run is in progress: {active[0]['run_id']} ({active[0]['state'].get('life_cycle_state')})")

    # 5. Diagnose the latest run that did not succeed: state and error of every task
    bad = next((r for r in runs if r.get("state", {}).get("result_state") not in (None, "SUCCESS")), None)
    if bad:
        detail = api("GET", "/api/2.2/jobs/runs/get", query={"run_id": bad["run_id"]})
        print(f"\nDiagnosis of run {bad['run_id']}: {detail.get('state', {}).get('state_message', '')[:400]}")
        for t in detail.get("tasks", []):
            st = t.get("state", {})
            line = f"  {t['task_key']:<24} {st.get('life_cycle_state')} {st.get('result_state', '')} {st.get('state_message', '')[:300]}"
            print(line)
            if st.get("result_state") in ("FAILED", "TIMEDOUT") or st.get("life_cycle_state") == "INTERNAL_ERROR":
                out = api("GET", "/api/2.2/jobs/runs/get-output", query={"run_id": t["run_id"]})
                print(f"    error: {(out.get('error') or '')[:600]}")
                print(f"    trace: {(out.get('error_trace') or '')[-1500:]}")


if __name__ == "__main__":
    main()
