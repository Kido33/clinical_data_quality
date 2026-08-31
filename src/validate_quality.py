import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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
print("Clinical Data Quality Validation")
print("=" * 60)


# ------------------------------------------------------------
# 1. Patients
# ------------------------------------------------------------

print("\n[1] Patients Quality Check")

patients = pd.read_sql(
    """
    SELECT *
    FROM quality_test.patients
    """,
    engine
)

patient_results = []

# CQ001: Primary key null
null_id = patients["Id"].isna().sum()

patient_results.append({
    "rule_id": "CQ001",
    "category": "Completeness",
    "table_name": "patients",
    "column_name": "Id",
    "violation_count": int(null_id),
    "severity": "Exclude"
})

# CQ002: Birthdate missing
null_birthdate = patients["BIRTHDATE"].isna().sum()

patient_results.append({
    "rule_id": "CQ002",
    "category": "Completeness",
    "table_name": "patients",
    "column_name": "BIRTHDATE",
    "violation_count": int(null_birthdate),
    "severity": "Flag"
})

# VQ001: Invalid gender
invalid_gender = (
    ~patients["GENDER"].isin(["M", "F"]) &
    patients["GENDER"].notna()
).sum()

patient_results.append({
    "rule_id": "VQ001",
    "category": "Validity",
    "table_name": "patients",
    "column_name": "GENDER",
    "violation_count": int(invalid_gender),
    "severity": "Flag"
})

# UQ001: Duplicate patient ID
duplicate_patient_ids = (
    patients["Id"]
    .duplicated(keep=False)
    .sum()
)

patient_results.append({
    "rule_id": "UQ001",
    "category": "Uniqueness",
    "table_name": "patients",
    "column_name": "Id",
    "violation_count": int(duplicate_patient_ids),
    "severity": "Exclude"
})


# ------------------------------------------------------------
# 2. Encounters
# ------------------------------------------------------------

print("[2] Encounters Quality Check")

encounters = pd.read_sql(
    """
    SELECT *
    FROM quality_test.encounters
    """,
    engine
)

encounter_results = []

# RQ001: Patient FK
patient_ids = set(patients["Id"].dropna())

orphan_patients = (
    ~encounters["PATIENT"].isin(patient_ids)
).sum()

encounter_results.append({
    "rule_id": "RQ001",
    "category": "Referential Integrity",
    "table_name": "encounters",
    "column_name": "PATIENT",
    "violation_count": int(orphan_patients),
    "severity": "Exclude"
})

# TQ001: START > STOP
encounters["START"] = pd.to_datetime(
    encounters["START"],
    errors="coerce"
)

encounters["STOP"] = pd.to_datetime(
    encounters["STOP"],
    errors="coerce"
)

temporal_errors = (
    encounters["START"] > encounters["STOP"]
).sum()

encounter_results.append({
    "rule_id": "TQ001",
    "category": "Temporal",
    "table_name": "encounters",
    "column_name": "START/STOP",
    "violation_count": int(temporal_errors),
    "severity": "Exclude"
})


# ------------------------------------------------------------
# 3. Result table
# ------------------------------------------------------------

results = pd.DataFrame(
    patient_results + encounter_results
)

print("\n" + "=" * 60)
print("Validation Results")
print("=" * 60)

print(
    results[
        [
            "rule_id",
            "category",
            "table_name",
            "column_name",
            "violation_count",
            "severity"
        ]
    ].to_string(index=False)
)


# ------------------------------------------------------------
# 4. Save quality results
# ------------------------------------------------------------

with engine.begin() as connection:

    connection.execute(
        text(
            """
            CREATE SCHEMA IF NOT EXISTS quality
            """
        )
    )

    results.to_sql(
        "rule_results",
        connection,
        schema="quality",
        if_exists="replace",
        index=False
    )

print("\nSaved → quality.rule_results")

print("\n" + "=" * 60)
print("Validation completed successfully")
print("=" * 60)