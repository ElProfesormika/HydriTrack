#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk ingest HydroTrack meter CSV")
    parser.add_argument(
        "--csv",
        default="CALCUL_JPD_2025.csv",
        help="Path to CSV file containing meter series",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="HydroTrack API base URL",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=500,
        help="Maximum rows to ingest",
    )
    return parser.parse_args()


def try_parse_datetime(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def coerce_float(value: Any) -> float | None:
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def ingest(csv_path: Path, api_base: str, max_rows: int) -> int:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV vide ou en-tete introuvable")

        datetime_col = next(
            (c for c in reader.fieldnames if "date" in c.lower() or "hora" in c.lower()),
            None,
        )
        numeric_cols = [c for c in reader.fieldnames if c != datetime_col]

        sent = 0
        for row in reader:
            if sent >= max_rows:
                break

            timestamp = (
                try_parse_datetime(row.get(datetime_col, "")) if datetime_col else None
            ) or datetime.now(timezone.utc)

            for col in numeric_cols:
                value = coerce_float(row.get(col))
                if value is None:
                    continue
                payload = {
                    "timestamp": timestamp.isoformat(),
                    "meter_id": col,
                    "volume": max(0.0, value),
                    "flow_rate": max(0.0, value),
                }
                response = requests.post(
                    f"{api_base}/api/meters/data",
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                sent += 1
                if sent >= max_rows:
                    break
        return sent


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV introuvable: {csv_path}")

    count = ingest(csv_path=csv_path, api_base=args.api_base, max_rows=args.max_rows)
    print(f"Ingestion terminee: {count} points envoyes vers {args.api_base}")


if __name__ == "__main__":
    main()
