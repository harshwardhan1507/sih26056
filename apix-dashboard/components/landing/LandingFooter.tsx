"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUp,
  LayoutDashboard,
  TrendingUp,
  Compass,
  Clock,
  BookOpen,
  ShieldCheck,
  Code2,
  FileCode,
  Radio,
  FileText,
} from "lucide-react";

export function LandingFooter() {
  const scrollToTop = () => {
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <footer className="bg-white border-t border-[#E2E8F0] text-[#64748B] font-sans selection:bg-[#1E3A8A] selection:text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
        {/* Top Header Row: Status Indicator & Launch Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-12 border-b border-[#E2E8F0]">
          <div className="flex items-center gap-2 text-xs font-mono tracking-wider uppercase text-[#475569]">
            <span className="h-2 w-2 rounded-full bg-[#1E3A8A] animate-pulse" />
            <span className="font-semibold text-[#0F172A]">Active National Indexation Engine</span>
            <span className="text-[#94A3B8]">·</span>
            <span>MoSPI CPI 2024 Series</span>
          </div>

          <Link
            href="/overview"
            className="inline-flex items-center gap-2 text-xs font-semibold text-[#1E3A8A] hover:text-[#1D4ED8] group transition-colors self-start sm:self-auto"
          >
            <span>Launch Operational Dashboard</span>
            <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Huge Brand Typography Section */}
        <div className="py-12 sm:py-16">
          <h2 className="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black tracking-tighter text-[#0F172A] leading-none select-none">
            APIx<span className="text-[#1E3A8A]">.</span>
          </h2>
          <p className="text-xs sm:text-sm md:text-base text-[#64748B] font-mono mt-4 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-[#0F172A] font-semibold">Real-Time Airfare Price Index</span>
            <span className="text-[#CBD5E1]">·</span>
            <span>MoSPI CPI 2024 Augmentation</span>
            <span className="text-[#CBD5E1]">·</span>
            <span>Problem Statement SIH-26056</span>
          </p>
        </div>

        {/* Multi-Column Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 py-12 border-y border-[#E2E8F0] text-xs">
          {/* Column 1: Live Portal & Dashboard */}
          <div className="space-y-4">
            <h4 className="text-[11px] font-mono uppercase tracking-wider text-[#0F172A] font-bold">
              Portal & Dashboard
            </h4>
            <ul className="space-y-3">
              <li>
                <Link
                  href="/overview"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <LayoutDashboard className="h-4 w-4 text-[#94A3B8]" />
                  <span>National Overview Dashboard</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/index-trend"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <TrendingUp className="h-4 w-4 text-[#94A3B8]" />
                  <span>Historical Index Trends</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/routes"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <Compass className="h-4 w-4 text-[#94A3B8]" />
                  <span>12 DGCA Traffic Corridors</span>
                </Link>
              </li>
              <li>
                <a
                  href="#advance-pricing"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <Clock className="h-4 w-4 text-[#94A3B8]" />
                  <span>5 Advance Booking Horizons</span>
                </a>
              </li>
            </ul>
          </div>

          {/* Column 2: Methodology & Data Audit */}
          <div className="space-y-4">
            <h4 className="text-[11px] font-mono uppercase tracking-wider text-[#0F172A] font-bold">
              Methodology & Audit
            </h4>
            <ul className="space-y-3">
              <li>
                <Link
                  href="/methodology"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <BookOpen className="h-4 w-4 text-[#94A3B8]" />
                  <span>Chained Jevons Formulation</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/data/quality"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <ShieldCheck className="h-4 w-4 text-[#94A3B8]" />
                  <span>Data Quality & Hygiene Engine</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/sources"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <Radio className="h-4 w-4 text-[#94A3B8]" />
                  <span>Sources & Multi-Tier Provenance</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/routes/DEL-BOM"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <FileText className="h-4 w-4 text-[#94A3B8]" />
                  <span>Delhi-Mumbai Route Dossier</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Developer & Feeds */}
          <div className="space-y-4">
            <h4 className="text-[11px] font-mono uppercase tracking-wider text-[#0F172A] font-bold">
              Developer & Feeds
            </h4>
            <ul className="space-y-3">
              <li>
                <Link
                  href="/api-docs"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <Code2 className="h-4 w-4 text-[#94A3B8]" />
                  <span>FastAPI OpenAPI Specs</span>
                </Link>
              </li>
              <li>
                <a
                  href="#api"
                  className="flex items-center gap-2.5 text-[#475569] hover:text-[#1E3A8A] transition-colors"
                >
                  <FileCode className="h-4 w-4 text-[#94A3B8]" />
                  <span>REST API Endpoints Reference</span>
                </a>
              </li>
              <li>
                <span className="flex items-center gap-2.5 text-[#64748B]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#1E3A8A]" />
                  <span>Sub-10ms Automated CPI Ingestion</span>
                </span>
              </li>
              <li>
                <span className="flex items-center gap-2.5 text-[#64748B]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#1E3A8A]" />
                  <span>DGCA Passenger Traffic Weights</span>
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar with Language / Meta, Copyright, and Back to Top Button */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] font-mono text-[#64748B]">
          <div className="flex items-center gap-4">
            <span className="font-semibold text-[#0F172A] border-b-2 border-[#1E3A8A] pb-0.5">
              English
            </span>
            <span className="text-[#94A3B8]">·</span>
            <span>Ministry of Statistics & Programme Implementation</span>
          </div>

          <div className="text-center sm:text-left text-[#94A3B8]">
            © 2026 <strong className="text-[#475569]">APIx</strong> · SIH Problem Statement SIH-26056. All rights reserved.
          </div>

          {/* Scroll to Top Circle Button */}
          <button
            onClick={scrollToTop}
            title="Scroll to top"
            className="w-9 h-9 rounded-full bg-[#F1F5F9] hover:bg-[#E2E8F0] border border-[#CBD5E1] flex items-center justify-center text-[#0F172A] hover:text-[#1E3A8A] shadow-xs transition-all hover:scale-105 active:scale-95 cursor-pointer"
            aria-label="Back to top"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </div>
    </footer>
  );
}
