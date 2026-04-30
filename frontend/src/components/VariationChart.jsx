import { Line } from "react-chartjs-2";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";

export function VariationChart({ timeseries }) {
  const labels = timeseries.map((item) =>
    new Date(item.bucket).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
  );
  const chartData = {
    labels,
    datasets: [
      {
        label: "Anomalies",
        data: timeseries.map((item) => item.anomalies),
        borderColor: "#1565c0",
        backgroundColor: "rgba(21, 101, 192, 0.12)",
        fill: true,
        tension: 0.35,
      },
      {
        label: "Alertes",
        data: timeseries.map((item) => item.alerts),
        borderColor: "#0277bd",
        backgroundColor: "rgba(2, 119, 189, 0.1)",
        fill: true,
        tension: 0.35,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: chartText, font: { size: 12 } } },
    },
    scales: {
      x: {
        ticks: { color: chartText },
        grid: { color: chartGrid },
      },
      y: {
        ticks: { color: chartText },
        grid: { color: chartGrid },
        beginAtZero: true,
      },
    },
  };

  return (
    <section className="card chart-container">
      <h3>Courbes de variation (anomalies & alertes)</h3>
      <div className="chart-wrapper">
        <Line data={chartData} options={options} />
      </div>
    </section>
  );
}
