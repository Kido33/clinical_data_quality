# Clinical Data Quality Rules

## 1. Purpose

본 문서는 Clinical Data Quality 프로젝트에서 사용하는
데이터 품질 검증 규칙의 정의와 판정 기준을 설명한다.

Validation 결과에 따라 각 규칙은 다음 두 가지 처리 정책을 사용한다.

- Flag: 데이터는 유지하되 품질 이슈를 표시
- Exclude: 해당 레코드를 분석 데이터셋에서 제외

---

## 2. Rule Overview

| Rule ID | Category | Table | Column | Rule | Severity |
|---|---|---|---|---|---|
| CQ001 | Completeness | patients | Id | Patient ID must not be NULL | Exclude |
| CQ002 | Completeness | patients | BIRTHDATE | Birthdate should not be NULL | Flag |
| VQ001 | Validity | patients | GENDER | Gender must be M or F | Flag |
| UQ001 | Uniqueness | patients | Id | Patient ID must be unique | Exclude |
| RQ001 | Referential Integrity | encounters | PATIENT | Patient ID must exist in patients | Exclude |
| TQ001 | Temporal | encounters | START/STOP | START must not be later than STOP | Exclude |

---

## 3. Completeness Rules

### CQ001 - Patient ID Completeness

**Target**

`patients.Id`

**Condition**

```text
Id IS NULL

Severity

Exclude

Rationale

Patient ID is the primary identifier used to associate patient-level
and encounter-level records. Missing identifiers prevent reliable
record linkage.

CQ002 - Birthdate Completeness

Target

patients.BIRTHDATE

Condition

BIRTHDATE IS NULL

Severity

Flag

Rationale

Missing birthdate reduces demographic completeness but does not
necessarily prevent the patient record from being used in downstream
analysis.

4. Validity Rules
VQ001 - Gender Code Validity

Target

patients.GENDER

Valid values

M
F

Invalid condition

GENDER NOT IN ('M', 'F')
AND GENDER IS NOT NULL

Severity

Flag

Rationale

Invalid categorical values indicate a data quality issue but do not
necessarily make the entire patient record unusable.

5. Uniqueness Rules
UQ001 - Patient ID Uniqueness

Target

patients.Id

Condition

COUNT(Id) > 1

for the same patient ID.

Severity

Exclude

Rationale

Duplicate patient identifiers can result in duplicate entities and
ambiguous patient-level analysis.

Processing policy

When duplicate records are detected, one representative record is
retained according to the following priority:

Higher completeness
Earlier/original record when completeness is tied

Note: A duplicate violation count represents the number of records
participating in duplicate groups and does not necessarily equal the
number of records ultimately excluded.

6. Referential Integrity Rules
RQ001 - Encounter Patient Reference

Target

encounters.PATIENT

Condition

The value of encounters.PATIENT must exist in patients.Id.

Severity

Exclude

Rationale

An encounter without a valid patient reference cannot be reliably
linked to a patient-level entity.

7. Temporal Rules
TQ001 - Encounter Temporal Consistency

Target

encounters.START, encounters.STOP

Condition

START > STOP

Severity

Exclude

Rationale

An encounter cannot logically end before it starts.

8. Severity Policy
Severity	Processing
Flag	Record retained, quality issue recorded
Exclude	Record excluded from analysis dataset
9. Rule Execution

All rules are evaluated independently before the final exclusion
decision is applied.

The final analysis dataset applies the exclusion policy to records
affected by rules with Exclude severity.


---

# `docs/methodology.md`

**목적:**  
> "이 프로젝트를 어떤 방법으로 구축했는가?"

여기서는 **규칙의 세부 정의를 반복하지 않습니다.** 규칙은 위 문서로 링크합니다.

```markdown
# Clinical Data Quality Methodology

## 1. Overview

본 프로젝트는 합성 임상 데이터(Synthea)를 대상으로
데이터 품질 문제를 의도적으로 주입하고,
사전에 정의된 품질 규칙을 이용하여 오류를 탐지한 뒤
분석용 데이터셋을 구축하는 재현 가능한 데이터 품질 파이프라인이다.

---

## 2. Pipeline

```text
Synthea
   ↓
CSV Dataset
   ↓
PostgreSQL Raw Schema
   ↓
Error Injection
   ↓
quality_test Schema
   ↓
Quality Validation
   ↓
quality.rule_results
   ↓
Flag / Exclude Policy
   ↓
Analysis Dataset
   ↓
Quality Report
3. Data Source
Synthea

Synthea-generated synthetic clinical data were used as the source
dataset.

Initial dataset:

Table	Rows
patients	18
encounters	1,042
observations	20,113

The project uses PostgreSQL as the central storage and validation
environment.

4. Database Architecture
raw
├── patients
├── encounters
└── observations

quality_test
├── patients
├── encounters
└── injection_log

quality
└── rule_results

analysis
├── patients
└── encounters
Schema Roles
Schema	Purpose
raw	Original loaded data
quality_test	Error-injected test data
quality	Validation results
analysis	Final analysis-ready dataset
5. Error Injection

Errors are intentionally introduced into the test dataset to validate
the quality-control pipeline.

Injection Types
Error Type	Table	Target	Target Rows
Missing	patients	BIRTHDATE	1
Invalid Code	patients	GENDER	1
Duplicate	patients	Id	1
Temporal	encounters	START/STOP	10

Random seed:

42

Detailed injection implementation is maintained in:

src/inject_errors.py

6. Validation

The injected dataset is evaluated using the predefined
data quality rules.

Detailed rule definitions:

data_quality_rules.md

Validation results are stored in:

quality.rule_results
7. Parallel Rule Evaluation

Each quality rule is evaluated independently.

A record may therefore have multiple quality issues simultaneously.

The validation process does not stop after the first detected error.

8. Flag / Exclude Policy
Flag

Records with non-critical quality issues are retained and marked.

Examples:

Missing BIRTHDATE
Invalid GENDER
Exclude

Records with structural integrity problems are removed from the
analysis dataset.

Examples:

Duplicate patient identifier
Invalid patient reference
Invalid temporal relationship
9. Analysis Dataset Construction

The analysis dataset is constructed from the quality-tested dataset.

Patient Processing
Identify completeness and validity issues
Identify duplicate patient IDs
Select one representative record for duplicate groups
Remove records violating exclusion-level patient rules
Encounter Processing
Validate patient references
Validate temporal consistency
Remove encounters violating exclusion-level rules
10. Reporting

The pipeline generates CSV-based quality reports.

reports/
├── rule_results.csv
├── quality_report.csv
├── dataset_summary.csv
├── injection_summary.csv
└── flag_summary.csv

These reports provide both rule-level violations and
before/after dataset summaries.

11. Reproducibility

The pipeline uses:

Python
PostgreSQL
SQLAlchemy
pandas
psycopg2
python-dotenv

Error injection uses a fixed random seed:

42

This allows the same test conditions to be reproduced.


---

# `docs/data_quality_report.md`

이 문서는 **방법론이 아니라 실제 실행 결과**를 보여줍니다.

즉,

> methodology = 어떻게 했는가  
> report = 그래서 실제로 뭐가 나왔는가

입니다.

```markdown
# Clinical Data Quality Report

