-- ============================================================
-- Clinical Data Quality
-- Quality Metrics
-- ============================================================


-- ============================================================
-- 1. Patient ID Completeness Rate
-- ============================================================

SELECT
    'CQ001' AS rule_id,
    'Patient ID Completeness' AS metric_name,
    COUNT(*) AS total_rows,
    COUNT("Id") AS valid_rows,
    COUNT(*) - COUNT("Id") AS invalid_rows,
    ROUND(
        COUNT("Id") * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) AS quality_rate
FROM quality_test.patients;


-- ============================================================
-- 2. Birthdate Completeness Rate
-- ============================================================

SELECT
    'CQ002' AS rule_id,
    'Birthdate Completeness' AS metric_name,
    COUNT(*) AS total_rows,
    COUNT("BIRTHDATE") AS valid_rows,
    COUNT(*) - COUNT("BIRTHDATE") AS invalid_rows,
    ROUND(
        COUNT("BIRTHDATE") * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) AS quality_rate
FROM quality_test.patients;


-- ============================================================
-- 3. Gender Validity Rate
-- ============================================================

SELECT
    'VQ001' AS rule_id,
    'Gender Validity' AS metric_name,
    COUNT(*) AS total_rows,

    COUNT(*) FILTER (
        WHERE "GENDER" IN ('M', 'F')
    ) AS valid_rows,

    COUNT(*) FILTER (
        WHERE "GENDER" IS NOT NULL
          AND "GENDER" NOT IN ('M', 'F')
    ) AS invalid_rows,

    ROUND(
        COUNT(*) FILTER (
            WHERE "GENDER" IN ('M', 'F')
        ) * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) AS quality_rate

FROM quality_test.patients;


-- ============================================================
-- 4. Patient ID Uniqueness Rate
-- ============================================================

WITH duplicate_ids AS (

    SELECT
        "Id"
    FROM quality_test.patients
    WHERE "Id" IS NOT NULL
    GROUP BY "Id"
    HAVING COUNT(*) > 1

)

SELECT
    'UQ001' AS rule_id,
    'Patient ID Uniqueness' AS metric_name,

    COUNT(*) AS total_rows,

    COUNT(*) FILTER (
        WHERE "Id" NOT IN (
            SELECT "Id"
            FROM duplicate_ids
        )
    ) AS unique_rows,

    COUNT(*) FILTER (
        WHERE "Id" IN (
            SELECT "Id"
            FROM duplicate_ids
        )
    ) AS duplicate_group_rows,

    ROUND(
        COUNT(*) FILTER (
            WHERE "Id" NOT IN (
                SELECT "Id"
                FROM duplicate_ids
            )
        ) * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) AS quality_rate

FROM quality_test.patients;


-- ============================================================
-- 5. Referential Integrity Rate
-- ============================================================

SELECT
    'RQ001' AS rule_id,
    'Encounter Patient Referential Integrity' AS metric_name,

    COUNT(*) AS total_rows,

    COUNT(*) FILTER (
        WHERE p."Id" IS NOT NULL
    ) AS valid_rows,

    COUNT(*) FILTER (
        WHERE p."Id" IS NULL
    ) AS invalid_rows,

    ROUND(
        COUNT(*) FILTER (
            WHERE p."Id" IS NOT NULL
        ) * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) AS quality_rate

FROM quality_test.encounters e

LEFT JOIN (
    SELECT DISTINCT "Id"
    FROM quality_test.patients
    WHERE "Id" IS NOT NULL
) p
    ON e."PATIENT" = p."Id";


-- ============================================================
-- 6. Temporal Consistency Rate
-- ============================================================

SELECT
    'TQ001' AS rule_id,
    'Encounter Temporal Consistency' AS metric_name,

    COUNT(*) AS total_rows,

    COUNT(*) FILTER (
        WHERE "START"::timestamp <= "STOP"::timestamp
    ) AS valid_rows,

    COUNT(*) FILTER (
        WHERE "START"::timestamp > "STOP"::timestamp
    ) AS invalid_rows,

    ROUND(
        COUNT(*) FILTER (
            WHERE "START"::timestamp <= "STOP"::timestamp
        ) * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) AS quality_rate

FROM quality_test.encounters;


-- ============================================================
-- 7. Combined Quality Metrics
-- ============================================================

WITH metrics AS (

    -- CQ001
    SELECT
        'CQ001' AS rule_id,
        'Completeness' AS category,
        COUNT(*) AS total_rows,
        COUNT("Id") AS valid_rows
    FROM quality_test.patients

    UNION ALL

    -- CQ002
    SELECT
        'CQ002',
        'Completeness',
        COUNT(*),
        COUNT("BIRTHDATE")
    FROM quality_test.patients

    UNION ALL

    -- VQ001
    SELECT
        'VQ001',
        'Validity',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE "GENDER" IN ('M', 'F')
        )
    FROM quality_test.patients

    UNION ALL

    -- UQ001
    SELECT
        'UQ001',
        'Uniqueness',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE "Id" NOT IN (
                SELECT "Id"
                FROM quality_test.patients
                WHERE "Id" IS NOT NULL
                GROUP BY "Id"
                HAVING COUNT(*) > 1
            )
        )
    FROM quality_test.patients

    UNION ALL

    -- RQ001
    SELECT
        'RQ001',
        'Referential Integrity',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE p."Id" IS NOT NULL
        )
    FROM quality_test.encounters e
    LEFT JOIN (
        SELECT DISTINCT "Id"
        FROM quality_test.patients
        WHERE "Id" IS NOT NULL
    ) p
        ON e."PATIENT" = p."Id"

    UNION ALL

    -- TQ001
    SELECT
        'TQ001',
        'Temporal',
        COUNT(*),
        COUNT(*) FILTER (
            WHERE "START"::timestamp <= "STOP"::timestamp
        )
    FROM quality_test.encounters

)

SELECT
    rule_id,
    category,
    total_rows,
    valid_rows,
    total_rows - valid_rows AS invalid_rows,

    ROUND(
        valid_rows * 100.0 /
        NULLIF(total_rows, 0),
        2
    ) AS quality_rate

FROM metrics

ORDER BY rule_id;