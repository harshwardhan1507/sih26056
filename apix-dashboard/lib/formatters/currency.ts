/**
 * Indian Rupee (INR) Currency Formatter
 *
 * Formats numeric values into Indian numbering format with rupee symbol.
 * Handles null / undefined gracefully (returning '—') to ensure sold-out
 * and missing values are NEVER rendered as ₹0.00.
 */

export interface CurrencyFormatOptions {
  fallback?: string;
  fractionDigits?: number;
}

export function formatINR(
  val: number | null | undefined,
  options: CurrencyFormatOptions = {}
): string {
  const { fallback = "—", fractionDigits = 0 } = options;

  if (val === null || val === undefined || Number.isNaN(val)) {
    return fallback;
  }

  // Use en-IN locale for Indian comma placement (lakhs/crores)
  const formatted = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  }).format(val);

  return `₹${formatted}`;
}
