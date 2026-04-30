import { EventList } from "../components/EventList";
import { MapPanel } from "../components/MapPanel";
import { MeterMapPanel } from "../components/MeterMapPanel";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function MapPage() {
  const { mapZones, mapAlerts, mapMeters, alerts, anomalies } = useRealtimeDashboard();

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h2>Cartographie</h2>
          <p>
            Deux vues complementaires : capteurs d&apos;ondes de pression par zone du site, et compteurs d&apos;eau du
            reseau EP avec code couleur selon les anomalies ML.
          </p>
        </div>
      </header>

      <div className="maps-two">
        <MapPanel
          zones={mapZones}
          alerts={mapAlerts}
          title="Carte capteurs & zones"
          caption="Cercles bleus : zones d'implantation (spec HydroTrack). Marqueurs : alertes de fuite geolocalisees."
        />
        <MeterMapPanel
          meters={mapMeters}
          anomalies={anomalies}
          title="Carte des compteurs"
          caption="Un marqueur par compteur reseau. Orange / rouge si une anomalie recente concerne ce compteur."
        />
      </div>

      <section className="split-grid">
        <article className="card">
          <h3>Zones instrumentees</h3>
          <ul className="event-list">
            {mapZones.map((zone) => (
              <li key={zone.id}>
                <strong>{zone.name}</strong>
                <p>
                  Lat {zone.lat.toFixed(5)} — Lng {zone.lng.toFixed(5)}
                </p>
              </li>
            ))}
          </ul>
        </article>

        <EventList title="Alertes (contexte carto)" items={alerts} mode="alerts" />
      </section>
    </div>
  );
}
