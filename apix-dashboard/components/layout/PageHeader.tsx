import React from "react";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  actions,
}: PageHeaderProps) {
  return (
    <div className="pb-6 mb-8 border-b border-[#E2E8F0]">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          {eyebrow && (
            <p className="text-[11px] font-mono uppercase tracking-widest text-[#1E3A8A] font-semibold mb-1">
              {eyebrow}
            </p>
          )}
          <h2 className="text-3xl md:text-4xl font-bold text-[#0F172A] tracking-tight">
            {title}
          </h2>
          {subtitle && (
            <p className="text-sm text-[#64748B] mt-1.5 max-w-2xl leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
