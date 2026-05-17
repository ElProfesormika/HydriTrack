import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";

import { DashboardHeader } from "../components/DashboardHeader";
import { EventList } from "../components/EventList";
import { InsightCard } from "../components/InsightCard";
import { KpiCard } from "../components/KpiCard";
import { MeterDeepDivePanel } from "../components/MeterDeepDivePanel";
import { MeterFlowChart } from "../components/MeterFlowChart";
import { Link } from "react-router-dom";
import { MetersTrendChart } from "../components/MetersTrendChart";
import { TopMetersBarChart } from "../components/TopMetersBarChart";
import { VariationChart } from "../components/VariationChart";
import { useRealtimeDashboard } from "../hooks/useRealtimeDashboard";

export function DashboardCompteursPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const deepDiveRef = useRef(null);
  const scrolledFromMapRef = useRef(false);
  const {
    overview,
    timeseries,
    meterFlowSeries,
    meterFlowPerMeter,
    anomalies,
    alerts,
    mapMeters,
    selectedMeterId,
    selectedMeterProfile,
    isConnected,
    error,
    refresh,
    setSelectedMeter,
  } = useRealtimeDashboard();
  const meter = overview?.meter_kpis || {};
  const topMeters = overview?.top_anomalous_meters || [];
  const meterOptions = (mapMeters || []).map((m) => m.meter_id).filter(Boolean);
  const meterFromUrl = searchParams.get("meter");

  useEffect(() => {
    if (!meterFromUrl || !meterOptions.length) return;
    if (!meterOptions.includes(meterFromUrl)) return;
    if (meterFromUrl !== selectedMeterId) {
      scrolledFromMapRef.current = false;
      setSelectedMeter(meterFromUrl);
    }
  }, [meterFromUrl, meterOptions, selectedMeterId, setSelectedMeter]);

  useEffect(() => {
    if (!meterFromUrl || !selectedMeterProfile || scrolledFromMapRef.current) return;
    if (selectedMeterId !== meterFromUrl) return;
    deepDiveRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    scrolledFromMapRef.current = true;
  }, [meterFromUrl, selectedMeterId, selectedMeterProfile]);

  function handleMeterChange(meterId) {
    setSelectedMeter(meterId);
    setSearchParams(meterId ? { meter: meterId } : {}, { replace: true });
  }

  return (
    <div className="page">
      <DashboardHeader
        title="Suivi compteurs"
        description="Pilotage detaille des debits, volumes et signaux de risque pour chaque compteur avec classification ML uniforme."
        isConnected={isConnected}
      />

      {error ? <p className="error-box">{error}</p> : null}

      <article className="card releves-promo-card">
        <h3>Saisie des releves</h3>
        <p className="map-caption">
          Ajoutez ou modifiez les releves manuels sur la page dediee (historique des 10 derniers enregistrements).
        </p>
        <Link to="/releves" className="btn-primary releves-promo-link">
          Ouvrir la page Releves
        </Link>
      </article>

      <section className="kpi-grid">
        <KpiCard title="Compteurs distincts" value={meter.distinct_meters || 0} subtitle="Identifiants actifs" />
        <KpiCard title="Points télémetrie" value={meter.total_points || 0} subtitle="Mesures enregistrées" />
        <KpiCard title="Débit moyen" value={Number(meter.avg_flow || 0).toFixed(2)} subtitle="Réseau" />
        <KpiCard title="Débit max observé" value={Number(meter.max_flow || 0).toFixed(2)} subtitle="Pic" />
        <KpiCard title="Volume cumulé" value={Number(meter.total_volume || 0).toFixed(2)} subtitle="m³" />
      </section>

      <section className="split-grid charts-two-debit">
        <MeterFlowChart series={meterFlowSeries} />
        <TopMetersBarChart items={topMeters} />
      </section>

      <MetersTrendChart buckets={meterFlowPerMeter?.buckets} series={meterFlowPerMeter?.series} />
      <div ref={deepDiveRef} id="suivi-detail-compteur" className="suivi-detail-anchor">
        <MeterDeepDivePanel
          meterId={selectedMeterId}
          meterOptions={meterOptions}
          profile={selectedMeterProfile}
          onChangeMeter={handleMeterChange}
        />
      </div>

      <VariationChart timeseries={timeseries} />

      <section className="split-grid">
        <EventList title="Dernières alertes (gravité codée)" items={alerts} mode="alerts" />
        <InsightCard title="Cohérence de detection ML">
          <p className="map-caption">
            Meme logique de classification pour tous les compteurs : IsolationForest (n=300), score d'anomalie et seuils
            de gravite en 4 niveaux.
          </p>
          <ul className="event-list event-list--compact">
            {anomalies.slice(0, 8).map((item, idx) => (
              <li key={`meter-anom-${idx}-${item.timestamp || "na"}`}>
                <strong>{item.meter_id || "N/A"}</strong>
                <p>
                  {new Date(item.timestamp).toLocaleString("fr-FR")} - score {Number(item.score || 0).toFixed(2)} /
                  fuite {Math.round(Number(item.leak_probability || 0) * 100)}%
                </p>
              </li>
            ))}
            {!anomalies.length ? <li>Aucune anomalie recente.</li> : null}
          </ul>
        </InsightCard>
      </section>
    </div>
  );
}
