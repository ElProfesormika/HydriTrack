#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

DEFAULT_TARGET_METERS = [
    "AMPERE_1",
    "AMPERE_2",
    "BCA1",
    "BCA2",
    "BECQUEREL",
    "CCAS",
    "CHARPAK",
    "EINSTEIN",
    "SIMULATEUR",
    "FARADAY",
    "FRANKLIN",
    "JOLIOT_CURIE_1",
    "JOLIOT_CURIE_2",
    "NEWTON",
    "PAP",
    "VOLTA",
    "AVOGADRO",
    "EDISON",
    "COULOMB1",
    "COULOMB2",
    "TREMPLIN",
    "SALLE_MUSCULATION",
    "COMPTEUR_23",
]


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
    parser.add_argument(
        "--target-count",
        type=int,
        default=23,
        help="Number of target meters to feed with default distribution",
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


def _distribution_factor(index: int) -> float:
    return 0.92 + (index % 7) * 0.025


def ingest(csv_path: Path, api_base: str, max_rows: int, target_count: int) -> int:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ";"
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV vide ou en-tete introuvable")

        datetime_col = next(
            (c for c in reader.fieldnames if "date" in c.lower() or "hora" in c.lower()),
            None,
        )
        numeric_cols = [
            c
            for c in reader.fieldnames
            if c != datetime_col and "_qualite" not in c.lower() and "qualite" not in c.lower()
        ]
        target_meters = DEFAULT_TARGET_METERS[: max(1, min(target_count, len(DEFAULT_TARGET_METERS)))]
        source_prev: dict[str, float] = {}
        target_volume: dict[str, float] = {meter_id: 0.0 for meter_id in target_meters}
        prev_ts: datetime | None = None

        sent = 0
        failed = 0
        session = requests.Session()
        for row in reader:
            if sent >= max_rows:
                break

            timestamp = (
                try_parse_datetime(row.get(datetime_col, "")) if datetime_col else None
            ) or datetime.now(timezone.utc)
            hours = 1.0
            if prev_ts is not None:
                dt = (timestamp - prev_ts).total_seconds() / 3600.0
                hours = max(dt, 1.0 / 3600.0)
            prev_ts = timestamp

            source_deltas: list[float] = []
            for col in numeric_cols:
                value = coerce_float(row.get(col))
                if value is None:
                    continue
                prev = source_prev.get(col)
                source_prev[col] = value
                if prev is None:
                    continue
                source_deltas.append(max(0.0, value - prev))
            if not source_deltas:
                continue

            for idx, meter_id in enumerate(target_meters):
                source_delta = source_deltas[idx % len(source_deltas)]
                distributed_delta = source_delta * _distribution_factor(idx)
                target_volume[meter_id] += distributed_delta
                payload = {
                    "timestamp": timestamp.isoformat(),
                    "meter_id": meter_id,
                    "volume": round(max(0.0, target_volume[meter_id]), 4),
                    "flow_rate": round(max(0.0, distributed_delta / hours), 4),
                }
                response = None
                for _ in range(3):
                    try:
                        response = session.post(
                            f"{api_base}/api/meters/data",
                            json=payload,
                            timeout=15,
                        )
                        break
                    except requests.RequestException:
                        time.sleep(0.2)
                if response is None:
                    failed += 1
                    if failed <= 8:
                        print(
                            f"[warn] echec reseau meter={payload['meter_id']} ts={payload['timestamp']}"
                        )
                    continue
                if not response.ok:
                    failed += 1
                    if failed <= 8:
                        print(
                            f"[warn] ligne rejetee meter={payload['meter_id']} ts={payload['timestamp']} "
                            f"status={response.status_code} body={response.text[:180]}"
                        )
                    continue
                sent += 1
                time.sleep(0.005)
                if sent >= max_rows:
                    break
        if failed:
            print(f"[warn] points rejetes: {failed}")
        print(
            f"[info] compteurs cibles alimentes: {len(target_meters)} -> "
            + ", ".join(target_meters)
        )
        return sent


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV introuvable: {csv_path}")

    count = ingest(
        csv_path=csv_path,
        api_base=args.api_base,
        max_rows=args.max_rows,
        target_count=args.target_count,
    )
    print(f"Ingestion terminee: {count} points envoyes vers {args.api_base}")


if __name__ == "__main__":
    main()
