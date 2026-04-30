import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { DashboardAlertesPage } from "./pages/DashboardAlertesPage";
import { DashboardCapteursPage } from "./pages/DashboardCapteursPage";
import { DashboardCompteursPage } from "./pages/DashboardCompteursPage";
import { DashboardDetectionPage } from "./pages/DashboardDetectionPage";
import { DashboardPage } from "./pages/DashboardPage";
import { MapPage } from "./pages/MapPage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/dashboard/compteurs" element={<DashboardCompteursPage />} />
        <Route path="/dashboard/capteurs" element={<DashboardCapteursPage />} />
        <Route path="/dashboard/alertes" element={<DashboardAlertesPage />} />
        <Route path="/dashboard/detection" element={<DashboardDetectionPage />} />
        <Route path="/cartographie" element={<MapPage />} />
      </Routes>
    </AppLayout>
  );
}
