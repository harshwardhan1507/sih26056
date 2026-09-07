"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";

export function LandingNavbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "National Index", href: "#overview" },
    { label: "12 Corridors", href: "#corridors" },
    { label: "Advance Pricing", href: "#advance-pricing" },
    { label: "Methodology", href: "#methodology" },
    { label: "REST API", href: "#api" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 backdrop-blur-md border-b border-[#E2E8F0] shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center shrink-0">
          <Link href="/" className="group inline-flex items-center select-none">
            <span className="text-2xl sm:text-3xl font-black tracking-tighter text-[#0F172A] leading-none transition-opacity group-hover:opacity-90">
              APIx<span className="text-[#1E3A8A]">.</span>
            </span>
          </Link>
        </div>

        {/* Desktop Links - Equidistant & Clean with Growing Underline */}
        <nav className="hidden md:flex items-center justify-center flex-1 max-w-2xl mx-auto px-6">
          <div className="flex items-center justify-between w-full">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="relative group py-2 text-xs font-semibold text-[#475569] hover:text-[#1E3A8A] transition-colors tracking-tight select-none"
              >
                <span>{link.label}</span>
                <span className="absolute bottom-0 left-0 w-0 h-[2px] bg-[#1E3A8A] rounded-full transition-all duration-300 ease-out group-hover:w-full" />
              </a>
            ))}
          </div>
        </nav>

        {/* Action CTA */}
        <div className="hidden sm:flex items-center shrink-0">
          <Link
            href="/overview"
            className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#1E3A8A] hover:bg-[#1D4ED8] text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <span>Launch Dashboard</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Mobile toggle */}
        <div className="flex md:hidden items-center gap-2">
          <Link
            href="/overview"
            className="px-3 py-1.5 rounded bg-[#1E3A8A] text-white text-xs font-semibold"
          >
            Dashboard
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-[#64748B] hover:text-[#0F172A] rounded-md focus:outline-none"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#E2E8F0] bg-white px-4 pt-2 pb-5 space-y-2">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm text-[#0F172A] font-medium"
            >
              {link.label}
            </a>
          ))}
          <div className="pt-3 border-t border-[#E2E8F0]">
            <Link
              href="/overview"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded bg-[#1E3A8A] text-white font-medium text-xs shadow-xs"
            >
              <span>Go to Full Dashboard</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
