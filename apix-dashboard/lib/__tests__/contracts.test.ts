/**
 * Phase 0 Architecture Contract & Formatter Verification
 */

import { formatINR } from "../formatters/currency";
import { formatPercent, getMovementPolarity } from "../formatters/percentage";
import { formatUTCtoIST } from "../formatters/dates";
import { config } from "../config";
import type {
  DataContextMetadata,
  QuoteItem,
  IndexSnapshot,
  RouteSnapshot,
} from "../api/types";

export function runContractVerifications(): boolean {
  // 1. Currency Formatter Verification
  if (formatINR(6842) !== "₹6,842") {
    throw new Error(`formatINR(6842) failed: got ${formatINR(6842)}`);
  }
  if (formatINR(null) !== "—") {
    throw new Error(`formatINR(null) must return fallback '—': got ${formatINR(null)}`);
  }
  if (formatINR(undefined) !== "—") {
    throw new Error(`formatINR(undefined) must return fallback '—'`);
  }

  // 2. Percentage Formatter Verification
  if (formatPercent(2.4) !== "+2.4%") {
    throw new Error(`formatPercent(2.4) failed: got ${formatPercent(2.4)}`);
  }
  if (formatPercent(-1.8) !== "-1.8%") {
    throw new Error(`formatPercent(-1.8) failed: got ${formatPercent(-1.8)}`);
  }
  if (formatPercent(0) !== "0.0%") {
    throw new Error(`formatPercent(0) failed: got ${formatPercent(0)}`);
  }
  if (formatPercent(null) !== "—") {
    throw new Error(`formatPercent(null) failed: got ${formatPercent(null)}`);
  }
  if (getMovementPolarity(2.4) !== "positive" || getMovementPolarity(-1.8) !== "negative") {
    throw new Error(`getMovementPolarity failed`);
  }

  // 3. Date & Timezone Formatter Verification (UTC -> IST)
  const formattedIst = formatUTCtoIST("2026-09-04T12:02:00Z");
  if (!formattedIst.includes("IST") || !formattedIst.includes("2026")) {
    throw new Error(`formatUTCtoIST failed: got ${formattedIst}`);
  }
  if (formatUTCtoIST(null) !== "—") {
    throw new Error(`formatUTCtoIST(null) failed`);
  }

  // 4. Config verification
  if (typeof config.isLiveApiConfigured() !== "boolean") {
    throw new Error("config.isLiveApiConfigured() must return boolean");
  }

  // 5. Types & Invariants Verification
  const meta: DataContextMetadata = {
    mode: "demo",
    dataset_type: "synthetic",
    generated_at: "2026-09-04T12:00:00Z",
    last_updated_ist: "04 Sep 2026 · 17:30 IST",
    stale: false,
  };

  const soldOutQuote: QuoteItem = {
    id: "Q-TEST-01",
    collected_at_utc: "2026-09-04T12:00:00Z",
    departure_date: "2026-09-05",
    advance_window_days: 1,
    origin_iata: "DEL",
    destination_iata: "BOM",
    carrier_iata: "6E",
    fare_class: "Economy",
    total_fare_inr: null, // Invariant: null for sold_out
    source_id: "test_adapter",
    collection_method: "api",
    quality_flag: "sold_out",
    quality_reason: "Sold out: No fare available at collection time",
    metadata: meta,
  };

  const validQuote: QuoteItem = {
    id: "Q-TEST-02",
    collected_at_utc: "2026-09-04T12:00:00Z",
    departure_date: "2026-09-11",
    advance_window_days: 7,
    origin_iata: "DEL",
    destination_iata: "BOM",
    carrier_iata: "AI",
    fare_class: "Economy",
    total_fare_inr: 6842,
    source_id: "test_adapter",
    collection_method: "tariff_sheet",
    quality_flag: "ok",
    metadata: meta,
  };

  const sampleSnapshot: IndexSnapshot = {
    date: "2026-09-04",
    value: 103.7,
    change_pct: 2.4,
    base: 100.0,
    average_fare: 6842,
    quotes: 300,
    routes: 12,
    quality_score: 96.8,
    metadata: meta,
  };

  const sampleRoute: RouteSnapshot = {
    route_id: "DEL-BOM",
    origin: "DEL",
    destination: "BOM",
    origin_city: "Delhi",
    destination_city: "Mumbai",
    weight: 0.192,
    current_index: 108.4,
    change_pct: 8.2,
    average_fare: 9420,
    coverage_status: "complete",
    sparkline: [100.0, 102.1, 108.4],
  };

  return Boolean(soldOutQuote && validQuote && sampleSnapshot && sampleRoute);
}
