/**
 * APIx Airfare Price Index — Live FastAPI Data Provider
 *
 * Connects to the upstream FastAPI service (default: http://localhost:8000).
 *
 * PROVENANCE RULE
 * ---------------
 * Every value this provider returns either comes from the API or is null.
 * It does not fill gaps with plausible-looking constants.
 *
 * This file previously did exactly that: it reported TripJack and TBO as
 * healthy APIs with invented success rates and latencies (the project has no
 * access to either), returned the same hardcoded index, change, fare and
 * sparkline for all twelve routes, substituted a magic INR 6,842 average fare,
 * and stamped `dataset_type: "production"` onto data the API itself reported
 * as 100% simulated.
 */

import { ApiXDataProvider } from "./provider";
import {
  CarrierFareItem,
  CollectionMethod,
  DataContextMetadata,
  DatasetProvenance,
  HealthStatus,
  IndexPoint,
  IndexSnapshot,
  QualityFlag,
  QualitySummary,
  QuoteFilters,
  QuoteItem,
  RouteDetail,
  RouteSnapshot,
  SourceStatusItem,
  AdvanceWindow,
  WindowDetail,
} from "./types";
import { config } from "../config";
import { formatUTCtoIST } from "../formatters/dates";

/** Provenance block returned by every data-bearing API response. */
type ApiProvenance = DatasetProvenance;

interface ApiQuote {
  collected_at_utc: string;
  observation_date: string;
  departure_date: string;
  advance_window_days: number;
  origin_iata: string;
  destination_iata: string;
  carrier_iata: string;
  fare_class: string;
  total_fare_inr: number | null;
  source_id: string;
  collection_method: string;
  quality_flag: string;
}

interface ApiRouteSummary {
  route_id: string;
  origin: string;
  destination: string;
  weight: number;
  current_index: number | null;
  change_pct: number | null;
  average_fare: number | null;
  matched_observations: number;
  coverage_status: "complete" | "partial" | "insufficient";
  series_length: number;
  sparkline: number[];
}

const CITY_NAMES: Record<string, string> = {
  DEL: "Delhi",
  BOM: "Mumbai",
  BLR: "Bengaluru",
  CCU: "Kolkata",
  MAA: "Chennai",
  HYD: "Hyderabad",
  GOI: "Goa",
};

const CARRIER_NAMES: Record<string, string> = {
  "6E": "IndiGo",
  AI: "Air India",
  QP: "Akasa Air",
  SG: "SpiceJet",
  IX: "Air India Express",
  UK: "Vistara",
  I5: "AirAsia",
  G8: "GO FIRST",
};

/** Display names for adapters that actually produce rows. */
const SOURCE_NAMES: Record<string, string> = {
  indigo_tariff_v1: "IndiGo Tariff Sheet (DGCA Rule 135)",
  air_india_tariff_v1: "Air India Tariff Sheet (DGCA Rule 135)",
  akasa_tariff_v1: "Akasa Air Tariff Sheet (DGCA Rule 135)",
  har_replay_ota_v1: "OTA HAR Replay",
  kaggle_easemytrip_v1: "EaseMyTrip Historical Panel",
  simulated_v1: "Simulated Fallback Engine",
};

const SOURCE_METHODS: Record<string, CollectionMethod> = {
  indigo_tariff_v1: "tariff_sheet",
  air_india_tariff_v1: "tariff_sheet",
  akasa_tariff_v1: "tariff_sheet",
  har_replay_ota_v1: "scrape",
  kaggle_easemytrip_v1: "historical_panel",
  simulated_v1: "simulated",
};

/**
 * Tier 1 commercial APIs the architecture reserves a slot for but which the
 * project has NO access to. Listed so the source matrix stays complete, always
 * as "not_integrated" with no invented metrics. See
 * docs/data-sources/COMMERCIAL_API_OUTREACH.md.
 */
const NOT_INTEGRATED_SOURCES: SourceStatusItem[] = [
  {
    source_id: "tripjack_api",
    name: "TripJack B2B API",
    type: "api",
    status: "not_integrated",
    quotes_contributed: 0,
    share_pct: 0,
    last_check_utc: "",
    success_rate: null,
    latency_ms: null,
    note: "Tier 1 slot. Access request pending; no adapter implemented.",
  },
  {
    source_id: "tbo_air_api",
    name: "TBO Air API",
    type: "api",
    status: "not_integrated",
    quotes_contributed: 0,
    share_pct: 0,
    last_check_utc: "",
    success_rate: null,
    latency_ms: null,
    note: "Tier 1 slot. Access request pending; no adapter implemented.",
  },
];

