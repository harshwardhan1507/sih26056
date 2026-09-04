"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
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
          subtitle="A daily measure of domestic airfare movement across 12 major passenger routes."
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
          subtitle="A daily measure of domestic airfare movement across 12 major passenger routes."
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
      {/* Hero Headline & Editorial Photo Block */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch pb-6 border-b border-[#E2E8F0]">
        {/* Left Column: Index Title and Big Number */}
        <div className="lg:col-span-7 flex flex-col justify-between">
          <div>
            <h2 className="text-4xl sm:text-5xl font-bold text-[#0F172A] tracking-tight uppercase">
              India Airfare Index
            </h2>
            <p className="text-xs text-[#64748B] mt-2 max-w-lg">
              A daily measure of domestic airfare movement across 12 major passenger routes.
            </p>
          </div>

          <div className="my-6">
            <Metric
              size="hero"
              label="Headline Index"
              value={snapshot.value !== null && snapshot.value !== undefined ? snapshot.value.toFixed(1) : "100.0"}
              delta={snapshot.change_pct}
              deltaLabel="vs previous collection period"
              subtext={`Base (Aug 2026) = 100.0 · Last updated: 04 Sep 2026 · 17:32 IST`}
            />
          </div>
        </div>

        {/* Right Column: Editorial Hero Visual Card - Clean Natural Photo without Blue Overlay */}
        <div className="lg:col-span-5 relative rounded-sm overflow-hidden border border-[#E2E8F0] bg-white min-h-[220px] flex flex-col justify-end p-5 shadow-xs">
          <img
            src="/hero_aviation.jpg"
            alt="Aviation over clouds"
            className="absolute inset-0 w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />
          
          <div className="relative z-10 text-white space-y-1">
            <span className="text-[10px] font-mono tracking-widest uppercase text-white/90 font-semibold block">
              National Air Corridor Basket
            </span>
            <p className="text-lg font-semibold leading-snug text-white max-w-xs">
              Higher frequencies, a more connected India.
            </p>
          </div>
        </div>
      </div>

      {/* Hero Chart: Fixed-Base Laspeyres Index Trend */}
      <div>
        <IndexTrendChart
          data={history}
          baseValue={snapshot.base}
          timeframe={timeframe}
          onTimeframeChange={setTimeframe}
        />
      </div>

      {/* Middle Grid: What's Driving the Index & Market Snapshot */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <MarketSnapshot
            averageFare={snapshot.average_fare}
            quotesCount={snapshot.quotes}
            routesCount={snapshot.routes}
            qualityScore={snapshot.quality_score}
          />
        </div>

        <div className="lg:col-span-5">
          <TopMovers routes={routes} limit={5} />
        </div>
      </div>

      {/* Ingestion Method Coverage Distribution */}
      <div>
        <CollectionCoverage
          byMethod={quality?.by_method}
          totalQuotes={snapshot.quotes}
        />
      </div>
    </div>
  );
}
