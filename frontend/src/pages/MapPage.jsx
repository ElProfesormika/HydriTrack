import { MapPanel } from "../components/MapPanel";
import { MeterMapPanel } from "../components/MeterMapPanel";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function MapPage() {
  const { mapZones, mapAlerts, mapMeters, anomalies } = useRealtimeDashboard();

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h2>Cartographie</h2>
          <p>
            Vue simplifiee du plan principal: emplacements capteurs et compteurs recales sur le site reel.
          </p>
        </div>
      </header>

      <div className="maps-two">
        <MapPanel
          zones={mapZones}
          alerts={mapAlerts}
          title="Carte capteurs & zones"
          caption="Zones capteurs et alertes replacees sur le plan central."
        />
        <MeterMapPanel
          meters={mapMeters}
          anomalies={anomalies}
          title="Carte des compteurs"
          caption="Compteurs du site principal avec code couleur des anomalies."
        />
      </div>
    </div>
  );
}
