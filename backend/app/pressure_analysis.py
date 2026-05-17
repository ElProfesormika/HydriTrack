"""Analyse des ondes de pression : confirmation de fuite et localisation sur troncon."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import PressureDataIn
from .network_topology import (
    interpolate_leak_plan_xy,
    segment_for_zone,
    segments_for_meter,
)

# Vitesse d'onde acoustique approximative dans conduite (m/s) — implementation par defaut
DEFAULT_WAVE_SPEED_M_S = 1200.0

# Seuils confirmation / localisation
PRESSURE_LEAK_SCORE_CONFIRM = 0.52
CORRELATION_MIN = 0.28
METER_LEAK_PROB_CONFIRM = 0.45


def pressure_leak_score(intensity: float, frequency: float, pressure_signal: float) -> float:
    """Score 0-1 de suspicion de fuite a partir du signal pression."""
    i = max(0.0, float(intensity)) / 100.0
    f = max(0.0, float(frequency)) / 25.0
    p = min(1.0, abs(float(pressure_signal)) / 3.0)
    return min(1.0, i * 0.5 + f * 0.35 + p * 0.15)


def correlate_sensor_readings(reading_a: dict[str, Any], reading_b: dict[str, Any]) -> float:
    """Correlation simplifiee entre deux capteurs d'une meme zone."""
    ia = float(reading_a.get("intensity") or 0)
    ib = float(reading_b.get("intensity") or 0)
    fa = float(reading_a.get("frequency") or 0)
    fb = float(reading_b.get("frequency") or 0)
    if ia + ib < 1e-6:
        return 0.0
    di = 1.0 - abs(ia - ib) / max(ia, ib, 1.0)
    df = 1.0 - abs(fa - fb) / max(fa, fb, 1.0) if fa + fb > 1e-6 else 0.5
    return max(0.0, min(1.0, (di + df) / 2.0))


def confirm_leak(
    *,
    meter_leak_probability: float | None,
    sensor_scores: list[float],
    correlation: float,
) -> tuple[bool, float]:
    """
    Etape 1 : confirmer ou infirmer une fuite a partir compteur + capteurs zone.
    """
    meter_signal = float(meter_leak_probability or 0) >= METER_LEAK_PROB_CONFIRM
    max_sensor = max(sensor_scores) if sensor_scores else 0.0
    pressure_signal = max_sensor >= PRESSURE_LEAK_SCORE_CONFIRM
    correlated = correlation >= CORRELATION_MIN

    if meter_signal and pressure_signal and correlated:
        confidence = min(1.0, (meter_leak_probability or 0) * 0.45 + max_sensor * 0.35 + correlation * 0.2)
        return True, round(confidence, 3)
    if pressure_signal and correlated and max_sensor >= 0.65:
        return True, round(max_sensor * 0.7 + correlation * 0.3, 3)
    if meter_signal and max_sensor >= 0.4:
        return False, round(max(meter_leak_probability or 0, max_sensor) * 0.5, 3)
    return False, round(max(max_sensor, float(meter_leak_probability or 0)) * 0.4, 3)


def estimate_leak_distance(
    segment: dict[str, Any],
    reading_upstream: dict[str, Any],
    reading_downstream: dict[str, Any],
    wave_speed_m_s: float = DEFAULT_WAVE_SPEED_M_S,
) -> tuple[float, float, float]:
    """
    Etape 2 : estimer la distance du point de fuite depuis le compteur amont (m).
    Retourne (distance_m, position_ratio 0-1, confidence).
    """
    length_m = float(segment.get("length_m") or 100.0)
    ia = float(reading_upstream.get("intensity") or 0)
    ib = float(reading_downstream.get("intensity") or 0)

    ts_a = reading_upstream.get("timestamp")
    ts_b = reading_downstream.get("timestamp")
    dt_s: float | None = None
    if ts_a and ts_b:
        try:
            ta = datetime.fromisoformat(str(ts_a).replace("Z", "+00:00"))
            tb = datetime.fromisoformat(str(ts_b).replace("Z", "+00:00"))
            dt_s = abs((tb - ta).total_seconds())
        except ValueError:
            dt_s = None

    if dt_s is not None and dt_s > 0.001 and wave_speed_m_s > 0:
        # d = (L + v * dt) / 2  (modele bilaterale simplifie)
        distance_m = max(0.0, min(length_m, (length_m + wave_speed_m_s * dt_s) / 2.0))
        confidence = min(1.0, 0.55 + min(dt_s, 2.0) * 0.15)
    else:
        # Fallback : amplitude plus forte cote plus proche de la fuite
        total = ia + ib
        if total < 1e-6:
            ratio = 0.5
            confidence = 0.25
        else:
            ratio = ib / total
            spread = abs(ia - ib) / max(ia, ib, 1.0)
            confidence = min(1.0, 0.35 + spread * 0.5)
        distance_m = length_m * ratio

    position_ratio = distance_m / length_m if length_m > 0 else 0.5
    return round(distance_m, 1), round(max(0.0, min(1.0, position_ratio)), 4), round(confidence, 3)


