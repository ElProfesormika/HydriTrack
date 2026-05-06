function createPlanMap(config) {
  const map = L.map(config.mapId, {
    crs: L.CRS.Simple,
    minZoom: -3,
    maxZoom: 2,
    zoomSnap: 0.25,
  });

  const planImage = new Image();
  planImage.src = config.imageUrl;

  planImage.onload = () => {
    const width = planImage.naturalWidth;
    const height = planImage.naturalHeight;
    const bounds = [
      [0, 0],
      [height, width],
    ];

    L.imageOverlay(config.imageUrl, bounds).addTo(map);
    map.fitBounds(bounds);
    map.setMaxBounds(bounds);

    (config.markers || []).forEach((item) => {
      const marker = L.marker([item.y, item.x]).addTo(map);
      marker.bindPopup(`<strong>${item.nom}</strong><br/>x: ${item.x} | y: ${item.y}`);
    });
  };

  planImage.onerror = () => {
    const target = document.getElementById(config.mapId);
    if (!target) return;
    target.innerHTML =
      "<p style='padding:12px;color:#b71c1c'>Erreur de chargement du plan. Verifie le chemin de l'image.</p>";
  };
}
