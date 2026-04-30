function formatDate(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("fr-FR");
}

export function EventList({ title, items, mode }) {
  return (
    <section className="card">
      <h3>{title}</h3>
      <ul className="event-list">
        {items.length === 0 ? <li>Aucune donnee disponible.</li> : null}
        {items.map((item, idx) => (
          <li key={`${mode}-${idx}-${item.timestamp || "na"}`}>
            {mode === "alerts" ? (
              <>
                <span className={`tag ${item.severity || "info"}`}>{item.severity || "info"}</span>
                <strong> {item.source_id}</strong>
                <p>{formatDate(item.timestamp)} - {item.message}</p>
              </>
            ) : (
              <>
                <strong>{item.meter_id}</strong>
                <p>
                  {formatDate(item.timestamp)} - score {Number(item.score || 0).toFixed(2)} /
                  fuite {Math.round((item.leak_probability || 0) * 100)}%
                </p>
              </>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