def analyze_pressure_event(
    payload: PressureDataIn,
    zone_id: int,
    segment: dict[str, Any],
    sensor_readings: dict[str, dict[str, Any]],
    meter_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Pipeline complet : signature, confirmation, localisation."""
    score = pressure_leak_score(payload.intensity, payload.frequency, payload.pressure_signal)
    sensor_scores = [
        pressure_leak_score(
            float(r.get("intensity") or 0),
            float(r.get("frequency") or 0),
            float(r.get("pressure_signal") or 0),
        )
        for r in sensor_readings.values()
    ]

    ids = segment.get("sensor_ids") or []
    correlation = 0.0
    if len(ids) >= 2 and ids[0] in sensor_readings and ids[1] in sensor_readings:
        correlation = correlate_sensor_readings(sensor_readings[ids[0]], sensor_readings[ids[1]])

    meter_prob = None
    if meter_context:
        meter_prob = float(meter_context.get("leak_probability") or 0)

    confirmed, confirm_conf = confirm_leak(
        meter_leak_probability=meter_prob,
        sensor_scores=sensor_scores + [score],
        correlation=correlation if correlation > 0 else 0.35,
    )

    result: dict[str, Any] = {
        "zone_id": zone_id,
        "segment_id": segment["id"],
        "pressure_leak_score": round(score, 3),
        "sensor_correlation": round(correlation, 3),
        "confirmed": confirmed,
        "confirmation_confidence": confirm_conf,
        "meter_context": meter_context,
    }

    if confirmed and len(ids) >= 2:
        up_reading = sensor_readings.get(ids[0], sensor_readings.get(payload.sensor_id, {}))
        down_reading = sensor_readings.get(ids[1], up_reading)
        distance_m, position_ratio, loc_conf = estimate_leak_distance(segment, up_reading, down_reading)
        plan_xy = interpolate_leak_plan_xy(segment, position_ratio)
        result.update(
            {
                "distance_m_from_upstream": distance_m,
                "segment_length_m": float(segment["length_m"]),
                "position_ratio": position_ratio,
                "localization_confidence": loc_conf,
                "plan_x": plan_xy["x"],
                "plan_y": plan_xy["y"],
                "upstream_meter": segment["upstream_meter"],
                "downstream_meter": segment["downstream_meter"],
            }
        )

    return result


def pending_meter_context_for_zone(zone_id: int, pending_by_meter: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    seg = segment_for_zone(zone_id)
    if not seg:
        return None
    for meter_id in (seg["upstream_meter"], seg["downstream_meter"]):
        ctx = pending_by_meter.get(meter_id)
        if ctx:
            return ctx
    return None


def register_meter_suspicion(meter_id: str, leak_probability: float, timestamp: datetime) -> list[int]:
    """Retourne les zone_id impactees par une suspicion compteur."""
    return [seg["zone_id"] for seg in segments_for_meter(meter_id)]


def build_localization_record(analysis: dict[str, Any], sensor_id: str, timestamp: datetime) -> dict[str, Any]:
    return {
        "timestamp": timestamp.isoformat(),
        "zone_id": analysis["zone_id"],
        "segment_id": analysis["segment_id"],
        "upstream_meter": analysis.get("upstream_meter"),
        "downstream_meter": analysis.get("downstream_meter"),
        "confirmed": bool(analysis.get("confirmed")),
        "confirmation_confidence": analysis.get("confirmation_confidence", 0),
        "distance_m_from_upstream": analysis.get("distance_m_from_upstream"),
        "segment_length_m": analysis.get("segment_length_m"),
        "position_ratio": analysis.get("position_ratio"),
        "localization_confidence": analysis.get("localization_confidence"),
        "plan_x": analysis.get("plan_x"),
        "plan_y": analysis.get("plan_y"),
        "pressure_leak_score": analysis.get("pressure_leak_score"),
        "sensor_correlation": analysis.get("sensor_correlation"),
        "trigger_sensor_id": sensor_id,
        "meter_source": (analysis.get("meter_context") or {}).get("meter_id"),
    }


def localization_alert_message(record: dict[str, Any]) -> str:
    zone_id = record.get("zone_id")
    if not record.get("confirmed"):
        return f"Signal pression zone {zone_id} — confirmation en attente"
    dist = record.get("distance_m_from_upstream")
    length = record.get("segment_length_m")
    up = record.get("upstream_meter", "?")
    return (
        f"Fuite confirmee zone {zone_id} : {dist:.0f} m depuis {up} "
        f"(troncon {length:.0f} m, confiance {record.get('localization_confidence', 0):.0%})"
    )
