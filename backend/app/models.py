from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MeterDataIn(BaseModel):
    timestamp: datetime
    meter_id: str = Field(min_length=1)
    volume: float = Field(ge=0)
    flow_rate: float = Field(ge=0)


class PressureDataIn(BaseModel):
    timestamp: datetime
    sensor_id: str = Field(min_length=1)
    zone: str = Field(min_length=1)
    pressure_signal: float
    frequency: float = Field(ge=0)
    intensity: float = Field(ge=0)


class Alert(BaseModel):
    timestamp: datetime
    severity: Literal["info", "warning", "critical"]
    category: Literal["anomaly", "leak_suspected", "leak_confirmed"]
    source_id: str
    message: str


class Anomaly(BaseModel):
    timestamp: datetime
    meter_id: str
    score: float
    leak_probability: float


class NetworkState(BaseModel):
    timestamp: datetime
    active_alerts: int
    latest_anomalies: int
    ingested_meter_points: int
    ingested_pressure_points: int
