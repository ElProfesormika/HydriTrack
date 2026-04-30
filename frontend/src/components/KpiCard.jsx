export function KpiCard({ title, value, subtitle }) {
  return (
    <article className="card kpi-card">
      <h3>{title}</h3>
      <p className="kpi-value">{value}</p>
      {subtitle ? <small>{subtitle}</small> : null}
    </article>
  );
}
