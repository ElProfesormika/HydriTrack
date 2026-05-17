import { useCallback, useEffect, useState } from "react";
import { adminApi } from "../../services/adminApi";

export function AdminDashboardPage() {
  const [overview, setOverview] = useState(null);
  const [audit, setAudit] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [ov, au] = await Promise.all([adminApi.getOverview(), adminApi.getAudit(15)]);
      setOverview(ov);
      setAudit(au.items || []);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runAction(fn) {
    setBusy(true);
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-page-header">
        <div>
          <h2>Vue d&apos;ensemble</h2>
          <p>Gestion globale du reseau HydroTrack — registre, telemetrie et incidents.</p>
        </div>
        <div className="admin-actions-row">
          <button type="button" className="btn-secondary" disabled={busy} onClick={() => runAction(adminApi.reloadRegistry)}>
            Recharger registre
          </button>
          <button type="button" className="btn-secondary" disabled={busy} onClick={() => runAction(adminApi.syncLeaks)}>
            Sync fuites
          </button>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}

      {overview ? (
        <section className="admin-kpi-grid">
          <article className="admin-kpi card">
            <span>Compteurs actifs</span>
            <strong>{overview.meters}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Zones</span>
            <strong>{overview.zones}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Capteurs</span>
            <strong>{overview.sensors}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Troncons</span>
            <strong>{overview.segments}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Alertes actives</span>
            <strong>{overview.active_alerts}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Fuites ouvertes</span>
            <strong>{overview.open_leaks}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Fuites reparees</span>
            <strong>{overview.repaired_leaks}</strong>
          </article>
          <article className="admin-kpi card">
            <span>Points telemetrie</span>
            <strong>{overview.telemetry?.meter_data || 0}</strong>
            <small>compteurs / {overview.telemetry?.pressure_data || 0} pression</small>
          </article>
        </section>
      ) : null}

      <section className="card">
        <h3>Journal d&apos;audit (dernieres actions)</h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Action</th>
                <th>Type</th>
                <th>ID</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {audit.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.timestamp).toLocaleString("fr-FR")}</td>
                  <td>{row.action}</td>
                  <td>{row.entity_type}</td>
                  <td>{row.entity_id}</td>
                  <td>{row.details || "—"}</td>
                </tr>
              ))}
              {!audit.length ? (
                <tr>
                  <td colSpan={5}>Aucune action enregistree.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
