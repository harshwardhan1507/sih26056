"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ChevronRight } from "lucide-react";

export function HeroSection() {
  return (
    <section
      id="overview"
      className="relative w-full h-[calc(100vh-4rem)] h-[calc(100dvh-4rem)] min-h-[520px] max-h-[1200px] border-b border-[#E2E8F0] overflow-hidden flex items-center"
    >
      {/* Background image layer covering exact screen ratio */}
      <div className="absolute inset-0 pointer-events-none">
        <img
          src="/bg-sunset-wing.jpg"
          alt="Aviation over clouds at sunset"
          className="w-full h-full object-cover object-center"
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 relative z-10 w-full">
        <div className="max-w-3xl space-y-4 sm:space-y-6">
          {/* White High-Contrast Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black text-white tracking-tight leading-[1.08] drop-shadow-md">
            Real-Time Airfare{" "}
            <span className="text-sky-300">
              Price Index
            </span>{" "}
            for India
          </h1>

          {/* White High-Contrast Subtext */}
          <p className="text-sm sm:text-base md:text-lg text-slate-100 font-medium leading-relaxed max-w-2xl drop-shadow-sm">
            Automated high-frequency price indexation across India&apos;s 12 major aviation corridors and 5 advance-booking horizons. Designed for the Ministry of Statistics and Programme Implementation (MoSPI) to augment national CPI measures.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap items-center gap-3 sm:gap-4 pt-2">
            <Link
              href="/overview"
              className="inline-flex items-center gap-2.5 px-5 py-3 sm:px-6 sm:py-3.5 rounded-md bg-[#1E3A8A] hover:bg-[#1D4ED8] text-white font-semibold text-xs sm:text-sm shadow-lg border border-blue-400/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <span>Launch Operational Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#corridors"
              className="inline-flex items-center gap-2 px-4 py-3 sm:px-5 sm:py-3.5 rounded-md bg-white/95 hover:bg-white text-[#0F172A] font-semibold text-xs sm:text-sm shadow-md backdrop-blur-md transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <span>Explore 12 Corridors</span>
              <ChevronRight className="h-4 w-4 text-[#475569]" />
            </a>
            <Link
              href="/methodology"
              className="inline-flex items-center gap-1.5 px-3 py-3 text-xs font-bold text-white hover:text-sky-300 transition-colors drop-shadow-sm"
            >
              <span>View Methodology</span>
              <span>→</span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
