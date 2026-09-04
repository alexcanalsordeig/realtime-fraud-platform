"""Land the transaction stream into the RAW layer (append-only Parquet)."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from generate_transactions import transaction_stream

# Where raw data lands. parents[1] = project root (one level up from ingestion/)
RAW_DIR = Path(__file__).resolve().parents[1] / "warehouse" / "raw"
BATCH_SIZE = 100


def write_batch(rows: list[dict], part: int) -> None:
    """Write one batch of transactions to a Parquet file in RAW."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df["_ingested_at"] = datetime.now(timezone.utc).isoformat()  # when we landed it
    out = RAW_DIR / f"transactions_raw_part_{part:05d}.parquet"
    df.to_parquet(out, index=False)
    print(f"[land_raw] wrote {len(rows)} rows -> {out.name}")


def main() -> None:
    batch: list[dict] = []
    part = 0
    try:
        for txn in transaction_stream():
            batch.append(txn)
            if len(batch) >= BATCH_SIZE:
                write_batch(batch, part)
                part += 1
                batch = []
    except KeyboardInterrupt:
        if batch:                       # save whatever is left before exiting
            write_batch(batch, part)
        print("\n[land_raw] stopped cleanly.")


if __name__ == "__main__":
    main()