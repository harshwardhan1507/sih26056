"use client";

import React, { useEffect, useState } from "react";
import { useData } from "@/lib/api/dataContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { SourceHealthTable } from "@/components/data/SourceHealthTable";
import { PipelineFlow } from "@/components/provenance/PipelineFlow";
import { QuoteBrowserTable } from "@/components/provenance/QuoteBrowserTable";
import { QuoteInspectorModal } from "@/components/provenance/QuoteInspectorModal";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import type { SourceStatusItem, QuoteItem } from "@/lib/api/types";

export default function SourcesPage() {
  const { provider, connectionStatus, toggleMode } = useData();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [sources, setSources] = useState<SourceStatusItem[]>([]);
  const [quotes, setQuotes] = useState<QuoteItem[]>([]);
  const [inspectedQuote, setInspectedQuote] = useState<QuoteItem | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadSourcesData() {
      setLoading(true);
      setError(null);
      try {
        const [srcRes, quotesRes] = await Promise.all([
          provider.getSources(),
          provider.getQuotes(),
        ]);
        if (isMounted) {
          setSources(srcRes);
          setQuotes(quotesRes);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load sources and quotes";
          setError(msg);
          setLoading(false);
        }
      }
    }

    loadSourcesData();

    return () => {
      isMounted = false;
    };
  }, [provider]);

  if (loading) {
    return (
      <div>
        <PageHeader
          eyebrow="Multi-Tier Ingestion & Provenance"
          title="Source Telemetry & Health"
          subtitle="Provider status, fallback rates, latency, and quote-level provenance audit trails."
        />
        <LoadingState label="Inspecting provider health telemetry and quote provenance logs..." rows={6} />
      </div>
    );
  }

  if (error || sources.length === 0) {
    return (
      <div>
        <PageHeader
          eyebrow="Multi-Tier Ingestion & Provenance"
          title="Source Telemetry & Health"
          subtitle="Provider status, fallback rates, latency, and quote-level provenance audit trails."
        />
        <ErrorState
          title="SOURCE TELEMETRY UNAVAILABLE"
          message={error || "Provider status telemetry could not be retrieved."}
          onSwitchToDemo={connectionStatus !== "LOCAL_DEMO" ? toggleMode : undefined}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        eyebrow="Multi-Tier Ingestion & Provenance"
        title="Source Telemetry & Health"
        subtitle="Provider status, fallback rates, response latency, and quote-level provenance audit trails across all collection tiers."
      />

      {/* Source Health Table */}
      <div>
        <SourceHealthTable sources={sources} />
      </div>

      {/* 6-Stage Econometric Pipeline Flow */}
      <div>
        <PipelineFlow />
      </div>

      {/* Quote-Level Observation Registry with Provenance Inspector */}
      <div>
        <QuoteBrowserTable
          quotes={quotes}
          onInspectQuote={setInspectedQuote}
        />
      </div>

      {/* Quote Inspector Modal */}
      <QuoteInspectorModal
        quote={inspectedQuote}
        onClose={() => setInspectedQuote(null)}
      />
    </div>
  );
}
