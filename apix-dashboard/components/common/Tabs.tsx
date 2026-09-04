"use client";

import React from "react";

export interface TabItem<T extends string> {
  id: T;
  label: string;
  disabled?: boolean;
  badge?: string | number;
}

interface TabsProps<T extends string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onChange: (id: T) => void;
  size?: "sm" | "md";
  className?: string;
}

export function Tabs<T extends string>({
  tabs,
  activeTab,
  onChange,
  size = "md",
  className = "",
}: TabsProps<T>) {
  return (
    <div
      className={`inline-flex p-0.5 bg-slate-100 border border-[#E2E8F0] rounded-sm font-mono ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const isDisabled = tab.disabled;

        return (
          <button
            key={tab.id}
            type="button"
            disabled={isDisabled}
            onClick={() => !isDisabled && onChange(tab.id)}
            className={`flex items-center gap-1.5 transition-all rounded-xs font-medium cursor-pointer ${
              size === "sm"
                ? "px-2.5 py-1 text-[11px]"
                : "px-3 py-1.5 text-xs"
            } ${
              isDisabled
                ? "text-[#64748B]/40 cursor-not-allowed line-through"
                : isActive
                ? "bg-[#1E3A8A] text-white shadow-xs"
                : "text-[#0F172A] hover:bg-slate-200/60"
            }`}
          >
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={`text-[9px] px-1 py-0.2 rounded-xs ${
                  isActive
                    ? "bg-white/20 text-white"
                    : "bg-[#E2E8F0] text-[#64748B]"
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
