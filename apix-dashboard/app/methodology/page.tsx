import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Scale } from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="space-y-12 max-w-5xl">
      {/* Page Header */}
      <PageHeader
        eyebrow="Econometric Foundations · MoSPI CPI Augmentation"
        title="Index Construction Methodology"
        subtitle="Technical documentation for the Ministry of Statistics and Programme Implementation (MoSPI) and Reserve Bank of India (RBI) regarding daily airfare price index calculation, matched-sample chaining, and DGCA passenger weighting."
      />

      {/* Overview Card */}
      <div className="border border-[#E2E8F0] bg-white rounded-sm p-6 space-y-4 shadow-xs">
        <div className="flex items-center gap-2">
          <Scale className="h-5 w-5 text-[#1E3A8A]" />
          <h3 className="text-xl font-bold text-[#0F172A]">
            Econometric Problem Statement & Purpose
          </h3>
        </div>
        <p className="text-xs text-[#64748B] leading-relaxed">
          Airfare constitutes an increasingly significant share of modern Indian urban consumer expenditure. However, conventional Consumer Price Index (CPI) collection relies on monthly physical surveys of static airline tariff sheets that fail to capture dynamic pricing algorithms, advance-purchase yield curves, or sold-out flight effects. APIx resolves this gap by automating daily multi-horizon price collection across major trunk routes and computing official elementary and aggregate price indices under international statistical standards (ILO/IMF Consumer Price Index Manual 2020).
        </p>
      </div>

      {/* Pillar 01: Data Collection & Scope */}
      <div className="border-t border-[#E2E8F0] pt-8 space-y-4">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded-xs border border-[#1E3A8A]/30">
            PILLAR 01
          </span>
          <h3 className="text-2xl font-bold text-[#0F172A]">
            Price Scope & Multi-Tier Collection Architecture
          </h3>
        </div>

        <p className="text-xs text-[#64748B] leading-relaxed">
          In accordance with the BLS and Eurostat standards for consumer price indices, APIx observes the <strong>total consumer price paid</strong> at the point of booking, rather than unbundled airline base fares. This encompasses base commercial fare, airline fuel surcharges (YQ), User Development Fees (UDF), Passenger Service Fees (PSF), Goods and Services Tax (GST), and mandatory OTA platform convenience fees.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="p-4 bg-white border border-[#E2E8F0] rounded-xs space-y-2 shadow-xs">
            <h4 className="font-mono text-xs font-semibold text-[#0F172A] uppercase">
              12 DGCA Domestic Trunk Routes
            </h4>
            <p className="text-xs text-[#64748B] leading-relaxed">
              Tracked across 7 metropolitan aviation hubs: Delhi (DEL), Mumbai (BOM), Bengaluru (BLR), Kolkata (CCU), Chennai (MAA), Hyderabad (HYD), and Goa (GOI). Represents over 65% of scheduled domestic seat-kilometers.
            </p>
          </div>

          <div className="p-4 bg-white border border-[#E2E8F0] rounded-xs space-y-2 shadow-xs">
            <h4 className="font-mono text-xs font-semibold text-[#0F172A] uppercase">
              5 Advance-Purchase Horizons
            </h4>
            <p className="text-xs text-[#64748B] leading-relaxed">
              Collected daily across <strong>T+1</strong> (next-day departure), <strong>T+7</strong> (1 week), <strong>T+15</strong> (2 weeks), <strong>T+30</strong> (1 month), and <strong>T+45</strong> (45 days) to measure distinct consumer booking lead behaviors without cross-window contamination.
            </p>
          </div>
        </div>
      </div>

      {/* Pillar 02: Elementary Jevons Index */}
      <div className="border-t border-[#E2E8F0] pt-8 space-y-4">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded-xs border border-[#1E3A8A]/30">
            PILLAR 02
          </span>
          <h3 className="text-2xl font-bold text-[#0F172A]">
            Elementary Level: Jevons Index & Matched-Sample Chaining
          </h3>
        </div>

        <p className="text-xs text-[#64748B] leading-relaxed">
          At the elementary level (within a specific route and advance window), price observations lack individual quantity weights. Traditional arithmetic formulas (Carli and Dutot) suffer from severe mathematical defects when applied to high-dispersion airline fares:
        </p>

        {/* Formula Box */}
        <div className="p-5 bg-white border border-[#E2E8F0] rounded-xs font-mono text-xs space-y-3 shadow-xs">
          <div className="text-[11px] text-[#1E3A8A] uppercase font-semibold">
            Jevons Geometric Mean Formula:
          </div>
          <div className="p-3 bg-slate-50 border border-[#E2E8F0] rounded-xs text-sm text-[#0F172A] overflow-x-auto text-center font-mono font-medium italic">
            I_Jevons^(t-1 → t) = [ ∏_(i ∈ S_t) ( p_(i,t) / p_(i,t-1) ) ] ^ (1 / |S_t|)
          </div>
          <p className="text-[11px] text-[#64748B] font-sans leading-relaxed">
            Where <em>S_t</em> represents the set of matched flight observations present in both observation period <em>t</em> and base period <em>t-1</em>, <em>p_(i,t)</em> is the total consumer fare for flight <em>i</em> on day <em>t</em>, and <em>|S_t|</em> is the count of matched observations.
          </p>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-xs space-y-2 shadow-xs">
          <h4 className="font-mono text-xs font-semibold text-[#0F172A] uppercase">
            Why Jevons Over Carli or Dutot?
          </h4>
          <ul className="space-y-1.5 text-xs text-[#64748B]">
            <li className="flex items-start gap-2">
              <span className="text-[#1E3A8A] font-mono font-bold">›</span>
              <span><strong>Time-Reversal Test:</strong> The Jevons index satisfies the time-reversal axiom: I^(t-1 → t) · I^(t → t-1) = 1.0. In contrast, the Carli arithmetic mean creates a persistent upward bias when prices oscillate.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#1E3A8A] font-mono font-bold">›</span>
              <span><strong>Commensurability:</strong> Invariant to changes in measurement units or airline currency denomination.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#1E3A8A] font-mono font-bold">›</span>
              <span><strong>Pure Price Change Isolation:</strong> Comparisons strictly compare T+7 today vs T+7 yesterday. Never cross advance horizons, which would confound product quality with price movement.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Pillar 03: Upper-Level Laspeyres Aggregation */}
      <div className="border-t border-[#E2E8F0] pt-8 space-y-4">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded-xs border border-[#1E3A8A]/30">
            PILLAR 03
          </span>
          <h3 className="text-2xl font-bold text-[#0F172A]">
            Upper-Level Aggregation: Fixed-Base Laspeyres with DGCA Traffic Weights
          </h3>
        </div>

        <p className="text-xs text-[#64748B] leading-relaxed">
          Elementary indices for each route are aggregated into the national APIx index using a fixed-base Laspeyres model weighted by domestic passenger traffic shares reported by the Directorate General of Civil Aviation (DGCA). Every day is compared against the base period, not against the previous day.
        </p>

        {/* Laspeyres Formula */}
        <div className="p-5 bg-white border border-[#E2E8F0] rounded-xs font-mono text-xs space-y-3 shadow-xs">
          <div className="text-[11px] text-[#1E3A8A] uppercase font-semibold">
            Fixed-Base Laspeyres Aggregation Formula:
          </div>
          <div className="p-3 bg-slate-50 border border-[#E2E8F0] rounded-xs text-sm text-[#0F172A] overflow-x-auto text-center font-mono font-medium italic">
            I_APIx^t = 100 × ∑_(r=1)^12 [ w_r × ( I_(r,t) / I_(r,0) ) ]
          </div>
          <p className="text-[11px] text-[#64748B] font-sans leading-relaxed">
            Where <em>w_r</em> is the official passenger traffic weight of route <em>r</em> derived from DGCA Trailing 12-Month city-pair statistics (normalised to sum to 1.0), and <em>I_(r,t)</em> is the elementary index for route <em>r</em> on day <em>t</em>.
          </p>
          <p className="text-[11px] text-[#64748B] font-sans leading-relaxed border-t border-[#E2E8F0] pt-3">
            <strong>Why not a daily chain.</strong> A daily-chained index multiplies a weighted <em>arithmetic</em> mean of price relatives at every step. By Jensen&apos;s inequality that mean exceeds 1 for noisy trendless prices — by exp(σ²) per link, which compounds to exp(nσ²). At airfare dispersion (σ ≈ 0.08) that is roughly <strong>+0.64% per day of purely spurious inflation</strong>. This is the documented high-frequency chain-drift problem (Ivancic, Diewert &amp; Fox 2011; Eurostat 2022; ONS 2023), and it is why CPI itself is not daily-chained. Under the fixed-base form, prices that rise and return to their starting level return the index to exactly 100.
          </p>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-xs space-y-2 shadow-xs">
          <h4 className="font-mono text-xs font-semibold text-[#0F172A] uppercase">
            Authoritative DGCA Passenger Weighting Spec
          </h4>
          <p className="text-xs text-[#64748B] leading-relaxed">
            Route weights are derived via <code>scripts/derive_weights.py</code> over the Trailing 12-Month window (June 2025 to May 2026) using official city-pair passenger records:
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-xs pt-1">
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">DEL-BOM: <strong>19.22%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">DEL-BLR: <strong>13.60%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">BOM-BLR: <strong>11.56%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">DEL-HYD: <strong>8.94%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">DEL-CCU: <strong>8.18%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">BLR-HYD: <strong>6.60%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">BOM-CCU: <strong>6.55%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">DEL-MAA: <strong>6.54%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">BOM-MAA: <strong>6.13%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">DEL-GOI: <strong>4.48%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">BLR-MAA: <strong>4.26%</strong></div>
            <div className="p-2 bg-slate-50 border border-[#E2E8F0] rounded-xs">BOM-GOI: <strong>3.94%</strong></div>
          </div>
        </div>
      </div>

      {/* Pillar 04: Quality Controls & Metropolitan Catchment */}
      <div className="border-t border-[#E2E8F0] pt-8 space-y-4">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded-xs border border-[#1E3A8A]/30">
            PILLAR 04
          </span>
          <h3 className="text-2xl font-bold text-[#0F172A]">
            Quality Hygiene, Outlier Screening & Catchment Normalization
          </h3>
        </div>

        <div className="space-y-3 text-xs text-[#64748B] leading-relaxed">
          <div className="p-4 bg-white border border-[#E2E8F0] rounded-xs space-y-2 shadow-xs">
            <h4 className="font-mono text-xs font-semibold text-[#0F172A] uppercase">
              Metropolitan Catchment Aggregation (Multi-Airport Markets)
            </h4>
            <p>
              Passengers booking flights to multi-airport metropolitan regions treat airports within the catchment as interchangeable economic substitutes. APIx aggregates:
            </p>
            <ul className="space-y-1 list-disc list-inside">
              <li><strong>Goa Catchment:</strong> Sums Dabolim (<code>GOI</code>) + Manohar International at Mopa (<code>GOX</code>) traffic into a single destination market code <code>GOI</code>.</li>
              <li><strong>Mumbai Catchment:</strong> Consolidates CSMT (<code>BOM</code>) and Navi Mumbai (<code>NMI</code>) to <code>BOM</code>.</li>
            </ul>
          </div>

          <div className="p-4 bg-white border border-[#E2E8F0] rounded-xs space-y-2 shadow-xs">
            <h4 className="font-mono text-xs font-semibold text-[#0F172A] uppercase">
              Outlier Screening & Sold-Out Handling
            </h4>
            <ul className="space-y-1.5">
              <li className="flex items-start gap-2">
                <span className="text-[#1E3A8A] font-mono font-bold">›</span>
                <span><strong>Time-Relative Screening:</strong> Each carrier&apos;s own period-to-period price relatives are screened by median absolute deviation on log relatives. Screening is deliberately <em>not</em> cross-sectional: flagging a carrier for being priced differently from its rivals treats genuine market dispersion as error and biases the index toward the cheapest carrier. Outliers are tagged, never deleted, and excluded from price relatives downstream.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#1E3A8A] font-mono font-bold">›</span>
                <span><strong>Sold-Out Observations:</strong> Unavailable flights are stored strictly with <code>total_fare_inr = null</code> and <code>quality_flag = &apos;sold_out&apos;</code>. They drop out of matched-sample chaining and are <strong>NEVER converted to ₹0.00</strong>, which would cause catastrophic false deflation.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
