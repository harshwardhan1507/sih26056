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
        borderTop ? "border-t border-[#D8D7D0]" : ""
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-baseline justify-between mb-4">
          <div>
            {title && (
              <h3 className="font-mono text-xs uppercase tracking-widest text-[#626863] font-semibold">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-[#626863] mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
