/**
 * APIx Airfare Price Index — Offline Fixture Data Provider
 *
 * Implements 100% offline demonstration engine.
 * Serves authentic statistical fixtures matching upstream backend models.
 * Zero external network dependencies.
 */

import { ApiXDataProvider } from "./provider";
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

import indexSummaryFixture from "@/data/fixtures/index-summary.json";
import indexHistoryFixture from "@/data/fixtures/index-history.json";
import routesFixture from "@/data/fixtures/routes.json";
import routeDetailsFixture from "@/data/fixtures/route-details.json";
import quotesFixture from "@/data/fixtures/quotes.json";
import qualityFixture from "@/data/fixtures/quality.json";
import sourcesFixture from "@/data/fixtures/sources.json";

export class FixtureDataProvider implements ApiXDataProvider {
  async getHealth(): Promise<HealthStatus> {
    return {
      status: "ok",
      version: "1.0.0-demo",
      timestamp_utc: new Date().toISOString(),
    };
  }

  async getIndex(): Promise<IndexSnapshot> {
    return indexSummaryFixture as IndexSnapshot;
  }

  async getIndexHistory(days?: number): Promise<IndexPoint[]> {
    const raw = indexHistoryFixture as IndexPoint[];
    if (!days || days <= 0) {
      return raw;
    }
    // Return last N days
    return raw.slice(-days);
  }

  async getRoutes(): Promise<RouteSnapshot[]> {
    return routesFixture as RouteSnapshot[];
  }

  async getRouteDetail(routeId: string): Promise<RouteDetail | null> {
    const canonical = routeId.trim().toUpperCase();
    const detailsMap = routeDetailsFixture as Record<string, RouteDetail>;

    if (detailsMap[canonical]) {
      return detailsMap[canonical];
    }

    // Fallback: Check if route exists in routes.json, synthesize standard window detail
    const route = (routesFixture as RouteSnapshot[]).find(
      (r) => r.route_id === canonical
    );
    if (!route) {
      return null;
    }

    // Return synthesized detail based on base route attributes
    const baseFare = route.average_fare || 6500;
    return {
      ...route,
      windows: {
        "T+1": {
          available: true,
          average_fare: Math.round(baseFare * 1.35),
          matched_observations: route.matched_observations || 30,
          coverage_status: route.coverage_status,
          carriers: [
            { carrier: "6E", name: "IndiGo", fare: Math.round(baseFare * 1.32), change_pct: 4.2, status: "available" },
            { carrier: "AI", name: "Air India", fare: Math.round(baseFare * 1.38), change_pct: 5.0, status: "available" },
          ],
          fare_history: [
            { day: 0, date: "2026-08-05", fare: Math.round(baseFare * 1.25) },
            { day: 30, date: "2026-09-04", fare: Math.round(baseFare * 1.35) },
          ],
        },
        "T+7": {
          available: true,
          average_fare: baseFare,
          matched_observations: route.matched_observations || 30,
          coverage_status: route.coverage_status,
          carriers: [
            { carrier: "6E", name: "IndiGo", fare: Math.round(baseFare * 0.98), change_pct: 2.1, status: "available" },
            { carrier: "AI", name: "Air India", fare: Math.round(baseFare * 1.02), change_pct: 2.8, status: "available" },
          ],
          fare_history: [
            { day: 0, date: "2026-08-05", fare: Math.round(baseFare * 0.95) },
            { day: 30, date: "2026-09-04", fare: baseFare },
          ],
        },
        "T+15": {
          available: true,
          average_fare: Math.round(baseFare * 0.88),
          matched_observations: route.matched_observations || 28,
          coverage_status: route.coverage_status,
          carriers: [
            { carrier: "6E", name: "IndiGo", fare: Math.round(baseFare * 0.87), change_pct: 1.2, status: "available" },
            { carrier: "AI", name: "Air India", fare: Math.round(baseFare * 0.89), change_pct: 1.5, status: "available" },
          ],
          fare_history: [
            { day: 0, date: "2026-08-05", fare: Math.round(baseFare * 0.86) },
            { day: 30, date: "2026-09-04", fare: Math.round(baseFare * 0.88) },
          ],
        },
        "T+30": {
          available: true,
          average_fare: Math.round(baseFare * 0.76),
          matched_observations: route.matched_observations || 25,
          coverage_status: route.coverage_status,
          carriers: [
            { carrier: "6E", name: "IndiGo", fare: Math.round(baseFare * 0.75), change_pct: 0.5, status: "available" },
            { carrier: "AI", name: "Air India", fare: Math.round(baseFare * 0.77), change_pct: 0.8, status: "available" },
          ],
          fare_history: [
            { day: 0, date: "2026-08-05", fare: Math.round(baseFare * 0.75) },
            { day: 30, date: "2026-09-04", fare: Math.round(baseFare * 0.76) },
          ],
        },
        "T+45": {
          available: true,
          average_fare: Math.round(baseFare * 0.68),
          matched_observations: route.matched_observations || 24,
          coverage_status: route.coverage_status,
          carriers: [
            { carrier: "6E", name: "IndiGo", fare: Math.round(baseFare * 0.67), change_pct: 0.2, status: "available" },
            { carrier: "AI", name: "Air India", fare: Math.round(baseFare * 0.69), change_pct: 0.4, status: "available" },
          ],
          fare_history: [
            { day: 0, date: "2026-08-05", fare: Math.round(baseFare * 0.67) },
            { day: 30, date: "2026-09-04", fare: Math.round(baseFare * 0.68) },
          ],
        },
      },
    };
  }

  async getQuotes(filters?: QuoteFilters): Promise<QuoteItem[]> {
    let quotes = quotesFixture as QuoteItem[];

    if (!filters) {
      return quotes;
    }

    if (filters.origin) {
      const orig = filters.origin.toUpperCase();
      quotes = quotes.filter((q) => q.origin_iata === orig);
    }

    if (filters.destination) {
      const dest = filters.destination.toUpperCase();
      quotes = quotes.filter((q) => q.destination_iata === dest);
    }

    if (filters.advance_window_days !== undefined) {
      quotes = quotes.filter(
        (q) => q.advance_window_days === filters.advance_window_days
      );
    }

    if (filters.date_from) {
      quotes = quotes.filter((q) => q.departure_date >= filters.date_from!);
    }

    if (filters.date_to) {
      quotes = quotes.filter((q) => q.departure_date <= filters.date_to!);
    }

    return quotes;
  }

  async getQuality(): Promise<QualitySummary> {
    return qualityFixture as QualitySummary;
  }

  async getSources(): Promise<SourceStatusItem[]> {
    return sourcesFixture as SourceStatusItem[];
  }
}

/**
 * Singleton instance for offline demo usage.
 */
export const fixtureProvider = new FixtureDataProvider();
