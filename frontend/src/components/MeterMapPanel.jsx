import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

function riskForMeter(meterId, anomalies) {
  if (!anomalies?.length) return "normal";
  const match = anomalies.find((a) => a.meter_id === meterId);
  if (!match) return "normal";
  const p = Number(match.leak_probability || 0);
  if (p >= 0.75) return "high";
  if (p >= 0.5) return "medium";
  return "normal";
}

const pathByRisk = {
  normal: { color: "#1565c0", fillColor: "#1976d2", fillOpacity: 0.85 },
  medium: { color: "#f57c00", fillColor: "#ff9800", fillOpacity: 0.9 },
  high: { color: "#c62828", fillColor: "#e53935", fillOpacity: 0.95 },
};

export function MeterMapPanel({
  meters,
  anomalies,
  title = "Carte des compteurs reseau",
  caption = "Positions des compteurs EP DATANUMIA. Couleur selon derniere anomalie connue (score / probabilite de fuite).",
}) {
  return (
    <section className="card map-panel">
      <h3>{title}</h3>
      {caption ? <p className="map-caption">{caption}</p> : null}
      <MapContainer center={[48.505, 3.53]} zoom={13} style={{ height: 420, width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {(meters || []).map((m) => {
          const risk = riskForMeter(m.meter_id, anomalies);
          const opts = pathByRisk[risk];
          return (
            <CircleMarker key={m.id} center={[m.lat, m.lng]} radius={risk === "high" ? 9 : 7} pathOptions={opts}>
              <Popup>
                <strong>{m.name}</strong>
                <br />
                ID: {m.meter_id}
                <br />
                Etat: {risk === "high" ? "Critique" : risk === "medium" ? "Surveillance" : "Normal"}
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </section>
  );
}
