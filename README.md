# Clinical Data Quality Pipeline

Synthetic Clinical Data를 대상으로 **임상 데이터 품질 규칙을 정의하고, 의도적으로 오류를 주입한 뒤 SQL 기반 검증을 수행하여 분석 가능한 데이터셋과 품질 지표를 생성하는 데이터 품질 관리 파이프라인**입니다.

단순한 데이터 정제를 넘어 다음 과정을 하나의 재현 가능한 파이프라인으로 구현했습니다.

```text
Synthetic Clinical Data
        ↓
PostgreSQL Raw Layer
        ↓
Error Injection
        ↓
Data Quality Validation
        ↓
Analysis Dataset Construction
        ↓
Quality Metrics
        ↓
Automated Testing
        ↓
GitHub Actions CI
```

---

## 1. Project Overview

### Objective

임상 데이터 분석 및 RWE(Real-World Evidence) 연구에서는 분석 모델보다 먼저 **분석에 사용할 데이터가 신뢰할 수 있는지 검증하는 과정**이 필요합니다.

본 프로젝트에서는 Synthea를 이용해 생성한 synthetic clinical data에 실제 데이터 품질 문제를 가정한 오류를 주입하고, 사전에 정의한 품질 규칙을 기반으로 오류를 탐지한 후 분석 대상 데이터셋을 구축합니다.

이를 통해 다음과 같은 데이터 관리 과정을 구현했습니다.

* Clinical data ingestion
* Data profiling
* Data quality rule definition
* Controlled error injection
* SQL-based validation
* Cohort / analysis dataset construction
* Quality metric generation
* Automated testing
* CI-based validation
* Reproducible execution

---

## 2. Key Features

### Data

* Synthea synthetic patient data generation
* PostgreSQL data loading
* Raw / Quality Test / Analysis layer 분리
* Patient / Encounter / Observation 데이터 관리

### Data Quality

* Completeness
* Validity
* Uniqueness
* Referential Integrity
* Temporal Consistency

### Error Injection

재현 가능한 검증을 위해 Random Seed `42`를 사용하여 다음 오류를 의도적으로 주입했습니다.

* Missing Value
* Invalid Code
* Duplicate Record
* Temporal Error

### Analysis Dataset

품질 검증 결과를 기반으로 분석 대상에서 제외해야 하는 데이터를 분리하여 다음 분석 데이터셋을 생성합니다.

* `analysis.patients`
* `analysis.encounters`

### Quality Metrics

각 품질 규칙에 대해 다음 지표를 생성합니다.

* Total Rows
* Valid Rows
* Invalid Rows
* Quality Rate

결과는 PostgreSQL과 CSV 형태로 저장합니다.

```text
quality.quality_metrics
reports/quality_metrics.csv
```

### Automated Testing

`pytest`를 사용하여 핵심 품질 규칙과 분석 데이터셋을 자동 검증합니다.

현재:

```text
12 tests
12 passed
```

### Continuous Integration

GitHub Actions를 이용하여 Push / Pull Request 발생 시 다음 과정을 자동 실행합니다.

```text
PostgreSQL
    ↓
Python
    ↓
Java
    ↓
Synthea
    ↓
Quality Pipeline
    ↓
pytest
```

---

## 3. Data Source

### Synthea

Synthea를 사용하여 synthetic clinical data를 생성했습니다.

현재 로컬 실행에서 생성된 기본 데이터는 다음과 같습니다.

| Dataset      |   Rows |
| ------------ | -----: |
| patients     |     18 |
| encounters   |  1,042 |
| observations | 20,113 |

생성 데이터는 Git 저장소에 직접 포함하지 않고 `.gitignore`를 통해 제외했습니다.

Synthea 실행 결과와 생성 데이터는 로컬 환경에서 재생성할 수 있도록 실행 방법을 문서화했습니다.

---

## 4. Pipeline Architecture

