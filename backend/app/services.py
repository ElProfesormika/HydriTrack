from __future__ import annotations

import math
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .admin_store import AdminStore
from .ml import MeterAnomalyEngine
from .models import Alert, Anomaly, MeterDataIn, MeterReadingIn, MeterReadingUpdate, NetworkState, PressureDataIn
from .persistence import SQLiteStore
from .pressure_analysis import (
    analyze_pressure_event,
    build_localization_record,
    localization_alert_message,
    pending_meter_context_for_zone,
    pressure_leak_score,
)
from .registry import NetworkRegistry

_BASE_LAT = 48.505
_BASE_LNG = 3.53


def _risk_from_leak(probability: float) -> str:
    if probability >= 0.75:
        return "critical"
    if probability >= 0.5:
        return "warning"
    if probability >= 0.25:
        return "caution"
    return "normal"


class InMemoryStore:
    def __init__(self, max_items: int = 500) -> None:
        self.meter_data: deque[MeterDataIn] = deque(maxlen=max_items)
        self.pressure_data: deque[PressureDataIn] = deque(maxlen=max_items)
        self.anomalies: deque[Anomaly] = deque(maxlen=max_items)
        self.alerts: deque[Alert] = deque(maxlen=max_items)
        self.pending_meter_suspicions: dict[str, dict[str, Any]] = {}
        self.ml_engine = MeterAnomalyEngine()
        self.sqlite = SQLiteStore(Path(__file__).resolve().parents[1] / "data" / "hydrotrack.db")
        self.registry = NetworkRegistry()
        self.admin = AdminStore(self.sqlite, self.registry)

    def _process_meter_ml(self, payload: MeterDataIn) -> dict[str, Any]:
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

        if leak_probability >= 0.45:
            self.pending_meter_suspicions[payload.meter_id] = {
                "meter_id": payload.meter_id,
                "leak_probability": leak_probability,
                "timestamp": payload.timestamp.isoformat(),
                "zone_ids": [int(s["zone_id"]) for s in self.registry.segments_for_meter(payload.meter_id)],
            }

        if leak_probability >= 0.75:
            alert = Alert(
                timestamp=payload.timestamp,
                severity="critical",
                category="leak_suspected",
                source_id=payload.meter_id,
                message=(
                    f"Fuite suspectee critique sur {payload.meter_id} "
                    f"(probabilite={leak_probability:.2f}) — confirmation capteurs en attente"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)
        elif leak_probability >= 0.5:
            alert = Alert(
                timestamp=payload.timestamp,
                severity="warning",
                category="anomaly",
                source_id=payload.meter_id,
                message=(
                    f"Anomalie significative sur {payload.meter_id} "
                    f"(probabilite={leak_probability:.2f})"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)
        elif leak_probability >= 0.25:
            alert = Alert(
                timestamp=payload.timestamp,
                severity="caution",
                category="anomaly",
                source_id=payload.meter_id,
                message=(
                    f"Surveillance renforcee sur {payload.meter_id} "
                    f"(probabilite={leak_probability:.2f})"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)
        elif leak_probability >= 0.1:
            alert = Alert(
                timestamp=payload.timestamp,
                severity="normal",
                category="anomaly",
                source_id=payload.meter_id,
                message=(
                    f"Leve legere sur {payload.meter_id} "
                    f"(probabilite={leak_probability:.2f})"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)

        return {
            "anomaly_score": round(anomaly_score, 2),
            "leak_probability": round(leak_probability, 2),
            "ml_model": "IsolationForest(n=300)+seuils quantiles decision (HydroTrack IA)",
        }

    def _segment_payload(self, seg: dict[str, Any]) -> dict[str, Any]:
        zid = int(seg["zone_id"])
        sensor_ids = [s["sensor_id"] for s in self.registry.sensors if int(s["zone_id"]) == zid]
        return {
            "id": seg["segment_id"],
            "segment_id": seg["segment_id"],
            "zone_id": zid,
            "upstream_meter": seg["upstream_meter"],
            "downstream_meter": seg["downstream_meter"],
            "length_m": float(seg["length_m"]),
            "sensor_ids": sensor_ids,
        }

    def ingest_meter(self, payload: MeterDataIn) -> dict[str, Any]:
        if payload.meter_id not in self.registry.meter_ids:
            raise ValueError(f"Compteur inconnu: {payload.meter_id}")
        self.meter_data.append(payload)
        meter_data_id = self.sqlite.insert_meter_data(payload)
        result = self._process_meter_ml(payload)
        result["meter_data_id"] = meter_data_id
        return result

    def score_meter_reading(self, payload: MeterDataIn) -> dict[str, Any]:
        if payload.meter_id not in self.registry.meter_ids:
            raise ValueError(f"Compteur inconnu: {payload.meter_id}")
        return self._process_meter_ml(payload)

    def ingest_pressure(self, payload: PressureDataIn) -> dict[str, Any]:
        self.pressure_data.append(payload)
        self.sqlite.insert_pressure_data(payload)

        zone_id = self.registry.resolve_zone_id(payload.zone) or self.registry.sensor_zone_id(
            payload.sensor_id
        )
        if zone_id is None:
            return {
                "status": "processed",
                "warning": f"Zone non reconnue: {payload.zone}",
                "pressure_leak_score": pressure_leak_score(
                    payload.intensity, payload.frequency, payload.pressure_signal
                ),
            }

        seg_row = self.registry.segment_for_zone(zone_id)
        if not seg_row:
            return {"status": "processed", "warning": "Segment introuvable"}
        segment = self._segment_payload(seg_row)

        sensor_readings = self.sqlite.latest_pressure_by_sensor_ids(segment["sensor_ids"])
        sensor_readings[payload.sensor_id] = {
            "sensor_id": payload.sensor_id,
            "timestamp": payload.timestamp.isoformat(),
            "zone": payload.zone,
            "pressure_signal": payload.pressure_signal,
            "frequency": payload.frequency,
            "intensity": payload.intensity,
        }

        meter_ctx = pending_meter_context_for_zone(zone_id, self.pending_meter_suspicions)
        analysis = analyze_pressure_event(
            payload, zone_id, segment, sensor_readings, meter_ctx
        )
        if analysis.get("confirmed") and analysis.get("position_ratio") is not None:
            plan = self.registry.interpolate_leak_plan_xy(segment, float(analysis["position_ratio"]))
            analysis["plan_x"] = plan["x"]
            analysis["plan_y"] = plan["y"]
        record = build_localization_record(analysis, payload.sensor_id, payload.timestamp)
        loc_id = self.sqlite.insert_leak_localization(record)
        if analysis.get("confirmed"):
            try:
                self.admin.create_leak_incident(
                    {
                        "localization_id": loc_id,
                        "zone_id": zone_id,
                        "segment_id": segment["segment_id"],
                        "status": "confirmed",
                        "detected_at": payload.timestamp.isoformat(),
                        "upstream_meter": segment["upstream_meter"],
                        "downstream_meter": segment["downstream_meter"],
                        "distance_m_from_upstream": analysis.get("distance_m_from_upstream"),
                        "meter_source": (meter_ctx or {}).get("meter_id"),
                        "admin_notes": "Detection automatique capteurs",
                    }
                )
            except Exception:
                pass

        result: dict[str, Any] = {
            "status": "processed",
            "localization_id": loc_id,
            "zone_id": zone_id,
            "segment_id": segment["segment_id"],
            **analysis,
        }

        now = datetime.now(timezone.utc)
        if analysis.get("confirmed"):
            if meter_ctx and meter_ctx.get("meter_id"):
                self.pending_meter_suspicions.pop(meter_ctx["meter_id"], None)
            severity = "critical" if (analysis.get("confirmation_confidence") or 0) >= 0.7 else "warning"
            alert = Alert(
                timestamp=now,
                severity=severity,
                category="leak_confirmed",
                source_id=payload.sensor_id,
                message=localization_alert_message(record),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)
            result["alert_created"] = True
        elif (analysis.get("pressure_leak_score") or 0) >= 0.55:
            alert = Alert(
                timestamp=now,
                severity="caution",
                category="leak_suspected",
                source_id=payload.sensor_id,
                message=(
                    f"Signal pression zone {zone_id} — analyse capteurs en cours "
                    f"(score={analysis.get('pressure_leak_score'):.2f})"
                ),
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)
            result["alert_created"] = True
        elif (analysis.get("pressure_leak_score") or 0) >= 0.35:
            alert = Alert(
                timestamp=now,
                severity="normal",
                category="anomaly",
                source_id=payload.sensor_id,
                message=f"Variation pression zone {zone_id} (capteur={payload.sensor_id})",
            )
            self.alerts.append(alert)
            self.sqlite.insert_alert(alert)

        return result

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

    def get_meter_flow_per_meter(
        self,
        bucket_minutes: int = 60,
        points: int = 72,
        meter_order: list[str] | None = None,
    ) -> dict:
        return self.sqlite.meter_flow_per_meter_series(
            bucket_minutes=bucket_minutes,
            points=points,
            meter_order=meter_order,
        )

    def get_alert_stats(self) -> dict:
        return self.sqlite.alert_stats()

    def get_sensors_catalog(self) -> list[dict]:
        return self.sqlite.sensors_catalog()

    def get_meter_profile(
        self,
        meter_id: str,
        bucket_minutes: int = 30,
        points: int = 48,
        recent_limit: int = 12,
    ) -> dict:
        return self.sqlite.meter_profile(
            meter_id=meter_id,
            bucket_minutes=bucket_minutes,
            points=points,
            recent_limit=recent_limit,
        )

    def list_meter_readings(self, limit: int = 10, meter_id: str | None = None) -> list[dict]:
        return self.sqlite.list_manual_readings(limit=limit, meter_id=meter_id)

    def get_meter_reading(self, reading_id: int) -> dict | None:
        return self.sqlite.get_manual_reading(reading_id)

    def create_meter_reading(self, payload: MeterReadingIn) -> dict[str, Any]:
        if payload.meter_id not in self.registry.meter_ids:
            raise ValueError(f"Compteur inconnu: {payload.meter_id}")
        now = datetime.now(timezone.utc).isoformat()
        meter_payload = MeterDataIn(
            timestamp=payload.timestamp,
            meter_id=payload.meter_id,
            volume=payload.volume,
            flow_rate=payload.flow_rate,
        )
        ml_result = self.ingest_meter(meter_payload)
        reading_id = self.sqlite.insert_manual_reading(
            timestamp=payload.timestamp.isoformat(),
            meter_id=payload.meter_id,
            volume=payload.volume,
            flow_rate=payload.flow_rate,
            notes=payload.notes or "",
            meter_data_id=ml_result.get("meter_data_id"),
            created_at=now,
            updated_at=now,
        )
        reading = self.sqlite.get_manual_reading(reading_id)
        return {"reading": reading, "ml": ml_result}

    def update_meter_reading(self, reading_id: int, payload: MeterReadingUpdate) -> dict[str, Any]:
        current = self.sqlite.get_manual_reading(reading_id)
        if not current:
            raise ValueError("Releve introuvable")

        meter_id = payload.meter_id or current["meter_id"]
        if meter_id not in self.registry.meter_ids:
            raise ValueError(f"Compteur inconnu: {meter_id}")

        ts_raw = payload.timestamp.isoformat() if payload.timestamp else current["timestamp"]
        volume = float(payload.volume if payload.volume is not None else current["volume"])
        flow_rate = float(payload.flow_rate if payload.flow_rate is not None else current["flow_rate"])
        notes = payload.notes if payload.notes is not None else (current.get("notes") or "")

        meter_payload = MeterDataIn(
            timestamp=datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")),
            meter_id=meter_id,
            volume=volume,
            flow_rate=flow_rate,
        )
        meter_data_id = current.get("meter_data_id")
        if meter_data_id:
            self.sqlite.update_meter_data(int(meter_data_id), meter_payload)
        else:
            meter_data_id = self.sqlite.insert_meter_data(meter_payload)

        ml_result = self.score_meter_reading(meter_payload)
        updated_at = datetime.now(timezone.utc).isoformat()
        self.sqlite.update_manual_reading(
            reading_id=reading_id,
            timestamp=ts_raw,
            meter_id=meter_id,
            volume=volume,
            flow_rate=flow_rate,
            notes=notes,
            meter_data_id=int(meter_data_id) if meter_data_id else None,
            updated_at=updated_at,
        )
        reading = self.sqlite.get_manual_reading(reading_id)
        return {"reading": reading, "ml": ml_result}

    def delete_meter_reading(self, reading_id: int) -> dict[str, Any]:
        row = self.sqlite.delete_manual_reading(reading_id)
        if not row:
            raise ValueError("Releve introuvable")
        meter_data_id = row.get("meter_data_id")
        if meter_data_id:
            self.sqlite.delete_meter_data(int(meter_data_id))
        return {"deleted": row}

    def get_network_topology(self) -> dict[str, Any]:
        return self.registry.export_topology()

    def get_zone_sensor_status(self) -> list[dict[str, Any]]:
        latest_leaks = self.sqlite.latest_leak_by_zone()
        items: list[dict[str, Any]] = []
        for zone in self.registry.zones:
            zid = int(zone["zone_id"])
            seg_row = self.registry.segment_for_zone(zid)
            if not seg_row:
                continue
            segment = self._segment_payload(seg_row)
            readings = self.sqlite.latest_pressure_by_sensor_ids(segment["sensor_ids"])
            sensors = []
            scores = []
            for sid in segment["sensor_ids"]:
                row = readings.get(sid)
                if row:
                    score = pressure_leak_score(
                        float(row.get("intensity") or 0),
                        float(row.get("frequency") or 0),
                        float(row.get("pressure_signal") or 0),
                    )
                    scores.append(score)
                    sensors.append(
                        {
                            "sensor_id": sid,
                            "last_seen": row.get("timestamp"),
                            "intensity": row.get("intensity"),
                            "frequency": row.get("frequency"),
                            "leak_score": round(score, 3),
                            "status": (
                                "critical"
                                if score >= 0.75
                                else "warning"
                                if score >= 0.5
                                else "caution"
                                if score >= 0.25
                                else "normal"
                            ),
                        }
                    )
                else:
                    sensors.append({"sensor_id": sid, "status": "offline", "leak_score": 0})

            leak = latest_leaks.get(zid)
            meter_ctx = pending_meter_context_for_zone(zid, self.pending_meter_suspicions)
            confirmation = "none"
            if leak and leak.get("confirmed"):
                confirmation = "confirmed"
            elif meter_ctx or (leak and not leak.get("confirmed")):
                confirmation = "pending"
            elif scores and max(scores) >= 0.55:
                confirmation = "pending"

            items.append(
                {
                    "zone_id": zid,
                    "zone_name": zone["name"],
                    "short_name": zone.get("short_name"),
                    "segment": {
                        "id": segment["segment_id"],
                        "upstream_meter": segment["upstream_meter"],
                        "downstream_meter": segment["downstream_meter"],
                        "length_m": segment["length_m"],
                    },
                    "sensors": sensors,
                    "confirmation_status": confirmation,
                    "pending_meter": meter_ctx,
                    "latest_localization": leak,
                    "max_sensor_score": round(max(scores) if scores else 0, 3),
                }
            )
        return items

    def get_leak_localizations(self, limit: int = 20, confirmed_only: bool = False) -> list[dict[str, Any]]:
        return self.sqlite.get_leak_localizations(limit=limit, confirmed_only=confirmed_only)

    def get_map_zones_enriched(self) -> list[dict[str, Any]]:
        latest = self.sqlite.latest_leak_by_zone()
        items = []
        for zone in self.registry.zones:
            zid = int(zone["zone_id"])
            seg = self.registry.segment_for_zone(zid)
            leak = latest.get(zid)
            status = "normal"
            if leak and leak.get("confirmed"):
                status = "leak_confirmed"
            elif leak or pending_meter_context_for_zone(zid, self.pending_meter_suspicions):
                status = "investigating"
            items.append(
                {
                    "id": zid,
                    "name": zone["name"],
                    "short_name": zone.get("short_name"),
                    "lat": zone.get("lat"),
                    "lng": zone.get("lng"),
                    "segment": seg,
                    "status": status,
                    "latest_localization": leak,
                }
            )
        return items

    def get_map_leak_markers(self, limit: int = 50) -> list[dict[str, Any]]:
        localizations = self.sqlite.get_leak_localizations(limit=limit, confirmed_only=True)
        items = []
        for loc in localizations:
            if loc.get("plan_x") is None or loc.get("plan_y") is None:
                continue
            zone = self.registry.zone_by_id(int(loc["zone_id"])) or {}
            items.append(
                {
                    "zone_id": loc["zone_id"],
                    "zone_name": zone.get("name", f"Zone {loc['zone_id']}") if zone else f"Zone {loc['zone_id']}",
                    "lat": zone.get("lat"),
                    "lng": zone.get("lng"),
                    "plan_x": loc["plan_x"],
                    "plan_y": loc["plan_y"],
                    "severity": "critical" if (loc.get("localization_confidence") or 0) >= 0.6 else "warning",
                    "message": (
                        f"Fuite localisee: {loc.get('distance_m_from_upstream', 0):.0f} m "
                        f"depuis {loc.get('upstream_meter')} "
                        f"({loc.get('localization_confidence', 0):.0%})"
                    ),
                    "timestamp": loc.get("timestamp"),
                    "distance_m_from_upstream": loc.get("distance_m_from_upstream"),
                    "segment_length_m": loc.get("segment_length_m"),
                    "upstream_meter": loc.get("upstream_meter"),
                    "downstream_meter": loc.get("downstream_meter"),
                }
            )
        return items

    def get_map_meter_items(self) -> list[dict[str, Any]]:
        telemetry = self.sqlite.latest_meter_telemetry_by_id()
        anomalies = self.sqlite.latest_anomaly_by_meter_id()
        labels = self.registry.meter_labels()
        items: list[dict[str, Any]] = []
        for idx, meter in enumerate(self.registry.meters):
            meter_id = meter["meter_id"]
            tel = telemetry.get(meter_id, {})
            anom = anomalies.get(meter_id)
            leak_p = float(anom["leak_probability"]) if anom else 0.0
            items.append(
                {
                    "id": idx + 1,
                    "meter_id": meter_id,
                    "name": labels.get(meter_id, meter_id.replace("_", " ")),
                    "lat": meter.get("lat") or _BASE_LAT + 0.009 * math.sin(2 * math.pi * idx / max(len(self.registry.meters), 1)),
                    "lng": meter.get("lng") or _BASE_LNG + 0.014 * math.cos(2 * math.pi * idx / max(len(self.registry.meters), 1)),
                    "last_reading_at": tel.get("last_reading_at"),
                    "last_flow_rate": tel.get("last_flow_rate"),
                    "last_volume": tel.get("last_volume"),
                    "latest_anomaly": anom,
                    "risk_level": _risk_from_leak(leak_p),
                }
            )
        return items
