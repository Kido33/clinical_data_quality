from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

RANDOM_SEED = 42

# Target injection rates
MISSING_RATE = 0.03
INVALID_CODE_RATE = 0.02
DUPLICATE_RATE = 0.01
TEMPORAL_RATE = 0.01


# ============================================================
# Database
# ============================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


# ============================================================
# Utility
# ============================================================

def target_count(total_rows: int, rate: float) -> int:
    """
    Calculate number of rows affected by an injection rule.

    Uses floor to avoid exceeding the requested rate.
    Minimum 1 row is guaranteed when the dataset is non-empty.
    """
    if total_rows == 0:
        return 0

    count = int(np.floor(total_rows * rate))

    return max(count, 1)


def print_section(title: str):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


# ============================================================
# Load raw data
# ============================================================

print_section("Loading raw data")

with engine.connect() as connection:

    patients = pd.read_sql(
        text('SELECT * FROM raw.patients'),
        connection
    )

    encounters = pd.read_sql(
        text('SELECT * FROM raw.encounters'),
        connection
    )

print(f"Patients:    {len(patients):,}")
print(f"Encounters:  {len(encounters):,}")


# ============================================================
# Create independent copies
# ============================================================

patients_test = patients.copy(deep=True)
encounters_test = encounters.copy(deep=True)

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# Error Injection Log
# ============================================================

injection_log = []


def log_injection(
    error_type,
    table_name,
    column_name,
    target_rows,
    actual_rows
):
    injection_log.append(
        {
            "error_type": error_type,
            "table_name": table_name,
            "column_name": column_name,
            "target_rows": target_rows,
            "actual_rows": actual_rows,
            "target_rate": (
                target_rows / len(patients)
                if table_name == "patients"
                else target_rows / len(encounters)
            ),
            "actual_rate": (
                actual_rows / len(patients)
                if table_name == "patients"
                else actual_rows / len(encounters)
            ),
        }
    )


# ============================================================
# 1. Missing Value Injection
# ============================================================

print_section("1. Missing Value Injection")

# Target: patients.BIRTHDATE
n_missing = target_count(
    len(patients_test),
    MISSING_RATE
)

missing_idx = rng.choice(
    patients_test.index,
    size=n_missing,
    replace=False
)

patients_test.loc[missing_idx, "BIRTHDATE"] = pd.NA

print(
    f"patients.BIRTHDATE → "
    f"{n_missing} rows set to NULL"
)

log_injection(
    error_type="Missing",
    table_name="patients",
    column_name="BIRTHDATE",
    target_rows=n_missing,
    actual_rows=n_missing,
)


# ============================================================
# 2. Invalid Code Injection
# ============================================================

print_section("2. Invalid Code Injection")

# Target: patients.GENDER
n_invalid = target_count(
    len(patients_test),
    INVALID_CODE_RATE
)

invalid_idx = rng.choice(
    patients_test.index,
    size=n_invalid,
    replace=False
)

patients_test.loc[invalid_idx, "GENDER"] = "X"

print(
    f"patients.GENDER → "
    f"{n_invalid} rows set to invalid code 'X'"
)

log_injection(
    error_type="InvalidCode",
    table_name="patients",
    column_name="GENDER",
    target_rows=n_invalid,
    actual_rows=n_invalid,
)


# ============================================================
# 3. Duplicate Injection
# ============================================================

print_section("3. Duplicate Injection")

n_duplicate = target_count(
    len(patients_test),
    DUPLICATE_RATE
)

duplicate_idx = rng.choice(
    patients_test.index,
    size=n_duplicate,
    replace=False
)

duplicate_rows = patients_test.loc[
    duplicate_idx
].copy()

patients_test = pd.concat(
    [
        patients_test,
        duplicate_rows
    ],
    ignore_index=True
)

print(
    f"patients → "
    f"{n_duplicate} duplicate rows added"
)

log_injection(
    error_type="Duplicate",
    table_name="patients",
    column_name="Id",
    target_rows=n_duplicate,
    actual_rows=n_duplicate,
)


# ============================================================
# 4. Temporal Error Injection
# ============================================================

print_section("4. Temporal Error Injection")

# Target: encounters
# Create STOP < START
n_temporal = target_count(
    len(encounters_test),
    TEMPORAL_RATE
)

temporal_idx = rng.choice(
    encounters_test.index,
    size=n_temporal,
    replace=False
)

# Make STOP earlier than START.
#
# We use START as the baseline and subtract one day.
# This creates a clear temporal inconsistency:
#
# STOP < START
#
start_dates = pd.to_datetime(
    encounters_test.loc[
        temporal_idx,
        "START"
    ],
    errors="coerce"
)

encounters_test.loc[
    temporal_idx,
    "STOP"
] = (
    start_dates - pd.Timedelta(days=1)
).dt.strftime(
    "%Y-%m-%dT%H:%M:%SZ"
)

print(
    f"encounters.START/STOP → "
    f"{n_temporal} rows modified"
)

log_injection(
    error_type="Temporal",
    table_name="encounters",
    column_name="START/STOP",
    target_rows=n_temporal,
    actual_rows=n_temporal,
)


# ============================================================
# Create quality_test schema
# ============================================================

print_section("Creating quality_test schema")

with engine.begin() as connection:

    connection.execute(
        text(
            "CREATE SCHEMA IF NOT EXISTS quality_test"
        )
    )


# ============================================================
# Save test datasets
# ============================================================

print_section("Saving injected datasets")

patients_test.to_sql(
    "patients",
    engine,
    schema="quality_test",
    if_exists="replace",
    index=False,
)

encounters_test.to_sql(
    "encounters",
    engine,
    schema="quality_test",
    if_exists="replace",
    index=False,
)

print(
    f"quality_test.patients: "
    f"{len(patients_test):,} rows"
)

print(
    f"quality_test.encounters: "
    f"{len(encounters_test):,} rows"
)


# ============================================================
# Save injection log
# ============================================================

injection_df = pd.DataFrame(
    injection_log
)

injection_df.to_sql(
    "injection_log",
    engine,
    schema="quality_test",
    if_exists="replace",
    index=False,
)


# ============================================================
# Verification
# ============================================================

print_section("Injection verification")

with engine.connect() as connection:

    patients_count = connection.execute(
        text(
            "SELECT COUNT(*) "
            "FROM quality_test.patients"
        )
    ).scalar()

    encounters_count = connection.execute(
        text(
            "SELECT COUNT(*) "
            "FROM quality_test.encounters"
        )
    ).scalar()

    injection_count = connection.execute(
        text(
            "SELECT COUNT(*) "
            "FROM quality_test.injection_log"
        )
    ).scalar()


print(
    f"quality_test.patients:     "
    f"{patients_count:,}"
)

print(
    f"quality_test.encounters:   "
    f"{encounters_count:,}"
)

print(
    f"quality_test.injection_log: "
    f"{injection_count:,}"
)


# ============================================================
# Summary
# ============================================================

print_section("Injection summary")

print(
    injection_df[
        [
            "error_type",
            "table_name",
            "column_name",
            "target_rows",
            "actual_rows",
            "target_rate",
            "actual_rate",
        ]
    ].to_string(index=False)
)

print()
print("=" * 60)
print("Error injection completed successfully")
print("=" * 60)
print(f"Random seed: {RANDOM_SEED}")