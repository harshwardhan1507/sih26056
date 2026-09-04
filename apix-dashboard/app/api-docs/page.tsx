"use client";

import React, { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Copy, Check, ExternalLink } from "lucide-react";

interface EndpointSpec {
  method: "GET";
  path: string;
  summary: string;
  description: string;
  params?: { name: string; type: string; required: boolean; description: string }[];
  curlExample: string;
  responseExample: Record<string, unknown>;
}

const ENDPOINTS: EndpointSpec[] = [
  {
    method: "GET",
    path: "/health",
    summary: "Liveness probe & API version",
    description: "Returns service status, current software version, and UTC timestamp.",
    curlExample: "curl -s http://localhost:8000/health",
    responseExample: {
      status: "ok",
      version: "1.0.0",
      timestamp_utc: "2026-09-04T12:02:15.124Z",
    },
  },
  {
    method: "GET",
    path: "/routes",
    summary: "Route basket & DGCA passenger weights",
    description: "Returns tracked 12-route basket with DGCA passenger weights and methodology attribution.",
    curlExample: "curl -s http://localhost:8000/routes",
    responseExample: {
      source: "Vonter/india-aviation-traffic (ODbL-1.0)",
      coverage_month: "2026-05",
      generated_date: "2026-09-04",
      total_basket_pax: 49572263,
      routes: [
        { route_id: "DEL-BOM", origin: "DEL", destination: "BOM", weight: 0.192173 },
        { route_id: "DEL-BLR", origin: "DEL", destination: "BLR", weight: 0.135988 },
        { route_id: "BOM-BLR", origin: "BOM", destination: "BLR", weight: 0.115589 },
      ],
    },
  },
  {
    method: "GET",
    path: "/quotes",
    summary: "Filterable fare quote records with provenance",
    description: "Queries collected price observations. Supports filtering by origin, destination, advance window, and departure date.",
    params: [
      { name: "origin", type: "string", required: false, description: "3-letter IATA origin code (e.g. 'DEL')" },
      { name: "destination", type: "string", required: false, description: "3-letter IATA destination code (e.g. 'BOM')" },
      { name: "advance_window_days", type: "integer", required: false, description: "Lead window: 1, 7, 15, 30, 45" },
      { name: "date_from", type: "string (YYYY-MM-DD)", required: false, description: "Filter departure date >= date_from" },
      { name: "date_to", type: "string (YYYY-MM-DD)", required: false, description: "Filter departure date <= date_to" },
    ],
    curlExample: "curl -s 'http://localhost:8000/quotes?origin=DEL&destination=BOM&advance_window_days=7'",
    responseExample: {
      count: 5,
      quotes: [
        {
          id: "Q-20260904-001",
          collected_at_utc: "2026-09-04T12:02:15Z",
          departure_date: "2026-09-11",
          advance_window_days: 7,
          origin_iata: "DEL",
          destination_iata: "BOM",
          carrier_iata: "6E",
          fare_class: "Economy",
          total_fare_inr: 7650.0,
          source_id: "tripjack_api_v2",
          collection_method: "api",
          quality_flag: "ok",
        },
      ],
    },
  },
  {
    method: "GET",
    path: "/index/elementary",
    summary: "Elementary Jevons index series",
    description: "Computes matched-sample geometric elementary Jevons index for a specified route and advance horizon.",
    params: [
      { name: "origin", type: "string", required: true, description: "3-letter IATA origin code (e.g. 'DEL')" },
      { name: "destination", type: "string", required: true, description: "3-letter IATA destination code (e.g. 'BOM')" },
      { name: "advance_window_days", type: "integer", required: true, description: "Advance lead horizon (e.g. 7)" },
    ],
    curlExample: "curl -s 'http://localhost:8000/index/elementary?origin=DEL&destination=BOM&advance_window_days=7'",
    responseExample: {
      origin: "DEL",
      destination: "BOM",
      advance_window_days: 7,
      base_value: 100.0,
      series_length: 31,
      series: [
        { day: 0, index_value: 100.0, carrier_count: 5 },
        { day: 1, index_value: 101.2, carrier_count: 5 },
        { day: 30, index_value: 108.4, carrier_count: 5 },
      ],
    },
  },
  {
    method: "GET",
    path: "/index/aggregate",
    summary: "Chained Laspeyres aggregate index series",
    description: "Returns official APIx aggregate national series weighted by DGCA route traffic shares.",
    curlExample: "curl -s http://localhost:8000/index/aggregate",
    responseExample: {
      base_value: 100.0,
      series_length: 31,
      series: [
        { day: 0, index_value: 100.0 },
        { day: 1, index_value: 100.4 },
        { day: 30, index_value: 103.7 },
      ],
    },
  },
  {
    method: "GET",
    path: "/sources/status",
    summary: "Multi-tier telemetry & fallback rate",
    description: "Surfaces distribution of collection methods (api, tariff_sheet, scrape, simulated) and fallback rates.",
    curlExample: "curl -s http://localhost:8000/sources/status",
    responseExample: {
      total_quotes: 300,
      by_method: { api: 126, tariff_sheet: 93, scrape: 54, simulated: 27 },
      fallback_simulated_percentage: 9.0,
      status_note: "Aggregated from multi-tier resolver telemetry.",
    },
  },
  {
    method: "GET",
    path: "/quality",
    summary: "Data quality & hygiene audit metrics",
    description: "Returns counts of quotes by quality flag: ok, outlier, imputed, and sold_out.",
    curlExample: "curl -s http://localhost:8000/quality",
    responseExample: {
      total_quotes: 300,
      by_quality_flag: { ok: 291, outlier: 6, sold_out: 3, imputed: 0 },
      ok_count: 291,
      sold_out_count: 3,
      outlier_count: 6,
      imputed_count: 0,
    },
  },
];

