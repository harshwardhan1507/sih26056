"use client";

import React from "react";
import { getCurrentISTHeaderDate } from "@/lib/formatters/dates";
import type { ConnectionStatus } from "@/lib/api/types";
import { Activity, Database, AlertCircle, Sparkles } from "lucide-react";

interface HeaderProps {
  connectionStatus?: ConnectionStatus;
  onToggleMode?: () => void;
  lastUpdated?: string;
}

export function Header({
  connectionStatus = "LOCAL_DEMO",
  onToggleMode,
  lastUpdated,
}: HeaderProps) {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const istDate = lastUpdated || (mounted ? getCurrentISTHeaderDate() : "04 Sep 2026 · 17:32 IST");

  return (
    <header className="h-14 border-b border-[#D8D7D0] bg-[#FAF9F5] px-6 flex items-center justify-between sticky top-0 z-30 select-none">
      <div className="flex items-center gap-4">
        {/* Live Data Badge */}
        <div className="flex items-center gap-2">
          {connectionStatus === "LIVE_CONNECTED" && (
            <button
              onClick={onToggleMode}
              title="Click to switch to Demo Mode"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#176B5B]/10 text-[#176B5B] border border-[#176B5B]/30 rounded text-xs font-mono font-medium hover:bg-[#176B5B]/20 transition-colors cursor-pointer"
            >
              <span className="h-2 w-2 rounded-full bg-[#176B5B] animate-pulse" />
              <span>Live Data</span>
            </button>
          )}

          {connectionStatus === "LOCAL_DEMO" && (
            <button
              onClick={onToggleMode}
              title="Click to attempt Live API connection"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#162923]/10 text-[#162923] border border-[#162923]/20 rounded text-xs font-mono font-medium hover:bg-[#162923]/20 transition-colors cursor-pointer"
            >
              <span className="h-2 w-2 rounded-full bg-emerald-600" />
              <span>Live Data (Demo)</span>
            </button>
          )}

          {connectionStatus === "API_UNAVAILABLE" && (
            <button
              onClick={onToggleMode}
              title="API is unreachable. Click to switch to Local Demo."
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-rose-50 text-rose-800 border border-rose-300 rounded text-xs font-mono font-medium hover:bg-rose-100 transition-colors cursor-pointer"
            >
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              <AlertCircle className="h-3.5 w-3.5" />
              <span>API Offline [Use Demo]</span>
            </button>
          )}
        </div>

        {/* IST Clock */}
        <span className="text-xs text-[#626863] font-mono border-l border-[#D8D7D0] pl-4 hidden sm:inline-block" suppressHydrationWarning>
          {istDate}
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs font-mono">
        <span className="text-xs text-[#626863] italic hidden md:inline-block font-serif">
          A more connected India through better data
        </span>

        {/* Official Tag */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#EAE8E0] text-[#111716] text-[11px] font-mono">
          <span className="h-1.5 w-1.5 rounded-full bg-[#176B5B]" />
          <span>MoSPI Augmented</span>
        </div>
      </div>
    </header>
  );
}
