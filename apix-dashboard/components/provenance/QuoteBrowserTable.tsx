"use client";

import React, { useState, useMemo } from "react";
import type { QuoteItem } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { StatusBadge } from "@/components/common/StatusBadge";
import {
  Search,
  Eye,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

interface QuoteBrowserTableProps {
  quotes: QuoteItem[];
  onInspectQuote: (quote: QuoteItem) => void;
  className?: string;
}

function getPageNumbers(current: number, total: number): (number | "...")[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  if (current <= 4) {
    return [1, 2, 3, 4, 5, "...", total];
  }
  if (current >= total - 3) {
    return [1, "...", total - 4, total - 3, total - 2, total - 1, total];
  }
  return [1, "...", current - 1, current, current + 1, "...", total];
}

export function QuoteBrowserTable({
  quotes,
  onInspectQuote,
  className = "",
}: QuoteBrowserTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [methodFilter, setMethodFilter] = useState<string>("ALL");
  const [qualityFilter, setQualityFilter] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

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

  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safeCurrentPage = Math.min(Math.max(1, currentPage), totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  const paginatedQuotes = useMemo(() => {
    return filtered.slice(startIndex, endIndex);
  }, [filtered, startIndex, endIndex]);

  const handleSearchChange = (val: string) => {
    setSearchTerm(val);
    setCurrentPage(1);
  };

  const handleMethodChange = (val: string) => {
    setMethodFilter(val);
    setCurrentPage(1);
  };

  const handleQualityChange = (val: string) => {
    setQualityFilter(val);
    setCurrentPage(1);
  };

  const handlePageSizeChange = (val: number) => {
    setPageSize(val);
    setCurrentPage(1);
  };

  const pageNumbers = getPageNumbers(safeCurrentPage, totalPages);

  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      {/* Table Header & Search/Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 mb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
              Quote-Level Observation Registry
            </h4>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-slate-100 text-[#64748B] font-medium">
              {totalItems.toLocaleString()} records
            </span>
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Full provenance audit trail for individual daily price observations
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Method Filter */}
          <select
            value={methodFilter}
            onChange={(e) => handleMethodChange(e.target.value)}
            className="bg-slate-50 border border-[#E2E8F0] rounded-xs px-2 py-1 text-xs font-mono text-[#0F172A] focus:outline-none focus:border-[#1E3A8A]"
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
            onChange={(e) => handleQualityChange(e.target.value)}
            className="bg-slate-50 border border-[#E2E8F0] rounded-xs px-2 py-1 text-xs font-mono text-[#0F172A] focus:outline-none focus:border-[#1E3A8A]"
          >
            <option value="ALL">All Flags</option>
            <option value="ok">Valid Only</option>
            <option value="outlier">Outliers</option>
            <option value="sold_out">Sold Out</option>
          </select>

          {/* Search */}
          <div className="relative w-48">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#64748B]" />
            <input
              type="text"
              placeholder="Search quotes..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full bg-slate-50 border border-[#E2E8F0] rounded-xs pl-8 pr-2 py-1 text-xs font-mono text-[#0F172A] placeholder-[#64748B]/60 focus:outline-none focus:border-[#1E3A8A]"
            />
          </div>
        </div>
      </div>

      {/* Quotes Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase tracking-wider bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Quote ID</th>
              <th className="py-2.5 px-3 font-semibold">Segment</th>
              <th className="py-2.5 px-3 font-semibold">Window</th>
              <th className="py-2.5 px-3 font-semibold">Carrier</th>
              <th className="py-2.5 px-3 font-semibold">Fare (INR)</th>
              <th className="py-2.5 px-3 font-semibold">Method</th>
              <th className="py-2.5 px-3 font-semibold">Quality</th>
              <th className="py-2.5 px-3 font-semibold text-right">Audit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {paginatedQuotes.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-[#64748B] font-mono text-xs">
                  No quotes match the selected filters.
                </td>
              </tr>
            ) : (
              paginatedQuotes.map((q) => (
                <tr
                  key={q.id}
                  onClick={() => onInspectQuote(q)}
                  className="hover:bg-slate-50 transition-colors cursor-pointer group"
                >
                  <td className="py-2.5 px-3 font-mono text-xs font-bold text-[#0F172A] group-hover:text-[#1E3A8A]">
                    {q.id}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-xs text-[#0F172A]">
                    {q.origin_iata} → {q.destination_iata}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-xs text-[#64748B]">
                    T+{q.advance_window_days}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-xs font-semibold text-[#0F172A]">
                    {q.carrier_iata}
                  </td>
                  <td className="py-2.5 px-3 text-xs font-bold tabular-nums text-[#0F172A]">
                    {formatINR(q.total_fare_inr)}
                  </td>
                  <td className="py-2.5 px-3">
                    <StatusBadge type="method" value={q.collection_method} size="sm" />
                  </td>
                  <td className="py-2.5 px-3">
                    <StatusBadge type="quality" value={q.quality_flag} size="sm" />
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectQuote(q);
                      }}
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#1E3A8A] hover:underline font-medium cursor-pointer"
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

      {/* Pagination Controls */}
      {totalItems > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 mt-2 border-t border-[#E2E8F0]">
          {/* Item count & filter indication */}
          <div className="text-[11px] font-mono text-[#64748B]">
            Showing <span className="font-semibold text-[#0F172A]">{startIndex + 1}</span>–
            <span className="font-semibold text-[#0F172A]">{endIndex}</span> of{" "}
            <span className="font-semibold text-[#0F172A]">{totalItems.toLocaleString()}</span> observations
            {totalItems !== quotes.length && (
              <span className="text-[#94A3B8]"> (filtered from {quotes.length.toLocaleString()})</span>
            )}
          </div>

          {/* Page navigation & page size */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            {/* Rows per page selector */}
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#64748B]">
              <span>Rows:</span>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                className="bg-slate-50 border border-[#E2E8F0] rounded-xs px-1.5 py-0.5 text-xs font-mono text-[#0F172A] focus:outline-none focus:border-[#1E3A8A]"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>

            {/* Navigation buttons */}
            <div className="inline-flex items-center gap-1">
              <button
                type="button"
                onClick={() => setCurrentPage(1)}
                disabled={safeCurrentPage === 1}
                aria-label="First page"
                className="p-1 rounded-xs border border-[#E2E8F0] bg-white text-[#64748B] hover:bg-slate-50 hover:text-[#0F172A] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronsLeft className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={safeCurrentPage === 1}
                aria-label="Previous page"
                className="p-1 rounded-xs border border-[#E2E8F0] bg-white text-[#64748B] hover:bg-slate-50 hover:text-[#0F172A] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>

              {/* Numbered Page Buttons */}
              <div className="hidden sm:inline-flex items-center gap-1">
                {pageNumbers.map((p, idx) =>
                  p === "..." ? (
                    <span
                      key={`ellipsis-${idx}`}
                      className="px-1.5 py-0.5 text-xs font-mono text-[#94A3B8]"
                    >
                      ...
                    </span>
                  ) : (
                    <button
                      key={`page-${p}`}
                      type="button"
                      onClick={() => setCurrentPage(p)}
                      className={`min-w-[24px] px-1.5 py-0.5 rounded-xs text-xs font-mono transition-colors cursor-pointer ${
                        p === safeCurrentPage
                          ? "bg-[#1E3A8A] text-white font-semibold"
                          : "border border-[#E2E8F0] bg-white text-[#64748B] hover:bg-slate-50 hover:text-[#0F172A]"
                      }`}
                    >
                      {p}
                    </button>
                  )
                )}
              </div>

              {/* Mobile page indicator */}
              <span className="sm:hidden text-xs font-mono text-[#64748B] px-1">
                {safeCurrentPage} / {totalPages}
              </span>

              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={safeCurrentPage === totalPages}
                aria-label="Next page"
                className="p-1 rounded-xs border border-[#E2E8F0] bg-white text-[#64748B] hover:bg-slate-50 hover:text-[#0F172A] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setCurrentPage(totalPages)}
                disabled={safeCurrentPage === totalPages}
                aria-label="Last page"
                className="p-1 rounded-xs border border-[#E2E8F0] bg-white text-[#64748B] hover:bg-slate-50 hover:text-[#0F172A] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <ChevronsRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
