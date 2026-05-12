import { CRS } from "leaflet";
import { CircleMarker, ImageOverlay, MapContainer, Popup } from "react-leaflet";
import { PlanMapFitBounds } from "./PlanMapFit";
import { METER_PLAN_POINTS, PLAN_BOUNDS, PLAN_HEIGHT, PLAN_WIDTH } from "./sitePlanCoordinates";
const PLAN_COMPTEURS_URL = "/plans/plan-compteurs.png";

function toMeterImageCoords(meters) {
  return (meters || []).map((meter, index) => {
    const fromLookup = METER_PLAN_POINTS[meter.meter_id];
    if (fromLookup) return { ...meter, ...fromLookup };
    return { ...meter, x: 320 + (index % 10) * 36, y: 620 + Math.floor(index / 10) * 28 };
  });
}

function latestAnomalyForMeter(meterId, anomalies) {
  const rows = (anomalies || []).filter((a) => a.meter_id === meterId);
  if (!rows.length) return null;
  return rows.reduce((best, cur) => {
    const tb = new Date(best.timestamp || 0).getTime();
    const tc = new Date(cur.timestamp || 0).getTime();
    return tc >= tb ? cur : best;
  });
}

function riskForMeter(meterId, anomalies) {
  if (!anomalies?.length) return "normal";
  const match = latestAnomalyForMeter(meterId, anomalies);
  if (!match) return "normal";
  const p = Number(match.leak_probability || 0);
  if (p >= 0.75) return "critical";
  if (p >= 0.5) return "warning";
  if (p >= 0.25) return "caution";
  return "normal";
}

const pathByRisk = {
  normal: { color: "#2e7d32", fillColor: "#43a047", fillOpacity: 0.88 },
  caution: { color: "#f9a825", fillColor: "#ffca28", fillOpacity: 0.92 },
  warning: { color: "#ef6c00", fillColor: "#ff9800", fillOpacity: 0.93 },
  critical: { color: "#c62828", fillColor: "#e53935", fillOpacity: 0.96 },
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
      <div className="map-panel-fill" style={{ aspectRatio: `${PLAN_WIDTH} / ${PLAN_HEIGHT}` }}>
        <MapContainer
          center={[PLAN_HEIGHT / 2, PLAN_WIDTH / 2]}
          zoom={-1}
          crs={CRS.Simple}
          minZoom={-4}
          maxZoom={3}
          maxBounds={PLAN_BOUNDS}
          className="map-leaflet"
        >
          <PlanMapFitBounds bounds={PLAN_BOUNDS} />
          <ImageOverlay url={PLAN_COMPTEURS_URL} bounds={PLAN_BOUNDS} />
          {metersImageCoords.map((m) => {
          const risk = riskForMeter(m.meter_id, anomalies);
          const opts = pathByRisk[risk];
          return (
            <CircleMarker
              key={m.id}
              center={[m.y, m.x]}
              radius={risk === "critical" ? 10 : risk === "warning" ? 8 : 7}
              pathOptions={opts}
            >
              <Popup>
                <strong>{m.name}</strong>
                <br />
                ID: {m.meter_id}
                <br />
                Etat:{" "}
                {risk === "critical"
                  ? "Critique"
                  : risk === "warning"
                    ? "Attention"
                    : risk === "caution"
                      ? "Vigilance"
                      : "Normal"}
              </Popup>
            </CircleMarker>
          );
          })}
        </MapContainer>
      </div>
    </section>
  );
}