export default function ApiDocsPage() {
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const handleCopy = (text: string, path: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Page Header */}
      <PageHeader
        eyebrow="Developer & Institutional Access"
        title="API Reference & Integration"
        subtitle="Complete specification of FastAPI REST endpoints serving route baskets, price quotes, Jevons elementary series, chained Laspeyres aggregates, and data-quality metrics."
        actions={
          <div className="flex items-center gap-2">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#0F172A] text-white rounded-xs text-xs font-mono hover:bg-[#0F172A]/90 transition-colors shadow-xs"
            >
              <span>Interactive Swagger UI</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        }
      />

      {/* Overview Banner */}
      <div className="p-4 border border-[#E2E8F0] bg-white rounded-sm flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs font-mono shadow-xs">
        <div>
          <span className="text-[#64748B]">Base URL:</span>{" "}
          <strong className="text-[#0F172A]">http://localhost:8000</strong>
          <span className="text-[#64748B] ml-3">· Protocol:</span>{" "}
          <strong className="text-[#0F172A]">HTTPS / JSON</strong>
        </div>
        <div className="text-[#1E3A8A] font-semibold">
          FastAPI v1.0.0 · OpenAPI 3.1
        </div>
      </div>

      {/* Endpoints List */}
      <div className="space-y-6">
        {ENDPOINTS.map((ep) => {
          const isCopied = copiedPath === ep.path;
          return (
            <div
              key={ep.path}
              className="border border-[#E2E8F0] bg-white rounded-sm p-5 space-y-4 shadow-xs"
            >
              {/* Endpoint Header */}
              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 pb-3 border-b border-[#E2E8F0]">
                <div className="flex items-center gap-3">
                  <span className="px-2 py-0.5 bg-[#1E3A8A] text-white font-mono text-[10px] font-bold rounded-xs tracking-wider">
                    {ep.method}
                  </span>
                  <span className="font-mono font-bold text-sm text-[#0F172A]">
                    {ep.path}
                  </span>
                </div>
                <span className="text-xs text-[#64748B] font-sans">
                  {ep.summary}
                </span>
              </div>

              {/* Description */}
              <p className="text-xs text-[#64748B] font-sans leading-relaxed">
                {ep.description}
              </p>

              {/* Parameters Table if any */}
              {ep.params && ep.params.length > 0 && (
                <div>
                  <h5 className="font-mono text-[10px] uppercase tracking-wider text-[#64748B] font-semibold mb-2">
                    Query Parameters
                  </h5>
                  <div className="overflow-x-auto border border-[#E2E8F0] rounded-xs bg-slate-50/50">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase">
                          <th className="py-1.5 px-3">Parameter</th>
                          <th className="py-1.5 px-3">Type</th>
                          <th className="py-1.5 px-3">Required</th>
                          <th className="py-1.5 px-3">Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E8F0] font-mono text-[11px]">
                        {ep.params.map((param) => (
                          <tr key={param.name}>
                            <td className="py-1.5 px-3 font-bold text-[#0F172A]">
                              {param.name}
                            </td>
                            <td className="py-1.5 px-3 text-[#64748B]">
                              {param.type}
                            </td>
                            <td className="py-1.5 px-3">
                              {param.required ? (
                                <span className="text-rose-700 font-semibold">Yes</span>
                              ) : (
                                <span className="text-[#64748B]">No</span>
                              )}
                            </td>
                            <td className="py-1.5 px-3 font-sans text-xs text-[#64748B]">
                              {param.description}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* cURL Example */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-[#64748B] font-semibold">
                    cURL Command
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(ep.curlExample, ep.path)}
                    className="inline-flex items-center gap-1 text-[10px] font-mono text-[#1E3A8A] hover:underline cursor-pointer"
                  >
                    {isCopied ? (
                      <>
                        <Check className="h-3 w-3 text-[#1E3A8A]" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        <span>Copy cURL</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="p-3 bg-[#0F172A] text-slate-100 rounded-xs font-mono text-xs overflow-x-auto selection:bg-[#1E3A8A]">
                  {ep.curlExample}
                </pre>
              </div>

              {/* JSON Response Preview */}
              <div>
                <span className="font-mono text-[10px] uppercase tracking-wider text-[#64748B] font-semibold block mb-1.5">
                  Response (200 OK)
                </span>
                <pre className="p-3 bg-slate-50 border border-[#E2E8F0] rounded-xs font-mono text-[11px] text-[#0F172A] overflow-x-auto max-h-56">
                  {JSON.stringify(ep.responseExample, null, 2)}
                </pre>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
