import { Line } from "react-chartjs-2";

import { pointColorFromLeak } from "../utils/riskLevels";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

export function MeterFlowChart({ series, title = "Evolution du débit (compteurs agrégés)" }) {
  const rows = Array.isArray(series) ? series : [];
  const labels = rows.map((row) =>
    new Date(row.bucket).toLocaleString("fr-FR", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  );

  const pointBg = rows.map((r) => pointColorFromLeak(r.max_leak_probability ?? 0));
  const pointBorder = pointBg.map((c) => c);

  const data = {
    labels,
    datasets: [
      {
        label: "Débit moyen",
        data: rows.map((r) => Number(r.avg_flow || 0)),
        borderColor: "#0d47a1",
        backgroundColor: "rgba(13, 71, 161, 0.06)",
        fill: true,
        tension: 0.35,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: pointBg,
        pointBorderColor: pointBorder,
        pointBorderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: chartText } },
      tooltip: {
        callbacks: {
          afterLabel(ctx) {
            const p = rows[ctx.dataIndex]?.max_leak_probability;
            if (p == null) return "";
            return `Risque fuite (max période): ${Math.round(Number(p) * 100)}%`;
          },
        },
      },
    },
    scales: {
      x: { ticks: { color: chartText }, grid: { color: chartGrid } },
      y: { ticks: { color: chartText }, grid: { color: chartGrid }, beginAtZero: true },
    },
  };

  return (
    <section className="card chart-container">
      <h3>{title}</h3>
      <p className="map-caption">Couleur des points : risque estimé (vert → rouge) sur l’intervalle.</p>
      <div className="chart-wrapper chart-wrapper--short">
        <Line data={data} options={options} />
      </div>
    </section>
  );
}
