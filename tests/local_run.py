"""Local end-to-end harness: runs the Databricks notebooks unchanged on a local Spark + Delta session.

It replaces only what Databricks provides (dbutils widgets and notebook context, display, Unity
Catalog). Tables go to the local `spark_catalog`, the raw archive to a local folder, and the
Bronze notebook switches from Auto Loader to an equivalent batch read (see its `ON_DATABRICKS` flag).

Usage (from the repository root):
    pip install pyspark==3.5.3 delta-spark==3.2.1 requests pandas
    python tests/local_run.py --start 2025-09-22 --end 2025-09-28        # a custom range
    python tests/local_run.py --backfill 2025                             # a full season
    python tests/local_run.py --daily                                     # daily mode (yesterday + lookback)
Set DELTA_JARS to a comma-separated list of local jars if Maven Central is not reachable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("MLB_LOCAL_WORKDIR", "/tmp/mlb_local"))
os.environ.setdefault("MLB_CATALOG", "spark_catalog")
os.environ.setdefault("MLB_RAW_ROOT", str(WORK / "raw"))
os.environ.setdefault("MLB_CHECKPOINT_ROOT", str(WORK / "checkpoints"))
os.environ.setdefault("MLB_EXPORT_DIR", str(WORK / "exports"))
sys.path.insert(0, str(REPO / "src" / "shared"))

PIPELINE = [
    "setup/01_Create_Metadata_Tables",
    "bronze/01_MLB_API_Extract",
    "bronze/02_MLB_API_Bronze",
    "silver/01_Silver_Dimensions",
    "silver/02_Silver_Games",
    "silver/03_Silver_Boxscores",
    "gold/01_Gold_Team_Metrics",
    "gold/02_Gold_Player_Metrics",
    "gold/03_Gold_Dominican_Players",
    "gold/04_Gold_Semantic_Layer",
    "gold/05_Gold_Game_Features",
    "ml/01_Win_Probability_Model",
    "quality/01_Data_Quality_Checks",
    "exports/01_Web_Platform_Export",
]


def build_spark():
    from pyspark.sql import SparkSession
    b = (SparkSession.builder.master("local[*]").appName("mlb-local")
         .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
         .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
         .config("spark.sql.warehouse.dir", str(WORK / "warehouse"))
         .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "6g"))
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.ui.enabled", "false").config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.session.timeZone", "UTC")
         .config("spark.sql.ansi.enabled", "true")  # same strict SQL mode as Databricks serverless
         .config("spark.hadoop.javax.jdo.option.ConnectionURL", f"jdbc:derby:;databaseName={WORK / 'metastore_db'};create=true")
         .enableHiveSupport())  # persistent local catalog, so --from-step can resume
    if os.environ.get("DELTA_JARS"):
        spark = b.config("spark.jars", os.environ["DELTA_JARS"]).getOrCreate()
    else:
        from delta import configure_spark_with_delta_pip
        spark = configure_spark_with_delta_pip(b).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    for s in ("bronze", "silver", "gold", "metadata", "quality"):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS spark_catalog.{s}")
    return spark


class _Widgets:
    def __init__(self, overrides):
        self.values, self.overrides = {}, overrides

    def text(self, name, default, label=None):
        self.values[name] = default

    def dropdown(self, name, default, choices, label=None):
        self.values[name] = default

    def get(self, name):
        return self.overrides.get(name, self.values[name])


class _Ctx:
    def __init__(self, path):
        self._p = path

    def __getattr__(self, item):  # entry_point.getDbutils().notebook().getContext().notebookPath().get()
        return lambda *a, **k: self if item != "get" else self._p


class FakeDbutils:
    def __init__(self, nb_path, overrides):
        self.widgets = _Widgets(overrides)
        self.notebook = type("N", (), {"entry_point": _Ctx(f"/Local/repo/src/{nb_path}")})()


def display(obj, n=20):
    if hasattr(obj, "show"):
        obj.show(n, truncate=60)
    else:
        print(obj.to_string() if hasattr(obj, "to_string") else obj)


def run_notebook(spark, nb_path, overrides):
    nb = json.loads((REPO / "src" / f"{nb_path}.ipynb").read_text())
    g = {"spark": spark, "dbutils": FakeDbutils(nb_path, overrides), "display": display, "__name__": "__main__"}
    t0 = time.time()
    print(f"\n{'=' * 100}\n▶ {nb_path}  {overrides or ''}\n{'=' * 100}")
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if src.lstrip().startswith("%"):
            continue
        exec(compile(src, nb_path, "exec"), g)
    print(f"✔ {nb_path} finished in {time.time() - t0:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--daily", action="store_true")
    mode.add_argument("--backfill", help="comma-separated seasons")
    mode.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--full-refresh", action="store_true", help="rebuild Silver facts from all Bronze history")
    ap.add_argument("--from-step", default=None, help="skip notebooks before this one (e.g. silver/01_Silver_Dimensions)")
    args = ap.parse_args()

    extract = {"max_workers": "8"}
    if args.daily:
        extract["mode"] = "daily"
    elif args.backfill:
        extract.update(mode="backfill", seasons=args.backfill)
    else:
        extract.update(start_date=args.start, end_date=args.end or args.start)

    spark = build_spark()
    steps = PIPELINE[PIPELINE.index(args.from_step):] if args.from_step else PIPELINE
    for nb in steps:
        params = extract if nb.endswith("Extract") else {}
        if args.full_refresh and nb.startswith("silver/"):
            params = {"full_refresh": "true"}
        run_notebook(spark, nb, params)


if __name__ == "__main__":
    main()
