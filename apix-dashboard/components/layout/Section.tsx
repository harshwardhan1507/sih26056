import React from "react";

interface SectionProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  borderTop?: boolean;
}

export function Section({
  title,
  subtitle,
  action,
  children,
  className = "",
  borderTop = true,
}: SectionProps) {
  return (
    <section
      className={`py-6 ${
        borderTop ? "border-t border-[#E2E8F0]" : ""
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-baseline justify-between mb-4">
          <div>
            {title && (
              <h3 className="font-mono text-xs uppercase tracking-widest text-[#64748B] font-semibold">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-[#64748B] mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
