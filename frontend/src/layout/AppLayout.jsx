import { NavLink } from "react-router-dom";

export function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>HydroTrack</h1>
        <p>Surveillance reseau eau EDF-CNPE</p>
        <nav>
          <div className="nav-section-label">Tableaux de bord</div>
          <NavLink to="/dashboard" end className={({ isActive }) => (isActive ? "active" : "")}>
            Synthese
          </NavLink>
          <NavLink to="/dashboard/compteurs" className={({ isActive }) => (isActive ? "active" : "")}>
            Compteurs
          </NavLink>
          <NavLink to="/dashboard/capteurs" className={({ isActive }) => (isActive ? "active" : "")}>
            Capteurs pression
          </NavLink>
          <NavLink to="/dashboard/alertes" className={({ isActive }) => (isActive ? "active" : "")}>
            Alertes
          </NavLink>
          <NavLink to="/dashboard/detection" className={({ isActive }) => (isActive ? "active" : "")}>
            Detection ML
          </NavLink>
          <div className="nav-section-label">Cartographie</div>
          <NavLink to="/cartographie" className={({ isActive }) => (isActive ? "active" : "")}>
            Cartes reseau
          </NavLink>
        </nav>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
