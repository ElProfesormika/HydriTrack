import { Line } from "react-chartjs-2";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

export function MeterFlowChart({ series, title = "Evolution du debit moyen (compteurs)" }) {
  const labels = (series || []).map((row) =>
    new Date(row.bucket).toLocaleString("fr-FR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  );
  const data = {
    labels,
    datasets: [
      {
        label: "Debit moyen",
        data: (series || []).map((r) => Number(r.avg_flow || 0)),
        borderColor: "#0d47a1",
        backgroundColor: "rgba(13, 71, 161, 0.08)",
        fill: true,
        tension: 0.35,
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
      x: { ticks: { color: chartText }, grid: { color: chartGrid } },
      y: { ticks: { color: chartText }, grid: { color: chartGrid }, beginAtZero: true },
    },
  };

  return (
    <section className="card chart-container">
      <h3>{title}</h3>
      <div className="chart-wrapper chart-wrapper--short">
        <Line data={data} options={options} />
      </div>
    </section>
  );
}
