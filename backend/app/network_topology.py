"""Topologie reseau : compteurs (troncons) + zones capteurs pression entre compteurs."""

from __future__ import annotations

from typing import Any

# 13 zones spec HydroTrack (capteurs entre troncons de compteurs)
NETWORK_ZONES: list[dict[str, Any]] = [
    {"id": 1, "name": "Zone 1 - CRT", "short_name": "CRT", "lat": 48.496, "lng": 3.503},
    {"id": 2, "name": "Zone 2 - Entreprise", "short_name": "Entreprise", "lat": 48.498, "lng": 3.508},
    {"id": 3, "name": "Zone 3 - AIE", "short_name": "AIE", "lat": 48.499, "lng": 3.513},
    {"id": 4, "name": "Zone 4 - Aire TFA / Vigilia", "short_name": "TFA / Vigilia", "lat": 48.501, "lng": 3.517},
    {"id": 5, "name": "Zone 5 - IPE", "short_name": "IPE", "lat": 48.502, "lng": 3.522},
    {"id": 6, "name": "Zone 6 - TR 3 / TR 4", "short_name": "TR 3/4", "lat": 48.504, "lng": 3.526},
    {"id": 7, "name": "Zone 7 - TR 2", "short_name": "TR 2", "lat": 48.505, "lng": 3.531},
    {"id": 8, "name": "Zone 8 - TR 1", "short_name": "TR 1", "lat": 48.507, "lng": 3.536},
    {"id": 9, "name": "Zone 9 - Refrigerants", "short_name": "Refrigerants", "lat": 48.509, "lng": 3.541},
    {"id": 10, "name": "Zone 10 - BTE", "short_name": "BTE", "lat": 48.510, "lng": 3.546},
    {"id": 11, "name": "Zone 11 - SUT / PAP", "short_name": "SUT / PAP", "lat": 48.512, "lng": 3.551},
    {"id": 12, "name": "Zone 12 - MIF / Restaurant", "short_name": "MIF", "lat": 48.514, "lng": 3.556},
    {"id": 13, "name": "Zone 13 - Accueil / Parking / Simulateur / CIP", "short_name": "Accueil", "lat": 48.516, "lng": 3.561},
]

# 2 capteurs pression par zone (extremites du troncon surveille)
def _sensors_for_zone(zone_id: int) -> list[str]:
    return [f"S_Z{zone_id:02d}_A", f"S_Z{zone_id:02d}_B"]


NETWORK_SEGMENTS: list[dict[str, Any]] = [
    {
        "id": "seg_z01",
        "zone_id": 1,
        "upstream_meter": "AVOGADRO",
        "downstream_meter": "BCA1",
        "length_m": 380.0,
        "sensor_ids": _sensors_for_zone(1),
    },
    {
        "id": "seg_z02",
        "zone_id": 2,
        "upstream_meter": "BCA1",
        "downstream_meter": "BCA2",
        "length_m": 210.0,
        "sensor_ids": _sensors_for_zone(2),
    },
    {
        "id": "seg_z03",
        "zone_id": 3,
        "upstream_meter": "BCA2",
        "downstream_meter": "JOLIOT_CURIE_1",
        "length_m": 340.0,
        "sensor_ids": _sensors_for_zone(3),
    },
    {
        "id": "seg_z04",
        "zone_id": 4,
        "upstream_meter": "JOLIOT_CURIE_1",
        "downstream_meter": "JOLIOT_CURIE_2",
        "length_m": 95.0,
        "sensor_ids": _sensors_for_zone(4),
    },
    {
        "id": "seg_z05",
        "zone_id": 5,
        "upstream_meter": "JOLIOT_CURIE_2",
        "downstream_meter": "FARADAY",
        "length_m": 280.0,
        "sensor_ids": _sensors_for_zone(5),
    },
    {
        "id": "seg_z06",
        "zone_id": 6,
        "upstream_meter": "FARADAY",
        "downstream_meter": "AMPERE_1",
        "length_m": 320.0,
        "sensor_ids": _sensors_for_zone(6),
    },
    {
        "id": "seg_z07",
        "zone_id": 7,
        "upstream_meter": "AMPERE_1",
        "downstream_meter": "AMPERE_2",
        "length_m": 120.0,
        "sensor_ids": _sensors_for_zone(7),
    },
    {
        "id": "seg_z08",
        "zone_id": 8,
        "upstream_meter": "AMPERE_2",
        "downstream_meter": "EINSTEIN",
        "length_m": 290.0,
        "sensor_ids": _sensors_for_zone(8),
    },
    {
        "id": "seg_z09",
        "zone_id": 9,
        "upstream_meter": "EINSTEIN",
        "downstream_meter": "CHARPAK",
        "length_m": 260.0,
        "sensor_ids": _sensors_for_zone(9),
    },
    {
        "id": "seg_z10",
        "zone_id": 10,
        "upstream_meter": "CHARPAK",
        "downstream_meter": "FRANKLIN",
        "length_m": 240.0,
        "sensor_ids": _sensors_for_zone(10),
    },
    {
        "id": "seg_z11",
        "zone_id": 11,
        "upstream_meter": "FRANKLIN",
        "downstream_meter": "PAP",
        "length_m": 410.0,
        "sensor_ids": _sensors_for_zone(11),
    },
    {
        "id": "seg_z12",
        "zone_id": 12,
        "upstream_meter": "PAP",
        "downstream_meter": "VOLTA",
        "length_m": 350.0,
        "sensor_ids": _sensors_for_zone(12),
    },
    {
        "id": "seg_z13",
        "zone_id": 13,
        "upstream_meter": "SIMULATEUR",
        "downstream_meter": "CCAS",
        "length_m": 300.0,
        "sensor_ids": _sensors_for_zone(13),
    },
]

