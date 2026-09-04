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
  dataset_type: "production" | "synthetic";
  generated_at?: string;
  last_updated_ist?: string;
  stale?: boolean;
}

export type CollectionMethod =
  | "api"
  | "tariff_sheet"
  | "scrape"
  | "simulated";

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
  average_fare: number;
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
  status: "available" | "fallback" | "degraded" | "failed";
  success_rate: number;
  last_check_utc: string;
  latency_ms: number;
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
}
