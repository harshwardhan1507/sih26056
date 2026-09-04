/**
 * Phase 2 Verification Script: Offline Fixture Engine & Edge Case Validation
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.resolve(__dirname, "../data/fixtures");

function loadFixture(name) {
  const filePath = path.join(fixturesDir, name);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

console.log("=== APIx Phase 2 Fixture Engine Verification ===");

// 1. Verify index-summary.json
console.log("Checking index-summary.json...");
const summary = loadFixture("index-summary.json");
if (typeof summary.value !== "number" || summary.value <= 0) throw new Error("Invalid index value");
if (summary.quotes !== 300) throw new Error("Expected 300 quotes");
if (summary.routes !== 12) throw new Error("Expected 12 routes");
if (summary.metadata.mode !== "demo") throw new Error("Expected mode: demo");
console.log(`✓ Index summary valid: ${summary.value} (Δ ${summary.change_pct}%), Mode: ${summary.metadata.mode}`);

// 2. Verify index-history.json & Gap Day Invariant
console.log("Checking index-history.json & gap handling...");
const history = loadFixture("index-history.json");
if (!Array.isArray(history) || history.length < 30) throw new Error("History must have at least 30 points");
const gapPoint = history.find((p) => p.day === 18);
if (!gapPoint || gapPoint.index_value !== null) {
  throw new Error("Day 18 must be an intentional gap point with index_value === null");
}
console.log(`✓ Index history valid: ${history.length} points, Gap day 18 verified (index_value = null)`);

// 3. Verify routes.json & DGCA Weights
console.log("Checking routes.json & DGCA passenger traffic weights...");
const routes = loadFixture("routes.json");
if (!Array.isArray(routes) || routes.length !== 12) throw new Error("Expected exactly 12 routes");
const weightSum = routes.reduce((acc, r) => acc + r.weight, 0);
if (Math.abs(weightSum - 1.0) > 0.005) {
  throw new Error(`DGCA weights must sum to approximately 1.0, got ${weightSum}`);
}
const partialRoute = routes.find((r) => r.coverage_status === "partial");
if (!partialRoute) throw new Error("Must have at least one route with partial coverage status");
console.log(`✓ 12 Routes valid. Weight sum: ${weightSum.toFixed(4)}. Partial route tested: ${partialRoute.route_id}`);

// 4. Verify route-details.json & Horizons
console.log("Checking route-details.json...");
const details = loadFixture("route-details.json");
const delBom = details["DEL-BOM"];
if (!delBom || !delBom.windows["T+1"] || !delBom.windows["T+45"]) {
  throw new Error("DEL-BOM must have complete windows T+1 through T+45");
}
// Check T+1 price > T+45 price (Advance decay progression)
const t1Fare = delBom.windows["T+1"].average_fare;
const t45Fare = delBom.windows["T+45"].average_fare;
if (t1Fare <= t45Fare) {
  throw new Error(`Expected T+1 fare (${t1Fare}) > T+45 fare (${t45Fare}) for advance decay progression`);
}
// Check carrier with null fare (outlier excluded or unavailable)
const t30Carriers = delBom.windows["T+30"].carriers;
const outlierCarrier = t30Carriers.find((c) => c.status === "outlier_excluded");
if (!outlierCarrier || outlierCarrier.fare !== null) {
  throw new Error("Expected outlier_excluded carrier with fare === null on T+30");
}
// Check disabled window
const bomGoi = details["BOM-GOI"];
if (!bomGoi || bomGoi.windows["T+45"].available !== false) {
  throw new Error("BOM-GOI T+45 must have available === false");
}
console.log(`✓ Route details valid. T+1 (${t1Fare}) > T+45 (${t45Fare}). Outlier & unavailable carrier invariants verified.`);

// 5. Verify quotes.json & Sold-Out Invariant
console.log("Checking quotes.json & sold_out null fare invariant...");
const quotes = loadFixture("quotes.json");
const soldOutQuote = quotes.find((q) => q.quality_flag === "sold_out");
if (!soldOutQuote) throw new Error("Must contain at least one sold_out quote");
if (soldOutQuote.total_fare_inr !== null) {
  throw new Error(`Sold out quote must have total_fare_inr === null, got ${soldOutQuote.total_fare_inr}`);
}
console.log(`✓ Quotes fixture valid. Sold out invariant passed: total_fare_inr is strictly null (never 0.00).`);

// 6. Verify quality.json
console.log("Checking quality.json...");
const quality = loadFixture("quality.json");
if (quality.score !== 96.8) throw new Error("Expected score 96.8");
if (quality.sold_out_count !== 3) throw new Error("Expected 3 sold out quotes");
if (quality.outlier_count !== 6) throw new Error("Expected 6 outliers");
if (!Array.isArray(quality.collection_runs) || quality.collection_runs.length !== 4) {
  throw new Error("Expected 4 historical collection runs");
}
console.log(`✓ Quality metrics valid: score ${quality.score}%, ${quality.collection_runs.length} collection runs.`);

// 7. Verify sources.json
console.log("Checking sources.json...");
const sources = loadFixture("sources.json");
if (!Array.isArray(sources) || sources.length !== 6) throw new Error("Expected 6 sources in health matrix");
console.log(`✓ Sources health matrix valid: ${sources.length} sources registered.`);

console.log("\n>>> ALL PHASE 2 DATA FIXTURE & INVARIANT CHECKS PASSED CLEANLY! <<<");
