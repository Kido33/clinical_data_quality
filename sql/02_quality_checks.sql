-- ============================================================
-- Clinical Data Quality
-- SQL Quality Checks
-- ============================================================


-- ============================================================
-- CQ001: Patient ID Completeness
-- ============================================================

SELECT
    'CQ001' AS rule_id,
    COUNT(*) AS violation_count
FROM quality_test.patients
WHERE "Id" IS NULL;


-- ============================================================
-- CQ002: Birthdate Completeness
-- ============================================================

SELECT
    'CQ002' AS rule_id,
    COUNT(*) AS violation_count
FROM quality_test.patients
WHERE "BIRTHDATE" IS NULL;


-- ============================================================
-- VQ001: Gender Validity
-- ============================================================

SELECT
    'VQ001' AS rule_id,
    COUNT(*) AS violation_count
FROM quality_test.patients
WHERE "GENDER" IS NOT NULL
  AND "GENDER" NOT IN ('M', 'F');


-- ============================================================
-- UQ001: Patient ID Uniqueness
-- ============================================================

SELECT
    'UQ001' AS rule_id,
    COUNT(*) AS duplicate_group_rows
FROM quality_test.patients
WHERE "Id" IN (
    SELECT "Id"
    FROM quality_test.patients
    GROUP BY "Id"
    HAVING COUNT(*) > 1
);


-- ============================================================
-- RQ001: Referential Integrity
-- ============================================================

SELECT
    'RQ001' AS rule_id,
    COUNT(*) AS violation_count
FROM quality_test.encounters e
LEFT JOIN quality_test.patients p
    ON e."PATIENT" = p."Id"
WHERE p."Id" IS NULL;


-- ============================================================
-- TQ001: Temporal Consistency
-- ============================================================

SELECT
    'TQ001' AS rule_id,
    COUNT(*) AS violation_count
FROM quality_test.encounters
WHERE "START"::timestamp > "STOP"::timestamp;


-- ============================================================
-- Combined Quality Check
-- ============================================================

SELECT
    'CQ001' AS rule_id,
    'Completeness' AS category,
    'patients' AS table_name,
    'Id' AS column_name,
    COUNT(*) AS violation_count
FROM quality_test.patients
WHERE "Id" IS NULL

UNION ALL

SELECT
    'CQ002',
    'Completeness',
    'patients',
    'BIRTHDATE',
    COUNT(*)
FROM quality_test.patients
WHERE "BIRTHDATE" IS NULL

UNION ALL

SELECT
    'VQ001',
    'Validity',
    'patients',
    'GENDER',
    COUNT(*)
FROM quality_test.patients
WHERE "GENDER" IS NOT NULL
  AND "GENDER" NOT IN ('M', 'F')

UNION ALL

SELECT
    'UQ001',
    'Uniqueness',
    'patients',
    'Id',
    COUNT(*)
FROM quality_test.patients
WHERE "Id" IN (
    SELECT "Id"
    FROM quality_test.patients
    GROUP BY "Id"
    HAVING COUNT(*) > 1
)

UNION ALL

SELECT
    'RQ001',
    'Referential Integrity',
    'encounters',
    'PATIENT',
    COUNT(*)
FROM quality_test.encounters e
LEFT JOIN quality_test.patients p
    ON e."PATIENT" = p."Id"
WHERE p."Id" IS NULL

UNION ALL

SELECT
    'TQ001',
    'Temporal',
    'encounters',
    'START/STOP',
    COUNT(*)
FROM quality_test.encounters
WHERE "START"::timestamp > "STOP"::timestamp

ORDER BY rule_id;