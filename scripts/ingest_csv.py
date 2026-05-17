#!/usr/bin/env python3
"""Import CSV via API (legacy). Prefer seed_meters_from_csv.py pour import rapide."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk ingest HydroTrack meter CSV")
    parser.add_argument(
        "--csv",
        default="Donnee_compteur_SEP.csv",
        help="Path to CSV file containing meter series",
    )
    parser.add_argument("--reset", action="store_true", help="Reset meter data before import")
    parser.add_argument(
        "--max-points",
        type=int,
        default=0,
        help="Max points to ingest (0 = all)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        csv_path = root / csv_path

    cmd = [
        sys.executable,
        str(root / "scripts" / "seed_meters_from_csv.py"),
        "--csv",
        str(csv_path),
    ]
    if args.reset:
        cmd.append("--reset")
    if args.max_points:
        cmd.extend(["--max-points", str(args.max_points)])

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
