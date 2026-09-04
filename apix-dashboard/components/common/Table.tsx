import React from "react";

interface TableProps {
  headers: React.ReactNode[];
  children: React.ReactNode;
  className?: string;
}

export function Table({ headers, children, className = "" }: TableProps) {
  return (
    <div className={`overflow-x-auto w-full ${className}`}>
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-[#D8D7D0] bg-[#FAF9F5]">
            {headers.map((header, idx) => (
              <th
                key={idx}
                className="py-2.5 px-3 font-mono uppercase tracking-wider text-[10px] text-[#626863] font-semibold"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#D8D7D0]/60 font-sans">
          {children}
        </tbody>
      </table>
    </div>
  );
}
