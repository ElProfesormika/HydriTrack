import { useCallback, useEffect, useState } from "react";
import { adminApi } from "../../services/adminApi";

const STATUSES = ["open", "confirmed", "repaired", "false_positive", "dismissed"];

export function AdminLeaksPage() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [notesEdit, setNotesEdit] = useState({});

  const load = useCallback(async () => {
    const res = await adminApi.listLeaks(80, filter || undefined);
    setItems(res.items || []);
  }, [filter]);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  async function markRepaired(id) {
    const notes = notesEdit[id] || "Fuite reparee — intervention terrain terminee";
    try {
      await adminApi.updateLeak(id, { status: "repaired", admin_notes: notes });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function setStatus(id, status) {
    try {
      await adminApi.updateLeak(id, { status, admin_notes: notesEdit[id] || "" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(id) {
    if (!window.confirm("Supprimer cet incident ?")) return;
    try {
      await adminApi.deleteLeak(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-page-header">
        <div>
          <h2>Incidents de fuite</h2>
          <p>Suivi des fuites detectees : confirmer, marquer comme reparees ou classer en faux positif.</p>
        </div>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="admin-select">
          <option value="">Tous</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </header>
      {error ? <p className="error-box">{error}</p> : null}

      <section className="card">
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Zone</th>
                <th>Troncon</th>
                <th>Distance</th>
                <th>Statut</th>
                <th>Detecte</th>
                <th>Repare</th>
                <th>Notes admin</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} className={row.status === "repaired" ? "row-repaired" : ""}>
                  <td>{row.id}</td>
                  <td>{row.zone_id}</td>
                  <td>
                    {row.upstream_meter} → {row.downstream_meter}
                  </td>
                  <td>
                    {row.distance_m_from_upstream != null
                      ? `${Number(row.distance_m_from_upstream).toFixed(0)} m`
                      : "—"}
                  </td>
                  <td>
                    <span className={`admin-status admin-status--${row.status}`}>{row.status}</span>
                  </td>
                  <td>{row.detected_at ? new Date(row.detected_at).toLocaleString("fr-FR") : "—"}</td>
                  <td>{row.repaired_at ? new Date(row.repaired_at).toLocaleString("fr-FR") : "—"}</td>
                  <td>
                    <input
                      className="admin-notes-input"
                      value={notesEdit[row.id] ?? row.admin_notes ?? ""}
                      onChange={(e) => setNotesEdit({ ...notesEdit, [row.id]: e.target.value })}
                      placeholder="Notes intervention..."
                    />
                  </td>
                  <td className="admin-row-actions">
                    {row.status !== "repaired" ? (
                      <button type="button" className="btn-primary btn-sm" onClick={() => markRepaired(row.id)}>
                        Reparee
                      </button>
                    ) : null}
                    <button type="button" className="btn-ghost btn-sm" onClick={() => setStatus(row.id, "false_positive")}>
                      Faux +
                    </button>
                    <button type="button" className="btn-danger btn-sm" onClick={() => remove(row.id)}>
                      Suppr.
                    </button>
                  </td>
                </tr>
              ))}
              {!items.length ? (
                <tr>
                  <td colSpan={9}>
                    Aucun incident. Utilisez « Sync fuites » sur le tableau de bord ou declenchez une detection.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
