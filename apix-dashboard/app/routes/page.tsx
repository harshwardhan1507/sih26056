"use client";

import React, { useEffect, useState } from "react";
import { useData } from "@/lib/api/dataContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { RouteTable } from "@/components/routes/RouteTable";
import { IndiaRouteMap } from "@/components/routes/IndiaRouteMap";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import type { RouteSnapshot } from "@/lib/api/types";

export default function RoutesPage() {
  const { provider, connectionStatus, toggleMode } = useData();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [routes, setRoutes] = useState<RouteSnapshot[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>("DEL-BOM");

  useEffect(() => {
    let isMounted = true;

    async function loadRoutesData() {
      setLoading(true);
      setError(null);
      try {
        const res = await provider.getRoutes();
        if (isMounted) {
          setRoutes(res);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load routes";
          setError(msg);
          setLoading(false);
        }
      }
    }

    loadRoutesData();

    return () => {
      isMounted = false;
    };
  }, [provider]);

  if (loading) {
    return (
      <div>
        <PageHeader
          eyebrow="DGCA Passenger Basket"
          title="Domestic Trunk Routes"
          subtitle="Authoritative 12-route network derived from Trailing 12-Month DGCA domestic city-pair passenger traffic."
        />
        <LoadingState label="Loading DGCA route weights and current price observations..." rows={6} />
      </div>
    );
  }

  if (error || routes.length === 0) {
    return (
      <div>
        <PageHeader
          eyebrow="DGCA Passenger Basket"
          title="Domestic Trunk Routes"
          subtitle="Authoritative 12-route network derived from Trailing 12-Month DGCA domestic city-pair passenger traffic."
        />
        <ErrorState
          title="ROUTE DATA UNAVAILABLE"
          message={error || "The route basket could not be retrieved."}
          onSwitchToDemo={connectionStatus !== "LOCAL_DEMO" ? toggleMode : undefined}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Editorial Header */}
      <PageHeader
        eyebrow="DGCA Passenger Basket"
        title="Domestic Trunk Routes"
        subtitle="Authoritative 12-route network derived from Trailing 12-Month DGCA domestic city-pair passenger traffic (June 2025 to May 2026)."
      />

      {/* Route Network Map with DGCA Basket Hierarchy */}
      <div>
        <IndiaRouteMap
          routes={routes}
          selectedRouteId={selectedRouteId}
          onSelectRoute={setSelectedRouteId}
        />
      </div>

      {/* Authoritative Route Table with Sparklines & Movement Indicators */}
      <div>
        <RouteTable
          routes={routes}
          selectedRouteId={selectedRouteId}
          onSelectRoute={setSelectedRouteId}
        />
      </div>
    </div>
  );
}
