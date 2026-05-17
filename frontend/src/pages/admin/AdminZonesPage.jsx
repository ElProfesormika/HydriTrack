import { useCallback, useEffect, useState } from "react";
import { adminApi } from "../../services/adminApi";

export function AdminZonesPage() {
  const [zones, setZones] = useState([]);
  const [segments, setSegments] = useState([]);
  const [error, setError] = useState("");
  const [zoneForm, setZoneForm] = useState({
    zone_id: "",
    name: "",
    short_name: "",
    plan_x: "",
    plan_y: "",
    active: true,
  });
  const [segEdit, setSegEdit] = useState(null);

  const load = useCallback(async () => {
    const [z, s] = await Promise.all([adminApi.listZones(true), adminApi.listSegments()]);
    setZones(z.items || []);
    setSegments(s.items || []);
  }, []);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  async function saveZone(e) {
    e.preventDefault();
    try {
      await adminApi.createZone({
        zone_id: Number(zoneForm.zone_id),
        name: zoneForm.name,
        short_name: zoneForm.short_name,
        plan_x: zoneForm.plan_x === "" ? null : Number(zoneForm.plan_x),
        plan_y: zoneForm.plan_y === "" ? null : Number(zoneForm.plan_y),
        active: zoneForm.active,
      });
      setZoneForm({ zone_id: "", name: "", short_name: "", plan_x: "", plan_y: "", active: true });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function saveSegment(e) {
    e.preventDefault();
    if (!segEdit) return;
    try {
      await adminApi.updateSegment(segEdit.segment_id, {
        upstream_meter: segEdit.upstream_meter,
        downstream_meter: segEdit.downstream_meter,
        length_m: Number(segEdit.length_m),
        active: segEdit.active,
        notes: segEdit.notes,
      });
      setSegEdit(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-page-header">
        <div>
          <h2>Zones & troncons</h2>
          <p>Zones capteurs entre compteurs et longueur des troncons pour la localisation.</p>
        </div>
      </header>
      {error ? <p className="error-box">{error}</p> : null}

      <section className="card admin-form-card">
        <h3>Nouvelle zone</h3>
        <form className="admin-form-grid" onSubmit={saveZone}>
          <label>
            ID zone
            <input value={zoneForm.zone_id} onChange={(e) => setZoneForm({ ...zoneForm, zone_id: e.target.value })} required />
          </label>
          <label>
            Nom
            <input value={zoneForm.name} onChange={(e) => setZoneForm({ ...zoneForm, name: e.target.value })} required />
          </label>
          <label>
            Nom court
            <input value={zoneForm.short_name} onChange={(e) => setZoneForm({ ...zoneForm, short_name: e.target.value })} />
          </label>
          <label>
            Plan X
            <input value={zoneForm.plan_x} onChange={(e) => setZoneForm({ ...zoneForm, plan_x: e.target.value })} />
          </label>
          <div className="admin-form-actions">
            <button type="submit" className="btn-primary">
              Creer zone
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <h3>Troncons reseau</h3>
        {segEdit ? (
          <form className="admin-form-grid admin-segment-edit" onSubmit={saveSegment}>
            <strong className="admin-form-full">Edition {segEdit.segment_id}</strong>
            <label>
              Compteur amont
              <input
                value={segEdit.upstream_meter}
                onChange={(e) => setSegEdit({ ...segEdit, upstream_meter: e.target.value })}
              />
            </label>
            <label>
              Compteur aval
              <input
                value={segEdit.downstream_meter}
                onChange={(e) => setSegEdit({ ...segEdit, downstream_meter: e.target.value })}
              />
            </label>
            <label>
              Longueur (m)
              <input
                type="number"
                value={segEdit.length_m}
                onChange={(e) => setSegEdit({ ...segEdit, length_m: e.target.value })}
              />
            </label>
            <div className="admin-form-actions admin-form-full">
              <button type="submit" className="btn-primary">
                Enregistrer troncon
              </button>
              <button type="button" className="btn-ghost" onClick={() => setSegEdit(null)}>
                Annuler
              </button>
            </div>
          </form>
        ) : null}
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Troncon</th>
                <th>Zone</th>
                <th>Amont → Aval</th>
                <th>Longueur m</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {segments.map((row) => (
                <tr key={row.segment_id}>
                  <td>
                    <code>{row.segment_id}</code>
                  </td>
                  <td>{row.zone_id}</td>
                  <td>
                    {row.upstream_meter} → {row.downstream_meter}
                  </td>
                  <td>{row.length_m}</td>
                  <td>
                    <button type="button" className="btn-ghost btn-sm" onClick={() => setSegEdit({ ...row, notes: row.notes || "" })}>
                      Modifier
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h3>Zones ({zones.length})</h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nom</th>
                <th>Actif</th>
              </tr>
            </thead>
            <tbody>
              {zones.map((z) => (
                <tr key={z.zone_id}>
                  <td>{z.zone_id}</td>
                  <td>{z.name}</td>
                  <td>{z.active ? "Oui" : "Non"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
