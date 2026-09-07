"use client";

import React, { useState } from "react";

interface WindowDetail {
  code: string;
  name: string;
  horizon: string;
  multiplier: string;
  description: string;
  cpiWeight: string;
  exampleFares: { carrier: string; price: number }[];
}

const ADVANCE_WINDOWS: Record<string, WindowDetail> = {
  "T+1": {
    code: "T+1",
    name: "Urgent Window",
    horizon: "24 Hours to Departure",
    multiplier: "+68% vs Base",
    cpiWeight: "15% Weight",
    description: "Captures peak last-minute demand and dynamic surge pricing where discounted fare buckets are closed.",
    exampleFares: [
      { carrier: "IndiGo (6E)", price: 9850 },
      { carrier: "Air India (AI)", price: 11400 },
      { carrier: "Akasa (QP)", price: 9200 },
    ],
  },
  "T+7": {
    code: "T+7",
    name: "Near-Term Window",
    horizon: "7 Days to Departure",
    multiplier: "+32% vs Base",
    cpiWeight: "25% Weight",
    description: "Reflects short-notice travel demand and mid-tier revenue management adjustments.",
    exampleFares: [
      { carrier: "IndiGo (6E)", price: 7600 },
      { carrier: "Air India (AI)", price: 8250 },
      { carrier: "Akasa (QP)", price: 7100 },
    ],
  },
  "T+15": {
    code: "T+15",
    name: "Median Benchmark",
    horizon: "15 Days to Departure",
    multiplier: "Reference Median",
    cpiWeight: "30% Weight",
    description: "The primary representative anchor for standard scheduled domestic travel across all carriers.",
    exampleFares: [
      { carrier: "IndiGo (6E)", price: 6450 },
      { carrier: "Air India (AI)", price: 6800 },
      { carrier: "Akasa (QP)", price: 5950 },
    ],
  },
  "T+30": {
    code: "T+30",
    name: "Early Planned",
    horizon: "30 Days to Departure",
    multiplier: "-18% vs Median",
    cpiWeight: "20% Weight",
    description: "Baseline inventory release pricing where advance discount fare classes remain accessible.",
    exampleFares: [
      { carrier: "IndiGo (6E)", price: 5200 },
      { carrier: "Air India (AI)", price: 5500 },
      { carrier: "Akasa (QP)", price: 4850 },
    ],
  },
  "T+45": {
    code: "T+45",
    name: "Base Horizon",
    horizon: "45 Days to Departure",
    multiplier: "-26% vs Median",
    cpiWeight: "10% Weight",
    description: "Earliest scheduled baseline pricing before dynamic inventory controls take effect.",
    exampleFares: [
      { carrier: "IndiGo (6E)", price: 4890 },
      { carrier: "Air India (AI)", price: 5150 },
      { carrier: "Akasa (QP)", price: 4600 },
    ],
  },
};

export function AdvanceWindowVisualizer() {
  const [selectedWindow, setSelectedWindow] = useState<string>("T+15");
  const current = ADVANCE_WINDOWS[selectedWindow];

  return (
    <section id="advance-pricing" className="py-16 sm:py-20 bg-white border-b border-[#E2E8F0]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-[#0F172A] tracking-tight">
            Controlling for Dynamic Yield Management
          </h2>
          <p className="text-xs sm:text-sm text-[#64748B] mt-2 leading-relaxed">
            Airline pricing changes dramatically based on lead time. APIx isolates lead-time variation by stratifying price quotes across 5 fixed advance booking windows.
          </p>
        </div>

        {/* 5 Tab Selector */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8 max-w-4xl mx-auto">
          {Object.keys(ADVANCE_WINDOWS).map((wKey) => {
            const w = ADVANCE_WINDOWS[wKey];
            const isSelected = selectedWindow === wKey;
            return (
              <button
                key={wKey}
                onClick={() => setSelectedWindow(wKey)}
                className={`p-3.5 rounded-lg border text-left transition-all cursor-pointer ${
                  isSelected
                    ? "bg-white border-[#1E3A8A] shadow-xs ring-1 ring-[#1E3A8A]"
                    : "bg-white/80 border-[#E2E8F0] hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`text-sm font-mono font-bold ${
                      isSelected ? "text-[#1E3A8A]" : "text-[#0F172A]"
                    }`}
                  >
                    {w.code}
                  </span>
                  <span className="text-[10px] font-mono text-[#64748B]">
                    {w.cpiWeight}
                  </span>
                </div>
                <div className="text-xs text-[#0F172A] font-medium truncate">
                  {w.name}
                </div>
                <div className="text-[11px] font-mono text-[#64748B] mt-0.5 truncate">
                  {w.multiplier}
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Horizon Card */}
        <div className="max-w-4xl mx-auto rounded-lg bg-white border border-[#E2E8F0] p-6 sm:p-8 shadow-xs">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-7 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold font-mono text-[#0F172A]">
                  {current.code}
                </span>
                <span className="text-xs font-semibold font-mono text-[#1E3A8A] bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                  {current.horizon}
                </span>
              </div>

              <h3 className="text-base font-bold text-[#0F172A]">
                {current.name}
              </h3>

              <p className="text-xs text-[#64748B] leading-relaxed">
                {current.description}
              </p>
            </div>

            {/* Carrier sample fares */}
            <div className="md:col-span-5 bg-[#F8FAFC] rounded-lg p-4 border border-[#E2E8F0] space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-[#E2E8F0] text-[11px] font-mono text-[#64748B]">
                <span>DEL-BOM Carrier Fare</span>
                <span>Price</span>
              </div>

              {current.exampleFares.map((f, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-xs py-1 font-mono"
                >
                  <span className="text-[#0F172A]">{f.carrier}</span>
                  <span className="font-bold text-[#0F172A]">
                    ₹{f.price.toLocaleString("en-IN")}
                  </span>
                </div>
              ))}

              <div className="pt-2 border-t border-[#E2E8F0] text-[10px] text-[#64748B] font-mono text-center">
                Strict matched carrier-flight tracking across collection dates
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