```text
                    Synthea
                       │
                       ▼
            Synthetic Clinical Data
                       │
                       ▼
                 PostgreSQL
                       │
                       ▼
                  raw schema
              ┌────────┼────────┐
              │        │        │
          patients encounters observations
                       │
                       ▼
                Error Injection
              ┌────────┼─────────┐
              │        │         │
           Missing  Invalid   Duplicate
              │      Code         │
              └────────┼─────────┘
                       │
                 Temporal Error
                       │
                       ▼
              quality_test schema
                       │
                       ▼
             Quality Validation
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Completeness     Validity      Uniqueness
        │              │              │
        ├──────────────┼──────────────┤
        │                             │
 Referential Integrity        Temporal Consistency
        │                             │
        └──────────────┬──────────────┘
                       ▼
             Analysis Dataset
                       │
          ┌────────────┴────────────┐
          │                         │
   analysis.patients       analysis.encounters
          │                         │
          └────────────┬────────────┘
                       ▼
                Quality Metrics
                       │
                       ▼
                  CSV Reports
                       │
                       ▼
                    pytest
                       │
                       ▼
               GitHub Actions CI
```

---

## 5. Data Quality Rules

총 6개의 핵심 품질 규칙을 정의했습니다.

| Rule ID | Category              | Target                  | Description                  |
| ------- | --------------------- | ----------------------- | ---------------------------- |
| CQ001   | Completeness          | `patients.Id`           | Patient ID NULL 여부 검증        |
| CQ002   | Completeness          | `patients.BIRTHDATE`    | Birthdate NULL 여부 검증         |
| VQ001   | Validity              | `patients.GENDER`       | 허용된 Gender Code 여부 검증        |
| UQ001   | Uniqueness            | `patients.Id`           | Patient ID 중복 여부 검증          |
| RQ001   | Referential Integrity | `encounters.PATIENT`    | Encounter의 Patient 참조 무결성 검증 |
| TQ001   | Temporal              | `encounters.START/STOP` | Encounter 시작/종료 시간 일관성 검증    |

---

## 6. Error Injection

실제 임상 데이터 품질 검증 상황을 재현하기 위해 `quality_test` 데이터셋에 의도적으로 오류를 주입했습니다.

| Error Type   | Table      | Column     | Injected Rows |
| ------------ | ---------- | ---------- | ------------: |
| Missing      | patients   | BIRTHDATE  |             1 |
| Invalid Code | patients   | GENDER     |             1 |
| Duplicate    | patients   | Id         |             1 |
| Temporal     | encounters | START/STOP |            10 |

재현성을 위해 Random Seed `42`를 사용했습니다.

오류가 주입된 데이터는 원본 `raw` 데이터와 분리하여 `quality_test` schema에 저장합니다.

```text
raw
 │
 └── original synthetic data
          │
          ▼
   Error Injection
          │
          ▼
quality_test
 │
 ├── patients
 ├── encounters
 └── injection_log
```

---

## 7. Quality Validation

오류가 주입된 데이터에 대해 SQL 기반 품질 규칙을 실행합니다.

검증 결과는 `quality.rule_results`에 저장됩니다.

현재 검증 결과:

| Rule  | Violations | Quality Rate |
| ----- | ---------: | -----------: |
| CQ001 |          0 |      100.00% |
| CQ002 |          1 |       94.74% |
| VQ001 |          1 |       94.74% |
| UQ001 |          2 |       89.47% |
| RQ001 |          0 |      100.00% |
| TQ001 |         10 |       99.04% |

`UQ001`의 경우 1개의 duplicate record를 추가했기 때문에 실제 검증에서는 동일한 Patient ID를 가진 **2개의 duplicate group rows**가 탐지됩니다.

---

## 8. Analysis Dataset Construction

품질 검증 결과 중 분석 결과에 직접적인 영향을 줄 수 있는 오류를 기준으로 분석 대상 데이터를 구성합니다.

