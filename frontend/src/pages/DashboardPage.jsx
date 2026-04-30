import { EventList } from "../components/EventList";
import { KpiCard } from "../components/KpiCard";
import { VariationChart } from "../components/VariationChart";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function DashboardPage() {
  const { overview, timeseries, alerts, anomalies, isConnected, error } = useRealtimeDashboard();

  const meter = overview?.meter_kpis || {};
  const sensors = overview?.sensor_kpis || {};
  const networkState = overview?.network_state || {};

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h2>Dashboard operationnel</h2>
          <p>KPIs compteurs/capteurs, alertes temps reel, courbes de variation.</p>
        </div>
        <div className={`connection-pill ${isConnected ? "online" : "offline"}`}>
          {isConnected ? "Backend connecte" : "Backend deconnecte"}
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}

      <section className="kpi-grid">
        <KpiCard title="Compteurs suivis" value={meter.distinct_meters || 0} subtitle="Identifiants uniques" />
        <KpiCard title="Points compteurs" value={meter.total_points || 0} subtitle="Volume de telemetrie" />
        <KpiCard title="Debit moyen" value={Number(meter.avg_flow || 0).toFixed(2)} subtitle="m3/h (estime)" />
        <KpiCard title="Volume cumule" value={Number(meter.total_volume || 0).toFixed(2)} subtitle="m3" />
        <KpiCard title="Capteurs pression" value={sensors.distinct_sensors || 0} subtitle="Capteurs uniques" />
        <KpiCard title="Zones instrumentees" value={sensors.distinct_zones || 0} subtitle="Couverture capteurs" />
        <KpiCard title="Intensite moyenne" value={Number(sensors.avg_intensity || 0).toFixed(2)} subtitle="Signal pression" />
        <KpiCard title="Alertes actives" value={networkState.active_alerts || 0} subtitle="Risque reseau" />
      </section>

      <VariationChart timeseries={timeseries} />

      <section className="split-grid">
        <EventList title="Points d'alertes recents" items={alerts} mode="alerts" />
        <EventList title="Anomalies recentes" items={anomalies} mode="anomalies" />
      </section>
    </div>
  );
}
