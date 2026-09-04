"use client";

import React, { useEffect, useState } from "react";
import { useData } from "@/lib/api/dataContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { QualityScoreHero } from "@/components/data/QualityScoreHero";
import { HygieneFlagsTable } from "@/components/data/HygieneFlagsTable";
import { CollectionCoverage } from "@/components/metrics/CollectionCoverage";
import { CollectionRunsTable } from "@/components/data/CollectionRunsTable";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import type { QualitySummary } from "@/lib/api/types";

export default function QualityPage() {
  const { provider, connectionStatus, toggleMode } = useData();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [quality, setQuality] = useState<QualitySummary | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadQualityData() {
      setLoading(true);
      setError(null);
      try {
        const res = await provider.getQuality();
        if (isMounted) {
          setQuality(res);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load quality metrics";
          setError(msg);
          setLoading(false);
        }
      }
    }

    loadQualityData();

    return () => {
      isMounted = false;
    };
  }, [provider]);

  if (loading) {
    return (
      <div>
        <PageHeader
          eyebrow="Data Hygiene & Quality Controls"
          title="Data Quality Audit"
          subtitle="Verification score, price outlier exclusion, sold-out missing observations, and zero-imputation transparency."
        />
        <LoadingState label="Auditing data hygiene metrics and historical collection clock runs..." rows={6} />
      </div>
    );
  }

  if (error || !quality) {
    return (
      <div>
        <PageHeader
          eyebrow="Data Hygiene & Quality Controls"
          title="Data Quality Audit"
          subtitle="Verification score, price outlier exclusion, sold-out missing observations, and zero-imputation transparency."
        />
        <ErrorState
          title="QUALITY METRICS UNAVAILABLE"
          message={error || "Quality audit telemetry could not be retrieved."}
          onSwitchToDemo={connectionStatus !== "LOCAL_DEMO" ? toggleMode : undefined}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        eyebrow="Data Hygiene & Quality Controls"
        title="Data Quality Audit"
        subtitle="Verification score, price outlier exclusion, sold-out missing observations, and zero-imputation transparency across all domestic observations."
      />

      {/* Quality Score Hero & Fallback Notice */}
      <div>
        <QualityScoreHero
          score={quality.score}
          totalQuotes={quality.total_quotes}
          validQuotes={quality.ok_count}
          outlierCount={quality.outlier_count}
          soldOutCount={quality.sold_out_count}
          imputedCount={quality.imputed_count}
          fallbackSimulatedPct={quality.fallback_simulated_pct}
        />
      </div>

      {/* Ingestion Method Coverage Distribution */}
      <div>
        <CollectionCoverage
          byMethod={quality.by_method}
          totalQuotes={quality.total_quotes}
        />
      </div>

      {/* Flag Treatment Matrix */}
      <div>
        <HygieneFlagsTable
          counts={{
            ok: quality.ok_count,
            outlier: quality.outlier_count,
            sold_out: quality.sold_out_count,
            missing: quality.missing_count,
            imputed: quality.imputed_count,
          }}
          total={quality.total_quotes}
        />
      </div>

      {/* Historical Collection Clock Runs Audit */}
      <div>
        <CollectionRunsTable runs={quality.collection_runs} />
      </div>
    </div>
  );
}