### Patients

```text
quality_test.patients
19 rows
      ↓
analysis.patients
18 rows
```

중복 Patient ID가 존재하는 데이터 중 분석 대상에서 제외할 record를 제거했습니다.

### Encounters

```text
quality_test.encounters
1,042 rows
      ↓
analysis.encounters
1,032 rows
```

Temporal Consistency를 위반한 10개의 Encounter를 분석 대상에서 제외했습니다.

Referential Integrity 위반은 발견되지 않았습니다.

---

## 9. Quality Metrics

각 품질 규칙에 대해 다음 지표를 생성합니다.

```text
Total Rows
Valid Rows
Invalid Rows
Quality Rate
```

결과는 PostgreSQL의 `quality.quality_metrics` 테이블에 저장하며 CSV 파일로도 출력합니다.

```text
reports/quality_metrics.csv
```

현재 생성된 지표:

| Rule  | Total | Valid | Invalid | Quality Rate |
| ----- | ----: | ----: | ------: | -----------: |
| CQ001 |    19 |    19 |       0 |      100.00% |
| CQ002 |    19 |    18 |       1 |       94.74% |
| RQ001 | 1,042 | 1,042 |       0 |      100.00% |
| TQ001 | 1,042 | 1,032 |      10 |       99.04% |
| UQ001 |    19 |    17 |       2 |       89.47% |
| VQ001 |    19 |    18 |       1 |       94.74% |

---

## 10. Automated Testing

`pytest`를 이용하여 데이터 품질 규칙과 분석 데이터셋을 자동 검증합니다.

현재 총 12개의 테스트가 구성되어 있습니다.

```text
12 tests
12 passed
```

검증 항목:

1. Database connection
2. Patient ID completeness
3. Birthdate completeness
4. Gender validity
5. Patient ID uniqueness
6. Encounter-patient referential integrity
7. Encounter temporal consistency
8. Analysis patient count
9. Analysis encounter count
10. Analysis temporal validity
11. Quality metrics rule coverage
12. Quality metric values

실행:

```bash
python -m pytest tests -v
```

---

## 11. Continuous Integration

GitHub Actions를 이용하여 코드 변경 시 자동으로 품질 검증을 수행합니다.

CI 환경:

| Component  | Version        |
| ---------- | -------------- |
| OS         | Ubuntu         |
| Python     | 3.11           |
| Java       | 17             |
| PostgreSQL | 17             |
| Synthea    | Latest release |

CI Pipeline:

```text
Checkout
    ↓
Setup Python 3.11
    ↓
Setup Java 17
    ↓
Start PostgreSQL 17
    ↓
Install Dependencies
    ↓
Download Synthea
    ↓
Verify Synthea
    ↓
Configure Database
    ↓
Run Clinical Data Quality Pipeline
    ↓
Run pytest
```

Workflow 파일:

```text
.github/workflows/quality_test.yml
```

Push와 Pull Request가 `main` branch를 대상으로 발생하면 자동으로 실행됩니다.

---

## 12. SQL

SQL 기반 데이터 품질 검증을 별도 파일로 관리했습니다.

```text
sql/
├── 01_profiling.sql
├── 02_quality_checks.sql
└── 03_quality_metrics.sql
```

### Profiling

기본적인 데이터 구조와 분포를 확인합니다.

```sql
\i 'sql/01_profiling.sql'
```

### Quality Checks

정의된 품질 규칙을 실행합니다.

```sql
\i 'sql/02_quality_checks.sql'
```

### Quality Metrics

품질 규칙별 품질 지표를 생성합니다.

```sql
\i 'sql/03_quality_metrics.sql'
```

---

## 13. Project Structure

