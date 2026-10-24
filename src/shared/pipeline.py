"""Reusable pipeline utilities: run logging, Delta MERGE upserts, incremental watermarks,
reading the latest API payloads from Bronze, and data-quality result recording.

Written once here instead of being copied into every notebook (the v1 pipeline duplicated
its logging function in three places).
"""
from __future__ import annotations

import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

import config as C


def new_run_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Run logging
# ---------------------------------------------------------------------------

class _Step:
    def __init__(self):
        self.records = 0
        self.message = ""


@contextmanager
def log_step(spark: SparkSession, run_id: str, layer: str, task: str, window: str = ""):
    """Log one pipeline step to metadata.pipeline_runs (SUCCESS or FAILED with traceback).

        with log_step(spark, RUN_ID, "silver", "silver_games", "2026-10-21..2026-10-23") as step:
            ...
            step.records = n
    """
    started = utc_now()
    step = _Step()
    status, message = "SUCCESS", ""
    try:
        yield step
        message = step.message or "OK"
    except Exception:
        status, message = "FAILED", traceback.format_exc()[-4000:]
        raise
    finally:
        ended = utc_now()
        row = [(C.PROJECT, run_id, layer, task, status, message, window, int(step.records or 0),
                started, ended, float((ended - started).total_seconds()))]
        spark.createDataFrame(row, (
            "pipeline_name string, run_id string, layer string, task string, status string, "
            "message string, execution_window string, records_processed long, started_at timestamp, "
            "ended_at timestamp, duration_seconds double")).write.format("delta").mode("append").saveAsTable(C.PIPELINE_RUNS)


# ---------------------------------------------------------------------------
# Delta writes
# ---------------------------------------------------------------------------

def merge_upsert(spark: SparkSession, df: DataFrame, target: str, keys: list[str],
                 update_condition: str | None = None, comment: str | None = None) -> int:
    """Idempotent upsert: creates the table on first run, otherwise MERGE on `keys`.
    `update_condition` (SQL over aliases t/s) can block regressive updates."""
    n = df.count()
    if not spark.catalog.tableExists(target):
        df.write.format("delta").saveAsTable(target)
        if comment:
            spark.sql(f"COMMENT ON TABLE {target} IS '{comment}'")
        return n
    if n == 0:
        return 0
    view = f"_src_{uuid.uuid4().hex[:8]}"
    df.createOrReplaceTempView(view)
    on = " AND ".join(f"t.{k} <=> s.{k}" for k in keys)
    cond = f" AND ({update_condition})" if update_condition else ""
    spark.sql(f"""
        MERGE INTO {target} t USING {view} s ON {on}
        WHEN MATCHED{cond} THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *""")
    spark.catalog.dropTempView(view)
    return n


def replace_table(spark: SparkSession, df: DataFrame, target: str, comment: str | None = None) -> int:
    """Full refresh for Gold aggregates (small, recomputed from Silver every run)."""
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
    if comment:
        spark.sql(f"COMMENT ON TABLE {target} IS '{comment}'")
    return spark.table(target).count()


# ---------------------------------------------------------------------------
# Incremental processing
# ---------------------------------------------------------------------------

def get_watermark(spark: SparkSession, consumer: str):
    rows = spark.sql(f"SELECT high_watermark FROM {C.WATERMARKS} WHERE consumer = '{consumer}'").collect()
    return rows[0][0] if rows else None


def set_watermark(spark: SparkSession, consumer: str, value) -> None:
    if value is None:
        return
    spark.createDataFrame([(consumer, value, utc_now())],
                          "consumer string, high_watermark timestamp, updated_at timestamp") \
        .createOrReplaceTempView("_wm")
    spark.sql(f"""
        MERGE INTO {C.WATERMARKS} t USING _wm s ON t.consumer = s.consumer
        WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *""")


def latest_payloads(spark: SparkSession, endpoint: str, since=None) -> DataFrame:
    """Latest successful payload per request_key for one endpoint, limited to keys that received
    a new Bronze row after `since` (None = full history). Columns: request_key, payload,
    extracted_at, _ingested_at."""
    df = spark.table(C.BRONZE_API_RESPONSES).where((F.col("endpoint") == endpoint) & (F.col("status_code") == 200))
    if since is not None:
        changed = df.where(F.col("_ingested_at") > F.lit(since)).select("request_key").distinct()
        df = df.join(changed, "request_key", "left_semi")
    w = Window.partitionBy("request_key").orderBy(F.col("extracted_at").desc(), F.col("_ingested_at").desc())
    return (df.withColumn("_rn", F.row_number().over(w)).where("_rn = 1")
              .select("request_key", "payload", "extracted_at", "_ingested_at"))


def max_ingested(df: DataFrame):
    return df.agg(F.max("_ingested_at")).collect()[0][0]


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def record_dq(spark: SparkSession, run_id: str, results: list[dict]) -> DataFrame:
    """results: dicts with check_id, check_name, layer, table_name, severity (CRITICAL/WARNING),
    failed_rows, checked_rows, details. Status is derived from failed_rows."""
    now = utc_now()
    rows = [(run_id, r["check_id"], r["check_name"], r["layer"], r["table_name"], r["severity"],
             "PASS" if int(r["failed_rows"]) == 0 else "FAIL", int(r["failed_rows"]),
             int(r.get("checked_rows", 0)), r.get("details", ""), now) for r in results]
    df = spark.createDataFrame(rows, (
        "run_id string, check_id string, check_name string, layer string, table_name string, "
        "severity string, status string, failed_rows long, checked_rows long, details string, "
        "checked_at timestamp"))
    df.write.format("delta").mode("append").saveAsTable(C.DQ_RESULTS)
    return df
