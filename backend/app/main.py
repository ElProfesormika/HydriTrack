import math
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .models import Alert, MeterDataIn, PressureDataIn
from .services import InMemoryStore

app = FastAPI(title="HydroTrack API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
store = InMemoryStore()
ws_clients: list[WebSocket] = []

NETWORK_ZONES = [
    {"id": 1, "name": "Zone 1 - CRT", "lat": 48.496, "lng": 3.503},
    {"id": 2, "name": "Zone 2 - Entreprise", "lat": 48.498, "lng": 3.508},
    {"id": 3, "name": "Zone 3 - AIE", "lat": 48.499, "lng": 3.513},
    {"id": 4, "name": "Zone 4 - Aire TFA / Vigilia", "lat": 48.501, "lng": 3.517},
    {"id": 5, "name": "Zone 5 - IPE", "lat": 48.502, "lng": 3.522},
    {"id": 6, "name": "Zone 6 - TR 3 / TR 4", "lat": 48.504, "lng": 3.526},
    {"id": 7, "name": "Zone 7 - TR 2", "lat": 48.505, "lng": 3.531},
    {"id": 8, "name": "Zone 8 - TR 1", "lat": 48.507, "lng": 3.536},
    {"id": 9, "name": "Zone 9 - Refrigerants", "lat": 48.509, "lng": 3.541},
    {"id": 10, "name": "Zone 10 - BTE", "lat": 48.510, "lng": 3.546},
    {"id": 11, "name": "Zone 11 - SUT / PAP", "lat": 48.512, "lng": 3.551},
    {"id": 12, "name": "Zone 12 - MIF / Restaurant", "lat": 48.514, "lng": 3.556},
    {"id": 13, "name": "Zone 13 - Accueil / Parking / Simulateur / CIP", "lat": 48.516, "lng": 3.561},
]

_METER_NAMES = [
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
]
_BASE_LAT = 48.505
_BASE_LNG = 3.53
NETWORK_METERS = [
    {
        "id": idx + 1,
        "meter_id": name,
        "name": name.replace("_", " "),
        "lat": _BASE_LAT + 0.009 * math.sin(2 * math.pi * idx / len(_METER_NAMES)),
        "lng": _BASE_LNG + 0.014 * math.cos(2 * math.pi * idx / len(_METER_NAMES)),
    }
    for idx, name in enumerate(_METER_NAMES)
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/meters/data")
async def ingest_meter_data(payload: MeterDataIn) -> dict:
    result = store.ingest_meter(payload)
    await _broadcast(
        {
            "type": "meter_data",
            "timestamp": payload.timestamp.isoformat(),
            "meter_id": payload.meter_id,
            "result": result,
        }
    )
    return {"status": "accepted", "result": result}


@app.post("/api/sensors/pressure")
async def ingest_pressure_data(payload: PressureDataIn) -> dict:
    result = store.ingest_pressure(payload)
    await _broadcast(
        {
            "type": "pressure_data",
            "timestamp": payload.timestamp.isoformat(),
            "sensor_id": payload.sensor_id,
            "zone": payload.zone,
        }
    )
    return {"status": "accepted", "result": result}


@app.get("/api/anomalies")
def get_anomalies(limit: int = 50) -> dict:
    items = store.get_anomalies(limit=limit)
    return {"count": len(items), "items": items}


@app.get("/api/alerts")
def get_alerts(limit: int = 50) -> dict:
    items = store.get_alerts(limit=limit)
    return {"count": len(items), "items": items}


@app.get("/api/network/state")
def get_network_state() -> dict:
    state = store.get_network_state()
    return state.model_dump()


@app.get("/api/dashboard/overview")
def get_dashboard_overview() -> dict:
    return store.get_dashboard_overview()


@app.get("/api/dashboard/timeseries")
def get_dashboard_timeseries(bucket_minutes: int = 30, points: int = 24) -> dict:
    items = store.get_timeseries(bucket_minutes=bucket_minutes, points=points)
    return {"count": len(items), "items": items}


@app.get("/api/dashboard/meter-flow-series")
def get_meter_flow_series(bucket_minutes: int = 60, points: int = 24) -> dict:
    items = store.get_meter_flow_timeseries(bucket_minutes=bucket_minutes, points=points)
    return {"count": len(items), "items": items}


@app.get("/api/dashboard/pressure-series")
def get_pressure_series(bucket_minutes: int = 60, points: int = 24) -> dict:
    items = store.get_pressure_timeseries(bucket_minutes=bucket_minutes, points=points)
    return {"count": len(items), "items": items}


@app.get("/api/dashboard/alert-stats")
def get_alert_stats() -> dict:
    return store.get_alert_stats()


@app.get("/api/map/zones")
def get_map_zones() -> dict:
    return {"count": len(NETWORK_ZONES), "items": NETWORK_ZONES}


@app.get("/api/map/alerts")
def get_map_alerts(limit: int = 50) -> dict:
    alerts = store.get_alerts(limit=limit)
    leak_items = [item for item in alerts if "leak" in item.get("category", "")]
    items = []
    for idx, item in enumerate(leak_items):
        zone = NETWORK_ZONES[idx % len(NETWORK_ZONES)]
        items.append(
            {
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "lat": zone["lat"] + idx * 0.0006,
                "lng": zone["lng"] + idx * 0.0004,
                "severity": item.get("severity", "warning"),
                "message": item.get("message", ""),
                "timestamp": item.get("timestamp"),
            }
        )
    return {"count": len(items), "items": items}


@app.get("/api/map/meters")
def get_map_meters() -> dict:
    return {"count": len(NETWORK_METERS), "items": NETWORK_METERS}


@app.post("/api/alerts/test")
async def create_test_alert() -> dict:
    alert = Alert(
        timestamp=datetime.now(timezone.utc),
        severity="info",
        category="anomaly",
        source_id="SYSTEM",
        message="Alerte de test HydroTrack",
    )
    store.add_alert(alert)
    await _broadcast({"type": "alert", "payload": alert.model_dump(mode="json")})
    return {"status": "created"}


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients.remove(websocket)


async def _broadcast(payload: dict) -> None:
    disconnected: list[WebSocket] = []
    for client in ws_clients:
        try:
            await client.send_json(payload)
        except RuntimeError:
            disconnected.append(client)
    for client in disconnected:
        if client in ws_clients:
            ws_clients.remove(client)
