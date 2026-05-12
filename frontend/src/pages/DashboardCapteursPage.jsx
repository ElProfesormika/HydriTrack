import { DashboardHeader } from "../components/DashboardHeader";
import { EventList } from "../components/EventList";
import { InsightCard } from "../components/InsightCard";
import { KpiCard } from "../components/KpiCard";
import { PressureIntensityChart } from "../components/PressureIntensityChart";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function DashboardCapteursPage() {
  const { overview, pressureSeries, alerts, isConnected, error } = useRealtimeDashboard();
  const sensors = overview?.sensor_kpis || {};

  const pressureAlerts = (alerts || []).filter(
    (a) => String(a.category || "").includes("leak") || String(a.source_id || "").toLowerCase().includes("sensor")
  );

  return (
    <div className="page">
      <DashboardHeader
        title="Suivi capteurs pression"
        description="Analyse des signaux de pression par zone (intensite, frequence, couverture) et impact sur le risque de fuite."
        isConnected={isConnected}
      />

      {error ? <p className="error-box">{error}</p> : null}

      <section className="kpi-grid">
        <KpiCard title="Points capteurs" value={sensors.total_points || 0} subtitle="Mesures pression" />
        <KpiCard title="Capteurs uniques" value={sensors.distinct_sensors || 0} subtitle="Instrumentation" />
        <KpiCard title="Zones couvertes" value={sensors.distinct_zones || 0} subtitle="Secteurs geographiques" />
        <KpiCard title="Intensite moyenne" value={Number(sensors.avg_intensity || 0).toFixed(2)} subtitle="Signal" />
        <KpiCard title="Intensite max" value={Number(sensors.max_intensity || 0).toFixed(2)} subtitle="Pic observe" />
      </section>

      <PressureIntensityChart series={pressureSeries} />

      <section className="split-grid">
        <EventList title="Alertes liees aux capteurs / fuites" items={pressureAlerts.length ? pressureAlerts : alerts} mode="alerts" />
        <InsightCard title="Logique metier">
          <p className="map-caption">
            Chaque nouveau lot pression declenche analyse signal, correlation inter-capteurs et mise a jour carte. Les
            seuils critiques alimentent les alertes geolocalisees sur la page Cartographie.
          </p>
        </InsightCard>
      </section>
    </div>
  );
}
