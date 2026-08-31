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
print("Building Analysis Dataset")
print("=" * 60)


# ============================================================
# 1. Load quality_test data
# ============================================================

patients = pd.read_sql(
    "SELECT * FROM quality_test.patients",
    engine
)

encounters = pd.read_sql(
    "SELECT * FROM quality_test.encounters",
    engine
)

print(f"\nInput patients:    {len(patients):,}")
print(f"Input encounters:  {len(encounters):,}")


# ============================================================
# 2. Patient-level quality flags
# ============================================================

# CQ002: BIRTHDATE missing
patients["flag_CQ002"] = patients["BIRTHDATE"].isna()

# VQ001: invalid GENDER code
patients["flag_VQ001"] = (
    ~patients["GENDER"].isin(["M", "F"]) &
    patients["GENDER"].notna()
)

# UQ001: duplicated patient ID
patients["duplicate_id"] = (
    patients["Id"].duplicated(keep=False)
)

# Number of Flag-level violations
patients["flag_count"] = (
    patients[
        ["flag_CQ002", "flag_VQ001"]
    ].sum(axis=1)
)


# ============================================================
# 3. Duplicate handling
# ============================================================

# Duplicate resolution policy:
# 1. Higher completeness
# 2. If tied, keep the first/original record
#
# The goal is NOT to remove all duplicated records.
# One representative record must remain.

quality_columns = [
    "Id",
    "BIRTHDATE",
    "GENDER"
]

patients["_completeness"] = (
    patients[quality_columns].notna().sum(axis=1)
)

patients = patients.sort_values(
    by=["Id", "_completeness"],
    ascending=[True, False]
)

analysis_patients = (
    patients
    .drop_duplicates(
        subset=["Id"],
        keep="first"
    )
    .copy()
)


# ============================================================
# 4. Remove records with missing Patient ID
# ============================================================

patient_id_missing_count = (
    analysis_patients["Id"].isna().sum()
)

analysis_patients = analysis_patients[
    analysis_patients["Id"].notna()
].copy()


# ============================================================
# 5. Remove temporary columns
# ============================================================

analysis_patients.drop(
    columns=["_completeness"],
    inplace=True
)


# ============================================================
# 6. Encounter-level quality checks
# ============================================================

encounters["START"] = pd.to_datetime(
    encounters["START"],
    errors="coerce"
)

encounters["STOP"] = pd.to_datetime(
    encounters["STOP"],
    errors="coerce"
)


# ------------------------------------------------------------
# RQ001: Referential Integrity
# ------------------------------------------------------------

valid_patient_ids = set(
    analysis_patients["Id"].dropna()
)

encounters["exclude_RQ001"] = (
    ~encounters["PATIENT"].isin(valid_patient_ids)
)


# ------------------------------------------------------------
# TQ001: Temporal consistency
# ------------------------------------------------------------

encounters["exclude_TQ001"] = (
    encounters["START"] > encounters["STOP"]
)


# ------------------------------------------------------------
# Final encounter exclusion
# ------------------------------------------------------------

encounters["exclude"] = (
    encounters[
        ["exclude_RQ001", "exclude_TQ001"]
    ].any(axis=1)
)

analysis_encounters = encounters[
    ~encounters["exclude"]
].copy()


# ============================================================
# 7. Save Analysis Dataset
# ============================================================

analysis_patients.to_sql(
    "patients",
    engine,
    schema="analysis",
    if_exists="replace",
    index=False
)

analysis_encounters.to_sql(
    "encounters",
    engine,
    schema="analysis",
    if_exists="replace",
    index=False
)


# ============================================================
# 8. Before / After Summary
# ============================================================

original_patient_count = len(
    pd.read_sql(
        "SELECT * FROM quality_test.patients",
        engine
    )
)

original_encounter_count = len(
    pd.read_sql(
        "SELECT * FROM quality_test.encounters",
        engine
    )
)

patient_excluded_count = (
    original_patient_count -
    len(analysis_patients)
)

encounter_excluded_count = (
    original_encounter_count -
    len(analysis_encounters)
)


print("\n" + "=" * 60)
print("Before / After Cohort")
print("=" * 60)

print(
    f"Patients:    "
    f"{original_patient_count:,} → "
    f"{len(analysis_patients):,}"
)

print(
    f"Encounters:  "
    f"{original_encounter_count:,} → "
    f"{len(analysis_encounters):,}"
)


# ============================================================
# 9. Exclusion Summary
# ============================================================

print("\n" + "=" * 60)
print("Exclusion Summary")
print("=" * 60)

print(
    f"Patient exclusions:   "
    f"{patient_excluded_count:,}"
)

print(
    f"Encounter exclusions: "
    f"{encounter_excluded_count:,}"
)

print(
    f"  - Referential Integrity: "
    f"{encounters['exclude_RQ001'].sum():,}"
)

print(
    f"  - Temporal:              "
    f"{encounters['exclude_TQ001'].sum():,}"
)


# ============================================================
# 10. Save confirmation
# ============================================================

print("\nSaved:")
print("analysis.patients")
print("analysis.encounters")


print("\n" + "=" * 60)
print("Analysis dataset construction completed")
print("=" * 60)