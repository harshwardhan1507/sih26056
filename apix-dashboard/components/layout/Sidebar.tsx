"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  MapPin,
  ShieldCheck,
  Radio,
  BookOpen,
  Code2,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const PRIMARY_NAV: NavItem[] = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Index / Trends", href: "/index-trend", icon: TrendingUp },
  { label: "Routes", href: "/routes", icon: MapPin },
];

const DATA_NAV: NavItem[] = [
  { label: "Data Quality", href: "/data/quality", icon: ShieldCheck },
  { label: "Sources & Provenance", href: "/sources", icon: Radio },
  { label: "Methodology", href: "/methodology", icon: BookOpen },
  { label: "API / Docs", href: "/api-docs", icon: Code2 },
];

export function Sidebar() {
  const pathname = usePathname();

  const isNavActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-60 bg-[#162923] text-[#FAF9F5] border-r border-[#1B362E] flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)] select-none">
      <div className="py-5 px-3">
        {/* Brand Header / Title */}
        <div className="mb-6 px-3">
          <div className="flex items-center gap-2">
            <span className="font-serif text-lg font-bold tracking-tight text-white">
              APIx
            </span>
          </div>
          <p className="text-[10px] text-[#A9C4B8] font-mono tracking-wider uppercase mt-0.5">
            Real-Time Airfare Price Index
          </p>
        </div>

        {/* Primary Navigation */}
        <nav className="space-y-1 mb-6">
          {PRIMARY_NAV.map((item) => {
            const Icon = item.icon;
            const active = isNavActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded transition-colors ${
                  active
                    ? "bg-[#1E3E34] text-white font-semibold shadow-xs"
                    : "text-[#A9C4B8] hover:text-white hover:bg-[#1E3E34]/50"
                }`}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 ${
                    active ? "text-emerald-400" : "text-[#A9C4B8]"
                  }`}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Data & System Section */}
        <div className="pt-4 border-t border-[#1E3E34]">
          <p className="px-3 mb-2 text-[10px] uppercase tracking-wider text-[#A9C4B8]/70 font-mono font-semibold">
            Data & System
          </p>
          <nav className="space-y-1">
            {DATA_NAV.map((item) => {
              const Icon = item.icon;
              const active = isNavActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded transition-colors ${
                    active
                      ? "bg-[#1E3E34] text-white font-semibold shadow-xs"
                      : "text-[#A9C4B8] hover:text-white hover:bg-[#1E3E34]/50"
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 shrink-0 ${
                      active ? "text-emerald-400" : "text-[#A9C4B8]"
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer provenance tag */}
      <div className="p-4 border-t border-[#1E3E34] text-[10px] text-[#A9C4B8]/70 font-mono leading-relaxed">
        <div className="text-white/90 font-medium">Ministry of Statistics</div>
        <div>and Programme Implementation</div>
        <div className="text-[9px] text-[#A9C4B8]/50 mt-1">SIH-26056 · v0.1.0</div>
      </div>
    </aside>
  );
}
