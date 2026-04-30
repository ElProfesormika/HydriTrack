import { AlertSeverityChart } from "../components/AlertSeverityChart";
import { EventList } from "../components/EventList";
import { KpiCard } from "../components/KpiCard";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function DashboardAlertesPage() {
  const { alertStats, alerts, overview, isConnected, error } = useRealtimeDashboard();
  const network = overview?.network_state || {};

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h2>Dashboard alertes & incidents</h2>
          <p>
            Vue operationnelle des incidents reseau : gravite, categories, volume sur 24 h et fil direct vers les
            notifications temps reel.
          </p>
        </div>
        <div className={`connection-pill ${isConnected ? "online" : "offline"}`}>
          {isConnected ? "Flux temps reel" : "Hors ligne"}
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}

      <section className="kpi-grid">
        <KpiCard title="Alertes totales" value={alertStats?.total ?? 0} subtitle="Historique base" />
        <KpiCard title="Dernieres 24 h" value={alertStats?.last_24h ?? 0} subtitle="Fenetre glissante" />
        <KpiCard title="Alertes actives (compteur)" value={network.active_alerts ?? 0} subtitle="Etat reseau" />
        <KpiCard title="Sources signalees" value={(overview?.top_alert_sources || []).length} subtitle="Top emetteurs" />
      </section>

      <section className="split-grid">
        <AlertSeverityChart bySeverity={alertStats?.by_severity} />
        <article className="card">
          <h3>Alertes par categorie</h3>
          <div className="stat-inline">
            {(alertStats?.by_category || []).map((row) => (
              <div key={row.category} className="stat-pill">
                <strong>{row.count}</strong>
                <span>{row.category}</span>
              </div>
            ))}
            {!(alertStats?.by_category || []).length ? <p className="empty-chart">Aucune categorie pour le moment.</p> : null}
          </div>
        </article>
      </section>

      <EventList title="Journal des alertes" items={alerts} mode="alerts" />
    </div>
  );
}
