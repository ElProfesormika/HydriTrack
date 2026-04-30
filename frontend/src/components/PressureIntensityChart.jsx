import { Line } from "react-chartjs-2";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

export function PressureIntensityChart({ series, title = "Evolution intensite / frequence (capteurs)" }) {
  const labels = (series || []).map((row) =>
    new Date(row.bucket).toLocaleString("fr-FR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  );
  const data = {
    labels,
    datasets: [
      {
        label: "Intensite moyenne",
        data: (series || []).map((r) => Number(r.avg_intensity || 0)),
        borderColor: "#0277bd",
        backgroundColor: "rgba(2, 119, 189, 0.08)",
        fill: true,
        tension: 0.35,
        yAxisID: "y",
      },
      {
        label: "Frequence moyenne",
        data: (series || []).map((r) => Number(r.avg_frequency || 0)),
        borderColor: "#3949ab",
        backgroundColor: "rgba(57, 73, 171, 0.06)",
        fill: true,
        tension: 0.35,
        yAxisID: "y1",
      },
    ],
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { labels: { color: chartText } },
    },
    scales: {
      x: { ticks: { color: chartText }, grid: { color: chartGrid } },
      y: {
        type: "linear",
        position: "left",
        ticks: { color: chartText },
        grid: { color: chartGrid },
        beginAtZero: true,
      },
      y1: {
        type: "linear",
        position: "right",
        ticks: { color: chartText },
        grid: { drawOnChartArea: false },
        beginAtZero: true,
      },
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
