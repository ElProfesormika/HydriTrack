import { CircleMarker, MapContainer, Marker, Popup, TileLayer } from "react-leaflet";

export function MapPanel({ zones, alerts, title = "Cartographie du reseau", caption }) {
  return (
    <section className="card map-panel">
      <h3>{title}</h3>
      {caption ? <p className="map-caption">{caption}</p> : null}
      <MapContainer center={[48.505, 3.53]} zoom={13} style={{ height: 420, width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {zones.map((zone) => (
          <CircleMarker
            key={zone.id}
            center={[zone.lat, zone.lng]}
            radius={7}
            pathOptions={{ color: "#3b82f6", fillColor: "#60a5fa", fillOpacity: 0.9 }}
          >
            <Popup>{zone.name}</Popup>
          </CircleMarker>
        ))}

        {alerts.map((alert, idx) => (
          <Marker key={`${alert.zone_id}-${idx}`} position={[alert.lat, alert.lng]}>
            <Popup>
              <strong>{alert.zone_name}</strong>
              <br />
              {alert.message}
              <br />
              Gravite: {alert.severity}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </section>
  );
}
