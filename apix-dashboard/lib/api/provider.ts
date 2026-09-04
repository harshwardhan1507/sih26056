/**
 * APIx Airfare Price Index — Data Provider Contract
 *
 * Implemented by:
 * 1. FixtureDataProvider: 100% offline fallback / demonstration engine
 * 2. FastApiProvider: Live HTTP client connecting to FastAPI backend
 */

import {
  HealthStatus,
  IndexPoint,
  IndexSnapshot,
  QualitySummary,
  QuoteFilters,
  QuoteItem,
  RouteDetail,
  RouteSnapshot,
  SourceStatusItem,
} from "./types";

export interface ApiXDataProvider {
  /**
   * Health check / liveness probe.
   */
  getHealth(): Promise<HealthStatus>;

  /**
   * Latest aggregate index snapshot (headline index, delta, average fare, data mode).
   */
  getIndex(): Promise<IndexSnapshot>;

  /**
   * Historical aggregate chained Laspeyres index points.
   * @param days Optional timeframe filter (e.g. 7, 30, 90). Defaults to all available.
   */
  getIndexHistory(days?: number): Promise<IndexPoint[]>;

  /**
   * Authoritative DGCA-weighted domestic route basket.
   */
  getRoutes(): Promise<RouteSnapshot[]>;

  /**
   * Per-route detailed breakdown across T+1..T+45 horizons, carrier fares, and decay curves.
   * @param routeId Canonical route identifier (e.g. 'DEL-BOM')
   */
  getRouteDetail(routeId: string): Promise<RouteDetail | null>;

  /**
   * Filterable quote observations with provenance and quality flags.
   */
  getQuotes(filters?: QuoteFilters): Promise<QuoteItem[]>;

  /**
   * Data quality and hygiene metrics (score, ok/outlier/sold-out/imputed breakdown, runs).
   */
  getQuality(): Promise<QualitySummary>;

  /**
   * Multi-tier data source telemetry and health matrix.
   */
  getSources(): Promise<SourceStatusItem[]>;
}
