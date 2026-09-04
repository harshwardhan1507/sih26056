"use client";

import React, { useState, useMemo } from "react";
import type { QuoteItem, QualityFlag, CollectionMethod } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { formatUTCtoIST } from "@/lib/formatters/dates";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Search, Eye, Filter } from "lucide-react";

interface QuoteBrowserTableProps {
  quotes: QuoteItem[];
  onInspectQuote: (quote: QuoteItem) => void;
  className?: string;
}

export function QuoteBrowserTable({
  quotes,
  onInspectQuote,
  className = "",
}: QuoteBrowserTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [methodFilter, setMethodFilter] = useState<string>("ALL");
  const [qualityFilter, setQualityFilter] = useState<string>("ALL");

  const filtered = useMemo(() => {
    return quotes.filter((q) => {
      // Search
      if (searchTerm.trim().length > 0) {
        const term = searchTerm.toLowerCase();
        const matchesTerm =
          q.id.toLowerCase().includes(term) ||
          q.origin_iata.toLowerCase().includes(term) ||
          q.destination_iata.toLowerCase().includes(term) ||
          q.carrier_iata.toLowerCase().includes(term) ||
          q.source_id.toLowerCase().includes(term);
        if (!matchesTerm) return false;
      }

      // Method filter
      if (methodFilter !== "ALL" && q.collection_method !== methodFilter) {
        return false;
      }

      // Quality filter
      if (qualityFilter !== "ALL" && q.quality_flag !== qualityFilter) {
        return false;
      }

      return true;
    });
  }, [quotes, searchTerm, methodFilter, qualityFilter]);

  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      {/* Table Header & Search/Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 mb-4 border-b border-[#D8D7D0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
            Quote-Level Observation Registry
          </h4>
          <p className="text-[11px] text-[#626863] mt-0.5">
            Full provenance audit trail for individual daily price observations
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Method Filter */}
          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
            className="bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs px-2 py-1 text-xs font-mono text-[#111716] focus:outline-none"
          >
            <option value="ALL">All Methods</option>
            <option value="api">API Direct</option>
            <option value="tariff_sheet">Tariff Sheet</option>
            <option value="scrape">Web Scrape</option>
            <option value="simulated">Simulated Fallback</option>
          </select>

          {/* Quality Flag Filter */}
          <select
            value={qualityFilter}
            onChange={(e) => setQualityFilter(e.target.value)}
            className="bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs px-2 py-1 text-xs font-mono text-[#111716] focus:outline-none"
          >
            <option value="ALL">All Flags</option>
            <option value="ok">Valid Only</option>
            <option value="outlier">Outliers</option>
            <option value="sold_out">Sold Out</option>
          </select>

          {/* Search */}
          <div className="relative w-48">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#626863]" />
            <input
              type="text"
              placeholder="Search quotes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs pl-8 pr-2 py-1 text-xs font-mono text-[#111716] placeholder-[#626863]/60 focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Quotes Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#D8D7D0] text-[10px] font-mono text-[#626863] uppercase tracking-wider bg-[#FAF9F5]">
              <th className="py-2 px-2 font-semibold">Quote ID</th>
              <th className="py-2 px-2 font-semibold">Segment</th>
              <th className="py-2 px-2 font-semibold">Window</th>
              <th className="py-2 px-2 font-semibold">Carrier</th>
              <th className="py-2 px-2 font-semibold">Fare (INR)</th>
              <th className="py-2 px-2 font-semibold">Method</th>
              <th className="py-2 px-2 font-semibold">Quality</th>
              <th className="py-2 px-2 font-semibold text-right">Audit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D8D7D0]/60 font-sans">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-[#626863] font-mono text-xs">
                  No quotes match the selected filters.
                </td>
              </tr>
            ) : (
              filtered.map((q) => (
                <tr
                  key={q.id}
                  onClick={() => onInspectQuote(q)}
                  className="hover:bg-[#F4F2EC] transition-colors cursor-pointer group"
                >
                  <td className="py-2.5 px-2 font-mono text-xs font-bold text-[#111716] group-hover:text-[#176B5B]">
                    {q.id}
                  </td>
                  <td className="py-2.5 px-2 font-mono text-xs text-[#111716]">
                    {q.origin_iata} → {q.destination_iata}
                  </td>
                  <td className="py-2.5 px-2 font-mono text-xs text-[#626863]">
                    T+{q.advance_window_days}
                  </td>
                  <td className="py-2.5 px-2 font-mono text-xs font-semibold text-[#111716]">
                    {q.carrier_iata}
                  </td>
                  <td className="py-2.5 px-2 font-serif text-xs font-bold tabular-nums text-[#111716]">
                    {formatINR(q.total_fare_inr)}
                  </td>
                  <td className="py-2.5 px-2">
                    <StatusBadge type="method" value={q.collection_method} size="sm" />
                  </td>
                  <td className="py-2.5 px-2">
                    <StatusBadge type="quality" value={q.quality_flag} size="sm" />
                  </td>
                  <td className="py-2.5 px-2 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectQuote(q);
                      }}
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#176B5B] hover:underline font-medium cursor-pointer"
                    >
                      <Eye className="h-3 w-3" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
