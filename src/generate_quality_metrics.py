import os
import pandas as pd
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

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


print("=" * 60)
print("Clinical Data Quality Metrics")
print("=" * 60)


# ============================================================
# 1. Calculate quality metrics
# ============================================================

metrics_sql = """
WITH metrics AS (

    -- ========================================================
    -- CQ001: Patient ID Completeness
    -- ========================================================

    SELECT
        'CQ001' AS rule_id,
        'Completeness' AS category,
        'patients' AS table_name,
        'Id' AS column_name,
        'Patient ID Completeness' AS metric_name,
        COUNT(*) AS total_rows,
        COUNT("Id") AS valid_rows,
        COUNT(*) - COUNT("Id") AS invalid_rows,
        ROUND(
            100.0 * COUNT("Id") / NULLIF(COUNT(*), 0),
            2
        ) AS quality_rate
    FROM quality_test.patients


    UNION ALL


    -- ========================================================
    -- CQ002: Birthdate Completeness
    -- ========================================================

    SELECT
        'CQ002',
        'Completeness',
        'patients',
        'BIRTHDATE',
        'Birthdate Completeness',
        COUNT(*),
        COUNT("BIRTHDATE"),
        COUNT(*) - COUNT("BIRTHDATE"),
        ROUND(
            100.0 * COUNT("BIRTHDATE") / NULLIF(COUNT(*), 0),
            2
        )
    FROM quality_test.patients


    UNION ALL


    -- ========================================================
    -- VQ001: Gender Validity
    -- ========================================================

    SELECT
        'VQ001',
        'Validity',
        'patients',
        'GENDER',
        'Gender Validity',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE "GENDER" IN ('M', 'F')
        ),
        COUNT(*) FILTER (
            WHERE "GENDER" NOT IN ('M', 'F')
            OR "GENDER" IS NULL
        ),
        ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE "GENDER" IN ('M', 'F')
            ) / NULLIF(COUNT(*), 0),
            2
        )
    FROM quality_test.patients


    UNION ALL


    -- ========================================================
    -- UQ001: Patient ID Uniqueness
    --
    -- A duplicated ID group means every row in that group
    -- is considered a uniqueness violation.
    -- ========================================================

    SELECT
        'UQ001',
        'Uniqueness',
        'patients',
        'Id',
        'Patient ID Uniqueness',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE "Id" IN (
                SELECT "Id"
                FROM quality_test.patients
                GROUP BY "Id"
                HAVING COUNT(*) = 1
            )
        ),
        COUNT(*) FILTER (
            WHERE "Id" IN (
                SELECT "Id"
                FROM quality_test.patients
                GROUP BY "Id"
                HAVING COUNT(*) > 1
            )
        ),
        ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE "Id" IN (
                    SELECT "Id"
                    FROM quality_test.patients
                    GROUP BY "Id"
                    HAVING COUNT(*) = 1
                )
            ) / NULLIF(COUNT(*), 0),
            2
        )
    FROM quality_test.patients


    UNION ALL


    -- ========================================================
    -- RQ001: Referential Integrity
    --
    -- EXISTS is used instead of JOIN so that duplicate patient
    -- records cannot multiply encounter rows.
    -- ========================================================

    SELECT
        'RQ001',
        'Referential Integrity',
        'encounters',
        'PATIENT',
        'Encounter Patient Referential Integrity',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE EXISTS (
                SELECT 1
                FROM quality_test.patients p
                WHERE p."Id" = e."PATIENT"
            )
        ),
        COUNT(*) FILTER (
            WHERE NOT EXISTS (
                SELECT 1
                FROM quality_test.patients p
                WHERE p."Id" = e."PATIENT"
            )
        ),
        ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM quality_test.patients p
                    WHERE p."Id" = e."PATIENT"
                )
            ) / NULLIF(COUNT(*), 0),
            2
        )
    FROM quality_test.encounters e


    UNION ALL


    -- ========================================================
    -- TQ001: Temporal Consistency
    -- ========================================================

    SELECT
        'TQ001',
        'Temporal',
        'encounters',
        'START/STOP',
        'Encounter Temporal Consistency',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE "START"::timestamp <= "STOP"::timestamp
        ),
        COUNT(*) FILTER (
            WHERE "START"::timestamp > "STOP"::timestamp
        ),
        ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE "START"::timestamp <= "STOP"::timestamp
            ) / NULLIF(COUNT(*), 0),
            2
        )
    FROM quality_test.encounters
)

SELECT *
FROM metrics
ORDER BY rule_id;
"""


# ============================================================
# 2. Execute
# ============================================================

metrics = pd.read_sql(
    text(metrics_sql),
    engine
)


# ============================================================
# 3. Save to PostgreSQL
# ============================================================

metrics.to_sql(
    "quality_metrics",
    engine,
    schema="quality",
    if_exists="replace",
    index=False
)


# ============================================================
# 4. Save CSV report
# ============================================================

os.makedirs("reports", exist_ok=True)

metrics.to_csv(
    "reports/quality_metrics.csv",
    index=False
)


# ============================================================
# 5. Display
# ============================================================

print("\n" + "=" * 60)
print("Quality Metrics")
print("=" * 60)

print(metrics.to_string(index=False))

print("\nSaved:")
print("quality.quality_metrics")
print("reports/quality_metrics.csv")

print("\n" + "=" * 60)
print("Quality metrics generation completed")
print("=" * 60)

