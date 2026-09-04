/**
 * APIx Airfare Price Index — Frontend Domain Contracts
 *
 * Core architectural principles:
 * 1. Collection method != Quality flag
 *    - CollectionMethod specifies the ingestion channel (api, tariff_sheet, scrape, simulated).
 *    - QualityFlag specifies data hygiene condition (ok, outlier, sold_out, missing, imputed).
 * 2. Invariants on missing / sold-out fares:
 *    - quality_flag === 'sold_out' => total_fare_inr is null (NEVER 0.00).
 *    - quality_flag === 'missing'  => total_fare_inr is null (NEVER 0.00).
 *    - quality_flag === 'outlier'  => fare exists, but is excluded from elementary index.
 *    - quality_flag === 'imputed'  => total_fare_inr is populated, UI flags as imputed.
 * 3. Statistical values are provider data:
 *    - Index values, weights, deltas, and fares are dynamic provider outputs.
 *    - Frontend components MUST NOT hardcode authoritative constants.
 */

export interface DataContextMetadata {
  mode: "live" | "demo";
  /**
   * What the numbers actually are. "mixed" exists because a real collection
   * run blends observed tariff-sheet fares with simulated fallback for
   * carriers that publish no sheet — reporting that as "production" would
   * overstate it, and as "synthetic" would understate it.
   */
  dataset_type: "production" | "mixed" | "synthetic" | "unknown";
  /** Share of the underlying rows produced by the simulator. */
  simulated_percentage?: number;
  /** File the API read the rows from. */
  source_file?: string;
  generated_at?: string;
  last_updated_ist?: string;
  stale?: boolean;
}

/** Provenance block returned by every data-bearing API response. */
export interface DatasetProvenance {
  dataset_type: "production" | "mixed" | "synthetic";
  source_file: string;
  is_live_collection: boolean;
  total_quotes: number;
  observed_quotes: number;
  simulated_quotes: number;
  simulated_percentage: number;
  note: string;
}

export type CollectionMethod =
  | "api"
  | "tariff_sheet"
  | "scrape"
  | "historical_panel"
  | "simulated"
  | "imputed"
  | "unknown";

export type QualityFlag =
  | "ok"
  | "outlier"
  | "sold_out"
  | "missing"
  | "imputed";

export type ConnectionStatus =
  | "LIVE_CONNECTED"
  | "LOCAL_DEMO"
  | "API_UNAVAILABLE";

export type AdvanceWindow = "T+1" | "T+7" | "T+15" | "T+30" | "T+45";

export interface QuoteItem {
  id: string;
  collected_at_utc: string; // ISO 8601 UTC string (e.g. 2026-09-04T12:02:00Z)
  departure_date: string;   // YYYY-MM-DD
  advance_window_days: number;
  origin_iata: string;
  destination_iata: string;
  carrier_iata: string;
  fare_class: string;
  total_fare_inr: number | null; // null for sold_out / missing, NEVER 0.00
  source_id: string;
  collection_method: CollectionMethod;
  quality_flag: QualityFlag;
  quality_reason?: string; // e.g. "Sold out: No fare available at collection time"
  metadata?: DataContextMetadata;
}

export interface IndexSnapshot {
  date: string;
  value: number;
  change_pct: number;
  base: number;
  /** null when no route reported a fare; the UI shows a dash, never a guess. */
  average_fare: number | null;
  quotes: number;
  routes: number;
  quality_score: number;
  metadata: DataContextMetadata;
}

export interface IndexPoint {
  day: number;
  date: string;
  index_value: number | null; // null represents gaps / no valid observations
  change_pct?: number | null;
  quotes?: number;
  matched_quotes?: number;
}

export interface RouteSnapshot {
  route_id: string;
  origin: string;
  destination: string;
  origin_city: string;
  destination_city: string;
  weight: number; // Consumed dynamically from backend basket (sums to ~1.0)
  current_index: number | null;
  change_pct: number | null;
  average_fare: number | null;
  matched_observations?: number;
  coverage_status: "complete" | "partial" | "insufficient";
  sparkline: (number | null)[];
}

export interface CarrierFareItem {
  carrier: string;
  name: string;
  fare: number | null; // null = unavailable / outlier excluded
  change_pct: number | null;
  status: "available" | "unavailable" | "outlier_excluded";
}

export interface WindowDetail {
  available: boolean;
  average_fare: number | null;
  matched_observations: number;
  coverage_status: "complete" | "partial" | "insufficient";
  carriers: CarrierFareItem[];
  fare_history: { day: number; date: string; fare: number | null }[];
}

export interface RouteDetail extends RouteSnapshot {
  windows: Record<AdvanceWindow, WindowDetail>;
}

export interface CollectionRunRecord {
  run_id: string;
  date: string;
  total: number;
  valid: number;
  outliers: number;
  sold_out: number;
  simulated_count: number;
  status: "ok" | "warning";
}

export interface QualitySummary {
  total_quotes: number;
  score: number;
  ok_count: number;
  outlier_count: number;
  sold_out_count: number;
  missing_count: number;
  imputed_count: number;
  by_method: Record<CollectionMethod, number>;
  fallback_simulated_pct: number;
  collection_runs: CollectionRunRecord[];
  metadata: DataContextMetadata;
}

export interface SourceStatusItem {
  source_id: string;
  name: string;
  type: CollectionMethod;
  /**
   * "not_integrated" is the honest state for a source the project has no
   * adapter for. The live provider used to report TripJack and TBO as
   * "available" with invented success rates and latencies, while the
   * project's own outreach register recorded both as access-pending.
   */
  status: "active" | "fallback" | "degraded" | "failed" | "not_integrated";
  /** Quotes this source actually contributed to the served dataset. */
  quotes_contributed: number;
  /** Share of the served dataset, 0-100. */
  share_pct: number;
  last_check_utc: string;
  /**
   * Only present when genuinely measured. Absent means not measured — the
   * UI must render a dash, never a plausible-looking number.
   */
  success_rate?: number | null;
  latency_ms?: number | null;
  note?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp_utc: string;
}

export interface QuoteFilters {
  origin?: string;
  destination?: string;
  advance_window_days?: number;
  date_from?: string;
  date_to?: string;
  limit?: number;
}
