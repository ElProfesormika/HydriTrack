from __future__ import annotations

import math
from collections import defaultdict, deque
from statistics import mean, pstdev
from typing import Any

try:
    from sklearn.ensemble import IsolationForest  # type: ignore
except Exception:  # pragma: no cover
    IsolationForest = None


class MeterAnomalyEngine:
    """Hybrid scorer inspired by hydrotrack_modele_ia.py.

    - Uses IsolationForest when available and enough points are present.
    - Falls back to a robust z-score strategy otherwise.
    """

    def __init__(self, window_size: int = 120) -> None:
        self.window_size = window_size
        self.values: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )
        self.models: dict[str, Any] = {}

    def score(self, meter_id: str, flow_rate: float) -> tuple[float, float]:
        series = self.values[meter_id]
        value = math.log1p(max(flow_rate, 0.0))
        series.append(value)

        if len(series) < 8:
            return 0.0, 0.0

        if IsolationForest is not None and len(series) >= 25:
            return self._score_with_isolation_forest(meter_id, value, list(series))
        return self._score_with_zscore(value, list(series))

    def _score_with_isolation_forest(
        self, meter_id: str, value: float, dataset: list[float]
    ) -> tuple[float, float]:
        model = self.models.get(meter_id)
        if model is None:
            model = IsolationForest(n_estimators=200, random_state=42)
            self.models[meter_id] = model

        x_data = [[item] for item in dataset]
        model.fit(x_data)
        decision = float(model.decision_function([[value]])[0])

        # Convert decision function to a 0..100 severity score.
        anomaly_score = max(0.0, min(100.0, (0.2 - decision) * 250))
        leak_probability = min(1.0, anomaly_score / 100.0)
        return anomaly_score, leak_probability

    @staticmethod
    def _score_with_zscore(value: float, dataset: list[float]) -> tuple[float, float]:
        center = mean(dataset)
        sigma = pstdev(dataset) or 1e-9
        zscore = abs((value - center) / sigma)
        anomaly_score = max(0.0, min(100.0, (zscore / 4.0) * 100.0))
        leak_probability = min(1.0, anomaly_score / 100.0)
        return anomaly_score, leak_probability
