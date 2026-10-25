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


def api(method, path, body=None, query=None):
    url = f"{HOST}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"::error::{method} {path} -> HTTP {e.code}: {e.read().decode()[:500]}")


def main():
    me = api("GET", "/api/2.0/preview/scim/v2/Me")["userName"]
    folder = f"/Users/{me}/{FOLDER_NAME}"
    print(f"Workspace user: {me}\nGit folder: {folder}")

    # 1. Git folder -> latest main (create it if it does not exist yet)
    repos = api("GET", "/api/2.0/repos", query={"path_prefix": folder}).get("repos", [])
    repo = next((r for r in repos if r.get("path") == folder), None)
    if repo is None:
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


if __name__ == "__main__":
    main()
