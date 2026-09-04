# APIx Airfare Price Index — Operations & Analytical Dashboard

Real-time Next.js 16 (React 19, Tailwind CSS v4) analytical dashboard built for the Ministry of Statistics and Programme Implementation (MoSPI / NSO) to monitor the Airfare Price Index (CPI 2024 series, Problem Statement SIH-26056).

## Overview

The APIx Dashboard delivers operational and analytical visibility into:
1. **Index Trend (`/index-trend`)**: Official chained Laspeyres index trajectory across 30-day horizons with advance-purchase window breakdown (T+1, T+7, T+15, T+30, T+45) and volatility metrics.
2. **Route Dynamics (`/routes`, `/routes/[routeId]`)**: DGCA passenger traffic-weighted route table, interactive India air corridor map, advance-purchase horizon decay curves, and carrier breakdown.
3. **Data Quality & Hygiene (`/data/quality`)**: Data quality score hero, collection run audit trails, and hygiene flags (outlier detection, sold-out tracking, class mean imputation).
4. **Source Health & Provenance (`/sources`)**: Carrier-aware multi-tier fallback status (Tier 1 API $\to$ Tier 2 Tariff Sheet $\to$ Tier 3 OTA Scrape $\to$ Tier 4 Simulator) and raw quote inspector.
5. **Methodological Transparency (`/methodology`) & API Explorer (`/api-docs`)**: Full documentation of Jevons elementary formulation, chained Laspeyres aggregation, and interactive OpenAPI contracts.

## Architecture

- **Dual-Mode Data Provider**: Transparently falls back from the live FastAPI backend (`http://localhost:8000`) to offline static fixtures in `data/fixtures/` with a visual live/demo badge.
- **Strict Invariant Adherence**:
  - Sold-out flights are represented as `null` fares (never `0.00`).
  - No crossing of advance windows (T+7 today vs T+7 yesterday).
  - Metropolitan Catchment Aggregation for Goa (`GOI` + `GOX`) and Mumbai (`BOM` + `NMI`).
- **Statistical Charts**: Built with SVG charts including horizon price decay curves, coordinated multi-series index trends, route sparklines, and India route corridor map.

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.13 (optional, for running live FastAPI backend)

### Installation & Development

```bash
cd apix-dashboard
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

### Verification Scripts

```bash
# Verify formatting contracts and utility invariants
node scripts/verify-contracts.mjs

# Verify JSON fixture schema and domain invariants
node scripts/verify-fixtures.mjs

# Verify live FastAPI integration (with backend running at localhost:8000)
node scripts/verify-api-integration.mjs

# Production build check
npm run build
```

### Environment Configuration

Copy `.env.local.example` to `.env.local`:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
If the backend is not running, the dashboard automatically falls back to offline fixtures in `data/fixtures/`.
