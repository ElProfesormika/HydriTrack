import { EventList } from "../components/EventList";
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
      <header className="page-header">
        <div>
          <h2>Dashboard capteurs pression</h2>
          <p>
            Suivi des ondes de pression par zone : intensite, frequence, couverture capteurs et correlation avec les
            alertes de fuite confirmee.
          </p>
        </div>
        <div className={`connection-pill ${isConnected ? "online" : "offline"}`}>
          {isConnected ? "Flux temps reel" : "Hors ligne"}
        </div>
      </header>

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
        <article className="card">
          <h3>Logique metier</h3>
          <p style={{ color: "var(--muted)", marginTop: 0 }}>
            Chaque nouveau lot pression declenche analyse signal, correlation inter-capteurs et mise a jour carte. Les
            seuils critiques alimentent les alertes geolocalisees sur la page Cartographie.
          </p>
        </article>
      </section>
    </div>
  );
}