ZONE_BY_ID = {z["id"]: z for z in NETWORK_ZONES}
SEGMENT_BY_ID = {s["id"]: s for s in NETWORK_SEGMENTS}
SEGMENTS_BY_ZONE = {z["id"]: next(s for s in NETWORK_SEGMENTS if s["zone_id"] == z["id"]) for z in NETWORK_ZONES}
SEGMENTS_BY_METER: dict[str, list[dict[str, Any]]] = {}
for _seg in NETWORK_SEGMENTS:
    for _meter in (_seg["upstream_meter"], _seg["downstream_meter"]):
        SEGMENTS_BY_METER.setdefault(_meter, []).append(_seg)

SENSOR_TO_ZONE: dict[str, int] = {}
SENSOR_TO_SEGMENT: dict[str, str] = {}
for _seg in NETWORK_SEGMENTS:
    for _sid in _seg["sensor_ids"]:
        SENSOR_TO_ZONE[_sid] = _seg["zone_id"]
        SENSOR_TO_SEGMENT[_sid] = _seg["id"]

# Coordonnees plan (pixels) alignees sur sitePlanCoordinates.js
METER_PLAN_XY: dict[str, dict[str, float]] = {
    "AMPERE_1": {"x": 620, "y": 460},
    "AMPERE_2": {"x": 640, "y": 500},
    "BCA1": {"x": 390, "y": 470},
    "BCA2": {"x": 410, "y": 500},
    "BECQUEREL": {"x": 350, "y": 530},
    "CCAS": {"x": 300, "y": 690},
    "CHARPAK": {"x": 720, "y": 500},
    "EINSTEIN": {"x": 680, "y": 445},
    "SIMULATEUR": {"x": 265, "y": 725},
    "FARADAY": {"x": 560, "y": 470},
    "FRANKLIN": {"x": 740, "y": 420},
    "JOLIOT_CURIE_1": {"x": 485, "y": 445},
    "JOLIOT_CURIE_2": {"x": 515, "y": 445},
    "NEWTON": {"x": 800, "y": 530},
    "PAP": {"x": 700, "y": 620},
    "VOLTA": {"x": 770, "y": 675},
    "AVOGADRO": {"x": 230, "y": 520},
    "EDISON": {"x": 210, "y": 650},
    "COULOMB1": {"x": 450, "y": 690},
    "COULOMB2": {"x": 530, "y": 690},
    "TREMPLIN": {"x": 620, "y": 690},
    "SALLE_MUSCULATION": {"x": 340, "y": 700},
}

ZONE_PLAN_XY: dict[int, dict[str, float]] = {
    1: {"x": 240, "y": 400},
    2: {"x": 300, "y": 430},
    3: {"x": 360, "y": 450},
    4: {"x": 430, "y": 455},
    5: {"x": 500, "y": 455},
    6: {"x": 565, "y": 455},
    7: {"x": 460, "y": 560},
    8: {"x": 555, "y": 560},
    9: {"x": 650, "y": 485},
    10: {"x": 705, "y": 455},
    11: {"x": 760, "y": 430},
    12: {"x": 640, "y": 640},
    13: {"x": 280, "y": 700},
}


def resolve_zone_id(zone_label: str) -> int | None:
    raw = (zone_label or "").strip().lower()
    if not raw:
        return None
    for zone in NETWORK_ZONES:
        zid = zone["id"]
        if raw in {str(zid), f"zone {zid}", f"zone{zid}"}:
            return zid
        if raw in zone["name"].lower() or raw in zone["short_name"].lower():
            return zid
    return None


def segment_for_zone(zone_id: int) -> dict[str, Any] | None:
    return SEGMENTS_BY_ZONE.get(zone_id)


def segments_for_meter(meter_id: str) -> list[dict[str, Any]]:
    return SEGMENTS_BY_METER.get(meter_id, [])


def interpolate_leak_plan_xy(segment: dict[str, Any], position_ratio: float) -> dict[str, float]:
    up = METER_PLAN_XY.get(segment["upstream_meter"], ZONE_PLAN_XY.get(segment["zone_id"], {"x": 500, "y": 500}))
    down = METER_PLAN_XY.get(segment["downstream_meter"], ZONE_PLAN_XY.get(segment["zone_id"], {"x": 500, "y": 500}))
    t = max(0.0, min(1.0, position_ratio))
    return {
        "x": up["x"] + (down["x"] - up["x"]) * t,
        "y": up["y"] + (down["y"] - up["y"]) * t,
    }


def network_topology_export() -> dict[str, Any]:
    zones = []
    for zone in NETWORK_ZONES:
        seg = SEGMENTS_BY_ZONE[zone["id"]]
        plan = ZONE_PLAN_XY.get(zone["id"], {"x": 500, "y": 500})
        zones.append(
            {
                **zone,
                "plan_x": plan["x"],
                "plan_y": plan["y"],
                "segment": {
                    "id": seg["id"],
                    "upstream_meter": seg["upstream_meter"],
                    "downstream_meter": seg["downstream_meter"],
                    "length_m": seg["length_m"],
                    "sensor_ids": seg["sensor_ids"],
                },
            }
        )
    return {
        "zones": zones,
        "segments": NETWORK_SEGMENTS,
        "sensor_count": sum(len(s["sensor_ids"]) for s in NETWORK_SEGMENTS),
    }