function toMetadata(p: ApiProvenance | undefined): DataContextMetadata {
  return {
    mode: "live",
    dataset_type: p?.dataset_type ?? "unknown",
    simulated_percentage: p?.simulated_percentage,
    source_file: p?.source_file,
    generated_at: new Date().toISOString(),
    last_updated_ist: formatUTCtoIST(new Date().toISOString()),
    stale: false,
  };
}

export class FastApiProvider implements ApiXDataProvider {
  private getBaseUrl(): string {
    const url = config.getEffectiveApiBaseUrl();
    if (!url) {
      throw new Error("FastAPI URL not configured in NEXT_PUBLIC_API_BASE_URL");
    }
    return url;
  }

  private async fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const baseUrl = this.getBaseUrl();
    const url = `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

    const res = await fetch(url, {
      ...options,
      headers: { Accept: "application/json", ...options?.headers },
    });

    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`API error (${res.status} ${res.statusText}): ${errText || endpoint}`);
    }

    return res.json() as Promise<T>;
  }

  async getHealth(): Promise<HealthStatus> {
    return this.fetchJson<HealthStatus>("/health");
  }

  async getIndex(): Promise<IndexSnapshot> {
    const [aggRes, quality, routeSummary] = await Promise.all([
      this.fetchJson<{
        base_value: number;
        series_length: number;
        methodology: string;
        dataset_type: string;
        series: { day: number; date: string | null; index_value: number; change_pct: number | null }[];
      }>("/index/aggregate"),
      this.getQuality(),
      this.fetchJson<{ count: number; provenance: ApiProvenance; routes: ApiRouteSummary[] }>(
        "/routes/summary",
      ),
    ]);

    const series = aggRes.series || [];
    const latest = series.length > 0 ? series[series.length - 1] : null;
    const prev = series.length > 1 ? series[series.length - 2] : null;

    const changePct =
      latest && prev && prev.index_value > 0
        ? Number((((latest.index_value - prev.index_value) / prev.index_value) * 100).toFixed(2))
        : 0;

    // Average fare across routes that actually reported one. No fallback
    // constant: if nothing reported, the value is null and the UI shows a dash.
    const routeFares = (routeSummary.routes || [])
      .map((r) => r.average_fare)
      .filter((f): f is number => f !== null && f > 0);
    const avgFare =
      routeFares.length > 0
        ? Math.round(routeFares.reduce((a, b) => a + b, 0) / routeFares.length)
        : null;

    return {
      // The series' own last date, not today's. Attaching today's date to a
      // series whose newest point is weeks old misrepresents freshness.
      date: latest?.date ?? "",
      value: latest?.index_value ?? 100.0,
      change_pct: changePct,
      base: aggRes.base_value ?? 100.0,
      average_fare: avgFare,
      quotes: quality.total_quotes,
      routes: routeSummary.count,
      quality_score: quality.score,
      metadata: {
        ...toMetadata(routeSummary.provenance),
        // The aggregate series carries its own provenance label, which can
        // differ from the quote dataset's (the series is a batch artifact).
        dataset_type:
          aggRes.dataset_type === "simulated"
            ? "synthetic"
            : routeSummary.provenance?.dataset_type ?? "unknown",
      },
    };
  }

  async getIndexHistory(days?: number): Promise<IndexPoint[]> {
    const aggRes = await this.fetchJson<{
      series: { day: number; date: string | null; index_value: number; change_pct: number | null }[];
    }>("/index/aggregate");

    const rawSeries = aggRes.series || [];
    const limit = days && days > 0 ? days : rawSeries.length;

    return rawSeries.slice(-limit).map((item) => ({
      day: item.day,
      // Real calendar date from the series. These used to be back-computed
      // from today, so the chart's x-axis was fiction.
      date: item.date ?? "",
      index_value: item.index_value,
      change_pct: item.change_pct,
    }));
  }

  async getRoutes(): Promise<RouteSnapshot[]> {
    const res = await this.fetchJson<{
      count: number;
      provenance: ApiProvenance;
      routes: ApiRouteSummary[];
    }>("/routes/summary");

    return (res.routes || []).map((r) => ({
      route_id: r.route_id,
      origin: r.origin,
      destination: r.destination,
      origin_city: CITY_NAMES[r.origin] || r.origin,
      destination_city: CITY_NAMES[r.destination] || r.destination,
      weight: r.weight,
      current_index: r.current_index,
      change_pct: r.change_pct,
      average_fare: r.average_fare,
      matched_observations: r.matched_observations,
      coverage_status: r.coverage_status,
      sparkline: r.sparkline ?? [],
    }));
  }

  async getRouteDetail(routeId: string): Promise<RouteDetail | null> {
    const canonical = routeId.trim().toUpperCase();
    const [orig, dest] = canonical.split("-");
    if (!orig || !dest) return null;

    const routes = await this.getRoutes();
    const route = routes.find((r) => r.route_id === canonical);
    if (!route) return null;

    const windowDefinitions: { tag: AdvanceWindow; days: number }[] = [
      { tag: "T+1", days: 1 },
      { tag: "T+7", days: 7 },
      { tag: "T+15", days: 15 },
      { tag: "T+30", days: 30 },
      { tag: "T+45", days: 45 },
    ];

    const windowResults = await Promise.all(
      windowDefinitions.map(async ({ tag, days }) => {
        const emptyWindow: WindowDetail = {
          available: false,
          average_fare: null,
          matched_observations: 0,
          coverage_status: "insufficient",
          carriers: [],
          fare_history: [],
        };

        try {
          const [elemRes, quotesRes] = await Promise.all([
            this.fetchJson<{
              series: { day: number; date: string; index_value: number; carrier_count: number }[];
            }>(
              `/index/elementary?origin=${orig}&destination=${dest}&advance_window_days=${days}`,
            ).catch(() => null),
            this.fetchJson<{ count: number; quotes: ApiQuote[] }>(
              `/quotes?origin=${orig}&destination=${dest}&advance_window_days=${days}`,
            ).catch(() => null),
          ]);

          const rawQuotes = quotesRes?.quotes ?? [];
          const series = elemRes?.series ?? [];

          // Order by observation date rather than trusting row order, then
          // take each carrier's first and last actual observation.
          const sorted = [...rawQuotes].sort((a, b) =>
            a.observation_date.localeCompare(b.observation_date),
          );
          const firstByCarrier: Record<string, ApiQuote> = {};
          const lastByCarrier: Record<string, ApiQuote> = {};
          for (const q of sorted) {
            const code = q.carrier_iata.toUpperCase();
            if (!firstByCarrier[code]) firstByCarrier[code] = q;
            lastByCarrier[code] = q;
          }

          const carriers: CarrierFareItem[] = Object.entries(lastByCarrier).map(([code, q]) => {
            const isOutlier = q.quality_flag?.toLowerCase() === "outlier";
            const isSoldOut =
              q.quality_flag?.toLowerCase() === "sold_out" || q.total_fare_inr === null;
            const fare = isSoldOut ? null : q.total_fare_inr;
            const status: CarrierFareItem["status"] = isOutlier
              ? "outlier_excluded"
              : isSoldOut
              ? "unavailable"
              : "available";

            const first = firstByCarrier[code];
            const changePct =
              fare !== null &&
              first &&
              first !== q &&
              first.total_fare_inr !== null &&
              first.total_fare_inr > 0
                ? Number((((fare - first.total_fare_inr) / first.total_fare_inr) * 100).toFixed(1))
                : null;

            return {
              carrier: code,
              name: CARRIER_NAMES[code] || code,
              fare,
              change_pct: changePct,
              status,
            };
          });

          const validFares = carriers
            .map((c) => c.fare)
            .filter((f): f is number => f !== null && f > 0);
          const averageFare =
            validFares.length > 0
              ? Math.round(validFares.reduce((a, b) => a + b, 0) / validFares.length)
              : null;

          // Index-implied fare path, dated from the series itself. Flagged as
          // derived rather than observed by the `fare` being null when there
          // is no anchor fare to scale.
          const fareHistory = series.map((pt) => ({
            day: pt.day,
            date: pt.date,
            fare: averageFare ? Math.round(averageFare * (pt.index_value / 100.0)) : null,
          }));

          const matchedObservations = rawQuotes.length;
          if (series.length === 0 && matchedObservations === 0) {
            return [tag, emptyWindow] as const;
          }

          const windowDetail: WindowDetail = {
            available: true,
            average_fare: averageFare,
            matched_observations: matchedObservations,
            coverage_status:
              series.length >= 30 ? "complete" : series.length > 1 ? "partial" : "insufficient",
            // No synthesised placeholder carrier row: an empty list means no
            // carrier was priced, and the UI must say so.
            carriers,
            fare_history: fareHistory,
          };

          return [tag, windowDetail] as const;
        } catch {
          return [tag, emptyWindow] as const;
        }
      }),
    );

    return {
      ...route,
      windows: Object.fromEntries(windowResults) as Record<AdvanceWindow, WindowDetail>,
    };
  }

  async getQuotes(filters?: QuoteFilters): Promise<QuoteItem[]> {
    const params = new URLSearchParams();
    if (filters?.origin) params.set("origin", filters.origin);
    if (filters?.destination) params.set("destination", filters.destination);
    if (filters?.advance_window_days) {
      params.set("advance_window_days", String(filters.advance_window_days));
    }
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);
    if (filters?.limit) params.set("limit", String(filters.limit));

    const qs = params.toString();
    const res = await this.fetchJson<{
      count: number;
      total_matched: number;
      provenance: ApiProvenance;
      quotes: ApiQuote[];
    }>(qs ? `/quotes?${qs}` : "/quotes");

    const metadata = toMetadata(res.provenance);

    return (res.quotes || []).map((q, idx) => ({
      id: `Q-LIVE-${idx + 1}`,
      collected_at_utc: q.collected_at_utc,
      departure_date: q.departure_date,
      advance_window_days: q.advance_window_days,
      origin_iata: q.origin_iata,
      destination_iata: q.destination_iata,
      carrier_iata: q.carrier_iata,
      fare_class: q.fare_class,
      total_fare_inr: q.total_fare_inr,
      source_id: q.source_id,
      // Unknown provenance defaults to "unknown", not to "api". Defaulting an
      // unlabelled row to the highest-trust tier launders its provenance.
      collection_method: (q.collection_method as CollectionMethod) || "unknown",
      quality_flag: (q.quality_flag as QualityFlag) || "ok",
      metadata,
    }));
  }

  async getQuality(): Promise<QualitySummary> {
    const [qual, srcStatus] = await Promise.all([
      this.fetchJson<{
        total_quotes: number;
        by_quality_flag: Record<string, number>;
        ok_count: number;
        sold_out_count: number;
        outlier_count: number;
        imputed_count: number;
        quality_score: number;
        provenance: ApiProvenance | null;
      }>("/quality"),
      this.fetchJson<{
        total_quotes: number;
        by_method: Record<string, number>;
        by_source_id: Record<string, number>;
        fallback_simulated_percentage: number;
        provenance: ApiProvenance | null;
      }>("/sources/status"),
    ]);

    const provenance = qual.provenance ?? srcStatus.provenance ?? undefined;

    return {
      total_quotes: qual.total_quotes,
      score: qual.quality_score,
      ok_count: qual.ok_count,
      outlier_count: qual.outlier_count,
      sold_out_count: qual.sold_out_count,
      missing_count: qual.by_quality_flag?.missing ?? 0,
      imputed_count: qual.imputed_count,
      by_method: {
        api: srcStatus.by_method?.api ?? 0,
        tariff_sheet: srcStatus.by_method?.tariff_sheet ?? 0,
        scrape: srcStatus.by_method?.scrape ?? 0,
        historical_panel: srcStatus.by_method?.historical_panel ?? 0,
        simulated: srcStatus.by_method?.simulated ?? 0,
        imputed: srcStatus.by_method?.imputed ?? 0,
        unknown: srcStatus.by_method?.unknown ?? 0,
      },
      fallback_simulated_pct: srcStatus.fallback_simulated_percentage,
      // One entry describing the dataset actually served. Fabricating a run
      // history the API does not expose would be inventing an audit trail.
      collection_runs: provenance
        ? [
            {
              run_id: provenance.source_file,
              date: "",
              total: provenance.total_quotes,
              valid: qual.ok_count,
              outliers: qual.outlier_count,
              sold_out: qual.sold_out_count,
              simulated_count: provenance.simulated_quotes,
              status: provenance.simulated_quotes > 0 ? "warning" : "ok",
            },
          ]
        : [],
      metadata: toMetadata(provenance),
    };
  }

  async getSources(): Promise<SourceStatusItem[]> {
    const srcStatus = await this.fetchJson<{
      total_quotes: number;
      by_method: Record<string, number>;
      by_source_id: Record<string, number>;
      fallback_simulated_percentage: number;
      provenance: ApiProvenance | null;
      status_note: string;
    }>("/sources/status");

    const now = new Date().toISOString();
    const total = srcStatus.total_quotes || 0;
    const bySource = srcStatus.by_source_id ?? {};

    // Sources that actually produced rows, with their real contribution.
    const active: SourceStatusItem[] = Object.entries(bySource)
      .sort((a, b) => b[1] - a[1])
      .map(([sourceId, count]) => ({
        source_id: sourceId,
        name: SOURCE_NAMES[sourceId] || sourceId,
        type: SOURCE_METHODS[sourceId] ?? "unknown",
        status: sourceId === "simulated_v1" ? "fallback" : "active",
        quotes_contributed: count,
        share_pct: total > 0 ? Number(((count / total) * 100).toFixed(1)) : 0,
        last_check_utc: now,
        // Not measured by this endpoint. Null renders as a dash; a number here
        // would be invented.
        success_rate: null,
        latency_ms: null,
      }));

    return [...active, ...NOT_INTEGRATED_SOURCES];
  }
}

export const fastApiProvider = new FastApiProvider();
