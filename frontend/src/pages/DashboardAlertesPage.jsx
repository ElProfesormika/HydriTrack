import { AlertSeverityChart } from "../components/AlertSeverityChart";
import { DashboardHeader } from "../components/DashboardHeader";
import { EventList } from "../components/EventList";
import { InsightCard } from "../components/InsightCard";
import { KpiCard } from "../components/KpiCard";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function DashboardAlertesPage() {
  const { alertStats, alerts, overview, isConnected, error } = useRealtimeDashboard();
  const network = overview?.network_state || {};

  return (
    <div className="page">
      <DashboardHeader
        title="Alertes et incidents"
        description="Vision priorisee des alertes reseau : gravite, categories, volume 24h et journal de suivi."
        isConnected={isConnected}
      />

      {error ? <p className="error-box">{error}</p> : null}

      <section className="kpi-grid">
        <KpiCard title="Alertes totales" value={alertStats?.total ?? 0} subtitle="Historique base" />
        <KpiCard title="Dernieres 24 h" value={alertStats?.last_24h ?? 0} subtitle="Fenetre glissante" />
        <KpiCard title="Alertes actives (compteur)" value={network.active_alerts ?? 0} subtitle="Etat reseau" />
        <KpiCard title="Sources signalees" value={(overview?.top_alert_sources || []).length} subtitle="Top emetteurs" />
      </section>

      <section className="split-grid">
        <AlertSeverityChart bySeverity={alertStats?.by_severity} />
        <InsightCard title="Alertes par categorie">
          <div className="stat-inline">
            {(alertStats?.by_category || []).map((row) => (
              <div key={row.category} className="stat-pill">
                <strong>{row.count}</strong>
                <span>{row.category}</span>
              </div>
            ))}
            {!(alertStats?.by_category || []).length ? <p className="empty-chart">Aucune categorie pour le moment.</p> : null}
          </div>
        </InsightCard>
      </section>

      <section className="split-grid">
        <EventList title="Journal des alertes" items={alerts} mode="alerts" />
        <InsightCard title="Sources les plus actives">
          <div className="stat-inline">
            {(overview?.top_alert_sources || []).slice(0, 6).map((row) => (
              <div key={row.source_id} className="stat-pill">
                <strong>{row.alert_count}</strong>
                <span>{row.source_id}</span>
              </div>
            ))}
            {!(overview?.top_alert_sources || []).length ? (
              <p className="empty-chart">Aucune source signalee pour le moment.</p>
            ) : null}
          </div>
        </InsightCard>
      </section>
    </div>
  );
}
