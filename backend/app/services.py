from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ml import MeterAnomalyEngine
from .models import Alert, Anomaly, MeterDataIn, NetworkState, PressureDataIn
from .persistence import SQLiteStore


class InMemoryStore:
    def __init__(self, max_items: int = 500) -> None:
        self.meter_data: deque[MeterDataIn] = deque(maxlen=max_items)
        self.pressure_data: deque[PressureDataIn] = deque(maxlen=max_items)
        self.anomalies: deque[Anomaly] = deque(maxlen=max_items)
        self.alerts: deque[Alert] = deque(maxlen=max_items)
        self.ml_engine = MeterAnomalyEngine()
        self.sqlite = SQLiteStore(Path(__file__).resolve().parents[1] / "data" / "hydrotrack.db")

    def ingest_meter(self, payload: MeterDataIn) -> dict[str, Any]:
        self.meter_data.append(payload)
        self.sqlite.insert_meter_data(payload)

        anomaly_score, leak_probability = self.ml_engine.score(
            meter_id=payload.meter_id, flow_rate=payload.flow_rate
        )

        anomaly = Anomaly(
            timestamp=payload.timestamp,
            meter_id=payload.meter_id,
            score=anomaly_score,
            leak_probability=leak_probability,
        )
        self.anomalies.append(anomaly)
        self.sqlite.insert_anomaly(anomaly)

        if leak_probability >= 0.75:
            alert = Alert(
                timestamp=datetime.now(timezone.utc),
                severity="critical",
                category="leak_suspected",
                source_id=payload.meter_id,
                message=(
                    f"Fuite suspectee sur {payload.meter_id} "
                    f"(probabilite={leak_probability:.2f})"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)
        elif leak_probability >= 0.5:
            alert = Alert(
                timestamp=datetime.now(timezone.utc),
                severity="warning",
                category="anomaly",
                source_id=payload.meter_id,
                message=f"Anomalie detectee sur {payload.meter_id}",
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)

        return {
            "anomaly_score": round(anomaly_score, 2),
            "leak_probability": round(leak_probability, 2),
        }

    def ingest_pressure(self, payload: PressureDataIn) -> dict[str, Any]:
        self.pressure_data.append(payload)
        self.sqlite.insert_pressure_data(payload)

        if payload.intensity >= 85 and payload.frequency >= 15:
            alert = Alert(
                timestamp=datetime.now(timezone.utc),
                severity="critical",
                category="leak_confirmed",
                source_id=payload.sensor_id,
                message=(
                    f"Fuite confirmee dans la zone {payload.zone} "
                    f"(capteur={payload.sensor_id})"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)

        return {"status": "processed"}

    def get_network_state(self) -> NetworkState:
        counts = self.sqlite.counts()
        return NetworkState(
            timestamp=datetime.now(timezone.utc),
            active_alerts=counts["alerts"],
            latest_anomalies=counts["anomalies"],
            ingested_meter_points=counts["meter_data"],
            ingested_pressure_points=counts["pressure_data"],
        )

    def get_anomalies(self, limit: int) -> list[dict]:
        return self.sqlite.get_latest_anomalies(limit=limit)

    def get_alerts(self, limit: int) -> list[dict]:
        return self.sqlite.get_latest_alerts(limit=limit)

    def add_alert(self, alert: Alert) -> None:
        self.alerts.append(alert)
        self.sqlite.insert_alert(alert)

    def get_dashboard_overview(self) -> dict:
        return {
            "network_state": self.get_network_state().model_dump(),
            "meter_kpis": self.sqlite.meter_kpis(),
            "sensor_kpis": self.sqlite.sensor_kpis(),
            "top_anomalous_meters": self.sqlite.top_anomalous_meters(),
            "top_alert_sources": self.sqlite.top_alert_sources(),
        }

    def get_timeseries(self, bucket_minutes: int = 30, points: int = 24) -> list[dict]:
        return self.sqlite.timeseries(bucket_minutes=bucket_minutes, points=points)

    def get_meter_flow_timeseries(self, bucket_minutes: int = 60, points: int = 24) -> list[dict]:
        return self.sqlite.meter_flow_timeseries(bucket_minutes=bucket_minutes, points=points)

    def get_pressure_timeseries(self, bucket_minutes: int = 60, points: int = 24) -> list[dict]:
        return self.sqlite.pressure_intensity_timeseries(bucket_minutes=bucket_minutes, points=points)

    def get_alert_stats(self) -> dict:
        return self.sqlite.alert_stats()
