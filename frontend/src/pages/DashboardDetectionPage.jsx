import { DashboardHeader } from "../components/DashboardHeader";
import { EventList } from "../components/EventList";
import { InsightCard } from "../components/InsightCard";
import { KpiCard } from "../components/KpiCard";
import { VariationChart } from "../components/VariationChart";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

function avgLeakProbability(items) {
  if (!items?.length) return 0;
  const sum = items.reduce((acc, row) => acc + Number(row.leak_probability || 0), 0);
  return sum / items.length;
}

export function DashboardDetectionPage() {
  const { overview, timeseries, anomalies, isConnected, error } = useRealtimeDashboard();
  const network = overview?.network_state || {};
  const recent = (anomalies || []).slice(0, 12);
  const avgLeak = avgLeakProbability(recent);

  return (
    <div className="page">
      <DashboardHeader
        title="Detection ML"
        description="Suivi de la detection d'anomalies par compteur avec probabilites de fuite et evolution du risque."
        isConnected={isConnected}
      />

      {error ? <p className="error-box">{error}</p> : null}

      <section className="kpi-grid">
        <KpiCard title="Anomalies en base" value={network.latest_anomalies ?? 0} subtitle="Scores stockes" />
        <KpiCard
          title="Risque moyen (echantillon)"
          value={`${Math.round(avgLeak * 100)}%`}
          subtitle="Prob. fuite sur derniers points"
        />
        <KpiCard title="Compteurs sous surveillance" value={(overview?.top_anomalous_meters || []).length} subtitle="Top signalements" />
        <KpiCard title="Points ML / compteur" value={network.ingested_meter_points ?? 0} subtitle="Donnees brutes" />
      </section>

      <VariationChart timeseries={timeseries} />

      <section className="split-grid">
        <InsightCard title="Referentiel modele">
          <p className="map-caption">
            Base technique alignee sur <code style={{ color: "var(--text-strong)" }}>hydrotrack_modele_ia.py</code> :
            features log(conso), IsolationForest, seuils par capteur. Les scores exposes ici proviennent du pipeline
            backend branché sur l&apos;ingestion temps reel.
          </p>
          <div className="stat-inline">
            <div className="stat-pill">
              <strong>{recent.length}</strong>
              <span>Taille echantillon recent</span>
            </div>
            <div className="stat-pill">
              <strong>{Math.round(avgLeak * 100)}%</strong>
              <span>Probabilite moyenne fuite</span>
            </div>
          </div>
        </InsightCard>
        <EventList title="Scores recents" items={anomalies} mode="anomalies" />
      </section>
    </div>
  );
}
