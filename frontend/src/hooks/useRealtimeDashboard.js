import { useEffect, useMemo, useState } from "react";
import { hydroApi } from "../services/api";

const WS_URL = "ws://localhost:8000/ws/events";

export function useRealtimeDashboard() {
  const [data, setData] = useState({
    overview: null,
    timeseries: [],
    meterFlowSeries: [],
    pressureSeries: [],
    alertStats: null,
    alerts: [],
    anomalies: [],
    mapZones: [],
    mapAlerts: [],
    mapMeters: [],
  });
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState("");

  async function loadAll() {
    try {
      const [
        overview,
        series,
        meterFlow,
        pressure,
        alertStats,
        alerts,
        anomalies,
        zones,
        mapAlerts,
        meters,
      ] = await Promise.all([
        hydroApi.getOverview(),
        hydroApi.getTimeSeries(),
        hydroApi.getMeterFlowSeries(),
        hydroApi.getPressureSeries(),
        hydroApi.getAlertStats(),
        hydroApi.getAlerts(),
        hydroApi.getAnomalies(),
        hydroApi.getMapZones(),
        hydroApi.getMapAlerts(),
        hydroApi.getMapMeters(),
      ]);
      setData({
        overview,
        timeseries: series.items || [],
        meterFlowSeries: meterFlow.items || [],
        pressureSeries: pressure.items || [],
        alertStats,
        alerts: alerts.items || [],
        anomalies: anomalies.items || [],
        mapZones: zones.items || [],
        mapAlerts: mapAlerts.items || [],
        mapMeters: meters.items || [],
      });
      setError("");
    } catch (err) {
      setError(err.message || "Echec de chargement");
    }
  }

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        setIsConnected(true);
        ws.send("subscribe");
      };
      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimer = setTimeout(connect, 2200);
      };
      ws.onerror = () => setIsConnected(false);
      ws.onmessage = () => loadAll();
    };

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  return useMemo(() => ({ ...data, isConnected, error }), [data, isConnected, error]);
}
