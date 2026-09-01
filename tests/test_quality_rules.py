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

    assert int(result.loc[0, "violations"]) > 0


def test_vq001_gender_validity():

    query = """
        SELECT COUNT(*) AS violations
        FROM quality_test.patients
        WHERE "GENDER" IS NOT NULL
          AND "GENDER" NOT IN ('M', 'F')
    """

    result = pd.read_sql(query, engine)

    assert int(result.loc[0, "violations"]) > 0


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
    ) > 0


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

    violations = int(result.loc[0, "violations"])

    # Controlled temporal errors must exist.
    assert violations > 0


# ============================================================
# Analysis Dataset
# ============================================================

def test_analysis_patient_count():

    query = """
        SELECT COUNT(*) AS row_count
        FROM analysis.patients
    """

    result = pd.read_sql(query, engine)

    analysis_count = int(
        result.loc[0, "row_count"]
    )

    expected_query = """
        SELECT COUNT(*) AS row_count
        FROM (
            SELECT DISTINCT ON ("Id") "Id"
            FROM quality_test.patients
            WHERE "Id" IS NOT NULL
            ORDER BY
                "Id",
                (
                    CASE WHEN "BIRTHDATE" IS NOT NULL THEN 1 ELSE 0 END
                    +
                    CASE WHEN "GENDER" IS NOT NULL THEN 1 ELSE 0 END
                ) DESC
        ) p
    """

    expected_result = pd.read_sql(
        expected_query,
        engine
    )

    expected_count = int(
        expected_result.loc[0, "row_count"]
    )

    assert analysis_count == expected_count


def test_analysis_encounter_count():

    query = """
        SELECT COUNT(*) AS row_count
        FROM analysis.encounters
    """

    result = pd.read_sql(query, engine)

    analysis_count = int(
        result.loc[0, "row_count"]
    )

    expected_query = """
        SELECT COUNT(*) AS row_count
        FROM quality_test.encounters e
        INNER JOIN analysis.patients p
          ON e."PATIENT" = p."Id"
        WHERE e."START"::timestamp <= e."STOP"::timestamp
    """

    expected_result = pd.read_sql(
        expected_query,
        engine
    )

    expected_count = int(
        expected_result.loc[0, "row_count"]
    )

    assert analysis_count == expected_count


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
        SELECT
            rule_id,
            quality_rate
        FROM quality.quality_metrics
        ORDER BY rule_id
    """

    metrics = pd.read_sql(
        query,
        engine
    )

    assert len(metrics) == 6

    assert metrics["quality_rate"].between(
        0,
        100
    ).all()

    # --------------------------------------------------------
    # CQ001
    # --------------------------------------------------------

    cq001 = pd.read_sql(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE "Id" IS NULL
            ) AS violations,
            COUNT(*) AS total
        FROM quality_test.patients
        """,
        engine
    )

    expected_cq001 = (
        100
        * (
            1
            - (
                cq001.loc[0, "violations"]
                / cq001.loc[0, "total"]
            )
        )
    )

    actual_cq001 = float(
        metrics.loc[
            metrics["rule_id"] == "CQ001",
            "quality_rate"
        ].iloc[0]
    )

    assert actual_cq001 == pytest.approx(
        expected_cq001,
        abs=0.01
    )

    # --------------------------------------------------------
    # CQ002
    # --------------------------------------------------------

    cq002 = pd.read_sql(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE "BIRTHDATE" IS NULL
            ) AS violations,
            COUNT(*) AS total
        FROM quality_test.patients
        """,
        engine
    )

    expected_cq002 = (
        100
        * (
            1
            - (
                cq002.loc[0, "violations"]
                / cq002.loc[0, "total"]
            )
        )
    )

    actual_cq002 = float(
        metrics.loc[
            metrics["rule_id"] == "CQ002",
            "quality_rate"
        ].iloc[0]
    )

    assert actual_cq002 == pytest.approx(
        expected_cq002,
        abs=0.01
    )

    # --------------------------------------------------------
    # VQ001
    # --------------------------------------------------------

    vq001 = pd.read_sql(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE "GENDER" IS NOT NULL
                  AND "GENDER" NOT IN ('M', 'F')
            ) AS violations,
            COUNT(*) AS total
        FROM quality_test.patients
        """,
        engine
    )

    expected_vq001 = (
        100
        * (
            1
            - (
                vq001.loc[0, "violations"]
                / vq001.loc[0, "total"]
            )
        )
    )

    actual_vq001 = float(
        metrics.loc[
            metrics["rule_id"] == "VQ001",
            "quality_rate"
        ].iloc[0]
    )

    assert actual_vq001 == pytest.approx(
        expected_vq001,
        abs=0.01
    )

    # --------------------------------------------------------
    # UQ001
    # --------------------------------------------------------

    uq001 = pd.read_sql(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT "Id") AS unique_ids
        FROM quality_test.patients
        """,
        engine
    )

    duplicate_rows = (
        uq001.loc[0, "total"]
        - uq001.loc[0, "unique_ids"]
    )

    expected_uq001 = (
        100
        * (
            1
            - (
                duplicate_rows
                / uq001.loc[0, "total"]
            )
        )
    )

    actual_uq001 = float(
        metrics.loc[
            metrics["rule_id"] == "UQ001",
            "quality_rate"
        ].iloc[0]
    )

    assert actual_uq001 == pytest.approx(
        expected_uq001,
        abs=0.01
    )

    # --------------------------------------------------------
    # RQ001
    # --------------------------------------------------------

    rq001 = pd.read_sql(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE p."Id" IS NULL
            ) AS violations,
            COUNT(*) AS total
        FROM quality_test.encounters e
        LEFT JOIN quality_test.patients p
          ON e."PATIENT" = p."Id"
        """,
        engine
    )

    expected_rq001 = (
        100
        * (
            1
            - (
                rq001.loc[0, "violations"]
                / rq001.loc[0, "total"]
            )
        )
    )

    actual_rq001 = float(
        metrics.loc[
            metrics["rule_id"] == "RQ001",
            "quality_rate"
        ].iloc[0]
    )

    assert actual_rq001 == pytest.approx(
        expected_rq001,
        abs=0.01
    )

    # --------------------------------------------------------
    # TQ001
    # --------------------------------------------------------

    tq001 = pd.read_sql(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE "START"::timestamp > "STOP"::timestamp
            ) AS violations,
            COUNT(*) AS total
        FROM quality_test.encounters
        """,
        engine
    )

    expected_tq001 = (
        100
        * (
            1
            - (
                tq001.loc[0, "violations"]
                / tq001.loc[0, "total"]
            )
        )
    )

    actual_tq001 = float(
        metrics.loc[
            metrics["rule_id"] == "TQ001",
            "quality_rate"
        ].iloc[0]
    )

    assert actual_tq001 == pytest.approx(
        expected_tq001,
        abs=0.01
    )
