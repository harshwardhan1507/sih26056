/**
 * Date and Timezone Formatter
 *
 * All backend and database timestamps are recorded in UTC (collected_at_utc).
 * The dashboard centrally converts and displays timestamps in Indian Standard Time (IST, UTC+5:30).
 *
 * Example:
 *   Input:  2026-09-04T12:02:00Z
 *   Output: 04 Sep 2026 · 17:32 IST
 */

export interface DateFormatOptions {
  format?: "full" | "date" | "time" | "short_date";
  fallback?: string;
}

export function formatUTCtoIST(
  utcIsoString: string | null | undefined,
  options: DateFormatOptions = {}
): string {
  const { format = "full", fallback = "—" } = options;

  if (!utcIsoString) {
    return fallback;
  }

  try {
    const d = new Date(utcIsoString);
    if (Number.isNaN(d.getTime())) {
      return fallback;
    }

    // Use Intl.DateTimeFormat with Asia/Kolkata timezone
    if (format === "date") {
      return new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
      }).format(d);
    }

    if (format === "short_date") {
      return new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
      }).format(d);
    }

    if (format === "time") {
      const timeStr = new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(d);
      return `${timeStr} IST`;
    }

    // Default "full": "04 Sep 2026 · 17:32 IST"
    const datePart = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(d);

    const timePart = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);

    return `${datePart} · ${timePart} IST`;
  } catch {
    return fallback;
  }
}

/**
 * Returns current timestamp formatted in IST for header displays.
 */
export function getCurrentISTHeaderDate(): string {
  return formatUTCtoIST(new Date().toISOString(), { format: "full" });
}
