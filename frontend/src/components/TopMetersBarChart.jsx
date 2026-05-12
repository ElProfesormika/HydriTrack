import { Bar } from "react-chartjs-2";

import { barColorFromAvgScore } from "../utils/riskLevels";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

export function TopMetersBarChart({ items, title = "Compteurs les plus signales (anomalies)" }) {
  const labels = (items || []).map((r) => r.meter_id || "?");
  const data = {
    labels,
    datasets: [
      {
        label: "Nombre d'anomalies",
        data: (items || []).map((r) => Number(r.anomaly_count || 0)),
        backgroundColor: (items || []).map((r) => barColorFromAvgScore(r.avg_score)),
        borderColor: "rgba(13, 71, 161, 0.45)",
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: chartText } },
    },
    scales: {
      x: { ticks: { color: chartText }, grid: { display: false } },
      y: { ticks: { color: chartText }, grid: { color: chartGrid }, beginAtZero: true },
    },
  };

  return (
    <section className="card chart-container">
      <h3>{title}</h3>
      <div className="chart-wrapper chart-wrapper--short">
        <Bar data={data} options={options} />
      </div>
    </section>
  );
}
