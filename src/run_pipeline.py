import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"


STEPS = [
    ("Validate environment", "check_env.py"),
    ("Load Synthea data", "load_synthea.py"),
    ("Inject test errors", "inject_errors.py"),
    ("Validate data quality", "validate_quality.py"),
    ("Build analysis dataset", "build_analysis_dataset.py"),
    ("Generate quality report", "generate_quality_report.py"),
]


def run_step(name, script):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(SRC_DIR / script)],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print(f"\n[FAILED] {name}")
        print(f"Script: {script}")
        sys.exit(result.returncode)

    print(f"\n[OK] {name}")


def main():
    print("=" * 60)
    print("Clinical Data Quality Pipeline")
    print("=" * 60)

    for name, script in STEPS:
        run_step(name, script)

    print("\n" + "=" * 60)
    print("Pipeline completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()