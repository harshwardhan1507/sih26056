"use client";

import React from "react";
import { Compass, Clock, BarChart3, ShieldCheck } from "lucide-react";

export function KeyMetricsRibbon() {
  const highlights = [
    {
      icon: Compass,
      title: "12 DGCA Traffic Corridors",
      description: "Weighted by official DGCA passenger-kilometre traffic to represent over 65% of all domestic Indian air travel.",
      tag: "DGCA Calibrated",
    },
    {
      icon: Clock,
      title: "5 Advance Booking Horizons",
      description: "Fixed-window sampling across T+1, T+7, T+15, T+30, and T+45 days to decouple yield management price escalation.",
      tag: "Horizon Stratified",
    },
    {
      icon: BarChart3,
      title: "Matched Chained Jevons",
      description: "Strict carrier-flight pair tracking across consecutive collection dates eliminates artificial index bias and composition drift.",
      tag: "CPI Manual Standard",
    },
    {
      icon: ShieldCheck,
      title: "100% Provenance & Audit",
      description: "Multi-tier ingestion with automated IQR outlier filtration, strict sold-out invariants, and daily audit logs.",
      tag: "MoSPI Aligned",
    },
  ];

  return (
    <section className="py-12 bg-[#F8FAFC] border-b border-[#E2E8F0]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {highlights.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-lg bg-white border border-[#E2E8F0] shadow-2xs hover:border-blue-200 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="p-2 rounded bg-blue-50 text-[#1E3A8A] border border-blue-100">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#F1F5F9] text-[#475569]">
                      {item.tag}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-[#0F172A] tracking-tight mb-1.5">
                    {item.title}
                  </h3>
                  <p className="text-xs text-[#64748B] leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