## 1. Executive Summary

Synthea-generated synthetic clinical data were loaded into PostgreSQL,
intentionally corrupted using controlled error injection, and evaluated
using six predefined data quality rules.

The validation pipeline successfully detected all injected error types
and generated an analysis-ready dataset according to the defined
Flag/Exclude policy.

---

## 2. Dataset Overview

### Initial Raw Dataset

| Table | Rows |
|---|---:|
| patients | 18 |
| encounters | 1,042 |
| observations | 20,113 |

---

## 3. Error Injection Results

| Error Type | Table | Column | Target | Actual | Target Rate | Actual Rate |
|---|---|---|---|---:|---:|---:|
| Missing | patients | BIRTHDATE | 1 | 1 | 5.56% | 5.26% |
| Invalid Code | patients | GENDER | 1 | 1 | 5.56% | 5.26% |
| Duplicate | patients | Id | 1 | 1 | 5.56% | 5.26% |
| Temporal | encounters | START/STOP | 10 | 10 | 0.96% | 0.96% |

> Actual rate is calculated against the post-injection dataset size.

---

## 4. Validation Results

| Rule | Category | Table | Violation Count | Severity |
|---|---|---|---:|---|
| CQ001 | Completeness | patients | 0 | Exclude |
| CQ002 | Completeness | patients | 1 | Flag |
| VQ001 | Validity | patients | 1 | Flag |
| UQ001 | Uniqueness | patients | 2 | Exclude |
| RQ001 | Referential Integrity | encounters | 0 | Exclude |
| TQ001 | Temporal | encounters | 10 | Exclude |

---

## 5. Analysis Dataset

### Before / After

| Table | Before | After | Excluded | Exclusion Rate |
|---|---:|---:|---:|---:|
| patients | 19 | 18 | 1 | 5.26% |
| encounters | 1,042 | 1,032 | 10 | 0.96% |

---

## 6. Rule-level Findings

### CQ002 - Missing Birthdate

Detected:

```text
1 record

Processing:

Flag

The patient record remains in the analysis dataset.

VQ001 - Invalid Gender

Detected:

1 record

Processing:

Flag

The patient record remains in the analysis dataset.

UQ001 - Duplicate Patient ID

Detected:

2 records participating in a duplicate group

The duplicate group contained one repeated patient ID.

One representative record was retained and one record was excluded.

Therefore:

Violation count: 2
Patient exclusion: 1

These metrics represent different concepts and should not be interpreted
as equivalent.

RQ001 - Referential Integrity

Detected:

0 violations

All encounter patient references corresponded to an existing patient.

TQ001 - Temporal Consistency

Detected:

10 violations

All 10 encounters where:

START > STOP

were excluded from the analysis dataset.

7. Quality Control Effect

The pipeline transformed the corrupted test cohort into an
analysis-oriented cohort.

Patients
19 → 18

Encounters
1,042 → 1,032

Flagged records were retained while exclusion-level violations were
removed.

8. Generated Outputs
reports/
├── rule_results.csv
├── quality_report.csv
├── dataset_summary.csv
├── injection_summary.csv
└── flag_summary.csv
9. Validation of Error Injection

All four intentionally injected error categories were successfully
detected:

Injected Error	Detected
Missing BIRTHDATE	Yes
Invalid GENDER	Yes
Duplicate Patient ID	Yes
Temporal Error	Yes
10. Limitations
The dataset is synthetic and does not represent real-world clinical
data distributions.
The current validation rules cover a limited set of quality dimensions.
Only selected Synthea tables are included in the current analysis
pipeline.
The current cohort is intentionally small and designed for pipeline
validation rather than statistical generalization.
Error injection rates and rule coverage should be expanded for
larger-scale validation.
11. Reproducibility

Random seed:

42

The generated reports correspond to the executed pipeline version and
the recorded validation results.


---

# 세 문서의 관계

이렇게 하면 역할이 깔끔해집니다.

```text
                    README
                      │
          "이 프로젝트가 뭔가?"
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
   methodology.md       data_quality_rules.md
   "어떻게 했나?"          "무엇을 기준으로
                            판단했나?"
          │                       │
          └───────────┬───────────┘
                      ↓
            data_quality_report.md
                 "결과는?"