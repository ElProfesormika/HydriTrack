import { CRS } from "leaflet";
import { CircleMarker, ImageOverlay, MapContainer, Marker, Popup } from "react-leaflet";
import { PlanMapFitBounds } from "./PlanMapFit";
import { PLAN_BOUNDS, PLAN_HEIGHT, PLAN_WIDTH, ZONE_PLAN_POINTS } from "./sitePlanCoordinates";
const PLAN_CAPTEURS_URL = "/plans/plan-capteurs.png";

function toZoneImageCoords(zones) {
  return (zones || []).map((zone, index) => {
    const fromLookup = ZONE_PLAN_POINTS[zone.id];
    if (fromLookup) return { ...zone, ...fromLookup };
    return { ...zone, x: 240 + (index % 8) * 60, y: 420 + Math.floor(index / 8) * 60 };
  });
}

function toAlertImageCoords(alerts) {
  return (alerts || []).map((alert, index) => {
    const base = ZONE_PLAN_POINTS[alert.zone_id] || { x: 470, y: 500 };
    const spreadX = (index % 3) * 14 - 14;
    const spreadY = Math.floor(index / 3) * 10;
    return {
      ...alert,
      x: Math.max(30, Math.min(PLAN_WIDTH - 30, base.x + spreadX)),
      y: Math.max(30, Math.min(PLAN_HEIGHT - 30, base.y + spreadY)),
    };
  });
}

export function MapPanel({ zones, alerts, title = "Cartographie du reseau", caption }) {
  const zonesImageCoords = toZoneImageCoords(zones);
  const alertsImageCoords = toAlertImageCoords(alerts);

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
          <ImageOverlay url={PLAN_CAPTEURS_URL} bounds={PLAN_BOUNDS} />

          {zonesImageCoords.map((zone) => (
            <CircleMarker
              key={zone.id}
              center={[zone.y, zone.x]}
              radius={7}
              pathOptions={{ color: "#3b82f6", fillColor: "#60a5fa", fillOpacity: 0.9 }}
            >
              <Popup>{zone.name}</Popup>
            </CircleMarker>
          ))}

          {alertsImageCoords.map((alert, idx) => (
            <Marker key={`${alert.zone_id}-${idx}`} position={[alert.y, alert.x]}>
              <Popup>
                <strong>{alert.zone_name}</strong>
                <br />
                {alert.message}
                <br />
                Gravité: {alert.severity}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </section>
  );
}
