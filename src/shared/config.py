"""Project-wide configuration for the MLB Performance Intelligence Platform.

Every notebook imports this module so table names, paths and business rules live in one place.
The catalog and storage roots can be overridden with environment variables (used by the local
test harness in `tests/`); in Databricks the defaults apply.
"""
import os

PROJECT = "mlb_performance_intelligence"
CATALOG = os.environ.get("MLB_CATALOG", "mlb_intelligence")
TIMEZONE = "America/Santo_Domingo"

# Unity Catalog Volumes: append-only landing archive for API responses and streaming checkpoints
RAW_ROOT = os.environ.get("MLB_RAW_ROOT", f"/Volumes/{CATALOG}/bronze/mlb_api_raw")
CHECKPOINT_ROOT = os.environ.get("MLB_CHECKPOINT_ROOT", f"/Volumes/{CATALOG}/metadata/checkpoints")

# Scope: regular season and every postseason round. Spring training (S), exhibitions (E)
# and the All-Star Game (A) are excluded because they do not count toward official stats.
GAME_TYPES = ("R", "F", "D", "L", "W")
GAME_TYPE_NAMES = {
    "R": "Regular Season",
    "F": "Wild Card",
    "D": "Division Series",
    "L": "League Championship Series",
    "W": "World Series",
}
POSTSEASON_TYPES = ("F", "D", "L", "W")

DEFAULT_BACKFILL_SEASONS = "2024,2025,2026"
DOMINICAN_COUNTRY = "Dominican Republic"
# The API occasionally returns a country code instead of the country name; normalize in Silver
COUNTRY_ALIASES = {"VEN": "Venezuela", "DOM": "Dominican Republic", "D.R.": "Dominican Republic",
                   "US": "USA", "United States": "USA", "PR": "Puerto Rico", "CUB": "Cuba", "MEX": "Mexico"}

# Sabermetric constants
PYTHAGOREAN_EXPONENT = 1.83   # Baseball-Reference "Pythagenport" fixed exponent
QUALIFIED_PA_PER_GAME = 3.1   # MLB batting-title rule
QUALIFIED_IP_PER_GAME = 1.0   # MLB ERA-title rule


def table(schema: str, name: str) -> str:
    """Fully qualified Unity Catalog table name."""
    return f"{CATALOG}.{schema}.{name}"


# Bronze
BRONZE_API_RESPONSES = table("bronze", "mlb_api_responses")

# Metadata
PIPELINE_RUNS = table("metadata", "pipeline_runs")
EXTRACT_REGISTER = table("metadata", "extract_register")
WATERMARKS = table("metadata", "watermarks")

# Quality
DQ_RESULTS = table("quality", "dq_results")
