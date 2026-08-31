import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


# ============================================================
# 0. Database connection
# ============================================================

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


print("=" * 60)
print("Clinical Data Quality Report")
print("=" * 60)


# ============================================================
# 1. Load validation results
# ============================================================

rule_results = pd.read_sql(
    "SELECT * FROM quality.rule_results",
    engine
)

print("\nLoaded rule results:")
print(rule_results.to_string(index=False))


# ============================================================
# 2. Load dataset counts
# ============================================================

quality_patients = pd.read_sql(
    "SELECT * FROM quality_test.patients",
    engine
)

quality_encounters = pd.read_sql(
    "SELECT * FROM quality_test.encounters",
    engine
)

analysis_patients = pd.read_sql(
    "SELECT * FROM analysis.patients",
    engine
)

analysis_encounters = pd.read_sql(
    "SELECT * FROM analysis.encounters",
    engine
)


# ============================================================
# 3. Dataset summary
# ============================================================

dataset_summary = pd.DataFrame([
    {
        "table_name": "patients",
        "before_rows": len(quality_patients),
        "after_rows": len(analysis_patients),
        "excluded_rows": (
            len(quality_patients) -
            len(analysis_patients)
        ),
        "exclusion_rate": (
            (
                len(quality_patients) -
                len(analysis_patients)
            )
            / len(quality_patients)
        )
    },
    {
        "table_name": "encounters",
        "before_rows": len(quality_encounters),
        "after_rows": len(analysis_encounters),
        "excluded_rows": (
            len(quality_encounters) -
            len(analysis_encounters)
        ),
        "exclusion_rate": (
            (
                len(quality_encounters) -
                len(analysis_encounters)
            )
            / len(quality_encounters)
        )
    }
])


# ============================================================
# 4. Rule-level quality report
# ============================================================

quality_report = rule_results.copy()

quality_report["violation_rate"] = (
    quality_report["violation_count"]
    / quality_report["table_name"].map({
        "patients": len(quality_patients),
        "encounters": len(quality_encounters)
    })
)


# ============================================================
# 5. Error injection summary
# ============================================================

injection_log = pd.read_sql(
    "SELECT * FROM quality_test.injection_log",
    engine
)

injection_summary = injection_log.copy()

injection_summary["actual_rate"] = (
    injection_summary["actual_rows"]
    / injection_summary["table_name"].map({
        "patients": len(quality_patients),
        "encounters": len(quality_encounters)
    })
)


# ============================================================
# 6. Flag summary
# ============================================================

flag_summary = pd.DataFrame([
    {
        "table_name": "patients",
        "rule_id": "CQ002",
        "flagged_rows": int(
            quality_patients["BIRTHDATE"].isna().sum()
        )
    },
    {
        "table_name": "patients",
        "rule_id": "VQ001",
        "flagged_rows": int(
            (
                ~quality_patients["GENDER"].isin(["M", "F"])
                & quality_patients["GENDER"].notna()
            ).sum()
        )
    }
])


# ============================================================
# 7. Save reports
# ============================================================

os.makedirs("reports", exist_ok=True)

rule_results.to_csv(
    "reports/rule_results.csv",
    index=False
)

quality_report.to_csv(
    "reports/quality_report.csv",
    index=False
)

dataset_summary.to_csv(
    "reports/dataset_summary.csv",
    index=False
)

injection_summary.to_csv(
    "reports/injection_summary.csv",
    index=False
)

flag_summary.to_csv(
    "reports/flag_summary.csv",
    index=False
)


# ============================================================
# 8. Console output
# ============================================================

print("\n" + "=" * 60)
print("Dataset Summary")
print("=" * 60)

print(
    dataset_summary.to_string(
        index=False
    )
)


print("\n" + "=" * 60)
print("Rule Summary")
print("=" * 60)

print(
    quality_report[
        [
            "rule_id",
            "category",
            "table_name",
            "column_name",
            "violation_count",
            "severity",
            "violation_rate"
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 60)
print("Error Injection Summary")
print("=" * 60)

print(
    injection_summary[
        [
            "error_type",
            "table_name",
            "column_name",
            "target_rows",
            "actual_rows",
            "target_rate",
            "actual_rate"
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 60)
print("Reports saved")
print("=" * 60)

print("reports/rule_results.csv")
print("reports/quality_report.csv")
print("reports/dataset_summary.csv")
print("reports/injection_summary.csv")
print("reports/flag_summary.csv")

print("\n" + "=" * 60)
print("Quality report generation completed")
print("=" * 60)