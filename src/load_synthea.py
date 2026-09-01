from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# --------------------------------------------------
# 1. Environment
# --------------------------------------------------

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# --------------------------------------------------
# 2. Database connection
# --------------------------------------------------

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# 3. Synthea data path
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_DIR = (
    PROJECT_ROOT
    / "tools"
    / "synthea"
    / "output"
    / "csv"
)


# --------------------------------------------------
# 4. Load CSV
# --------------------------------------------------

tables = {
    "patients": "patients.csv",
    "encounters": "encounters.csv",
    "observations": "observations.csv",
}


def main():

    print("=" * 60)
    print("Synthea -> PostgreSQL loading")
    print("=" * 60)

    for table_name, filename in tables.items():

        filepath = CSV_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"File not found: {filepath}"
            )

        print(f"\nLoading: {filename}")

        df = pd.read_csv(filepath)

        print(f"Rows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")

        df.to_sql(
            table_name,
            engine,
            schema="raw",
            if_exists="replace",
            index=False,
            method="multi",
        )

        print(
            f"Inserted -> raw.{table_name}"
        )
    # ============================================================
    # Create raw schema
    # ============================================================

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE SCHEMA IF NOT EXISTS raw"
            )
        )

    print("[OK] raw schema ready")

    # --------------------------------------------------
    # 5. Verify
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("Database verification")
    print("=" * 60)

    with engine.connect() as connection:

        for table_name in tables:

            result = connection.execute(
                text(
                    f"SELECT COUNT(*) "
                    f"FROM raw.{table_name}"
                )
            )

            count = result.scalar()

            print(
                f"raw.{table_name}: "
                f"{count:,} rows"
            )


if __name__ == "__main__":
    main()