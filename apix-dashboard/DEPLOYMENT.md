# APIx Dashboard — Vercel Deployment & Architecture Guide

This document outlines how to deploy the **APIx Airfare Price Index Dashboard** (`apix-dashboard`) to [Vercel](https://vercel.com) and explains the operational modes, backend integration requirements, and security considerations.

---

## 1. Quick Deploy to Vercel

### Step 1: Import Repository
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Select your GitHub repository (`sih26056`).

### Step 2: Configure Root Directory (CRITICAL)
Because this repository is structured with the Python backend (`apix/`) and Next.js frontend (`apix-dashboard/`) side-by-side:
- In the **Project Settings** screen, locate **Root Directory**.
- Click **Edit** and select **`apix-dashboard`**.
- Click **Continue**.

Vercel will automatically detect **Next.js** as the framework preset.

### Step 3: Build & Output Settings
The defaults are pre-configured:
- **Framework Preset**: Next.js
- **Build Command**: `npm run build` (runs Next.js 16 Turbopack build)
- **Output Directory**: `.next`
- **Install Command**: `npm install`

### Step 4: Environment Variables
Configure according to your desired operational mode:

| Variable | Required? | Default / Example | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | No (optional) | *Empty / Unset* | URL of the live FastAPI backend. If omitted, the dashboard defaults to **Demo Mode**. |

Click **Deploy**. Your dashboard will be live within ~1 minute with an edge-cached production deployment.

---

## 2. Operational Modes

The dashboard features a **Dual-Mode Data Architecture** (`lib/api/dataContext.tsx`):

### Mode A: Demo Mode (Default & Evaluator Mode)
- **Trigger**: Leave `NEXT_PUBLIC_API_BASE_URL` empty or unset in Vercel.
- **Behavior**:
  - The dashboard operates completely standalone using committed DGCA-grounded JSON fixtures in `data/fixtures/`.
  - Serves full 12-route passenger traffic-weighted basket, horizon price decay curves (T+1 to T+45), carrier market share distributions, and matched-sample Jevons/Laspeyres index trajectories.
  - No external backend or database connection required.
  - Zero cloud hosting costs for the evaluator.

### Mode B: Live Mode (Production Ingestion)
- **Trigger**: Set `NEXT_PUBLIC_API_BASE_URL=https://<your-backend-domain>` in Vercel Environment Variables.
- **Behavior**:
  - On initial render, `DataProvider` checks `${NEXT_PUBLIC_API_BASE_URL}/health` with a 3-second timeout.
  - When reachable, the dashboard switches to `LIVE_CONNECTED` and streams live index computations and quote observations.
  - **Fail-Safe Resilience**: If the live server becomes unreachable or restarts, the dashboard automatically transitions to `API_UNAVAILABLE` and cleanly falls back to offline fixtures so user interactions are never broken.

---

## 3. Production Backend Hosting (Railway Recommended)

If and when you host the Python FastAPI backend (`apix/api/main.py`), consider the following architectural requirements:

### Why Railway over Render:
- **Persistent Storage Volumes**: APIx collection logs (`fare_quote_log.csv`) and calculated series are stored on disk. Free-tier container hosts like Render use ephemeral filesystems that wipe disk contents on container restart or after 15 minutes of idle spin-down. Railway supports persistent storage volume mounts, ensuring collection history is preserved across deploys and restarts.

### Backend CORS Configuration:
Because `apix-dashboard` queries the API directly from the client's browser, the FastAPI backend must permit cross-origin requests from your Vercel domain.

In `apix/api/main.py`, CORS is controlled by the `APIX_CORS_ORIGINS` environment variable:
```bash
# On your Railway / backend container environment:
APIX_CORS_ORIGINS=https://<your-vercel-app>.vercel.app,https://<custom-domain>.gov.in
```

*Note: For security and browser standards compliance, wildcard `*` with credentials is explicitly disallowed.*

---

## 4. Edge Security & Performance

### Security Headers (`vercel.json`)
The dashboard includes edge security headers pre-configured in `apix-dashboard/vercel.json`:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: DENY`: Prevents clickjacking and unauthorized iframe embedding.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts referrer information leakage.

### Image Optimization (`next/image`)
All imagery (`/bg-sunset-wing.jpg`, `/airliner.jpg`, `/hero_aviation.jpg`) is served using Next.js `<Image>` components configured with:
- Positioned container parents (`relative` / `absolute inset-0`)
- Responsive `sizes` attributes for dynamic viewport-scaled srcsets
- Native WebP/AVIF compression via Vercel Edge Image Optimization
- Hero priority loading flags to optimize Largest Contentful Paint (LCP)

---

## 5. Pre-Deployment Verification

Always run the test suites before deploying or merging to `main`:

```bash
# 1. Run Python unit tests (backend logic & index methods)
py -m pytest tests/

# 2. Run contract formatting and fixture invariant checks
npm test --prefix apix-dashboard

# 3. Run ESLint (must report 0 errors, 0 warnings)
npm run lint --prefix apix-dashboard

# 4. Run Next.js production build
npm run build --prefix apix-dashboard
```
