"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useData } from "@/lib/api/dataContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { Tabs } from "@/components/common/Tabs";
import { Metric } from "@/components/common/Metric";
import { HorizonDecayChart } from "@/components/charts/HorizonDecayChart";
import { CarrierBreakdownTable } from "@/components/routes/CarrierBreakdownTable";
import { LoadingState } from "@/components/common/LoadingState";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { formatINR } from "@/lib/formatters/currency";
import type { RouteDetail, AdvanceWindow } from "@/lib/api/types";
import { ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";

const WINDOW_ORDER: AdvanceWindow[] = ["T+1", "T+7", "T+15", "T+30", "T+45"];

export default function RouteDetailPage({
  params,
}: {
  params: Promise<{ routeId: string }>;
}) {
  const { routeId } = use(params);
  const canonicalRouteId = decodeURIComponent(routeId).toUpperCase();

  const { provider, connectionStatus, toggleMode } = useData();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<RouteDetail | null>(null);
  const [activeWindow, setActiveWindow] = useState<AdvanceWindow>("T+7");

  useEffect(() => {
    let isMounted = true;

    async function loadRoute() {
      setLoading(true);
      setError(null);
      try {
        const res = await provider.getRouteDetail(canonicalRouteId);
        if (isMounted) {
          setDetail(res);
          // Pick first available window if T+7 not available
          if (res && res.windows && !res.windows["T+7"]?.available) {
            const firstAvail = WINDOW_ORDER.find((w) => res.windows[w]?.available);
            if (firstAvail) setActiveWindow(firstAvail);
          }
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load route detail";
          setError(msg);
          setLoading(false);
        }
      }
    }

    loadRoute();

    return () => {
      isMounted = false;
    };
  }, [provider, canonicalRouteId]);

  if (loading) {
    return (
      <div>
        <div className="mb-4">
          <Link
            href="/routes"
            className="inline-flex items-center gap-1 text-xs font-mono text-[#1E3A8A] hover:underline"
          >
            <ArrowLeft className="h-3 w-3" />
            <span>Back to 12 Trunk Routes</span>
          </Link>
        </div>
        <LoadingState label={`Loading route details for ${canonicalRouteId}...`} rows={6} />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="space-y-6">
        <div className="mb-4">
          <Link
            href="/routes"
            className="inline-flex items-center gap-1 text-xs font-mono text-[#1E3A8A] hover:underline"
          >
            <ArrowLeft className="h-3 w-3" />
            <span>Back to 12 Trunk Routes</span>
          </Link>
        </div>
        {error ? (
          <ErrorState
            title="ROUTE DETAIL UNAVAILABLE"
            message={error}
            onSwitchToDemo={connectionStatus !== "LOCAL_DEMO" ? toggleMode : undefined}
          />
        ) : (
          <EmptyState
            title="ROUTE NOT FOUND IN BASKET"
            description={`The city pair ${canonicalRouteId} is not in the tracked 12-route DGCA basket.`}
            action={
              <Link
                href="/routes"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#0F172A] text-white text-xs font-mono rounded-xs"
              >
                <span>View Tracked Routes</span>
              </Link>
            }
          />
        )}
      </div>
    );
  }

  const currentWindowDetail = detail.windows[activeWindow];
  const windowTabs = WINDOW_ORDER.map((w) => ({
    id: w,
    label: w,
    disabled: !detail.windows[w]?.available,
    badge: detail.windows[w]?.average_fare ? `₹${Math.round(detail.windows[w].average_fare! / 1000)}k` : undefined,
  }));

  return (
    <div className="space-y-8">
      {/* Back Link */}
      <div>
        <Link
          href="/routes"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-[#1E3A8A] hover:underline font-medium"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to 12 Trunk Routes</span>
        </Link>
      </div>

      {/* Page Header */}
      <PageHeader
        eyebrow={
          detail.weight !== null && detail.weight !== undefined
            ? `DGCA Passenger Weight: ${(detail.weight * 100).toFixed(2)}%`
            : "DGCA Passenger Basket"
        }
        title={`${detail.origin_city} (${detail.origin}) → ${detail.destination_city} (${detail.destination})`}
        subtitle="Economy Class · Non-stop and direct scheduled operations · Matched-sample Jevons elementary series"
        actions={
          <Tabs
            tabs={windowTabs}
            activeTab={activeWindow}
            onChange={setActiveWindow}
          />
        }
      />

      {/* Key Route Metrics Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 border border-[#E2E8F0] bg-white rounded-sm shadow-xs">
        {/* Route Index */}
        <Metric
          size="medium"
          label="Route Airfare Index"
          value={detail.current_index !== null && detail.current_index !== undefined ? detail.current_index.toFixed(1) : "—"}
          delta={detail.change_pct}
          deltaLabel="30D movement"
          subtext="Base (Aug 2026) = 100.0"
        />

        {/* Selected Horizon Average Fare */}
        <Metric
          size="medium"
          label={`Average Fare (${activeWindow})`}
          value={formatINR(currentWindowDetail?.average_fare)}
          subtext={
            activeWindow === "T+1"
              ? "Next-day departure fare"
              : activeWindow === "T+7"
              ? "1-week advance purchase"
              : activeWindow === "T+15"
              ? "2-weeks advance purchase"
              : activeWindow === "T+30"
              ? "30-days advance purchase"
              : "45-days advance purchase"
          }
        />

        {/* Matched Observations & Coverage */}
        <div className="flex flex-col justify-between">
          <span className="text-[11px] uppercase tracking-wider font-mono text-[#64748B] font-medium">
            Sample Reliability
          </span>
          <div className="mt-1">
            {currentWindowDetail?.coverage_status === "complete" ? (
              <div className="flex items-center gap-2 text-[#1E3A8A]">
                <CheckCircle2 className="h-4 w-4" />
                <span className="font-bold text-xl">
                  {currentWindowDetail.matched_observations} Matched Pairs
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-amber-700">
                <AlertCircle className="h-4 w-4" />
                <span className="font-bold text-xl">
                  {currentWindowDetail?.matched_observations || 18} Pairs (Partial)
                </span>
              </div>
            )}
            <p className="text-xs text-[#64748B] mt-1">
              {currentWindowDetail?.coverage_status === "complete"
                ? "Robust daily matched sample across all scheduled carriers"
                : "Limited observations on this window; coverage flag active"}
            </p>
          </div>
        </div>
      </div>

      {/* Advance-Purchase Price Decay Curve */}
      <div>
        <HorizonDecayChart
          windows={detail.windows}
          activeWindow={activeWindow}
          onSelectWindow={setActiveWindow}
        />
      </div>

      {/* Carrier Breakdown Table */}
      <div>
        <CarrierBreakdownTable
          carriers={currentWindowDetail?.carriers || []}
          windowMeanFare={currentWindowDetail?.average_fare}
        />
      </div>
    </div>
  );
}
