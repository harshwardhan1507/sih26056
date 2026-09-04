"use client";

import React from "react";
import type { QuoteItem } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { formatUTCtoIST } from "@/lib/formatters/dates";
import { StatusBadge } from "@/components/common/StatusBadge";
import { X, AlertCircle } from "lucide-react";

interface QuoteInspectorModalProps {
  quote: QuoteItem | null;
  onClose: () => void;
}

export function QuoteInspectorModal({
  quote,
  onClose,
}: QuoteInspectorModalProps) {
  if (!quote) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div
        className="bg-white border border-[#E2E8F0] rounded-sm max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-[#E2E8F0]">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-[#1E3A8A] uppercase tracking-widest font-semibold">
                Quote Provenance Inspector
              </span>
              <StatusBadge type="quality" value={quote.quality_flag} size="sm" />
            </div>
            <h3 className="font-mono font-bold text-lg text-[#0F172A] mt-1">
              {quote.id}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-xs hover:bg-slate-100 text-[#64748B] hover:text-[#0F172A] transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Flight & Commercial Details */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-slate-50 border border-[#E2E8F0] rounded-xs text-xs">
          <div>
            <span className="text-[10px] font-mono text-[#64748B] uppercase">
              Flight Segment
            </span>
            <div className="font-mono font-bold text-base text-[#0F172A] mt-0.5">
              {quote.origin_iata} → {quote.destination_iata}
            </div>
            <div className="text-[11px] text-[#64748B]">
              Advance Window: T+{quote.advance_window_days}
            </div>
          </div>

          <div>
            <span className="text-[10px] font-mono text-[#64748B] uppercase">
              Carrier & Class
            </span>
            <div className="font-mono font-bold text-base text-[#0F172A] mt-0.5">
              {quote.carrier_iata} ({quote.fare_class})
            </div>
            <div className="text-[11px] text-[#64748B]">
              Departure: {quote.departure_date}
            </div>
          </div>
        </div>

        {/* Observed Fare */}
        <div className="flex items-baseline justify-between p-3 border border-[#E2E8F0] rounded-xs bg-white">
          <div>
            <span className="text-[10px] font-mono text-[#64748B] uppercase">
              Observed Consumer Fare
            </span>
            <div className="text-3xl font-bold text-[#0F172A] tabular-nums mt-0.5">
              {formatINR(quote.total_fare_inr)}
            </div>
          </div>

          {quote.total_fare_inr === null && (
            <div className="text-right">
              <span className="text-xs font-mono text-rose-800 bg-rose-50 border border-rose-300 px-2 py-0.5 rounded-xs font-semibold">
                Missing / Sold Out
              </span>
              <p className="text-[10px] text-[#64748B] mt-1 italic">
                Safely nullified; never 0.00
              </p>
            </div>
          )}
        </div>

        {/* Ingestion Provenance Trail */}
        <div className="space-y-2 text-xs">
          <div className="text-[10px] font-mono uppercase tracking-widest text-[#64748B] font-semibold">
            Ingestion Provenance Trail
          </div>

          <div className="border border-[#E2E8F0] divide-y divide-[#E2E8F0] rounded-xs bg-white font-mono">
            <div className="flex justify-between p-2">
              <span className="text-[#64748B]">Source Adapter:</span>
              <span className="font-semibold text-[#0F172A]">{quote.source_id}</span>
            </div>

            <div className="flex justify-between p-2">
              <span className="text-[#64748B]">Collection Method:</span>
              <StatusBadge type="method" value={quote.collection_method} size="sm" />
            </div>

            <div className="flex justify-between p-2">
              <span className="text-[#64748B]">Timestamp (UTC):</span>
              <span className="text-[#0F172A]">{quote.collected_at_utc}</span>
            </div>

            <div className="flex justify-between p-2">
              <span className="text-[#64748B]">Timestamp (IST):</span>
              <span className="font-semibold text-[#1E3A8A]">
                {formatUTCtoIST(quote.collected_at_utc)}
              </span>
            </div>

            {quote.quality_reason && (
              <div className="p-2 bg-amber-50/80 text-amber-900 flex items-start gap-2">
                <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
                <span className="text-[11px] font-sans leading-relaxed">
                  {quote.quality_reason}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
          <span>Dataset: Synthetic / Historical Demo</span>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 bg-[#0F172A] text-white rounded-xs font-mono text-xs hover:bg-[#0F172A]/90 cursor-pointer transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
