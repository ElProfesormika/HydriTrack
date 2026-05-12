from __future__ import annotations

import sqlite3
import threading
from collections import defaultdict
from pathlib import Path
from typing import Any

from .models import Alert, Anomaly, MeterDataIn, PressureDataIn


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._create_tables()

    def _execute_commit(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._lock:
            self._conn.execute(sql, params)
            self._conn.commit()

    def _fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def _fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def _create_tables(self) -> None:
        with self._lock:
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
        self._execute_commit(
            """
            INSERT INTO meter_data(timestamp, meter_id, volume, flow_rate)
            VALUES (?, ?, ?, ?)
            """,
            (item.timestamp.isoformat(), item.meter_id, item.volume, item.flow_rate),
        )

    def insert_pressure_data(self, item: PressureDataIn) -> None:
        self._execute_commit(
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

    def insert_anomaly(self, item: Anomaly) -> None:
        self._execute_commit(
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

    def insert_alert(self, item: Alert) -> None:
        self._execute_commit(
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

    def get_latest_anomalies(self, limit: int) -> list[dict]:
        rows = self._fetchall(
            """
            SELECT timestamp, meter_id, score, leak_probability
            FROM anomalies ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]

    def get_latest_alerts(self, limit: int) -> list[dict]:
        rows = self._fetchall(
            """
            SELECT timestamp, severity, category, source_id, message
            FROM alerts ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]

    def counts(self) -> dict[str, int]:
        meter = self._fetchone("SELECT COUNT(*) AS n FROM meter_data")["n"]
        pressure = self._fetchone("SELECT COUNT(*) AS n FROM pressure_data")["n"]
        anomalies = self._fetchone("SELECT COUNT(*) AS n FROM anomalies")["n"]
        alerts = self._fetchone("SELECT COUNT(*) AS n FROM alerts")["n"]
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
        bm = bucket_minutes
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
                    SUM(CASE WHEN leak_probability < 0.25 THEN 1 ELSE 0 END) AS anom_normal,
                    SUM(
                        CASE
                            WHEN leak_probability >= 0.25 AND leak_probability < 0.5 THEN 1
                            ELSE 0
                        END
                    ) AS anom_caution,
                    SUM(
                        CASE
                            WHEN leak_probability >= 0.5 AND leak_probability < 0.75 THEN 1
                            ELSE 0
                        END
                    ) AS anom_warning,
                    SUM(CASE WHEN leak_probability >= 0.75 THEN 1 ELSE 0 END) AS anom_critical
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
                    SUM(CASE WHEN severity IN ('normal', 'nominal', 'info') THEN 1 ELSE 0 END) AS alert_normal,
                    SUM(CASE WHEN severity = 'caution' THEN 1 ELSE 0 END) AS alert_caution,
                    SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) AS alert_warning,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS alert_critical
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
                COALESCE(a.anom_normal, 0) AS anom_normal,
                COALESCE(a.anom_caution, 0) AS anom_caution,
                COALESCE(a.anom_warning, 0) AS anom_warning,
                COALESCE(a.anom_critical, 0) AS anom_critical,
                (
                    COALESCE(a.anom_normal, 0)
                    + COALESCE(a.anom_caution, 0)
                    + COALESCE(a.anom_warning, 0)
                    + COALESCE(a.anom_critical, 0)
                ) AS anomalies,
                COALESCE(b.alert_normal, 0) AS alert_normal,
                COALESCE(b.alert_caution, 0) AS alert_caution,
                COALESCE(b.alert_warning, 0) AS alert_warning,
                COALESCE(b.alert_critical, 0) AS alert_critical,
                (
                    COALESCE(b.alert_normal, 0)
                    + COALESCE(b.alert_caution, 0)
                    + COALESCE(b.alert_warning, 0)
                    + COALESCE(b.alert_critical, 0)
                ) AS alerts
            FROM all_buckets ab
            LEFT JOIN anomaly_buckets a ON a.bucket = ab.bucket
            LEFT JOIN alert_buckets b ON b.bucket = ab.bucket
            ORDER BY ab.bucket DESC
            LIMIT ?
            """,
            (bm, bm, bm, bm, points),
        ).fetchall()
        data = [dict(row) for row in rows]
        data.reverse()
        return data

    def anomaly_max_leak_by_bucket(self, bucket_minutes: int, points: int) -> list[dict]:
        bm = bucket_minutes
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
                MAX(leak_probability) AS max_leak
            FROM anomalies
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT ?
            """,
            (bm, bm, points),
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
        leaks = self.anomaly_max_leak_by_bucket(bucket_minutes=bucket_minutes, points=points)
        leak_map = {row["bucket"]: float(row["max_leak"] or 0.0) for row in leaks}
        for row in data:
            row["max_leak_probability"] = leak_map.get(row["bucket"], 0.0)
        return data

    def meter_flow_per_meter_series(
        self,
        bucket_minutes: int = 60,
        points: int = 72,
        meter_order: list[str] | None = None,
        limit_meters: int = 12,
    ) -> dict[str, Any]:
        if meter_order:
            meter_ids = list(meter_order)
        else:
            top_rows = self._conn.execute(
                """
                SELECT meter_id
                FROM meter_data
                GROUP BY meter_id
                ORDER BY COUNT(*) DESC
                LIMIT ?
                """,
                (limit_meters,),
            ).fetchall()
            meter_ids = [str(row["meter_id"]) for row in top_rows]
        if not meter_ids:
            return {"buckets": [], "series": []}

        placeholders = ",".join("?" * len(meter_ids))
        sql = f"""
            SELECT
                meter_id,
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
            WHERE meter_id IN ({placeholders})
            GROUP BY meter_id, bucket
            ORDER BY bucket ASC
        """
        params: list[Any] = [bucket_minutes, bucket_minutes, *meter_ids]
        rows = self._conn.execute(sql, params).fetchall()

        by_meter: dict[str, dict[str, float]] = defaultdict(dict)
        all_buckets: set[str] = set()
        for row in rows:
            b = str(row["bucket"])
            all_buckets.add(b)
            by_meter[str(row["meter_id"])][b] = float(row["avg_flow"] or 0)

        sorted_buckets = sorted(all_buckets)
        tail = sorted_buckets[-points:] if len(sorted_buckets) > points else sorted_buckets

        series: list[dict[str, Any]] = []
        for mid in meter_ids:
            pts = [{"bucket": b, "avg_flow": float(by_meter[mid].get(b, 0.0))} for b in tail]
            series.append({"meter_id": mid, "points": pts})

        return {"buckets": tail, "series": series}

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

    def meter_profile(
        self,
        meter_id: str,
        bucket_minutes: int = 30,
        points: int = 48,
        recent_limit: int = 12,
    ) -> dict[str, Any]:
        kpi_row = self._conn.execute(
            """
            SELECT
                COUNT(*) AS total_points,
                COALESCE(AVG(flow_rate), 0.0) AS avg_flow,
                COALESCE(MAX(flow_rate), 0.0) AS max_flow,
                COALESCE(SUM(volume), 0.0) AS total_volume
            FROM meter_data
            WHERE meter_id = ?
            """,
            (meter_id,),
        ).fetchone()
        anomaly_row = self._conn.execute(
            """
            SELECT
                COUNT(*) AS anomaly_points,
                COALESCE(AVG(score), 0.0) AS avg_anomaly_score,
                COALESCE(MAX(score), 0.0) AS max_anomaly_score,
                COALESCE(AVG(leak_probability), 0.0) AS avg_leak_probability,
                COALESCE(MAX(leak_probability), 0.0) AS max_leak_probability
            FROM anomalies
            WHERE meter_id = ?
            """,
            (meter_id,),
        ).fetchone()
        kpis = {**dict(kpi_row), **dict(anomaly_row)}

        flow_rows = self._conn.execute(
            """
            WITH meter_buckets AS (
                SELECT
                    strftime(
                        '%Y-%m-%dT%H:%M:00Z',
                        datetime(
                            (CAST(strftime('%s', timestamp) AS INTEGER) / (? * 60)) * (? * 60),
                            'unixepoch'
                        )
                    ) AS bucket,
                    COALESCE(AVG(flow_rate), 0.0) AS avg_flow,
                    COALESCE(SUM(volume), 0.0) AS total_volume,
                    COUNT(*) AS samples
                FROM meter_data
                WHERE meter_id = ?
                GROUP BY bucket
            ),
            anomaly_buckets AS (
                SELECT
                    strftime(
                        '%Y-%m-%dT%H:%M:00Z',
                        datetime(
                            (CAST(strftime('%s', timestamp) AS INTEGER) / (? * 60)) * (? * 60),
                            'unixepoch'
                        )
                    ) AS bucket,
                    MAX(leak_probability) AS max_leak_probability
                FROM anomalies
                WHERE meter_id = ?
                GROUP BY bucket
            )
            SELECT
                mb.bucket AS bucket,
                mb.avg_flow AS avg_flow,
                mb.total_volume AS total_volume,
                mb.samples AS samples,
                COALESCE(ab.max_leak_probability, 0.0) AS max_leak_probability
            FROM meter_buckets mb
            LEFT JOIN anomaly_buckets ab ON ab.bucket = mb.bucket
            ORDER BY mb.bucket DESC
            LIMIT ?
            """,
            (bucket_minutes, bucket_minutes, meter_id, bucket_minutes, bucket_minutes, meter_id, points),
        ).fetchall()
        flow_series = [dict(row) for row in flow_rows]
        flow_series.reverse()

        risk_rows = self._conn.execute(
            """
            SELECT
                SUM(CASE WHEN leak_probability < 0.25 THEN 1 ELSE 0 END) AS normal,
                SUM(
                    CASE WHEN leak_probability >= 0.25 AND leak_probability < 0.5 THEN 1 ELSE 0 END
                ) AS caution,
                SUM(
                    CASE WHEN leak_probability >= 0.5 AND leak_probability < 0.75 THEN 1 ELSE 0 END
                ) AS warning,
                SUM(CASE WHEN leak_probability >= 0.75 THEN 1 ELSE 0 END) AS critical
            FROM anomalies
            WHERE meter_id = ?
            """,
            (meter_id,),
        ).fetchone()
        risk_distribution = dict(risk_rows)

        anomaly_items = self._conn.execute(
            """
            SELECT timestamp, meter_id, score, leak_probability
            FROM anomalies
            WHERE meter_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (meter_id, recent_limit),
        ).fetchall()
        alert_items = self._conn.execute(
            """
            SELECT timestamp, severity, category, source_id, message
            FROM alerts
            WHERE source_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (meter_id, recent_limit),
        ).fetchall()

        return {
            "meter_id": meter_id,
            "kpis": kpis,
            "flow_series": flow_series,
            "risk_distribution": risk_distribution,
            "recent_anomalies": [dict(row) for row in anomaly_items],
            "recent_alerts": [dict(row) for row in alert_items],
            "classification_model": "IsolationForest(n=300)+seuils quantiles decision (HydroTrack IA)",
            "classification_scope": "Applique a chaque compteur individuellement",
        }

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

    def sensors_catalog(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT
                sensor_id,
                zone,
                COUNT(*) AS points,
                MAX(timestamp) AS last_seen
            FROM pressure_data
            GROUP BY sensor_id, zone
            ORDER BY sensor_id ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
