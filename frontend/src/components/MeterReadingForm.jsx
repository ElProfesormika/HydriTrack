import { useEffect, useState } from "react";
import { hydroApi } from "../services/api";

function toISOFromLocalDatetime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString();
}

export function MeterReadingForm({ onSaved }) {
  const [meters, setMeters] = useState([]);
  const [meterId, setMeterId] = useState("");
  const [volume, setVolume] = useState("");
  const [flowRate, setFlowRate] = useState("");
  const [readingAt, setReadingAt] = useState("");
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    hydroApi
      .getMapMeters()
      .then((res) => {
        if (cancelled) return;
        const items = res.items || [];
        setMeters(items);
        if (items.length) {
          setMeterId((prev) => prev || items[0].meter_id);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setStatus("");
    const ts = readingAt ? toISOFromLocalDatetime(readingAt) : new Date().toISOString();
    const vol = Number(volume);
    const flow = Number(flowRate);
    if (!meterId) {
      setStatus("Choisissez un compteur.");
      setSubmitting(false);
      return;
    }
    if (Number.isNaN(vol) || vol < 0 || Number.isNaN(flow) || flow < 0) {
      setStatus("Volume et debit doivent etre des nombres positifs.");
      setSubmitting(false);
      return;
    }
    try {
      const result = await hydroApi.postMeterData({
        timestamp: ts,
        meter_id: meterId,
        volume: vol,
        flow_rate: flow,
      });
      const ml = result.result?.ml_model ? ` · ${result.result.ml_model}` : "";
      setStatus(
        `Relevé enregistré — score ML ${result.result?.anomaly_score ?? "?"} · fuite ~${Math.round((result.result?.leak_probability ?? 0) * 100)}%${ml}`
      );
      setVolume("");
      setFlowRate("");
      if (typeof onSaved === "function") onSaved();
    } catch (err) {
      setStatus(err.message || "Erreur lors de l'enregistrement.");
    }
    setSubmitting(false);
  }

  return (
    <section className="card meter-reading-card">
      <h3>Nouveau relevé compteur</h3>
      <p className="map-caption">
        Enregistrer un volume et un débit : le backend analyse via le moteur ML et met à jour les courbes et alertes en direct.
      </p>
      <form className="meter-reading-form" onSubmit={handleSubmit}>
        <label>
          Compteur
          <select value={meterId} onChange={(e) => setMeterId(e.target.value)}>
            {(meters || []).map((m) => (
              <option key={m.meter_id} value={m.meter_id}>
                {m.name || m.meter_id} ({m.meter_id})
              </option>
            ))}
          </select>
        </label>
        <label>
          Date / heure
          <input
            type="datetime-local"
            value={readingAt}
            onChange={(e) => setReadingAt(e.target.value)}
            placeholder="Laisser vide pour maintenant"
          />
        </label>
        <label>
          Volume (m³)
          <input type="number" min={0} step={0.01} value={volume} onChange={(e) => setVolume(e.target.value)} required />
        </label>
        <label>
          Débit (m³/h ou unité métier)
          <input type="number" min={0} step={0.01} value={flowRate} onChange={(e) => setFlowRate(e.target.value)} required />
        </label>
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? "Envoi..." : "Enregistrer le relevé"}
        </button>
      </form>
      {status ? <p className="meter-reading-status">{status}</p> : null}
    </section>
  );
}
