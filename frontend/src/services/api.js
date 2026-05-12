const API_BASE = "http://localhost:8000";

async function request(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Erreur API ${response.status} sur ${path}`);
  }
  return response.json();
}

async function requestPost(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Erreur API ${response.status} sur ${path} ${text}`.trim());
  }
  return response.json();
}

export const hydroApi = {
  getOverview: () => request("/api/dashboard/overview"),
  getTimeSeries: (bucketMinutes = 30, points = 24) =>
    request(`/api/dashboard/timeseries?bucket_minutes=${bucketMinutes}&points=${points}`),
  getMeterFlowSeries: (bucketMinutes = 60, points = 24) =>
    request(`/api/dashboard/meter-flow-series?bucket_minutes=${bucketMinutes}&points=${points}`),
  getMeterFlowPerMeter: (bucketMinutes = 60, points = 72) =>
    request(`/api/dashboard/meter-flow-per-meter?bucket_minutes=${bucketMinutes}&points=${points}`),
  getMeterProfile: (meterId, bucketMinutes = 30, points = 48, recentLimit = 12) =>
    request(
      `/api/dashboard/meter-profile/${encodeURIComponent(
        meterId
      )}?bucket_minutes=${bucketMinutes}&points=${points}&recent_limit=${recentLimit}`
    ),
  postMeterData: (payload) => requestPost("/api/meters/data", payload),
  getPressureSeries: (bucketMinutes = 60, points = 24) =>
    request(`/api/dashboard/pressure-series?bucket_minutes=${bucketMinutes}&points=${points}`),
  getAlertStats: () => request("/api/dashboard/alert-stats"),
  getSensorsCatalog: () => request("/api/dashboard/sensors-catalog"),
  getAlerts: (limit = 15) => request(`/api/alerts?limit=${limit}`),
  getAnomalies: (limit = 15) => request(`/api/anomalies?limit=${limit}`),
  getMapZones: () => request("/api/map/zones"),
  getMapAlerts: (limit = 40) => request(`/api/map/alerts?limit=${limit}`),
  getMapMeters: () => request("/api/map/meters"),
};
