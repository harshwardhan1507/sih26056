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
  Globe,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const PRIMARY_NAV: NavItem[] = [
  { label: "Overview", href: "/overview", icon: LayoutDashboard },
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
    if (href === "/overview") return pathname === "/overview" || pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-60 bg-[#0B192C] text-slate-100 border-r border-[#1E293B] flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)] select-none">
      <div className="py-5 px-3">
        {/* Brand Header / Title */}
        <div className="mb-6 px-3">
          <Link href="/" className="group flex items-center justify-between select-none">
            <span className="text-2xl font-black tracking-tighter text-white leading-none">
              APIx<span className="text-sky-400">.</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-sky-300 border border-blue-800/60 group-hover:bg-blue-900 transition-colors">
              PORTAL ↗
            </span>
          </Link>
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
                    ? "bg-[#1E3A8A] text-white font-semibold shadow-xs"
                    : "text-slate-300 hover:text-white hover:bg-[#1E293B]"
                }`}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 ${
                    active ? "text-sky-300" : "text-slate-400"
                  }`}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Data & System Section */}
        <div className="pt-4 border-t border-[#1E293B]">
          <p className="px-3 mb-2 text-[10px] uppercase tracking-wider text-slate-400 font-mono font-semibold">
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
                      ? "bg-[#1E3A8A] text-white font-semibold shadow-xs"
                      : "text-slate-300 hover:text-white hover:bg-[#1E293B]"
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 shrink-0 ${
                      active ? "text-sky-300" : "text-slate-400"
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
      <div className="p-4 border-t border-[#1E293B] text-[10px] text-slate-400 font-mono leading-relaxed">
        <div className="text-white/90 font-medium">Ministry of Statistics</div>
        <div>and Programme Implementation</div>
        <div className="text-[9px] text-slate-500 mt-1">SIH-26056 · v0.1.0</div>
      </div>
    </aside>
  );
}
