/**
 * Percentage Formatter
 *
 * Formats numerical rate of change into signed percentage representations.
 * Handles null / undefined gracefully (returning '—').
 */

export interface PercentageFormatOptions {
  fallback?: string;
  decimals?: number;
  showSign?: boolean;
}

export function formatPercent(
  val: number | null | undefined,
  options: PercentageFormatOptions = {}
): string {
  const { fallback = "—", decimals = 1, showSign = true } = options;

  if (val === null || val === undefined || Number.isNaN(val)) {
    return fallback;
  }

  const fixed = Math.abs(val).toFixed(decimals);

  if (val > 0) {
    return showSign ? `+${fixed}%` : `${fixed}%`;
  }
  if (val < 0) {
    return `-${fixed}%`;
  }
  return `0.0%`;
}

export function getMovementPolarity(
  val: number | null | undefined
): "positive" | "negative" | "neutral" {
  if (val === null || val === undefined || Number.isNaN(val) || val === 0) {
    return "neutral";
  }
  return val > 0 ? "positive" : "negative";
}
