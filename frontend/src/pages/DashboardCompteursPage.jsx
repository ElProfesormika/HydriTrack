import { EventList } from "../components/EventList";
import { KpiCard } from "../components/KpiCard";
import { MeterFlowChart } from "../components/MeterFlowChart";
import { TopMetersBarChart } from "../components/TopMetersBarChart";
import { VariationChart } from "../components/VariationChart";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function DashboardCompteursPage() {
  const { overview, timeseries, meterFlowSeries, anomalies, isConnected, error } = useRealtimeDashboard();
  const meter = overview?.meter_kpis || {};
  const topMeters = overview?.top_anomalous_meters || [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h2>Dashboard compteurs</h2>
          <p>
            Telemetrie des compteurs d&apos;eau, consommation, debits et anomalies ML par point de mesure du reseau
            EP DATANUMIA.
          </p>
        </div>
        <div className={`connection-pill ${isConnected ? "online" : "offline"}`}>
          {isConnected ? "Flux temps reel" : "Hors ligne"}
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}

      <section className="kpi-grid">
        <KpiCard title="Compteurs distincts" value={meter.distinct_meters || 0} subtitle="Identifiants actifs" />
        <KpiCard title="Points telemetrie" value={meter.total_points || 0} subtitle="Mesures enregistrees" />
        <KpiCard title="Debit moyen" value={Number(meter.avg_flow || 0).toFixed(2)} subtitle="Unite selon source" />
        <KpiCard title="Debit max observe" value={Number(meter.max_flow || 0).toFixed(2)} subtitle="Pic reseau" />
        <KpiCard title="Volume cumule" value={Number(meter.total_volume || 0).toFixed(2)} subtitle="Integration volumes" />
      </section>

      <section className="split-grid">
        <MeterFlowChart series={meterFlowSeries} />
        <TopMetersBarChart items={topMeters} />
      </section>

      <VariationChart timeseries={timeseries} />

      <EventList title="Dernieres anomalies par compteur" items={anomalies} mode="anomalies" />
    </div>
  );
}
