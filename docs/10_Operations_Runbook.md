# Operations Runbook

## MLB Performance Intelligence Platform

Everything runs by itself every day. This page explains the cycle, how to check it and what to do when
something fails.

---

## 1. Daily cycle (America/Santo_Domingo)

| Time | Step | Where |
|---|---|---|
| 05:31 | Pull the Databricks Git folder to `main`, reset both jobs from the repository | GitHub Actions `deploy-mlb-databricks.yml` (portfolio repository) |
| 06:07 | Daily job, 13 tasks: yesterday's games + 3 days of lookback, upcoming calendar, Silver, Gold, model, quality, export | Databricks Lakeflow Jobs |
| 07:41, 09:41, 11:41, 14:41, 18:41 | Download the export, validate it, rebuild and publish the page if the data changed | GitHub Actions `refresh-mlb-platform.yml` |

GitHub schedules are best-effort (they can be late or skipped); the several refresh attempts make the daily
publication reliable. A run without new data publishes nothing.

## 2. Built-in safeguards

| Safeguard | Setting |
|---|---|
| Task retries | Extract: 2 retries; other tasks: 1 retry, 2 minutes apart |
| Timeouts | Extract 90 min, other tasks 20–30 min, whole job 2 h |
| Alerts | E-mail on failure and when a run lasts more than 1 hour |
| Concurrency | One run at a time |
| Quality gate | A CRITICAL data-quality failure stops the export, so the site keeps the last good data |
| Publish gate | The page is published only if the export is complete, recent and passed the critical checks |

## 3. How to check that it worked

1. **Jobs & Pipelines → mlb_performance_intelligence_daily → Runs**: today's run is green.
2. The web platform header shows **"Data through <yesterday's date>"**.
3. Details per task: `SELECT * FROM mlb_intelligence.metadata.pipeline_runs ORDER BY started_at DESC`.
4. Quality: the **Quality** page of the platform, or `quality.dq_results`.

## 4. Common situations

| Situation | What to do |
|---|---|
| The job failed | Open the failed task in *Runs* to see the error. Fix the code in GitHub; the next 05:31 deploy picks it up, or re-run the failed tasks with **Repair run** |
| The page did not update but the job is green | In GitHub → Actions → *Refresh MLB Performance Intelligence Platform* → **Run workflow** |
| Historical reload | Job → **Run now with different parameters**: `mode=backfill`, `seasons=2024,2025,2026` (already-landed files are skipped) |
| Rebuild Silver from Bronze | Same, with `full_refresh=true` |
| New season | Add it to the `seasons` parameter for the backfill; the daily mode follows the calendar automatically |
| GitHub secret expired | Create a new token in Databricks (**Settings → Developer → Access tokens**) and replace `DATABRICKS_TOKEN` in the portfolio repository (**Settings → Secrets and variables → Actions**) |

## 5. First-time deployment

1. Databricks: **Workspace → Create → Git folder** with this repository.
2. Open `src/setup/02_Deploy_Jobs` and run it: it creates the catalog, the jobs and (optionally) starts the backfill.
3. GitHub: add the secrets `DATABRICKS_HOST` and `DATABRICKS_TOKEN` to the repository that publishes the page.
