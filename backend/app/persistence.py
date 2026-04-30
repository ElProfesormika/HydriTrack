from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .models import Alert, Anomaly, MeterDataIn, PressureDataIn


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meter_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                volume REAL NOT NULL,
                flow_rate REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pressure_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                zone TEXT NOT NULL,
                pressure_signal REAL NOT NULL,
                frequency REAL NOT NULL,
                intensity REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                score REAL NOT NULL,
                leak_probability REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                source_id TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def insert_meter_data(self, item: MeterDataIn) -> None:
        self._conn.execute(
            """
            INSERT INTO meter_data(timestamp, meter_id, volume, flow_rate)
            VALUES (?, ?, ?, ?)
            """,
            (item.timestamp.isoformat(), item.meter_id, item.volume, item.flow_rate),
        )
        self._conn.commit()

    def insert_pressure_data(self, item: PressureDataIn) -> None:
        self._conn.execute(
            """
            INSERT INTO pressure_data(
                timestamp, sensor_id, zone, pressure_signal, frequency, intensity
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item.timestamp.isoformat(),
                item.sensor_id,
                item.zone,
                item.pressure_signal,
                item.frequency,
                item.intensity,
            ),
        )
        self._conn.commit()

    def insert_anomaly(self, item: Anomaly) -> None:
        self._conn.execute(
            """
            INSERT INTO anomalies(timestamp, meter_id, score, leak_probability)
            VALUES (?, ?, ?, ?)
            """,
            (
                item.timestamp.isoformat(),
                item.meter_id,
                item.score,
                item.leak_probability,
            ),
        )
        self._conn.commit()

    def insert_alert(self, item: Alert) -> None:
        self._conn.execute(
            """
            INSERT INTO alerts(timestamp, severity, category, source_id, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item.timestamp.isoformat(),
                item.severity,
                item.category,
                item.source_id,
                item.message,
            ),
        )
        self._conn.commit()

    def get_latest_anomalies(self, limit: int) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT timestamp, meter_id, score, leak_probability
            FROM anomalies ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_latest_alerts(self, limit: int) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT timestamp, severity, category, source_id, message
            FROM alerts ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def counts(self) -> dict[str, int]:
        meter = self._conn.execute("SELECT COUNT(*) AS n FROM meter_data").fetchone()["n"]
        pressure = self._conn.execute("SELECT COUNT(*) AS n FROM pressure_data").fetchone()["n"]
        anomalies = self._conn.execute("SELECT COUNT(*) AS n FROM anomalies").fetchone()["n"]
        alerts = self._conn.execute("SELECT COUNT(*) AS n FROM alerts").fetchone()["n"]
        return {
            "meter_data": int(meter),
            "pressure_data": int(pressure),
            "anomalies": int(anomalies),
            "alerts": int(alerts),
        }

    def meter_kpis(self) -> dict[str, Any]:
        row = self._conn.execute(
            """
            SELECT
                COUNT(*) AS total_points,
                COUNT(DISTINCT meter_id) AS distinct_meters,
                COALESCE(AVG(flow_rate), 0.0) AS avg_flow,
                COALESCE(MAX(flow_rate), 0.0) AS max_flow,
                COALESCE(SUM(volume), 0.0) AS total_volume
            FROM meter_data
            """
        ).fetchone()
        return dict(row)

    def sensor_kpis(self) -> dict[str, Any]:
        row = self._conn.execute(
            """
            SELECT
                COUNT(*) AS total_points,
                COUNT(DISTINCT sensor_id) AS distinct_sensors,
                COUNT(DISTINCT zone) AS distinct_zones,
                COALESCE(AVG(intensity), 0.0) AS avg_intensity,
                COALESCE(MAX(intensity), 0.0) AS max_intensity
            FROM pressure_data
            """
        ).fetchone()
        return dict(row)

    def top_anomalous_meters(self, limit: int = 6) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT meter_id, COUNT(*) AS anomaly_count, AVG(score) AS avg_score
            FROM anomalies
            GROUP BY meter_id
            ORDER BY anomaly_count DESC, avg_score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def top_alert_sources(self, limit: int = 6) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT source_id, COUNT(*) AS alert_count
            FROM alerts
            GROUP BY source_id
            ORDER BY alert_count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def timeseries(self, bucket_minutes: int = 30, points: int = 24) -> list[dict]:
        rows = self._conn.execute(
            """
            WITH anomaly_buckets AS (
                SELECT
                    strftime(
                        '%Y-%m-%dT%H:%M:00Z',
                        datetime(
                            (CAST(strftime('%s', timestamp) AS INTEGER) / (? * 60)) * (? * 60),
                            'unixepoch'
                        )
                    ) AS bucket,
                    COUNT(*) AS anomalies
                FROM anomalies
                GROUP BY bucket
            ),
            alert_buckets AS (
                SELECT
                    strftime(
                        '%Y-%m-%dT%H:%M:00Z',
                        datetime(
                            (CAST(strftime('%s', timestamp) AS INTEGER) / (? * 60)) * (? * 60),
                            'unixepoch'
                        )
                    ) AS bucket,
                    COUNT(*) AS alerts
                FROM alerts
                GROUP BY bucket
            ),
            all_buckets AS (
                SELECT bucket FROM anomaly_buckets
                UNION
                SELECT bucket FROM alert_buckets
            )
            SELECT
                ab.bucket AS bucket,
                COALESCE(a.anomalies, 0) AS anomalies,
                COALESCE(b.alerts, 0) AS alerts
            FROM all_buckets ab
            LEFT JOIN anomaly_buckets a ON a.bucket = ab.bucket
            LEFT JOIN alert_buckets b ON b.bucket = ab.bucket
            ORDER BY ab.bucket DESC
            LIMIT ?
            """,
            (bucket_minutes, bucket_minutes, bucket_minutes, bucket_minutes, points),
        ).fetchall()
        data = [dict(row) for row in rows]
        data.reverse()
        return data

    def meter_flow_timeseries(self, bucket_minutes: int = 60, points: int = 24) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT
                strftime(
                    '%Y-%m-%dT%H:%M:00Z',
                    datetime(
                        (CAST(strftime('%s', timestamp) AS INTEGER) / (? * 60)) * (? * 60),
                        'unixepoch'
                    )
                ) AS bucket,
                COALESCE(AVG(flow_rate), 0.0) AS avg_flow,
                COUNT(*) AS samples
            FROM meter_data
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT ?
            """,
            (bucket_minutes, bucket_minutes, points),
        ).fetchall()
        data = [dict(row) for row in rows]
        data.reverse()
        return data

    def pressure_intensity_timeseries(self, bucket_minutes: int = 60, points: int = 24) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT
                strftime(
                    '%Y-%m-%dT%H:%M:00Z',
                    datetime(
                        (CAST(strftime('%s', timestamp) AS INTEGER) / (? * 60)) * (? * 60),
                        'unixepoch'
                    )
                ) AS bucket,
                COALESCE(AVG(intensity), 0.0) AS avg_intensity,
                COALESCE(AVG(frequency), 0.0) AS avg_frequency,
                COUNT(*) AS samples
            FROM pressure_data
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT ?
            """,
            (bucket_minutes, bucket_minutes, points),
        ).fetchall()
        data = [dict(row) for row in rows]
        data.reverse()
        return data

    def alert_stats(self) -> dict[str, Any]:
        by_severity = self._conn.execute(
            """
            SELECT severity, COUNT(*) AS count
            FROM alerts
            GROUP BY severity
            """
        ).fetchall()
        by_category = self._conn.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM alerts
            GROUP BY category
            """
        ).fetchall()
        total = self._conn.execute("SELECT COUNT(*) AS n FROM alerts").fetchone()["n"]
        last_24h = self._conn.execute(
            """
            SELECT COUNT(*) AS n FROM alerts
            WHERE datetime(timestamp) >= datetime('now', '-1 day')
            """
        ).fetchone()["n"]
        return {
            "total": int(total),
            "last_24h": int(last_24h),
            "by_severity": [dict(row) for row in by_severity],
            "by_category": [dict(row) for row in by_category],
        }
