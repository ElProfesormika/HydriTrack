/** Couleurs : normal (vert), vigilance (jaune), attention (orange), critique (rouge) */
export const RISK_COLORS = {
  normal: "#2e7d32",
  caution: "#f9a825",
  warning: "#ef6c00",
  critical: "#c62828",
};

export function pointColorFromLeak(probability) {
  const p = Number(probability) || 0;
  if (p >= 0.75) return RISK_COLORS.critical;
  if (p >= 0.5) return RISK_COLORS.warning;
  if (p >= 0.25) return RISK_COLORS.caution;
  return RISK_COLORS.normal;
}

export function barColorFromAvgScore(score) {
  const s = Number(score) || 0;
  if (s >= 0.85) return "rgba(198, 40, 40, 0.75)";
  if (s >= 0.65) return "rgba(239, 108, 0, 0.72)";
  if (s >= 0.45) return "rgba(249, 168, 37, 0.7)";
  return "rgba(46, 125, 50, 0.55)";
}
