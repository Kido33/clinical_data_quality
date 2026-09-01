import os

import pandas as pd
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# Environment
# ============================================================

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


if not all([
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
]):
    pytest.skip(
        "Database environment variables are not configured.",
        allow_module_level=True,
    )


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


# ============================================================
# Database Connection
# ============================================================

def test_database_connection():

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        ).scalar()

    assert result == 1


# ============================================================
# Patient Quality Rules
# ============================================================

def test_cq001_patient_id_completeness():

    query = """
        SELECT COUNT(*) AS violations
        FROM quality_test.patients
        WHERE "Id" IS NULL
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) == 0


def test_cq002_birthdate_completeness():

    query = """
        SELECT COUNT(*) AS violations
        FROM quality_test.patients
        WHERE "BIRTHDATE" IS NULL
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) == 1


def test_vq001_gender_validity():

    query = """
        SELECT COUNT(*) AS violations
        FROM quality_test.patients
        WHERE "GENDER" IS NOT NULL
          AND "GENDER" NOT IN ('M', 'F')
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) == 1


def test_uq001_patient_id_uniqueness():

    query = """
        SELECT COUNT(*) AS duplicate_group_rows
        FROM (
            SELECT "Id"
            FROM quality_test.patients
            GROUP BY "Id"
            HAVING COUNT(*) > 1
        ) d
        JOIN quality_test.patients p
          ON p."Id" = d."Id"
    """

    result = pd.read_sql(query, engine)

    assert int(
        result.loc[0, "duplicate_group_rows"]
    ) == 2


# ============================================================
# Encounter Quality Rules
# ============================================================

def test_rq001_encounter_patient_referential_integrity():

    query = """
        SELECT COUNT(*) AS violations
        FROM quality_test.encounters e
        LEFT JOIN quality_test.patients p
          ON e."PATIENT" = p."Id"
        WHERE p."Id" IS NULL
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) == 0


def test_tq001_encounter_temporal_consistency():

    query = """
        SELECT COUNT(*) AS violations
        FROM quality_test.encounters
        WHERE "START"::timestamp > "STOP"::timestamp
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) == 10


# ============================================================
# Analysis Dataset
# ============================================================

def test_analysis_patient_count():

    query = """
        SELECT COUNT(*) AS row_count
        FROM analysis.patients
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "row_count"]) == 18


def test_analysis_encounter_count():

    query = """
        SELECT COUNT(*) AS row_count
        FROM analysis.encounters
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "row_count"]) == 1032


def test_analysis_encounters_temporally_valid():

    query = """
        SELECT COUNT(*) AS violations
        FROM analysis.encounters
        WHERE "START" > "STOP"
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) == 0


# ============================================================
# Quality Metrics
# ============================================================

def test_quality_metrics_contains_all_rules():

    query = """
        SELECT rule_id
        FROM quality.quality_metrics
        ORDER BY rule_id
    """

    result = pd.read_sql(query, engine)

    expected_rules = [
        "CQ001",
        "CQ002",
        "RQ001",
        "TQ001",
        "UQ001",
        "VQ001",
    ]

    assert result["rule_id"].tolist() == expected_rules


def test_quality_metric_values():

    query = """
        SELECT rule_id, quality_rate
        FROM quality.quality_metrics
        ORDER BY rule_id
    """

    result = pd.read_sql(query, engine)

    expected = {
        "CQ001": 100.00,
        "CQ002": 94.74,
        "RQ001": 100.00,
        "TQ001": 99.04,
        "UQ001": 89.47,
        "VQ001": 94.74,
    }

    actual = dict(
        zip(
            result["rule_id"],
            result["quality_rate"]
        )
    )

    assert set(actual.keys()) == set(expected.keys())

    for rule_id, expected_rate in expected.items():

        assert float(actual[rule_id]) == pytest.approx(
            expected_rate,
            abs=0.01
        )