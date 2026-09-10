"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Code2, Copy, Check, Terminal, ArrowRight } from "lucide-react";

export function ApiDeveloperSection() {
  const [activeTab, setActiveTab] = useState<"python" | "curl" | "ts">("python");
  const [copied, setCopied] = useState(false);

  const snippets = {
    python: `import httpx

# Query the latest national headline index
response = httpx.get("http://localhost:8000/api/v1/index/latest")
data = response.json()

print(f"National Index: {data['value']} ({data['change_pct']:+.2f}%)")
print(f"Base Period:    {data['base_period']}")
print(f"Active Quotes:  {data['quotes_count']}")`,

    curl: `# Fetch current Laspeyres national headline index
curl -X GET "http://localhost:8000/api/v1/index/latest" \\
     -H "Accept: application/json"`,

    ts: `// Modern TypeScript / Next.js client integration
interface IndexResponse {
  date: string;
  value: number;
  change_pct: number;
  base_period: string;
  quotes_count: number;
}

const res = await fetch("http://localhost:8000/api/v1/index/latest");
const data: IndexResponse = await res.json();
console.log(\`APIx Headline: \${data.value}\`);`,
  };

  const copyCode = () => {
    navigator.clipboard.writeText(snippets[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="api" className="py-16 sm:py-20 border-b border-[#E2E8F0] relative overflow-hidden flex items-center min-h-[580px]">
      {/* Background airliner image with NO white overlay */}
      <div className="absolute inset-0 pointer-events-none">
        <Image
          src="/airliner.jpg"
          alt="Airliner cruising in blue sky"
          fill
          sizes="100vw"
          className="object-cover object-center"
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: API overview inside clean white panel */}
          <div className="lg:col-span-5 bg-white/95 backdrop-blur-md rounded-2xl border border-white/40 p-8 shadow-xl space-y-5">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-blue-50 text-[#1E3A8A] border border-blue-200/80 text-[11px] font-mono font-medium">
              <Code2 className="h-3.5 w-3.5" />
              <span>DEVELOPER & STATISTICAL INTEGRATION</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold text-[#0F172A] tracking-tight">
              High-Frequency REST API & Feeds
            </h2>

            <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">
              APIx provides lightweight, sub-10ms REST endpoints designed for automated ingestion into MoSPI&apos;s CPI calculation pipeline and economic research systems.
            </p>

            <div className="space-y-2 font-mono text-xs text-[#0F172A]">
              <div className="flex items-center gap-2 p-2.5 rounded bg-[#F8FAFC] border border-[#E2E8F0]">
                <span className="px-1.5 py-0.5 rounded bg-blue-50 text-[#1E3A8A] border border-blue-200 text-[10px] font-bold">
                  GET
                </span>
                <span className="text-[#0F172A] font-semibold">/api/v1/index/latest</span>
                <span className="ml-auto text-[10px] text-[#64748B]">Headline</span>
              </div>
              <div className="flex items-center gap-2 p-2.5 rounded bg-[#F8FAFC] border border-[#E2E8F0]">
                <span className="px-1.5 py-0.5 rounded bg-blue-50 text-[#1E3A8A] border border-blue-200 text-[10px] font-bold">
                  GET
                </span>
                <span className="text-[#0F172A] font-semibold">/api/v1/routes</span>
                <span className="ml-auto text-[10px] text-[#64748B]">12 Corridors</span>
              </div>
              <div className="flex items-center gap-2 p-2.5 rounded bg-[#F8FAFC] border border-[#E2E8F0]">
                <span className="px-1.5 py-0.5 rounded bg-blue-50 text-[#1E3A8A] border border-blue-200 text-[10px] font-bold">
                  GET
                </span>
                <span className="text-[#0F172A] font-semibold">/api/v1/quotes</span>
                <span className="ml-auto text-[10px] text-[#64748B]">Panel Quotes</span>
              </div>
            </div>

            <div className="pt-2">
              <Link
                href="/api-docs"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded bg-[#1E3A8A] hover:bg-[#1D4ED8] text-white font-semibold text-xs shadow-xs transition-colors"
              >
                <span>Interactive OpenAPI Documentation</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          {/* Right Column: Code Box */}
          <div className="lg:col-span-7">
            <div className="rounded-2xl bg-white/95 backdrop-blur-md border border-white/40 overflow-hidden shadow-xl">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 bg-[#F8FAFC] border-b border-[#E2E8F0]">
                <div className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-[#64748B]" />
                  <div className="flex gap-1">
                    {(["python", "curl", "ts"] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors cursor-pointer ${
                          activeTab === tab
                            ? "bg-white text-[#1E3A8A] border border-[#E2E8F0] shadow-2xs font-bold"
                            : "text-[#64748B] hover:text-[#0F172A]"
                        }`}
                      >
                        {tab === "python" ? "Python" : tab === "curl" ? "cURL" : "TypeScript"}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={copyCode}
                  className="flex items-center gap-1.5 text-[11px] font-mono text-[#64748B] hover:text-[#0F172A] px-2 py-1 rounded hover:bg-slate-100 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Code content */}
              <pre className="p-5 text-xs font-mono text-[#0F172A] bg-white/90 overflow-x-auto leading-relaxed">
                <code>{snippets[activeTab]}</code>
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
