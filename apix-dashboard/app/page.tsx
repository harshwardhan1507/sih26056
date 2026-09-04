"use client";

import React, { useEffect, useState } from "react";
import { useData } from "@/lib/api/dataContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { Metric } from "@/components/common/Metric";
import { IndexTrendChart } from "@/components/charts/IndexTrendChart";
import { TopMovers } from "@/components/metrics/TopMovers";
import { MarketSnapshot } from "@/components/metrics/MarketSnapshot";
import { CollectionCoverage } from "@/components/metrics/CollectionCoverage";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import type {
  IndexSnapshot,
  IndexPoint,
  RouteSnapshot,
  QualitySummary,
} from "@/lib/api/types";

export default function OverviewPage() {
  const { provider, connectionStatus, toggleMode } = useData();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [snapshot, setSnapshot] = useState<IndexSnapshot | null>(null);
  const [history, setHistory] = useState<IndexPoint[]>([]);
  const [routes, setRoutes] = useState<RouteSnapshot[]>([]);
  const [quality, setQuality] = useState<QualitySummary | null>(null);

  const [timeframe, setTimeframe] = useState<"7D" | "30D" | "90D">("30D");

  useEffect(() => {
    let isMounted = true;

    async function loadOverviewData() {
      setLoading(true);
      setError(null);
      try {
        const [snapRes, histRes, routesRes, qualRes] = await Promise.all([
          provider.getIndex(),
          provider.getIndexHistory(90),
          provider.getRoutes(),
          provider.getQuality(),
        ]);

        if (isMounted) {
          setSnapshot(snapRes);
          setHistory(histRes);
          setRoutes(routesRes);
          setQuality(qualRes);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load index data";
          setError(msg);
          setLoading(false);
        }
      }
    }

    loadOverviewData();

    return () => {
      isMounted = false;
    };
  }, [provider]);

  if (loading) {
    return (
      <div>
        <PageHeader
          eyebrow="National Chained Series"
          title="India Airfare Index"
          subtitle="A daily measure of domestic airfare movement across India's major passenger routes."
        />
        <LoadingState label="Loading national airfare index and market drivers..." rows={5} />
      </div>
    );
  }

  if (error || !snapshot) {
    return (
      <div>
        <PageHeader
          eyebrow="National Chained Series"
          title="India Airfare Index"
          subtitle="A daily measure of domestic airfare movement across India's major passenger routes."
        />
        <ErrorState
          title="INDEX DATA UNAVAILABLE"
          message={error || "The latest collection has not produced a valid index for this period."}
          onSwitchToDemo={connectionStatus !== "LOCAL_DEMO" ? toggleMode : undefined}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Editorial Page Header */}
      <PageHeader
        eyebrow="National Chained Series"
        title="India Airfare Index"
        subtitle="A daily measure of domestic airfare movement across India's major passenger routes."
      />

      {/* Hero Metric: The Headline Number */}
      <div className="border-b border-[#D8D7D0] pb-6">
        <Metric
          size="hero"
          label="Airfare Price Index"
          value={snapshot.value.toFixed(1)}
          delta={snapshot.change_pct}
          deltaLabel="vs previous collection period"
          subtext={`Base (${snapshot.base.toFixed(1)}) = 100.0 · ${snapshot.date}`}
        />
      </div>

      {/* Hero Chart: Chained Laspeyres Index Trend */}
      <div>
        <IndexTrendChart
          data={history}
          baseValue={snapshot.base}
          timeframe={timeframe}
          onTimeframeChange={setTimeframe}
        />
      </div>

      {/* Middle Grid: What's Driving the Index & Collection Coverage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopMovers routes={routes} limit={5} />
        <CollectionCoverage
          byMethod={quality?.by_method}
          totalQuotes={snapshot.quotes}
        />
      </div>

      {/* Bottom Row: Market Snapshot Cluster */}
      <div>
        <MarketSnapshot
          averageFare={snapshot.average_fare}
          quotesCount={snapshot.quotes}
          routesCount={snapshot.routes}
          qualityScore={snapshot.quality_score}
        />
      </div>
    </div>
  );
}
