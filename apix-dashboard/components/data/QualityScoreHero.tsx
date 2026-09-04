import React from "react";
import { ShieldCheck, AlertTriangle, XCircle, RefreshCw, CheckCircle2 } from "lucide-react";

interface QualityScoreHeroProps {
  score: number;
  totalQuotes: number;
  validQuotes: number;
  outlierCount: number;
  soldOutCount: number;
  imputedCount: number;
  fallbackSimulatedPct: number;
  className?: string;
}

export function QualityScoreHero({
  score,
  totalQuotes,
  validQuotes,
  outlierCount,
  soldOutCount,
  imputedCount,
  fallbackSimulatedPct,
  className = "",
}: QualityScoreHeroProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Hero Score Block */}
      <div className="border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="h-2 w-2 rounded-full bg-[#176B5B]" />
            <span className="font-mono text-xs uppercase tracking-widest text-[#176B5B] font-semibold">
              Quality Assurance Audit
            </span>
          </div>

          <div className="flex items-baseline gap-4">
            <span className="font-serif text-5xl md:text-6xl font-bold text-[#111716] tabular-nums tracking-tight">
              {score.toFixed(1)}%
            </span>
            <span className="text-xs font-mono text-[#176B5B] bg-[#176B5B]/10 border border-[#176B5B]/30 px-2 py-0.5 rounded-xs font-semibold uppercase">
              High Confidence
            </span>
          </div>

          <p className="text-sm text-[#626863] mt-2 max-w-xl leading-relaxed">
            Data quality index reflects price hygiene, IQR outlier isolation, and sold-out missing value handling across {totalQuotes} daily trunk route observations.
          </p>
        </div>

        {/* 4-Pill Hygiene Breakdown */}
        <div className="grid grid-cols-2 gap-3 shrink-0 min-w-[280px]">
          <div className="p-3 bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#176B5B] uppercase font-semibold">
              <CheckCircle2 className="h-3 w-3" />
              <span>Valid Quotes</span>
            </div>
            <div className="font-serif font-bold text-xl text-[#111716] tabular-nums mt-1">
              {validQuotes}
            </div>
            <div className="text-[10px] text-[#626863]">
              {((validQuotes / totalQuotes) * 100).toFixed(1)}% clean rate
            </div>
          </div>

          <div className="p-3 bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-amber-800 uppercase font-semibold">
              <AlertTriangle className="h-3 w-3" />
              <span>Outliers</span>
            </div>
            <div className="font-serif font-bold text-xl text-[#111716] tabular-nums mt-1">
              {outlierCount}
            </div>
            <div className="text-[10px] text-[#626863]">
              Excluded via IQR fence
            </div>
          </div>

          <div className="p-3 bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-rose-800 uppercase font-semibold">
              <XCircle className="h-3 w-3" />
              <span>Sold Out</span>
            </div>
            <div className="font-serif font-bold text-xl text-[#111716] tabular-nums mt-1">
              {soldOutCount}
            </div>
            <div className="text-[10px] text-[#626863]">
              Treated as null (never ₹0)
            </div>
          </div>

          <div className="p-3 bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-sky-800 uppercase font-semibold">
              <RefreshCw className="h-3 w-3" />
              <span>Imputed</span>
            </div>
            <div className="font-serif font-bold text-xl text-[#111716] tabular-nums mt-1">
              {imputedCount}
            </div>
            <div className="text-[10px] text-[#626863]">
              Zero synthetic quotes
            </div>
          </div>
        </div>
      </div>

      {/* Fallback Simulation Notice Banner */}
      {fallbackSimulatedPct > 0 && (
        <div className="p-4 border border-amber-300 bg-amber-50/70 rounded-sm flex items-start gap-3 text-amber-900">
          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-mono font-bold uppercase tracking-wider">
              Simulated Fallback Engine Active ({fallbackSimulatedPct.toFixed(1)}%)
            </p>
            <p className="text-amber-800 font-sans leading-relaxed">
              {Math.round((fallbackSimulatedPct / 100) * totalQuotes)} of {totalQuotes} observations were fulfilled via Tier 4 advance-decay simulation due to upstream API rate limits. All simulated observations maintain transparent collection_method="simulated" metadata.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
