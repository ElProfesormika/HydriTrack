import { Bar, Line } from "react-chartjs-2";

import { EventList } from "./EventList";
import { pointColorFromLeak } from "../utils/riskLevels";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

export function MeterDeepDivePanel({
  meterId,
  meterOptions,
  profile,
  onChangeMeter,
}) {
  const activeMeterId = meterId || meterOptions[0] || "";
  const flowSeries = profile?.flow_series || [];
  const labels = flowSeries.map((row) =>
    new Date(row.bucket).toLocaleString("fr-FR", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  );
  const leakPoints = flowSeries.map((row) => Number(row.max_leak_probability || 0));
  const riskDistribution = profile?.risk_distribution || {};
  const risks = {
    normal: Number(riskDistribution.normal || 0),
    caution: Number(riskDistribution.caution || 0),
    warning: Number(riskDistribution.warning || 0),
    critical: Number(riskDistribution.critical || 0),
  };

  const flowData = {
    labels,
    datasets: [
      {
        label: "Debit moyen (m3/h)",
        data: flowSeries.map((row) => Number(row.avg_flow || 0)),
        borderColor: "#0d47a1",
        backgroundColor: "rgba(13, 71, 161, 0.10)",
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointBackgroundColor: leakPoints.map((p) => pointColorFromLeak(p)),
      },
      {
        label: "Volume cumule sur intervalle (m3)",
        data: flowSeries.map((row) => Number(row.total_volume || 0)),
        borderColor: "#00838f",
        backgroundColor: "rgba(0, 131, 143, 0.08)",
        yAxisID: "y1",
        tension: 0.25,
        pointRadius: 2,
      },
    ],
  };

  const flowOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: chartText } },
    },
    scales: {
      x: { ticks: { color: chartText }, grid: { color: chartGrid } },
      y: { ticks: { color: chartText }, grid: { color: chartGrid }, beginAtZero: true },
      y1: {
        position: "right",
        ticks: { color: "#006064" },
        grid: { drawOnChartArea: false },
        beginAtZero: true,
      },
    },
  };

  const riskBarData = {
    labels: ["Normal", "Vigilance", "Attention", "Critique"],
    datasets: [
      {
        label: "Occurrences",
        data: [risks.normal, risks.caution, risks.warning, risks.critical],
        backgroundColor: ["#2e7d32cc", "#f9a825cc", "#ef6c00cc", "#c62828cc"],
        borderRadius: 6,
      },
    ],
  };

  if (!meterOptions.length) {
    return (
      <section className="card">
        <h3>Suivi detaille par compteur</h3>
        <p className="empty-chart">Aucun compteur disponible pour le moment.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="meter-deep-header">
        <div>
          <h3>Suivi detaille par compteur</h3>
          <p className="map-caption">
            Classification ML uniforme sur tous les compteurs ({profile?.classification_model || "HydroTrack IA"}).
          </p>
        </div>
        <label className="meter-select-label">
          Compteur suivi
          <select value={activeMeterId} onChange={(event) => onChangeMeter(event.target.value)}>
            {meterOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="stat-inline">
        <div className="stat-pill">
          <strong>{Number(profile?.kpis?.total_points || 0)}</strong>
          <span>Points compteur</span>
        </div>
        <div className="stat-pill">
          <strong>{Number(profile?.kpis?.avg_flow || 0).toFixed(2)}</strong>
          <span>Debit moyen m3/h</span>
        </div>
        <div className="stat-pill">
          <strong>{Number(profile?.kpis?.total_volume || 0).toFixed(2)}</strong>
          <span>Volume cumule m3</span>
        </div>
        <div className="stat-pill">
          <strong>{Math.round(Number(profile?.kpis?.max_leak_probability || 0) * 100)}%</strong>
          <span>Risque max observe</span>
        </div>
      </div>

      <div className="split-grid meter-deep-charts">
        <div className="chart-wrapper chart-wrapper--short">
          <Line data={flowData} options={flowOptions} />
        </div>
        <div className="chart-wrapper chart-wrapper--short">
          <Bar
            data={riskBarData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { labels: { color: chartText } } },
              scales: {
                x: { ticks: { color: chartText }, grid: { display: false } },
                y: { ticks: { color: chartText }, grid: { color: chartGrid }, beginAtZero: true },
              },
            }}
          />
        </div>
      </div>

      <div className="split-grid">
        <EventList title="Alertes du compteur selectionne" items={profile?.recent_alerts || []} mode="alerts" />
        <EventList
          title="Anomalies du compteur selectionne"
          items={profile?.recent_anomalies || []}
          mode="anomalies"
        />
      </div>
    </section>
  );
}
