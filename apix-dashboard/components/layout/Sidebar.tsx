"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LineChart,
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
  { label: "Overview", href: "/", icon: LineChart },
  { label: "Index & Trends", href: "/index-trend", icon: TrendingUp },
  { label: "Routes", href: "/routes", icon: MapPin },
];

const DATA_NAV: NavItem[] = [
  { label: "Quality", href: "/data/quality", icon: ShieldCheck },
  { label: "Sources", href: "/sources", icon: Radio },
  { label: "Methodology", href: "/methodology", icon: BookOpen },
  { label: "API Reference", href: "/api-docs", icon: Code2 },
];

export function Sidebar() {
  const pathname = usePathname();

  const isNavActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-64 border-r border-[#D8D7D0] bg-[#FAF9F5] flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="py-6 px-4">
        {/* Editorial Subtitle */}
        <div className="mb-6 px-3">
          <p className="text-[10px] tracking-widest uppercase text-[#626863] font-mono">
            National Airfare Basket
          </p>
          <p className="text-xs text-[#111716] font-serif italic mt-0.5">
            MoSPI CPI Augmentation
          </p>
        </div>

        {/* Primary Navigation */}
        <nav className="space-y-1 mb-8">
          {PRIMARY_NAV.map((item) => {
            const Icon = item.icon;
            const active = isNavActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-sm transition-colors ${
                  active
                    ? "bg-[#176B5B]/10 text-[#176B5B] border-l-2 border-[#176B5B] font-semibold"
                    : "text-[#111716] hover:bg-[#F4F2EC] text-opacity-80"
                }`}
              >
                <Icon
                  className={`h-4 w-4 ${
                    active ? "text-[#176B5B]" : "text-[#626863]"
                  }`}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* System & Data Section */}
        <div className="pt-4 border-t border-[#D8D7D0]/60">
          <p className="px-3 mb-2 text-[10px] uppercase tracking-wider text-[#626863] font-mono font-semibold">
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
                  className={`flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-sm transition-colors ${
                    active
                      ? "bg-[#176B5B]/10 text-[#176B5B] border-l-2 border-[#176B5B] font-semibold"
                      : "text-[#111716] hover:bg-[#F4F2EC] text-opacity-80"
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 ${
                      active ? "text-[#176B5B]" : "text-[#626863]"
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
      <div className="p-4 border-t border-[#D8D7D0] text-[10px] text-[#626863] font-mono leading-relaxed">
        <div>Series: APIx 2026.09</div>
        <div>DGCA Traffic Weighted</div>
        <div className="text-[9px] text-[#626863]/80 mt-1">SIH Problem #26056</div>
      </div>
    </aside>
  );
}
