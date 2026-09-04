"use client";

import React from "react";
import { getCurrentISTHeaderDate } from "@/lib/formatters/dates";
import type { ConnectionStatus } from "@/lib/api/types";
import { Activity, Database, AlertCircle } from "lucide-react";

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
    <header className="h-16 border-b border-[#D8D7D0] bg-[#FAF9F5] px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-baseline gap-4">
        <h1 className="font-serif text-xl tracking-tight text-[#111716]">
          APIx
        </h1>
        <span className="hidden sm:inline-block text-xs uppercase tracking-widest text-[#626863] font-mono border-l border-[#D8D7D0] pl-4">
          India Airfare Price Index
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs font-mono">
        {/* IST Clock */}
        <span className="text-[#626863] hidden md:inline-block" suppressHydrationWarning>
          {istDate}
        </span>

        {/* Connection status badge */}
        <div className="flex items-center gap-2">
          {connectionStatus === "LIVE_CONNECTED" && (
            <button
              onClick={onToggleMode}
              title="Click to switch to Demo Mode"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#176B5B]/10 text-[#176B5B] border border-[#176B5B]/30 rounded-sm hover:bg-[#176B5B]/20 transition-colors cursor-pointer"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-[#176B5B] animate-pulse" />
              <Activity className="h-3 w-3" />
              <span className="font-semibold tracking-wider uppercase">Live API</span>
            </button>
          )}

          {connectionStatus === "LOCAL_DEMO" && (
            <button
              onClick={onToggleMode}
              title="Click to attempt Live API connection"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-300 rounded-sm hover:bg-amber-100 transition-colors cursor-pointer"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
              <Database className="h-3 w-3" />
              <span className="font-semibold tracking-wider uppercase">Local Demo</span>
            </button>
          )}

          {connectionStatus === "API_UNAVAILABLE" && (
            <button
              onClick={onToggleMode}
              title="API is unreachable. Click to switch to Local Demo."
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-rose-50 text-rose-800 border border-rose-300 rounded-sm hover:bg-rose-100 transition-colors cursor-pointer"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
              <AlertCircle className="h-3 w-3" />
              <span className="font-semibold tracking-wider uppercase">API Unavailable</span>
              <span className="hidden lg:inline underline text-[10px] ml-1">[Use Demo]</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
