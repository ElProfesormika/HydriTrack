import { useEffect } from "react";
import { useMap } from "react-leaflet";

/**
 * Ajuste le plan image sur tout le viewport Leaflet sans marge ni bandes vides ;
 * réagit au redimensionnement du cadre parent (aspect-ratio du site).
 */
export function PlanMapFitBounds({ bounds }) {
  const map = useMap();

  useEffect(() => {
    const fit = () => {
      map.invalidateSize(false);
      map.fitBounds(bounds, { animate: false, padding: [0, 0] });
    };

    fit();
    const pane = map.getContainer()?.closest(".map-panel-fill");
    const ro = pane ? new ResizeObserver(() => fit()) : null;
    if (pane && ro) ro.observe(pane);
    window.addEventListener("resize", fit);

    return () => {
      window.removeEventListener("resize", fit);
      if (ro) ro.disconnect();
    };
  }, [map, bounds]);

  return null;
}
