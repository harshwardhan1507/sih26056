/**
 * Node.js Runtime Verification Script for APIx Dashboard Formatter Contracts
 */

// 1. Currency Formatter Logic
function formatINR(val, options = {}) {
  const { fallback = "—", fractionDigits = 0 } = options;
  if (val === null || val === undefined || Number.isNaN(val)) {
    return fallback;
  }
  const formatted = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  }).format(val);
  return `₹${formatted}`;
}

// 2. Percentage Formatter Logic
function formatPercent(val, options = {}) {
  const { fallback = "—", decimals = 1, showSign = true } = options;
  if (val === null || val === undefined || Number.isNaN(val)) {
    return fallback;
  }
  const fixed = Math.abs(val).toFixed(decimals);
  if (val > 0) return showSign ? `+${fixed}%` : `${fixed}%`;
  if (val < 0) return `-${fixed}%`;
  return `0.0%`;
}

// 3. Date & Timezone Formatter Logic (UTC to IST)
function formatUTCtoIST(utcIsoString, options = {}) {
  const { fallback = "—" } = options;
  if (!utcIsoString) return fallback;
  try {
    const d = new Date(utcIsoString);
    if (Number.isNaN(d.getTime())) return fallback;
    const datePart = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(d);
    const timePart = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);
    return `${datePart} · ${timePart} IST`;
  } catch {
    return fallback;
  }
}

// Run verifications
console.log("Testing formatINR...");
if (formatINR(6842) !== "₹6,842") throw new Error("formatINR(6842) failed");
if (formatINR(null) !== "—") throw new Error("formatINR(null) failed");
if (formatINR(undefined) !== "—") throw new Error("formatINR(undefined) failed");
console.log("✓ formatINR passed: 6842 -> " + formatINR(6842) + ", null -> " + formatINR(null));

console.log("Testing formatPercent...");
if (formatPercent(2.4) !== "+2.4%") throw new Error("formatPercent(2.4) failed");
if (formatPercent(-1.8) !== "-1.8%") throw new Error("formatPercent(-1.8) failed");
if (formatPercent(0) !== "0.0%") throw new Error("formatPercent(0) failed");
if (formatPercent(null) !== "—") throw new Error("formatPercent(null) failed");
console.log("✓ formatPercent passed: +2.4% / -1.8% / 0.0% / null");

console.log("Testing formatUTCtoIST...");
const ist = formatUTCtoIST("2026-09-04T12:02:00Z");
if (!ist.includes("IST") || !ist.includes("2026")) throw new Error("formatUTCtoIST failed");
console.log("✓ formatUTCtoIST passed: 2026-09-04T12:02:00Z -> " + ist);

console.log("All Phase 0 contract checks PASSED cleanly!");
