"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useData } from "@/lib/api/dataContext";
import type { RouteSnapshot } from "@/lib/api/types";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import defaultRoutes from "@/data/fixtures/routes.json";

export function InteractiveRouteMatrix() {
  const { provider } = useData();
  const [routes, setRoutes] = useState<RouteSnapshot[]>(defaultRoutes as RouteSnapshot[]);

  useEffect(() => {
    let mounted = true;
    async function loadRoutes() {
      try {
        const rts = await provider.getRoutes();
        if (mounted && rts && rts.length > 0) setRoutes(rts);
      } catch (err) {
        // fallback to default
      }
    }
    loadRoutes();
    return () => {
      mounted = false;
    };
  }, [provider]);

  // Duplicate items for seamless infinite marquee loop
  const displayRoutes = [...routes, ...routes];

  return (
    <section id="corridors" className="py-16 sm:py-20 bg-white border-b border-[#E2E8F0] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-10">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-[#0F172A] tracking-tight">
              India&apos;s 12 High-Density Air Corridors
            </h2>
            <p className="text-xs sm:text-sm text-[#64748B] mt-1.5 max-w-2xl">
              Calibrated by official DGCA domestic passenger traffic weights to represent economic activity across major metro centers.
            </p>
          </div>

          <Link
            href="/routes"
            className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-[#1E3A8A] hover:underline self-start md:self-auto"
          >
            <span>View All Routes Analytics</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Infinite Autoplay Marquee Scrolling Left to Right with Pause on Hover */}
      <div className="relative w-full overflow-hidden py-4 group">
        {/* Edge gradient masks for smooth fade */}
        <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-white to-transparent z-10 hidden sm:block" />
        <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-white to-transparent z-10 hidden sm:block" />

        <div className="flex w-max gap-5 animate-marquee-ltr group-hover:[animation-play-state:paused]">
          {displayRoutes.map((route, idx) => {
            const isPositive = (route.change_pct ?? 0) >= 0;
            const weightPct = ((route.weight ?? 0) * 100).toFixed(1);

            return (
              <Link
                key={`${route.route_id}-${idx}`}
                href={`/routes/${route.route_id}`}
                className="w-[300px] sm:w-[320px] shrink-0 p-5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] hover:border-[#1E3A8A] hover:bg-white hover:shadow-md transition-all flex flex-col justify-between select-none"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-base font-bold font-mono text-[#0F172A] group-hover:text-[#1E3A8A] transition-colors">
                        {route.origin} → {route.destination}
                      </span>
                      <ArrowUpRight className="h-4 w-4 text-[#94A3B8] group-hover:text-[#1E3A8A] transition-colors" />
                    </div>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 text-[#1E3A8A] font-semibold border border-blue-200/80">
                      {weightPct}% WT
                    </span>
                  </div>

                  <div className="text-xs text-[#64748B] mb-3">
                    {route.origin_city} to {route.destination_city}
                  </div>

                  {/* Weight progress bar */}
                  <div className="w-full bg-[#E2E8F0] h-1.5 rounded-full overflow-hidden mb-3">
                    <div
                      className="bg-[#1E3A8A] h-full rounded-full"
                      style={{ width: `${Math.min(100, Math.max(10, Number(weightPct) * 4.5))}%` }}
                    />
                  </div>
                </div>

                <div className="pt-3 border-t border-[#E2E8F0] flex items-end justify-between text-xs font-mono">
                  <div>
                    <span className="text-[10px] uppercase text-[#64748B] block">
                      Current Index
                    </span>
                    <div className="flex items-baseline gap-1.5 mt-0.5">
                      <span className="text-sm font-bold text-[#0F172A]">
                        {route.current_index?.toFixed(1) ?? "100.0"}
                      </span>
                      <span
                        className={`text-[10px] font-semibold ${
                          isPositive ? "text-[#1D4ED8]" : "text-[#DC2626]"
                        }`}
                      >
                        {isPositive ? `+${route.change_pct?.toFixed(1)}%` : `${route.change_pct?.toFixed(1)}%`}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] uppercase text-[#64748B] block">
                      Mean Fare
                    </span>
                    <span className="text-xs font-bold text-[#0F172A] mt-0.5 block">
                      {route.average_fare ? `₹${route.average_fare.toLocaleString("en-IN")}` : "—"}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      <style jsx global>{`
        @keyframes marquee-ltr {
          0% {
            transform: translateX(-50%);
          }
          100% {
            transform: translateX(0%);
          }
        }
        .animate-marquee-ltr {
          animation: marquee-ltr 35s linear infinite;
        }
      `}</style>
    </section>
  );
}
