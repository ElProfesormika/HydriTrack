import { Line } from "react-chartjs-2";

const chartText = "#0d47a1";
const chartGrid = "rgba(13, 71, 161, 0.12)";
const SERIES_PALETTE = [
  "#1565c0",
  "#2e7d32",
  "#6a1b9a",
  "#00838f",
  "#6d4c41",
  "#c62828",
  "#283593",
  "#f57f17",
  "#5d4037",
  "#ad1457",
  "#00695c",
  "#4527a0",
  "#e65100",
  "#827717",
  "#01579b",
  "#558b2f",
  "#4e342e",
  "#37474f",
  "#880e4f",
];

export function MetersTrendChart({
  buckets,
  series,
  title = "Débit par compteur (tous les compteurs configurés)",
}) {
  const safeBuckets = buckets?.length ? buckets : [];
  const labels = safeBuckets.map((b) =>
    new Date(b).toLocaleString("fr-FR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  );

  const safeSeries = series || [];
  const datasets = safeSeries.map((s, idx) => {
    const byBucket = {};
    (s.points || []).forEach((pt) => {
      byBucket[pt.bucket] = Number(pt.avg_flow || 0);
    });
    const color = SERIES_PALETTE[idx % SERIES_PALETTE.length];
    return {
      label: s.meter_id,
      data: safeBuckets.map((b) => byBucket[b] ?? 0),
      borderColor: color,
      backgroundColor: "transparent",
      borderWidth: 2,
      tension: 0.3,
      pointRadius: 0,
    };
  });

  const data = { labels, datasets };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: chartText, boxWidth: 12 },
      },
      tooltip: { mode: "index", intersect: false },
    },
    interaction: { mode: "nearest", axis: "x", intersect: false },
    scales: {
      x: { ticks: { color: chartText, maxRotation: 45 }, grid: { color: chartGrid } },
      y: { ticks: { color: chartText }, grid: { color: chartGrid }, beginAtZero: true },
    },
  };

  if (!safeSeries.length) {
    return (
      <section className="card chart-container">
        <h3>{title}</h3>
        <p className="empty-chart">Aucune donnée compteur pour tracer les courbes.</p>
      </section>
    );
  }

  return (
    <section className="card chart-container">
      <h3>{title}</h3>
      <div className="chart-wrapper chart-wrapper--multi-meters">
        <Line data={data} options={options} />
      </div>
    </section>
  );
}
