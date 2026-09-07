"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Layers,
  Filter,
  Calculator,
  BarChart,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

export function MethodologyPipeline() {
  const [activeStep, setActiveStep] = useState<number>(0);

  const steps = [
    {
      stepNumber: "01",
      icon: Layers,
      title: "Multi-Tier Ingestion",
      tag: "Automated & Compliant",
      shortDesc: "Daily collection across airline published tariff sheets (Tier 2), compliant HAR replay (Tier 3), and synthetic fallback (Tier 4).",
      formula: "S = { IndiGo, Air India, Akasa, SpiceJet }",
      highlights: [
        "Off-peak IST 02:00-05:00 scraping window respect",
        "Carrier-aware multi-tier resolver fallback",
        "Polite per-host token bucket rate limiting",
      ],
    },
    {
      stepNumber: "02",
      icon: Filter,
      title: "Hygiene & Outlier Defence",
      tag: "Strict Data Invariants",
      shortDesc: "Automated IQR outlier filtration and strict data invariant verification before statistical processing.",
      formula: "Sanity: ₹1,500 ≤ P_quote ≤ ₹60,000;  P_sold_out = null",
      highlights: [
        "Sold-out vs missing distinction (never coerced to 0.00)",
        "Interquartile Range (IQR) flare filter",
        "Deduplication across identical flight code & timestamp",
      ],
    },
    {
      stepNumber: "03",
      icon: Calculator,
      title: "Matched-Sample Chained Jevons",
      tag: "Elementary Formulation",
      shortDesc: "Computes geometric mean of price ratios strictly across matched flight pairs to prevent artificial composition drift.",
      formula: "I_r,w(t-1 → t) = ∏ (P_k,t / P_k,t-1)^(1/n)",
      highlights: [
        "Matches exact carrier flight and advance window",
        "Chain-linked sequentially to avoid ungrounded substitution",
        "Compliant with UN CPI Manual 2020 standards",
      ],
    },
    {
      stepNumber: "04",
      icon: BarChart,
      title: "DGCA Laspeyres Aggregation",
      tag: "National Headline Index",
      shortDesc: "Aggregates elementary route indices using official DGCA passenger traffic weights into the headline national series.",
      formula: "APIx_t = ∑ (w_r * I_r,t),  where ∑ w_r = 1.000",
      highlights: [
        "Base period normalized: August 2026 = 100.0",
        "Quarterly DGCA passenger traffic weighting",
        "Sub-millisecond index aggregation pipeline",
      ],
    },
  ];

  return (
    <section id="methodology" className="py-16 sm:py-20 bg-white border-b border-[#E2E8F0]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-[#0F172A] tracking-tight">
              Four-Stage National Index Architecture
            </h2>
            <p className="text-xs sm:text-sm text-[#64748B] mt-1.5 max-w-2xl">
              From automated carrier fare harvesting to high-integrity Laspeyres index publishing for the Ministry of Statistics.
            </p>
          </div>

          <Link
            href="/methodology"
            className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-[#1E3A8A] hover:underline self-start md:self-auto"
          >
            <span>Read Full Mathematical Dossier</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 4 Step Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isSelected = activeStep === idx;

            return (
              <button
                key={idx}
                onClick={() => setActiveStep(idx)}
                className={`text-left p-5 rounded-lg border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? "bg-blue-50/50 border-[#1E3A8A] ring-1 ring-[#1E3A8A] shadow-xs"
                    : "bg-white border-[#E2E8F0] hover:border-slate-300"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[11px] font-mono font-bold text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      STEP {step.stepNumber}
                    </span>
                    <div className="p-1.5 rounded bg-[#F8FAFC] text-[#1E3A8A] border border-[#E2E8F0]">
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>

                  <h3 className="text-sm font-bold text-[#0F172A] mb-1.5">
                    {step.title}
                  </h3>

                  <p className="text-xs text-[#64748B] leading-relaxed mb-3">
                    {step.shortDesc}
                  </p>
                </div>

                <div className="text-[11px] font-mono text-[#1E3A8A] font-medium">
                  {step.tag}
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Stage Detail */}
        <div className="rounded-lg bg-[#F8FAFC] border border-[#E2E8F0] p-6 sm:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div className="lg:col-span-7 space-y-3">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#1E3A8A] text-white">
                  PHASE {steps[activeStep].stepNumber}
                </span>
                <h4 className="text-lg font-bold text-[#0F172A]">
                  {steps[activeStep].title}
                </h4>
              </div>

              <p className="text-xs sm:text-sm text-[#64748B] leading-relaxed">
                {steps[activeStep].shortDesc}
              </p>

              <div className="space-y-1.5 pt-1">
                {steps[activeStep].highlights.map((h, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-[#0F172A]">
                    <CheckCircle2 className="h-4 w-4 text-[#1E3A8A] shrink-0" />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-5 bg-white rounded-lg p-5 border border-[#E2E8F0] font-mono text-xs shadow-2xs">
              <div className="text-[#64748B] text-[10px] uppercase pb-2 mb-2 border-b border-[#E2E8F0]">
                Mathematical Specification
              </div>
              <div className="p-3 rounded bg-[#F8FAFC] border border-[#E2E8F0] text-[#1E3A8A] font-mono text-xs tracking-wide">
                {steps[activeStep].formula}
              </div>
              <div className="text-[10px] text-[#64748B] mt-2">
                Calibrated against MoSPI guidelines & DGCA data standards.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
