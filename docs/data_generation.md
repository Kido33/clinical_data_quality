# Synthea Data Generation

## 1. Purpose

This project uses Synthea synthetic patient data to demonstrate a clinical data quality management workflow.

Synthea generates synthetic healthcare records that can be loaded into PostgreSQL and evaluated using predefined data quality rules.

---

## 2. Synthea Version

The project uses the Synthea standalone executable JAR:

```text
synthea-with-dependencies.jar
```

The JAR is intentionally excluded from Git tracking and is downloaded automatically in the GitHub Actions workflow.

---

## 3. Data Generation Configuration

The current local dataset was generated with the following configuration:

| Parameter       | Value         |
| --------------- | ------------- |
| State           | Massachusetts |
| Seed            | 1788156358927 |
| Clinician Seed  | 1788156358927 |
| Reference Date  | 2026-08-31    |
| End Date        | 2026-08-31    |
| Patient Count   | 18            |
| Modules         | *             |
| Java            | 17.0.20.1     |
| Synthea Version | d9d07a6       |

The configuration information was obtained from the Synthea metadata generated during execution.

---

## 4. Generate Synthea Data

From the project root:

```powershell
java -jar tools\synthea\synthea-with-dependencies.jar `
    -s 1788156358927 `
    -p 18 `
    -r 20260831 `
    -e 20260831 `
    Massachusetts
```

Generated files are written under:

```text
tools/synthea/output/
```

The CSV files used by this project are:

```text
tools/synthea/output/csv/patients.csv
tools/synthea/output/csv/encounters.csv
tools/synthea/output/csv/observations.csv
```

---

## 5. Database Loading

The selected Synthea datasets are loaded into PostgreSQL using:

```text
src/load_synthea.py
```

The source data are stored in:

```text
raw.patients
raw.encounters
raw.observations
```

---

## 6. Reproducibility

A fixed random seed is used to make the synthetic data generation process reproducible.

The generated metadata file should be retained locally for verification:

```text
tools/synthea/output/metadata/
```

The generated Synthea output itself is excluded from Git because it consists of generated data artifacts rather than source code.

---

## 7. Data Quality Test Design

After loading the Synthea data, controlled data quality errors are injected into a copy of the raw dataset.

The current test cases include:

* Missing BIRTHDATE
* Invalid GENDER code
* Duplicate patient ID
* Invalid encounter START/STOP relationship

The injected dataset is stored separately under:

```text
quality_test.patients
quality_test.encounters
```

The original raw dataset remains unchanged.

---

## 8. Quality Validation

The validation pipeline evaluates six quality rules:

| Rule  | Category              | Description                       |
| ----- | --------------------- | --------------------------------- |
| CQ001 | Completeness          | Patient ID completeness           |
| CQ002 | Completeness          | Birthdate completeness            |
| VQ001 | Validity              | Gender code validity              |
| UQ001 | Uniqueness            | Patient ID uniqueness             |
| RQ001 | Referential Integrity | Encounter-to-patient relationship |
| TQ001 | Temporal              | Encounter START/STOP consistency  |

Rules marked `Exclude` are used to construct the analysis dataset.

Rules marked `Flag` are retained as data quality issues without automatically excluding the record.

---

## 9. End-to-End Pipeline

The complete workflow can be executed using:

```powershell
python src\run_pipeline.py
```

The pipeline performs:

1. Environment validation
2. Synthea CSV loading
3. Controlled error injection
4. Data quality validation
5. Analysis dataset construction
6. Quality metrics generation
7. Quality report generation

Automated quality tests can then be executed using:

```powershell
python -m pytest tests -v
```

---

## 10. CI Validation

GitHub Actions executes the same quality workflow in a clean environment.

The CI workflow:

1. Starts PostgreSQL
2. Installs Python dependencies
3. Downloads Synthea
4. Verifies the Synthea executable
5. Configures the database
6. Runs the quality pipeline
7. Executes pytest

This provides automated regression testing for the clinical data quality rules.
