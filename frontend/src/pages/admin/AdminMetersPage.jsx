import { useCallback, useEffect, useState } from "react";
import { adminApi } from "../../services/adminApi";

const EMPTY = { meter_id: "", name: "", plan_x: "", plan_y: "", active: true, notes: "" };

export function AdminMetersPage() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const res = await adminApi.listMeters(true);
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
    setEditing(row.meter_id);
    setForm({
      meter_id: row.meter_id,
      name: row.name || "",
      plan_x: row.plan_x ?? "",
      plan_y: row.plan_y ?? "",
      active: Boolean(row.active),
      notes: row.notes || "",
    });
  }

  async function save(e) {
    e.preventDefault();
    setError("");
    try {
      const body = {
        name: form.name,
        plan_x: form.plan_x === "" ? null : Number(form.plan_x),
        plan_y: form.plan_y === "" ? null : Number(form.plan_y),
        active: form.active,
        notes: form.notes,
      };
      if (editing) {
        await adminApi.updateMeter(editing, body);
      } else {
        await adminApi.createMeter({
          meter_id: form.meter_id,
          ...body,
        });
      }
      setForm(EMPTY);
      setEditing(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(id, hard = false) {
    if (!window.confirm(hard ? "Suppression definitive ?" : "Desactiver ce compteur ?")) return;
    try {
      await adminApi.deleteMeter(id, hard);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-page-header">
        <div>
          <h2>Compteurs</h2>
          <p>Ajouter, modifier ou desactiver les compteurs du reseau.</p>
        </div>
        <button type="button" className="btn-primary" onClick={openCreate}>
          + Nouveau compteur
        </button>
      </header>
      {error ? <p className="error-box">{error}</p> : null}

      <section className="card admin-form-card">
        <h3>{editing ? `Modifier ${editing}` : "Nouveau compteur"}</h3>
        <form className="admin-form-grid" onSubmit={save}>
          {!editing ? (
            <label>
              ID compteur
              <input
                value={form.meter_id}
                onChange={(e) => setForm({ ...form, meter_id: e.target.value })}
                required
              />
            </label>
          ) : null}
          <label>
            Nom affiche
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </label>
          <label>
            Plan X
            <input value={form.plan_x} onChange={(e) => setForm({ ...form, plan_x: e.target.value })} />
          </label>
          <label>
            Plan Y
            <input value={form.plan_y} onChange={(e) => setForm({ ...form, plan_y: e.target.value })} />
          </label>
          <label className="admin-checkbox">
            <input
              type="checkbox"
              checked={form.active}
              onChange={(e) => setForm({ ...form, active: e.target.checked })}
            />
            Actif
          </label>
          <label className="admin-form-full">
            Notes
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} />
          </label>
          <div className="admin-form-actions admin-form-full">
            <button type="submit" className="btn-primary">
              {editing ? "Enregistrer" : "Creer"}
            </button>
            {editing ? (
              <button type="button" className="btn-ghost" onClick={openCreate}>
                Annuler
              </button>
            ) : null}
          </div>
        </form>
      </section>

      <section className="card">
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nom</th>
                <th>Plan</th>
                <th>Actif</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.meter_id} className={!row.active ? "row-inactive" : ""}>
                  <td>
                    <code>{row.meter_id}</code>
                  </td>
                  <td>{row.name}</td>
                  <td>
                    {row.plan_x != null ? `${Number(row.plan_x).toFixed(0)}, ${Number(row.plan_y).toFixed(0)}` : "—"}
                  </td>
                  <td>{row.active ? "Oui" : "Non"}</td>
                  <td className="admin-row-actions">
                    <button type="button" className="btn-ghost btn-sm" onClick={() => openEdit(row)}>
                      Modifier
                    </button>
                    <button type="button" className="btn-ghost btn-sm" onClick={() => remove(row.meter_id, false)}>
                      Desactiver
                    </button>
                    <button type="button" className="btn-danger btn-sm" onClick={() => remove(row.meter_id, true)}>
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