```text
clinical_data_quality/
│
├── .github/
│   └── workflows/
│       └── quality_test.yml
│
├── docs/
│   └── data_generation.md
│
├── reports/
│   ├── dataset_summary.csv
│   ├── flag_summary.csv
│   ├── injection_summary.csv
│   ├── quality_metrics.csv
│   ├── quality_report.csv
│   └── rule_results.csv
│
├── sql/
│   ├── 01_profiling.sql
│   ├── 02_quality_checks.sql
│   └── 03_quality_metrics.sql
│
├── src/
│   ├── build_analysis_dataset.py
│   ├── check_env.py
│   ├── generate_quality_metrics.py
│   ├── generate_quality_report.py
│   ├── inject_errors.py
│   ├── load_synthea.py
│   ├── run_pipeline.py
│   └── validate_quality.py
│
├── tests/
│   └── test_quality_rules.py
│
├── tools/
│   └── synthea/
│
├── .gitignore
└── README.md
```

Synthea 실행 파일과 생성 데이터는 `.gitignore`를 통해 Git repository에서 제외합니다.

---

## 14. Reproducibility

### 1. Environment

`.env` 파일에 PostgreSQL 연결 정보를 설정합니다.

```text
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clinical_dq
```

### 2. Run Synthea

Synthea JAR를 `tools/synthea/`에 배치한 후 synthetic data를 생성합니다.

생성 데이터:

```text
tools/synthea/output/csv/
```

Synthea 실행 및 데이터 생성 과정은 다음 문서에 정리했습니다.

```text
docs/data_generation.md
```

### 3. Run Pipeline

전체 품질 관리 파이프라인:

```bash
python src/run_pipeline.py
```

### 4. Run Automated Tests

```bash
python -m pytest tests -v
```

---

## 15. Technical Skills

### Clinical / RWE Data

* Clinical Data
* Synthetic Patient Data
* Patient / Encounter Data
* Clinical Data Quality
* Data Validation
* Data Cleaning
* Cohort Construction
* Analysis Dataset Preparation
* RWE Data Preparation

### Data Quality

* Data Profiling
* Completeness
* Validity
* Uniqueness
* Referential Integrity
* Temporal Consistency
* Quality Metrics
* Error Injection
* Data Quality Validation

### Database

* PostgreSQL
* SQL
* Relational Data Modeling
* SQL-based Data Validation

### Python

* Python
* Pandas
* SQLAlchemy
* pytest
* python-dotenv

### Automation / DevOps

* Git
* GitHub
* GitHub Actions
* CI
* Automated Testing
* Reproducible Pipeline

---

## 16. End-to-End Execution

전체 프로세스는 다음 명령 하나로 실행할 수 있습니다.

```bash
python src/run_pipeline.py
```

파이프라인은 다음 순서로 실행됩니다.

```text
Validate Environment
        ↓
Load Synthea Data
        ↓
Inject Test Errors
        ↓
Validate Data Quality
        ↓
Build Analysis Dataset
        ↓
Generate Quality Report
        ↓
Generate Quality Metrics
        ↓
Pipeline Completed
```

자동화된 테스트:

```bash
python -m pytest tests -v
```

현재 로컬 환경에서:

```text
Pipeline: SUCCESS
pytest: 12 passed
```

---

## 17. Project Outcome

본 프로젝트를 통해 synthetic clinical data를 대상으로 **데이터 생성 → 적재 → 오류 주입 → 품질 검증 → 분석 데이터셋 구축 → 품질 지표 생성 → 자동 테스트 → CI 검증**까지 연결된 end-to-end clinical data quality workflow를 구현했습니다.

특히 데이터 오류를 단순히 제거하는 방식이 아니라,

```text
Quality Rule Definition
        ↓
Controlled Error Injection
        ↓
Rule-based Detection
        ↓
Exclusion / Analysis Dataset Construction
        ↓
Quality Metrics
        ↓
Automated Validation
```

의 구조로 설계하여 **분석에 사용되는 데이터의 품질을 사전에 확인하고 재현 가능한 방식으로 관리하는 것**을 프로젝트의 핵심으로 두었습니다.
