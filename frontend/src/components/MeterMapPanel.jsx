import { CRS } from "leaflet";
import { CircleMarker, ImageOverlay, MapContainer, Popup } from "react-leaflet";
import { METER_PLAN_POINTS, PLAN_BOUNDS, PLAN_HEIGHT, PLAN_WIDTH } from "./sitePlanCoordinates";
const PLAN_COMPTEURS_URL = "/plans/plan-compteurs.png";

function toMeterImageCoords(meters) {
  return (meters || []).map((meter, index) => {
    const fromLookup = METER_PLAN_POINTS[meter.meter_id];
    if (fromLookup) return { ...meter, ...fromLookup };
    return { ...meter, x: 320 + (index % 10) * 36, y: 620 + Math.floor(index / 10) * 28 };
  });
}

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
  const metersImageCoords = toMeterImageCoords(meters || []);

  return (
    <section className="card map-panel">
      <h3>{title}</h3>
      {caption ? <p className="map-caption">{caption}</p> : null}
      <MapContainer
        center={[PLAN_HEIGHT / 2, PLAN_WIDTH / 2]}
        zoom={-1}
        crs={CRS.Simple}
        minZoom={-3}
        maxZoom={2}
        maxBounds={PLAN_BOUNDS}
        style={{ height: 420, width: "100%" }}
      >
        <ImageOverlay url={PLAN_COMPTEURS_URL} bounds={PLAN_BOUNDS} />
        {metersImageCoords.map((m) => {
          const risk = riskForMeter(m.meter_id, anomalies);
          const opts = pathByRisk[risk];
          return (
            <CircleMarker key={m.id} center={[m.y, m.x]} radius={risk === "high" ? 9 : 7} pathOptions={opts}>
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
