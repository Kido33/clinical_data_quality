import subprocess
import sys


def run_step(name, script):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    subprocess.run(
        [sys.executable, script],
        check=True
    )

    print(f"\n[OK] {name}")


def main():

    # ========================================================
    # 1. Validate environment
    # ========================================================

    run_step(
        "Validate environment",
        "src/check_env.py"
    )

    # ========================================================
    # 2. Load Synthea data
    # ========================================================

    run_step(
        "Load Synthea data",
        "src/load_synthea.py"
    )

    # ========================================================
    # 3. Inject test errors
    # ========================================================

    run_step(
        "Inject test errors",
        "src/inject_errors.py"
    )

    # ========================================================
    # 4. Validate data quality
    # ========================================================

    run_step(
        "Validate data quality",
        "src/validate_quality.py"
    )

    # ========================================================
    # 5. Build analysis dataset
    # ========================================================

    run_step(
        "Build analysis dataset",
        "src/build_analysis_dataset.py"
    )

    # ========================================================
    # 6. Generate quality report
    # ========================================================

    run_step(
        "Generate quality report",
        "src/generate_quality_report.py"
    )

    # ========================================================
    # 7. Generate quality metrics
    # ========================================================

    run_step(
        "Generate quality metrics",
        "src/generate_quality_metrics.py"
    )

    # ========================================================
    # Pipeline completed
    # ========================================================

    print("\n" + "=" * 60)
    print("Pipeline completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()