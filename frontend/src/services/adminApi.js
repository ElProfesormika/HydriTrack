const API_BASE = "http://localhost:8000";
const KEY_STORAGE = "hydrotrack_admin_key";

export function getAdminKey() {
  return sessionStorage.getItem(KEY_STORAGE) || "";
}

export function setAdminKey(key) {
  sessionStorage.setItem(KEY_STORAGE, String(key || "").trim());
}

export function clearAdminKey() {
  sessionStorage.removeItem(KEY_STORAGE);
}

async function adminRequest(path, options = {}) {
  const key = getAdminKey();
  const headers = {
    "Content-Type": "application/json",
    "X-Admin-Key": key,
    ...(options.headers || {}),
  };
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    clearAdminKey();
    throw new Error("Session admin expiree — reconnectez-vous");
  }
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Erreur ${response.status}: ${text || path}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const adminApi = {
  login: async (username, password) => {
    const response = await fetch(`${API_BASE}/api/admin/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Identifiant ou mot de passe incorrect");
    }
    const data = await response.json();
    setAdminKey(data.token);
    return data;
  },

  getOverview: () => adminRequest("/api/admin/overview"),
  getAudit: (limit = 30) => adminRequest(`/api/admin/audit?limit=${limit}`),
  reloadRegistry: () => adminRequest("/api/admin/registry/reload", { method: "POST" }),
  syncLeaks: () => adminRequest("/api/admin/leaks/sync-from-localizations", { method: "POST" }),

  listMeters: (includeInactive = true) =>
    adminRequest(`/api/admin/meters?include_inactive=${includeInactive}`),
  createMeter: (body) => adminRequest("/api/admin/meters", { method: "POST", body: JSON.stringify(body) }),
  updateMeter: (id, body) =>
    adminRequest(`/api/admin/meters/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteMeter: (id, hard = false) =>
    adminRequest(`/api/admin/meters/${encodeURIComponent(id)}?hard=${hard}`, { method: "DELETE" }),

  listZones: (includeInactive = true) =>
    adminRequest(`/api/admin/zones?include_inactive=${includeInactive}`),
  createZone: (body) => adminRequest("/api/admin/zones", { method: "POST", body: JSON.stringify(body) }),
  updateZone: (id, body) =>
    adminRequest(`/api/admin/zones/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteZone: (id, hard = false) =>
    adminRequest(`/api/admin/zones/${id}?hard=${hard}`, { method: "DELETE" }),

  listSensors: (includeInactive = true) =>
    adminRequest(`/api/admin/sensors?include_inactive=${includeInactive}`),
  createSensor: (body) => adminRequest("/api/admin/sensors", { method: "POST", body: JSON.stringify(body) }),
  updateSensor: (id, body) =>
    adminRequest(`/api/admin/sensors/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteSensor: (id, hard = false) =>
    adminRequest(`/api/admin/sensors/${encodeURIComponent(id)}?hard=${hard}`, { method: "DELETE" }),

  listSegments: () => adminRequest("/api/admin/segments"),
  updateSegment: (id, body) =>
    adminRequest(`/api/admin/segments/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(body) }),

  listAlerts: (limit = 100, status) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.set("status", status);
    return adminRequest(`/api/admin/alerts?${params}`);
  },
  updateAlert: (id, body) =>
    adminRequest(`/api/admin/alerts/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteAlert: (id) => adminRequest(`/api/admin/alerts/${id}`, { method: "DELETE" }),

  listLeaks: (limit = 50, status) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.set("status", status);
    return adminRequest(`/api/admin/leaks?${params}`);
  },
  updateLeak: (id, body) =>
    adminRequest(`/api/admin/leaks/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteLeak: (id) => adminRequest(`/api/admin/leaks/${id}`, { method: "DELETE" }),
};
