export function DashboardHeader({ title, description, isConnected, onlineLabel = "Flux temps reel", offlineLabel = "Hors ligne" }) {
  return (
    <header className="page-header">
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div className={`connection-pill ${isConnected ? "online" : "offline"}`}>
        {isConnected ? onlineLabel : offlineLabel}
      </div>
    </header>
  );
}
