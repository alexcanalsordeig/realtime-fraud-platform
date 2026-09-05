"""Load raw transaction Parquet files from disk into BigQuery."""

import glob
import pandas_gbq
from pathlib import Path

import pandas as pd
from google.oauth2 import service_account

# --- Config ---
PROJECT_ID = "fraud-platform-507716"
DATASET = "fraud"
TABLE = "raw_transactions"
KEY_PATH = Path(__file__).resolve().parents[1] / ".secrets" / "bigquery_key.json"
RAW_DIR = Path(__file__).resolve().parents[1] / "warehouse" / "raw"


def main() -> None:
    # 1. Read all raw Parquet files and combine them
    files = glob.glob(str(RAW_DIR / "*.parquet"))
    if not files:
        print("No parquet files found in warehouse/raw/")
        return
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    print(f"Read {len(df)} transactions from {len(files)} files")

    # 2. Authenticate to BigQuery with the service account key
    credentials = service_account.Credentials.from_service_account_file(str(KEY_PATH))

    # 3. Upload to BigQuery (replace the table if it already exists)
    destination = f"{DATASET}.{TABLE}"
    pandas_gbq.to_gbq(
        df,
        destination_table=destination,
        project_id=PROJECT_ID,
        credentials=credentials,
        if_exists="replace",
        location="europe-west1",
    )
    print(f"Loaded {len(df)} rows into {PROJECT_ID}.{destination}")


if __name__ == "__main__":
    main()