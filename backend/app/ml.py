from __future__ import annotations

import math
import statistics
from collections import defaultdict, deque
from typing import Any

import numpy as np

try:
    from sklearn.ensemble import IsolationForest  # type: ignore
except Exception:  # pragma: no cover
    IsolationForest = None


class MeterAnomalyEngine:
    """Aligné sur `hydrotrack_modele_ia.py` :
    ``IsolationForest(n_estimators=300)`` sur ``log1p(débit)``,
    puis niveaux JAUNE / ORANGE / ROUGE à partir des quantiles du ``decision_function``
    par compteur (scores les plus faibles = le plus aberrant).

    Fallback : même logique robuste ``z-score`` si sklearn indisponible ou trop peu de points.
    """

    def __init__(self, window_size: int = 200, n_trees: int = 300) -> None:
        self.window_size = window_size
        self.n_trees = n_trees
        self.values: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=self.window_size))
        self.decisions: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=self.window_size))
        self.models: dict[str, Any] = {}

    @staticmethod
    def _pct(data: list[float], p: float) -> float:
        if not data:
            return 0.0
        arr = np.asarray(data, dtype=np.float64)
        return float(np.quantile(arr, p))

    def score(self, meter_id: str, flow_rate: float) -> tuple[float, float]:
        series = self.values[meter_id]
        value = math.log1p(max(flow_rate, 0.0))
        series.append(value)

        if len(series) < 8:
            return 0.0, 0.0

        if IsolationForest is None or len(series) < 18:
            return self._score_with_zscore(value, list(series))

        model = self.models.get(meter_id)
        if model is None:
            model = IsolationForest(n_estimators=self.n_trees, contamination="auto", random_state=42)
            self.models[meter_id] = model

        x_data = [[item] for item in series]
        model.fit(x_data)
        raw_decision = float(model.decision_function([[value]])[0])

        history_snap = list(self.decisions[meter_id])
        calibrated_scores = history_snap + [raw_decision]
        self.decisions[meter_id].append(raw_decision)

        if len(calibrated_scores) >= 24:
            q10 = self._pct(calibrated_scores, 0.10)
            q03 = self._pct(calibrated_scores, 0.03)
            q01 = self._pct(calibrated_scores, 0.01)
            eps = max((max(calibrated_scores) - min(calibrated_scores)) * 1e-6, 1e-9)

            if raw_decision < q01 - eps / 100:
                leak_probability = min(1.0, 0.92 + min(0.07, -(raw_decision - q01) / max(eps * 120, 2e-3)))
            elif raw_decision < q03 - eps / 100:
                leak_probability = 0.70
            elif raw_decision < q10:
                leak_probability = 0.36
            else:
                leak_probability = 0.06

            anomaly_score = max(0.0, min(100.0, leak_probability * 100.0))
        else:
            anomaly_score, leak_probability = self._decision_fallback(raw_decision)

        return anomaly_score, leak_probability

    @staticmethod
    def _score_with_zscore(value: float, dataset: list[float]) -> tuple[float, float]:
        center = statistics.mean(dataset)
        sigma = statistics.pstdev(dataset) if len(dataset) > 1 else 1e-9
        sigma = sigma or 1e-9
        zscore = abs((value - center) / sigma)
        anomaly_score = max(0.0, min(100.0, (zscore / 4.0) * 100.0))
        leak_probability = min(1.0, anomaly_score / 100.0)
        return anomaly_score, leak_probability

    @staticmethod
    def _decision_fallback(decision: float) -> tuple[float, float]:
        anomaly_score = max(0.0, min(100.0, (0.2 - decision) * 250))
        leak_probability = min(1.0, anomaly_score / 100.0 + 1e-4)
        return anomaly_score, leak_probability
