"use client";

import React from "react";
import { LandingNavbar } from "@/components/landing/LandingNavbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { KeyMetricsRibbon } from "@/components/landing/KeyMetricsRibbon";
import { InteractiveRouteMatrix } from "@/components/landing/InteractiveRouteMatrix";
import { AdvanceWindowVisualizer } from "@/components/landing/AdvanceWindowVisualizer";
import { MethodologyPipeline } from "@/components/landing/MethodologyPipeline";
import { ApiDeveloperSection } from "@/components/landing/ApiDeveloperSection";
import { LandingFooter } from "@/components/landing/LandingFooter";

export default function LandingPage() {
  return (
    <div className="w-full min-h-screen bg-[#F8FAFC] text-[#0F172A] flex flex-col font-sans selection:bg-[#1E3A8A] selection:text-white">
      {/* Top sticky landing navigation */}
      <LandingNavbar />

      {/* Main landing contents */}
      <main className="flex-1 w-full">
        {/* Hero Section with live headline metrics & terminal */}
        <HeroSection />

        {/* 4-Pillar Metric Highlights */}
        <KeyMetricsRibbon />

        {/* Interactive DGCA Corridors Matrix */}
        <InteractiveRouteMatrix />

        {/* Advance Horizon Decoupling Visualizer (T+1 to T+45) */}
        <AdvanceWindowVisualizer />

        {/* 4-Stage Statistical Pipeline (Ingestion -> Jevons -> Laspeyres) */}
        <MethodologyPipeline />

        {/* REST API & Developer Integration */}
        <ApiDeveloperSection />
      </main>

      {/* Institutional Footer */}
      <LandingFooter />
    </div>
  );
}

