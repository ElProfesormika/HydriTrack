import { Doughnut } from "react-chartjs-2";

const palette = {
  normal: "#2e7d32",
  nominal: "#2e7d32",
  info: "#2e7d32",
  caution: "#f9a825",
  warning: "#ef6c00",
  critical: "#c62828",
};

export function AlertSeverityChart({ bySeverity, title = "Repartition des alertes par gravite" }) {
  const rows = bySeverity || [];
  const labels = rows.map((r) => r.severity || "inconnu");
  const values = rows.map((r) => Number(r.count || 0));
  const total = values.reduce((a, b) => a + b, 0);
  const colors = labels.map((s) => palette[s] || "#3949ab");

  if (!total) {
    return (
      <section className="card chart-container">
        <h3>{title}</h3>
        <p className="empty-chart">Aucune alerte enregistree pour le moment.</p>
      </section>
    );
  }

  const data = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: colors,
        borderColor: "#ffffff",
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: { color: "#0d47a1", padding: 12 },
      },
    },
  };

  return (
    <section className="card chart-container">
      <h3>{title}</h3>
      <div className="chart-wrapper chart-wrapper--doughnut">
        <Doughnut data={data} options={options} />
      </div>
    </section>
  );
}
