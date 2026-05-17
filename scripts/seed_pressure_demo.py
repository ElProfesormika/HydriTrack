#!/usr/bin/env python3
"""Injecte des donnees pression de demo pour tester confirmation + localisation."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.network_topology import NETWORK_SEGMENTS  # noqa: E402

API = "http://127.0.0.1:8000"


def post_pressure(client: httpx.Client, sensor_id: str, zone_name: str, intensity: float, frequency: float, ts: datetime) -> None:
    payload = {
        "timestamp": ts.isoformat(),
        "sensor_id": sensor_id,
        "zone": zone_name,
        "pressure_signal": round(intensity / 45.0, 3),
        "frequency": frequency,
        "intensity": intensity,
    }
    r = client.post(f"{API}/api/sensors/pressure", json=payload, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    print(f"  {sensor_id} I={intensity} -> confirmed={data.get('result', {}).get('confirmed')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=API)
    parser.add_argument("--zone-id", type=int, default=6, help="Zone a simuler (defaut: 6 TR3/4)")
    args = parser.parse_args()
    global API
    API = args.api.rstrip("/")

    seg = next(s for s in NETWORK_SEGMENTS if s["zone_id"] == args.zone_id)
    zone_name = f"Zone {args.zone_id}"
    ids = seg["sensor_ids"]
    now = datetime.now(timezone.utc)

    print(f"Simulation fuite zone {args.zone_id} ({seg['upstream_meter']} -> {seg['downstream_meter']})")
    with httpx.Client() as client:
        # Capteur amont : signal plus fort (fuite plus proche cote aval dans fallback amplitude)
        post_pressure(client, ids[0], zone_name, intensity=78.0, frequency=14.0, ts=now - timedelta(seconds=2))
        post_pressure(client, ids[1], zone_name, intensity=88.0, frequency=16.5, ts=now)

    print("Termine. Consultez /dashboard/capteurs et /cartographie.")


if __name__ == "__main__":
    main()
