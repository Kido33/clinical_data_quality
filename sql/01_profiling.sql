-- ============================================================
-- Clinical Data Quality
-- SQL Data Profiling
-- ============================================================

-- ============================================================
-- 1. Table Row Counts
-- ============================================================

SELECT
    'raw.patients' AS table_name,
    COUNT(*) AS row_count
FROM raw.patients

UNION ALL

SELECT
    'raw.encounters',
    COUNT(*)
FROM raw.encounters

UNION ALL

SELECT
    'raw.observations',
    COUNT(*)
FROM raw.observations

UNION ALL

SELECT
    'quality_test.patients',
    COUNT(*)
FROM quality_test.patients

UNION ALL

SELECT
    'quality_test.encounters',
    COUNT(*)
FROM quality_test.encounters

UNION ALL

SELECT
    'analysis.patients',
    COUNT(*)
FROM analysis.patients

UNION ALL

SELECT
    'analysis.encounters',
    COUNT(*)
FROM analysis.encounters;


-- ============================================================
-- 2. Patient ID Profiling
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT("Id") AS non_null_ids,
    COUNT(*) - COUNT("Id") AS null_ids,
    COUNT(DISTINCT "Id") AS distinct_ids,
    COUNT(*) - COUNT(DISTINCT "Id") AS duplicate_excess_rows
FROM quality_test.patients;


-- ============================================================
-- 3. Patient Demographic Profiling
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT("BIRTHDATE") AS non_null_birthdate,
    COUNT(*) - COUNT("BIRTHDATE") AS null_birthdate,

    COUNT("GENDER") AS non_null_gender,
    COUNT(*) - COUNT("GENDER") AS null_gender,

    COUNT(DISTINCT "GENDER") AS distinct_gender_values

FROM quality_test.patients;


-- ============================================================
-- 4. Gender Distribution
-- ============================================================

SELECT
    "GENDER",
    COUNT(*) AS row_count,
    ROUND(
        COUNT(*) * 100.0 /
        NULLIF((SELECT COUNT(*) FROM quality_test.patients), 0),
        2
    ) AS percentage
FROM quality_test.patients
GROUP BY "GENDER"
ORDER BY row_count DESC;


-- ============================================================
-- 5. Birthdate Range
-- ============================================================

SELECT
    MIN("BIRTHDATE") AS earliest_birthdate,
    MAX("BIRTHDATE") AS latest_birthdate,
    COUNT(*) AS total_rows,
    COUNT("BIRTHDATE") AS valid_birthdate_rows
FROM quality_test.patients;


-- ============================================================
-- 6. Encounter Profiling
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT("Id") AS non_null_encounter_ids,
    COUNT(*) - COUNT("Id") AS null_encounter_ids,

    COUNT("PATIENT") AS non_null_patient_fk,
    COUNT(*) - COUNT("PATIENT") AS null_patient_fk,

    COUNT("START") AS non_null_start,
    COUNT(*) - COUNT("START") AS null_start,

    COUNT("STOP") AS non_null_stop,
    COUNT(*) - COUNT("STOP") AS null_stop

FROM quality_test.encounters;


-- ============================================================
-- 7. Encounter Class Distribution
-- ============================================================

SELECT
    "ENCOUNTERCLASS",
    COUNT(*) AS row_count,
    ROUND(
        COUNT(*) * 100.0 /
        NULLIF((SELECT COUNT(*) FROM quality_test.encounters), 0),
        2
    ) AS percentage
FROM quality_test.encounters
GROUP BY "ENCOUNTERCLASS"
ORDER BY row_count DESC;


-- ============================================================
-- 8. Encounter Date Range
-- ============================================================

SELECT
    MIN("START") AS earliest_start,
    MAX("START") AS latest_start,
    MIN("STOP") AS earliest_stop,
    MAX("STOP") AS latest_stop
FROM quality_test.encounters;


-- ============================================================
-- 9. Temporal Profiling
-- ============================================================

SELECT
    COUNT(*) AS total_encounters,

    COUNT(*) FILTER (
        WHERE "START"::timestamp <= "STOP"::timestamp
    ) AS temporally_valid,

    COUNT(*) FILTER (
        WHERE "START"::timestamp > "STOP"::timestamp
    ) AS temporal_invalid

FROM quality_test.encounters;


-- ============================================================
-- 10. Referential Integrity Profiling
-- ============================================================

SELECT
    COUNT(*) AS total_encounters,

    COUNT(*) FILTER (
        WHERE p."Id" IS NOT NULL
    ) AS matched_patient_records,

    COUNT(*) FILTER (
        WHERE p."Id" IS NULL
    ) AS orphan_encounters

FROM quality_test.encounters e

LEFT JOIN (
    SELECT DISTINCT "Id"
    FROM quality_test.patients
    WHERE "Id" IS NOT NULL
) p
    ON e."PATIENT" = p."Id";


-- ============================================================
-- 11. Observation Profiling
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT("PATIENT") AS non_null_patient_id,
    COUNT(*) - COUNT("PATIENT") AS null_patient_id,

    COUNT("ENCOUNTER") AS non_null_encounter_id,
    COUNT(*) - COUNT("ENCOUNTER") AS null_encounter_id,

    COUNT("VALUE") AS non_null_value,
    COUNT(*) - COUNT("VALUE") AS null_value

FROM raw.observations;


-- ============================================================
-- 12. Observation Category Distribution
-- ============================================================

SELECT
    "CATEGORY",
    COUNT(*) AS row_count
FROM raw.observations
GROUP BY "CATEGORY"
ORDER BY row_count DESC;