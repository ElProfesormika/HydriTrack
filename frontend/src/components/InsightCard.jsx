export function InsightCard({ title, children }) {
  return (
    <article className="card insight-card">
      <h3>{title}</h3>
      <div className="insight-card-content">{children}</div>
    </article>
  );
}
