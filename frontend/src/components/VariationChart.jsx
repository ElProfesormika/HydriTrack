import { Bar } from "react-chartjs-2";

import { RISK_COLORS } from "../utils/riskLevels";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

const anomalyStackOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: chartText, boxWidth: 10, font: { size: 11 } },
    },
    tooltip: { mode: "index", intersect: false },
  },
  scales: {
    x: {
      stacked: true,
      ticks: { color: chartText, maxRotation: 35 },
      grid: { display: false },
    },
    y: {
      stacked: true,
      ticks: { color: chartText, precision: 0 },
      grid: { color: chartGrid },
      beginAtZero: true,
    },
  },
};

function anomNormal(row) {
  return Number(row.anom_normal ?? row.anom_nominal ?? 0);
}

function alertNormal(row) {
  return Number(row.alert_normal ?? row.alert_nominal ?? 0);
}

export function VariationChart({ timeseries }) {
  const ts = Array.isArray(timeseries) ? timeseries : [];

  if (ts.length === 0) {
    return (
      <section className="card chart-container">
        <h3>Suivi anomalies & alertes (barres empilées par gravité)</h3>
        <p className="empty-chart">Pas encore de données sur la période sélectionnée.</p>
      </section>
    );
  }

  const labels = ts.map((item) =>
    new Date(item.bucket).toLocaleString("fr-FR", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  );

  const anomaliesData = {
    labels,
    datasets: [
      {
        label: "Anomalies — normal",
        data: ts.map((i) => anomNormal(i)),
        backgroundColor: `${RISK_COLORS.normal}aa`,
        borderColor: RISK_COLORS.normal,
        borderWidth: 1,
        stack: "anom",
      },
      {
        label: "Anomalies — vigilance",
        data: ts.map((i) => Number(i.anom_caution ?? 0)),
        backgroundColor: `${RISK_COLORS.caution}cc`,
        borderColor: RISK_COLORS.caution,
        borderWidth: 1,
        stack: "anom",
      },
      {
        label: "Anomalies — attention",
        data: ts.map((i) => Number(i.anom_warning ?? 0)),
        backgroundColor: `${RISK_COLORS.warning}cc`,
        borderColor: RISK_COLORS.warning,
        borderWidth: 1,
        stack: "anom",
      },
      {
        label: "Anomalies — critique",
        data: ts.map((i) => Number(i.anom_critical ?? 0)),
        backgroundColor: `${RISK_COLORS.critical}cc`,
        borderColor: RISK_COLORS.critical,
        borderWidth: 1,
        stack: "anom",
      },
    ],
  };

  const alertsData = {
    labels,
    datasets: [
      {
        label: "Alertes — info / normal",
        data: ts.map((i) => alertNormal(i)),
        backgroundColor: `${RISK_COLORS.normal}99`,
        borderColor: RISK_COLORS.normal,
        borderWidth: 1,
        stack: "alr",
      },
      {
        label: "Alertes — vigilance",
        data: ts.map((i) => Number(i.alert_caution ?? 0)),
        backgroundColor: `${RISK_COLORS.caution}cc`,
        borderColor: RISK_COLORS.caution,
        borderWidth: 1,
        stack: "alr",
      },
      {
        label: "Alertes — attention",
        data: ts.map((i) => Number(i.alert_warning ?? 0)),
        backgroundColor: `${RISK_COLORS.warning}cc`,
        borderColor: RISK_COLORS.warning,
        borderWidth: 1,
        stack: "alr",
      },
      {
        label: "Alertes — critique",
        data: ts.map((i) => Number(i.alert_critical ?? 0)),
        backgroundColor: `${RISK_COLORS.critical}cc`,
        borderColor: RISK_COLORS.critical,
        borderWidth: 1,
        stack: "alr",
      },
    ],
  };

  return (
    <section className="card chart-container">
      <h3>Suivi anomalies & alertes (barres empilées par gravité)</h3>
      <p className="map-caption">
        Vert = normal · jaune = vigilance · orange = attention · rouge = critique — aligné avec la détection ML (IsolationForest + quantiles type HydroTrack IA).
      </p>
      <div className="variation-chart-split">
        <div className="chart-wrapper variation-chart-pane">
          <Bar data={anomaliesData} options={anomalyStackOpts} />
        </div>
        <div className="chart-wrapper variation-chart-pane">
          <Bar data={alertsData} options={anomalyStackOpts} />
        </div>
      </div>
    </section>
  );
}
