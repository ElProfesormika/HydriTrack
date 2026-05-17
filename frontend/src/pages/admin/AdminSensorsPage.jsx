import { useCallback, useEffect, useState } from "react";
import { adminApi } from "../../services/adminApi";

const EMPTY = { sensor_id: "", zone_id: 1, segment_id: "", role: "upstream", name: "", active: true, notes: "" };

export function AdminSensorsPage() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const res = await adminApi.listSensors(true);
    setItems(res.items || []);
  }, []);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY);
  }

  function openEdit(row) {
    setEditing(row.sensor_id);
    setForm({
      sensor_id: row.sensor_id,
      zone_id: row.zone_id,
      segment_id: row.segment_id || "",
      role: row.role || "upstream",
      name: row.name || "",
      active: Boolean(row.active),
      notes: row.notes || "",
    });
  }

  async function save(e) {
    e.preventDefault();
    setError("");
    try {
      const body = {
        zone_id: Number(form.zone_id),
        segment_id: form.segment_id || null,
        role: form.role,
        name: form.name,
        active: form.active,
        notes: form.notes,
      };
      if (editing) await adminApi.updateSensor(editing, body);
      else await adminApi.createSensor({ sensor_id: form.sensor_id, ...body });
      openCreate();
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(id, hard = false) {
    if (!window.confirm(hard ? "Suppression definitive ?" : "Desactiver ?")) return;
    try {
      await adminApi.deleteSensor(id, hard);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-page-header">
        <div>
          <h2>Capteurs pression</h2>
          <p>Gestion des capteurs par zone (2 par troncon en configuration standard).</p>
        </div>
        <button type="button" className="btn-primary" onClick={openCreate}>
          + Nouveau capteur
        </button>
      </header>
      {error ? <p className="error-box">{error}</p> : null}

      <section className="card admin-form-card">
        <h3>{editing ? `Modifier ${editing}` : "Nouveau capteur"}</h3>
        <form className="admin-form-grid" onSubmit={save}>
          {!editing ? (
            <label>
              ID capteur
              <input value={form.sensor_id} onChange={(e) => setForm({ ...form, sensor_id: e.target.value })} required />
            </label>
          ) : null}
          <label>
            Zone
            <input type="number" min={1} value={form.zone_id} onChange={(e) => setForm({ ...form, zone_id: e.target.value })} />
          </label>
          <label>
            Role
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="upstream">Amont</option>
              <option value="downstream">Aval</option>
            </select>
          </label>
          <label>
            Nom
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </label>
          <label className="admin-checkbox">
            <input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} />
            Actif
          </label>
          <div className="admin-form-actions admin-form-full">
            <button type="submit" className="btn-primary">
              {editing ? "Enregistrer" : "Creer"}
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Zone</th>
                <th>Role</th>
                <th>Actif</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.sensor_id}>
                  <td>
                    <code>{row.sensor_id}</code>
                  </td>
                  <td>{row.zone_id}</td>
                  <td>{row.role}</td>
                  <td>{row.active ? "Oui" : "Non"}</td>
                  <td className="admin-row-actions">
                    <button type="button" className="btn-ghost btn-sm" onClick={() => openEdit(row)}>
                      Modifier
                    </button>
                    <button type="button" className="btn-danger btn-sm" onClick={() => remove(row.sensor_id, true)}>
                      Suppr.
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
