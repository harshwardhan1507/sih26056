"use client";

import React, { useState } from "react";
import { CheckCircle2 } from "lucide-react";

interface PipelineStage {
  step: number;
  title: string;
  tag: string;
  shortDesc: string;
  details: string[];
}

const STAGES: PipelineStage[] = [
  {
    step: 1,
    title: "Multi-Tier Ingestion",
    tag: "Collection & Resolver",
    shortDesc: "Prioritized fallback: Direct APIs → Tariff Sheets → Playwright Scraping → Simulation Engine.",
    details: [
      "Tier 1: B2B Aggregator APIs (TripJack / TBO) provide structured GDS feeds.",
      "Tier 2: Airline Tariff Sheets parsed for declared commercial fare bands.",
      "Tier 3: Playwright browser automation extracts public consumer web fares with HAR recording.",
      "Tier 4: Simulated fallback applies advance-purchase decay curves when upstream APIs throttle.",
      "Carrier-aware fallback ensures missing airline quotes query lower tiers without duplicating found carriers.",
    ],
  },
  {
    step: 2,
    title: "Normalization",
    tag: "Standardization",
    shortDesc: "Unifies multi-airport catchments (GOI/GOX, BOM/NMI) and computes total consumer fare paid.",
    details: [
      "Metropolitan Catchment Aggregation: Sums Goa Dabolim (GOI) + Mopa (GOX) traffic to reflect true consumer destination expenditure.",
      "Mumbai airport normalization: BOM and Navi Mumbai (NMI) consolidated to metropolitan code BOM.",
      "Consumer scope: Base fare + mandatory fuel surcharge + UDF + PSF + OTA convenience fees included.",
      "All observation timestamps normalized to standardized UTC with microsecond precision.",
    ],
  },
  {
    step: 3,
    title: "Schema Validation",
    tag: "Structural Integrity",
    shortDesc: "Pydantic V2 schema validation guarantees field types, ISO dates, and IATA codes.",
    details: [
      "Strict schema enforcement: origin_iata, destination_iata, carrier_iata validated against 3-letter/2-letter standards.",
      "Advance window validated strictly into the 5 official APIx horizons: 1, 7, 15, 30, 45 days.",
      "Departure date and collection timestamp parsed to ISO 8601 specifications.",
      "Rejects malformed JSON records before pipeline ingestion.",
    ],
  },
  {
    step: 4,
    title: "Quality Controls",
    tag: "Hygiene & Fences",
    shortDesc: "IQR price fences isolate outliers; sold-out flights safely flagged as null, never ₹0.",
    details: [
      "IQR Outlier Fences: Identifies price spikes exceeding Q3 + 3.0 * IQR per (route, window) cell.",
      "Outliers flagged with quality_flag='outlier' and excluded from index calculation.",
      "Sold-out flights: Explicitly recorded with total_fare_inr = null. NEVER replaced with 0.00.",
      "Drops unavailable flights from matched pairs to avoid artificial deflationary spikes.",
    ],
  },
  {
    step: 5,
    title: "Elementary Jevons Index",
    tag: "Matched Chaining",
    shortDesc: "Geometric mean of price relatives with matched-sample chaining across consecutive days.",
    details: [
      "Jevons formula: Geometric mean of price relatives avoids Carli arithmetic upward bias.",
      "Matched-sample chaining: Only flight observations present on both day t and day t-1 enter ratio.",
      "Never compares across windows: T+7 today is compared strictly against T+7 yesterday.",
      "Base value anchored to 100.0 at day 0 for each (route, advance_window) segment.",
    ],
  },
  {
    step: 6,
    title: "Laspeyres Aggregation",
    tag: "DGCA Route Weighted",
    shortDesc: "Chains elementary series using official DGCA passenger-traffic weights over Trailing 12-Month period.",
    details: [
      "Chained Laspeyres formula weights each route by its passenger traffic share in the 12-route basket.",
      "Weights derived from DGCA city-pair data over Trailing 12-Month window (June 2025 - May 2026).",
      "Route weights sum to 1.0 (DEL-BOM 19.2%, DEL-BLR 13.6%, down to BOM-GOI 3.9%).",
      "Produces the final national APIx headline series for MoSPI CPI augmentation.",
    ],
  },
];

export function PipelineFlow({ className = "" }: { className?: string }) {
  const [expandedStep, setExpandedStep] = useState<number | null>(1);

  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="pb-3 mb-4 border-b border-[#E2E8F0]">
        <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
          Econometric Pipeline Architecture
        </h4>
        <p className="text-[11px] text-[#64748B] mt-0.5">
          From raw multi-tier ingestion through IQR hygiene to chained Laspeyres index aggregation
        </p>
      </div>

      {/* 6-Stage Linear Step Flow */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mb-6">
        {STAGES.map((s) => {
          const isSelected = expandedStep === s.step;
          return (
            <button
              key={s.step}
              type="button"
              onClick={() => setExpandedStep(isSelected ? null : s.step)}
              className={`p-2.5 rounded-xs border text-left transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? "border-[#1E3A8A] bg-blue-50/80 shadow-xs"
                  : "border-[#E2E8F0] bg-slate-50 hover:bg-slate-100"
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono text-[#64748B] mb-1">
                  <span>STEP 0{s.step}</span>
                  {isSelected && <CheckCircle2 className="h-3 w-3 text-[#1E3A8A]" />}
                </div>
                <div className="font-mono font-bold text-xs text-[#0F172A] line-clamp-1">
                  {s.title}
                </div>
              </div>
              <div className="text-[10px] text-[#64748B] font-sans mt-2 line-clamp-2">
                {s.tag}
              </div>
            </button>
          );
        })}
      </div>

      {/* Detail Drawer for Selected Stage */}
      {expandedStep !== null && (
        <div className="p-4 bg-slate-50 border border-[#E2E8F0] rounded-xs transition-all">
          {(() => {
            const current = STAGES.find((s) => s.step === expandedStep);
            if (!current) return null;

            return (
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-[#1E3A8A] font-bold">
                      STAGE 0{current.step}:
                    </span>
                    <h5 className="text-lg font-bold text-[#0F172A]">
                      {current.title}
                    </h5>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-[#0F172A] text-white px-2 py-0.5 rounded-xs">
                    {current.tag}
                  </span>
                </div>

                <p className="text-xs text-[#0F172A] font-medium mb-3">
                  {current.shortDesc}
                </p>

                <ul className="space-y-1.5 text-xs text-[#64748B] font-sans">
                  {current.details.map((d, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-[#1E3A8A] font-mono font-bold">›</span>
                      <span className="leading-relaxed">{d}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
