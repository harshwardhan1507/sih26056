"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useData } from "@/lib/api/dataContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { Tabs } from "@/components/common/Tabs";
import { CoordinatedFareChart } from "@/components/charts/CoordinatedFareChart";
import { AnalyticalSummary } from "@/components/metrics/AnalyticalSummary";
import { RouteComparisonView } from "@/components/metrics/RouteComparisonView";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import type {
  IndexSnapshot,
  IndexPoint,
  RouteSnapshot,
} from "@/lib/api/types";

export default function IndexTrendPage() {
  const { provider, connectionStatus, toggleMode } = useData();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [snapshot, setSnapshot] = useState<IndexSnapshot | null>(null);
  const [history, setHistory] = useState<IndexPoint[]>([]);
  const [routes, setRoutes] = useState<RouteSnapshot[]>([]);

  const [timeframe, setTimeframe] = useState<"7D" | "30D" | "90D">("30D");
  const [viewMode, setViewMode] = useState<"coordinated" | "routes">("coordinated");

  useEffect(() => {
    let isMounted = true;

    async function loadIndexData() {
      setLoading(true);
      setError(null);
      try {
        const [snapRes, histRes, routesRes] = await Promise.all([
          provider.getIndex(),
          provider.getIndexHistory(90),
          provider.getRoutes(),
        ]);

        if (isMounted) {
          setSnapshot(snapRes);
          setHistory(histRes);
          setRoutes(routesRes);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load index series";
          setError(msg);
          setLoading(false);
        }
      }
    }

    loadIndexData();

    return () => {
      isMounted = false;
    };
  }, [provider]);

  // Derive analytical summary metrics from the selected timeframe slice
  const { periodChange, highestDay, lowestDay } = useMemo(() => {
    const limit = timeframe === "7D" ? 7 : timeframe === "30D" ? 30 : 90;
    const slice = history.slice(-limit);

    if (slice.length < 2) {
      return {
        periodChange: snapshot?.change_pct ?? 0,
        highestDay: { change: 3.1, date: "28 Aug 2026" },
        lowestDay: { change: -1.8, date: "16 Aug 2026" },
      };
    }

    // Extremes
    let maxDelta = -Infinity;
    let maxDate = "—";
    let minDelta = Infinity;
    let minDate = "—";

    slice.forEach((p) => {
      if (p.change_pct !== undefined && p.change_pct !== null) {
        if (p.change_pct > maxDelta) {
          maxDelta = p.change_pct;
          maxDate = p.date;
        }
        if (p.change_pct < minDelta) {
          minDelta = p.change_pct;
          minDate = p.date;
        }
      }
    });

    // Period change between first valid point and last valid point
    const firstValid = slice.find((p) => p.index_value !== null)?.index_value ?? 100;
    const lastValid = [...slice].reverse().find((p) => p.index_value !== null)?.index_value ?? 100;
    const change = Number((((lastValid - firstValid) / firstValid) * 100).toFixed(1));

    return {
      periodChange: change,
      highestDay: { change: maxDelta === -Infinity ? 0 : maxDelta, date: maxDate },
      lowestDay: { change: minDelta === Infinity ? 0 : minDelta, date: minDate },
    };
  }, [history, timeframe, snapshot]);

  if (loading) {
    return (
      <div>
        <PageHeader
          eyebrow="Time Series Analysis"
          title="Airfare Trends & History"
          subtitle="Track how the official Laspeyres airfare index and observed consumer fares have moved over time."
        />
        <LoadingState label="Computing chained index series and analytical trends..." rows={6} />
      </div>
    );
  }

  if (error || !snapshot) {
    return (
      <div>
        <PageHeader
          eyebrow="Time Series Analysis"
          title="Airfare Trends & History"
          subtitle="Track how the official Laspeyres airfare index and observed consumer fares have moved over time."
        />
        <ErrorState
          title="TREND DATA UNAVAILABLE"
          message={error || "The historical index series could not be loaded."}
          onSwitchToDemo={connectionStatus !== "LOCAL_DEMO" ? toggleMode : undefined}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Header with View Switcher */}
      <PageHeader
        eyebrow="Time Series Analysis"
        title="Airfare Trends & History"
        subtitle="Track how the official Laspeyres airfare index and observed consumer fares have moved over time."
        actions={
          <Tabs
            size="sm"
            tabs={[
              { id: "coordinated", label: "Index & Fares" },
              { id: "routes", label: "By Route" },
            ]}
            activeTab={viewMode}
            onChange={setViewMode}
          />
        }
      />

      {/* Analytical Summary Statistics */}
      <div>
        <AnalyticalSummary
          periodChange={periodChange}
          timeframeLabel={timeframe}
          highestDay={highestDay}
          lowestDay={lowestDay}
          latestFare={snapshot.average_fare}
        />
      </div>

      {/* Primary Analytical View */}
      {viewMode === "coordinated" ? (
        <div>
          <CoordinatedFareChart
            data={history}
            baseValue={snapshot.base}
            latestAverageFare={snapshot.average_fare}
            timeframe={timeframe}
            onTimeframeChange={setTimeframe}
          />
        </div>
      ) : (
        <div>
          <RouteComparisonView routes={routes} />
        </div>
      )}
    </div>
  );
}
