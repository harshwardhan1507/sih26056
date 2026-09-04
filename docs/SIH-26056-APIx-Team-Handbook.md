# SIH 2026 — PS 26056
# Real-time Airfare Price Index (APIx) for India
## Team Handbook & Resource Pack

**Problem Statement ID:** 26056
**Title:** Development of a Real-time Airfare Price Index for India through Automated Web Scraping of Airline and OTA Portals for Augmentation of the Consumer Price Index (CPI)
**Sponsor:** Ministry of Statistics and Programme Implementation (MoSPI) / National Statistical Office (NSO)
**Document version:** Final, September 2026

---

# PART 0 — THE TWO-MINUTE BRIEF

**New to this? Read only this page first.**

### What we're building
A system that automatically collects airfare prices for major Indian routes every day, cleans them, and turns them into a price index number — the way MoSPI turns vegetable prices into food inflation. Output: a daily/weekly/monthly Airfare Price Index (APIx), a dashboard, and an API that MoSPI and RBI could consume.

### The one thing that makes us different
**The problem statement's opening premise is out of date, and we can prove it with the ministry's own documents.**

The PS says CPI collects airfares "manually from ticketing offices." As of the new CPI series launched February 2026, MoSPI *already* collects airfares online, weekly, through State Regional Offices checking well-known websites.

Every other team will walk in and say "you do this manually, let us automate it." We walk in and say: *"We know you already collect airfares online. Here's how to scale it from weekly-manual to daily-automated."* That reframe is worth more than any feature.

> **Replacement threatens people. Scaling flatters them.** Never say the word "replace."

### The three risks that will kill us
1. **We start collecting data too late.** The PS demands 30 days of back-tested results. That's a wall-clock constraint, not a coding one. Crude collector running inside two weeks or the deliverable is gone.
2. **We build a scraper and a dashboard and nothing else.** That's what everyone builds. The index methodology is where we win.
3. **We try to beat anti-bot systems.** Illegal-adjacent, undeployable, and unnecessary. See Part 6.

### What's already done for us (don't rebuild these)
| Thing | Where | Saves |
|---|---|---|
| DGCA route traffic, cleaned to CSV | GitHub, see §3.2 | ~1 week of PDF parsing |
| 300k historical Indian fare records with advance-purchase window | Kaggle, see §3.4 | Lets us build the index module in week 1 |
| Official MoSPI Python client | `pip install mospi-esankhyiki` | CPI data access, zero work |

### Who should read what
| Role | Read |
|---|---|
| Everyone | Part 0, Part 1 |
| Index / stats owner | Parts 1, 4, Appendix B |
| Scraping / backend | Parts 3, 5, 6, Appendix C |
| Dashboard / frontend | Parts 5, 8 |
| Presenter / PPT | Parts 0, 1, 2, 8 |

---

# TABLE OF CONTENTS

- **Part 0** — The Two-Minute Brief
- **Part 1** — The Strategic Reframe *(read this before writing any code)*
- **Part 2** — What We're Actually Building
- **Part 3** — Data Sources
- **Part 4** — Index Methodology *(where we win)*
- **Part 5** — Engineering Stack
- **Part 6** — Legal, Ethics & the Anti-Bot Question
- **Part 7** — Timeline & Ownership
- **Part 8** — The Demo & The Pitch
- **Appendix A** — Complete Link Directory
- **Appendix B** — Formal Bibliography
- **Appendix C** — Database Schema
- **Appendix D** — Outreach Email Template
- **Appendix E** — Things That Changed Recently (don't trust old tutorials)

---

# PART 1 — THE STRATEGIC REFRAME

## 1.1 The finding

MoSPI rebased the CPI from 2012=100 to 2024=100 and launched the new series in **February 2026**. Buried in the documentation is this, from the official FAQ:

> *"How are the prices for airfares collected in the CPI 2024 series? Airfares are collected through well-known online platforms."*

And from the Expert Group Report on Comprehensive Updation of CPI:

> *§3.9 — Airfare for the international direct routes are incorporated into the price collection framework in CPI 2024.*
> *Airfare data are to be collected by State Regional Offices from the well-known websites.*
> *§3.8 — Price collection of telecom services and online media services (OTT) will be done centrally by PSD through the online sources.*

**Supporting facts, all from MoSPI sources:**

- The CPI 2024 series supplements traditional collection with **alternative data sources**: e-commerce prices as an additional market in 12 large towns, online sources for select services such as airfares and OTT subscriptions, and administrative data for standardised services like rail fares, postal charges and fuel prices.
- **Online prices are collected weekly.** Physical market prices are collected monthly.
- **12 online markets** were added across 12 towns with population above 25 lakh.
- **CAPI** (Computer Assisted Personal Interviewing) was introduced — collection now happens on handheld devices with built-in validation and real-time monitoring.
- The Expert Group's **fifth meeting on 4 April 2024** specifically discussed "airfare routes and period" and price collection for airfare including international fare.
- HCES 2023-24 found household expenditure through online platforms at **4.0% rural and 10.5% urban** — the stated justification for adding online markets.

## 1.2 Why this matters more than anything else in this document

Read the PS description again:

> *"The current CPI framework, however, collects 'Transport and Communication' sub-group prices, including air travel fares, primarily through manual price-collection from a limited set of outlets and ticketing offices."*

That description predates the CPI 2024 launch. **Every competing team will quote it verbatim** — because it's in the problem statement, and because they won't read the Expert Group Report.

A MoSPI judge hearing "you collect airfares manually from ticketing offices" hears a team that didn't do its homework about the ministry's own recent, significant modernisation programme.

## 1.3 How to say it

**Don't say:** "MoSPI collects airfares manually. We'll automate it."

**Do say:** "We know PSD already collects airfares online, weekly, through State Regional Offices, and that international direct routes were added in CPI 2024. That's a manual online process on a limited route set at a single booking window. We've built the industrialised version — daily, five advance-purchase windows, DGCA-weighted route basket, with a full audit trail."

## 1.4 The gap table — put this on a slide

| Dimension | CPI 2024 today | APIx |
|---|---|---|
| Frequency | Weekly | Daily |
| Advance-purchase windows | Single collection period | T+1, T+7, T+15, T+30, T+45 |
| Route coverage | Limited defined route set | DGCA passenger-weighted basket |
| Collection | Manual, by SRO staff | Automated, scheduled, retried |
| Reproducibility | Human judgement in the loop | Full provenance on every quote |
| Latency to publication | Monthly, ~12 day lag | Same-day |

## 1.5 Two more facts for slide two

**Relevance is rising.** Transport's CPI weight went up in the rebasing:

| Sector | CPI 2012 | CPI 2024 |
|---|---|---|
| Rural | 5.645 | 8.644 |
| Urban | 7.129 | 8.985 |
| **Combined** | **6.394** | **8.796** |

*(Source: MoSPI Annexure V — see Appendix A. Item-level weights are also public; pull the specific air-travel item weight and quote it.)*

**The ministry has appetite for exactly this.** In March 2025, MoSPI was reported to be considering a separate **e-commerce price index**, and had asked e-commerce firms to share data on goods and services sold. The institutional direction of travel is toward alternative data sources. We are pushing on an open door.

## 1.6 A note on the PS wording

The PS says: *"an index-construction module based on **PSD** given routes and weights."*

**PSD = Price Statistics Division of MoSPI.** The PS is telling us the ministry would supply the basket and weights in a real deployment. Design the index module to accept an externally-supplied basket configuration file rather than hardcoding routes. Mention this in the presentation — it shows we read the PS carefully.

---

# PART 2 — WHAT WE'RE ACTUALLY BUILDING

## 2.1 The four deliverables (from the PS)

| # | Deliverable | Owner | Risk |
|---|---|---|---|
| a | Multi-source collection engine | Backend | Medium — mitigated by hybrid design |
| b | Cleaned, de-duplicated fare database | Backend + Data | Low |
| c | Index-construction module | **Stats owner** | **This is where we win or lose** |
| d | Interactive dashboard + API | Frontend | Low |
| — | 30 days back-tested vs DGCA data | Everyone | **HIGH — schedule risk, start now** |

## 2.2 System shape

```
   ┌──────────────── COLLECTION LAYER ────────────────┐
   │                                                   │
   │  Tier 1: Licensed APIs (TripJack / TBO / TP)     │
   │  Tier 2: Mandated tariff sheets  ← see §3.3      │
   │  Tier 3: Polite scraping (robots-compliant)      │
   │  Tier 4: Cached HAR replay (demo safety)         │
   │                                                   │
   │  → resolver.py picks best available per route     │
   └───────────────────────┬───────────────────────────┘
                           │
              every quote tagged with:
              source_id · collection_method · quality_flag
                           │
   ┌───────────────────────▼───────────────────────────┐
   │  CLEANING PIPELINE                                │
   │  outliers · missing prices · fare decomposition   │
   └───────────────────────┬───────────────────────────┘
                           │
   ┌───────────────────────▼───────────────────────────┐
   │  INDEX MODULE                                     │
   │  Jevons (elementary) → chained Laspeyres (upper)  │
   │  DGCA passenger weights                           │
   └──────────┬───────────────────────────┬────────────┘
              │                           │
     ┌────────▼────────┐        ┌─────────▼─────────┐
     │  Dashboard      │        │  FastAPI + OpenAPI │
     │  (public view)  │        │  (NSO / RBI feed)  │
     └─────────────────┘        └────────────────────┘
```

## 2.3 Scope discipline

**In scope:** 10–12 city pairs, 5 advance-purchase windows, 5–6 carriers, daily collection, one index family, one dashboard, one API.

**Out of scope (say so explicitly, it reads as maturity):** fare prediction, booking, international routes beyond a token demonstration, real-time streaming, mobile app.

Judges reward teams that scoped deliberately over teams that promised everything.

---

# PART 3 — DATA SOURCES

## 3.1 Fare data — status board

> ⚠️ **Amadeus is dead.** The Self-Service developer portal was decommissioned on **17 July 2026**; keys deactivated, portal inaccessible. Only Amadeus Enterprise remains, requiring IATA/ARC accreditation. Every tutorial older than mid-2026 will tell you to use it. Ignore them.

| Provider             | Access             | Real fares?       | India coverage | Verdict                       |
| -------------------- | ------------------ | ----------------- | -------------- | ----------------------------- |
| Amadeus Self-Service | ❌ Dead (Jul 2026)  | —                 | —              | Do not use                    |
| **TripJack**         | B2B, email them    | ✅                 | Excellent      | **Best fit — contact week 1** |
| **TBO**              | B2B, email them    | ✅                 | Excellent      | Second best — contact week 1  |
| **Travelpayouts**    | Free self-serve    | Cached            | Good           | Best free option              |
| Duffel               | Free test mode     | ❌ Sandbox         | —              | Pipeline shape only           |
| FlightAPI.io         | ~20–100 free calls | ✅                 | Moderate       | Demo scale                    |
| Aviationstack        | 100/month          | Schedules > fares | Moderate       | Marginal                      |

**TripJack** aggregates real-time inventory from LCCs, GDS, NDC, private and SOTO fares across 40+ countries, and says integration typically goes live in one to two weeks. Run by Atlas Travel Group, an IATA-approved agency. → Email template in **Appendix D**.

## 3.2 Route weights — DGCA

The PS requires city-pair selection "on the basis of DGCA passenger-traffic data."

**★★ Do not parse DGCA PDFs yourself.** `Vonter/india-aviation-traffic` on GitHub has already scraped and normalised them into CSVs under the Open Database License:

| File | Contents |
|---|---|
| `domestic/city.csv` | **Monthly city-pair passenger, freight and mail traffic, mid-2015 onwards** ← our weights |
| `domestic/carrier.csv` | Monthly carrier-wise traffic, mid-2015 onwards |
| `international/city.csv` | Quarterly city-pair, 2015 onwards |
| `international/carrier.csv` | Monthly carrier-wise |

Clone day one. Route weights become a twenty-minute pandas job. **Attribute properly under ODbL in our documentation.**

**Context figures for the deck:**
- Domestic carriers flew ~1.29 crore passengers in August 2025; Jan–Aug 2025 was 1,107.26 lakh vs 1,054.66 lakh in 2024 (+4.99%).
- Market share Aug 2025: IndiGo ~64.2%, Air India Group ~27.3%, Akasa ~5.4%, SpiceJet ~2%.
- India had 74 airports in 2014, 163 by late 2025. Domestic passengers: ~70m (2014) → 137m (2019).
- Growth has stalled: Jan–Apr 2026 cumulative growth was **0.06%**, against 7–10% annually for most of the previous decade.

## 3.3 ★ The hidden legal fare source — mandated tariff sheets

**This is a competitive advantage almost nobody will find.**

Under **Sub-Rule (2) of Rule 135 of the Aircraft Rules, 1937**, airfares established by airlines must be published on their websites. **DGCA Air Transport Circular 2 of 2010** requires airlines to display route-wise tariff sheets across their network in various fare categories, in the manner offered in the market.

The original directive was specific — airlines must:
- Furnish route-wise tariff across their network, in various fare categories, **to DGCA on the first day of every calendar month**
- Report any significant change to the filed tariff **within 24 hours**
- Maintain all tariff records in office
- **Publish airfares on their websites** or in daily newspapers

Critically, the requirement covers each **"fare bucket"** — the price slabs for each group of seats on each route. Tariff sheets must indicate the *range* of fares on all routes so passengers can see the various fares offered by each airline on every single route.

### Why this changes everything

| Booking engine      | Tariff sheet                    |
| ------------------- | ------------------------------- |
| Anti-bot protected  | Compliance page, no protection  |
| ToS-ambiguous       | Legally *required* to be public |
| One quote at a time | The whole fare ladder           |
| JS-heavy, fragile   | Usually static                  |
|                     |                                 |

**Build a `tariff_sheet` adapter alongside the live-quote adapter.** It gives us a second, legally unimpeachable stream — plus a genuinely novel analysis nobody else will have:

> **Declared fare bucket ranges vs. observed transacted quotes.** Are airlines pricing within their filed tariff? That's a compliance-monitoring feature we get almost for free, and it's exactly what DGCA's Tariff Monitoring Unit exists to check (§3.5).

**Action:** someone spend two hours locating the current tariff sheet page for IndiGo, Air India, Air India Express, Akasa and SpiceJet. IndiGo publishes tariff sheets on goindigo.in.

## 3.4 ★ Historical panel — build the index module before we have any data

Public Kaggle dataset: **300,261 distinct flight booking options** scraped from EaseMyTrip, covering India's **top six metro cities**, collected over **50 days from 11 February to 31 March 2022**, split into economy and business class.

Fields: airline, flight number, source city, destination city, departure time, arrival time, stops, class, duration, **days left before departure**, price.

> **`days_left` is our advance-purchase window.** This is a working historical panel with exactly the dimensions APIx needs.

**Use it in week 1** to build and validate `index/` — Jevons, chained Laspeyres, outlier handling, missing-price imputation — on real Indian fares, with zero scraping. Then swap in the live feed.

`kaggle.com/datasets/shubhambathwal/flight-price-prediction`

Secondary panel for robustness: PromptCloud's EaseMyTrip set, 199,244 records, 1 April – 30 June 2020, with crawl timestamps.

## 3.5 ★ DGCA's Tariff Monitoring Unit — our second customer

DGCA runs a **Tariff Monitoring Unit (TMU)** that monitors airfares on **78 selected routes** on a random basis **by checking airlines' websites, monthly**, to ensure airlines don't charge outside their declared range. Those 78 routes cover about **27% of domestic traffic**. It was established in **2010** to monitor and compare fares **manually**, originally as a "Tariff Analysis Unit" after fares ran 25–30% high on major routes.

**It's expanding.** In December 2025 the Aviation Minister told the Rajya Sabha that the TMU will be **further strengthened**, and that **international routes are now also being monitored** alongside domestic ones.

### The pitch

> The TMU is a manual monthly spot-check on 78 routes. APIx is a daily automated check on any number of routes, with a full audit trail and the same statutory basis. Same government, second customer, zero additional code.

**Bonus context — a tension we resolve.** In March 2025 DGCA asked airlines to submit granular, ticket-wise fare data going back two years. The Federation of Indian Airlines objected that disclosing such confidential data publicly risks airlines' competitiveness. **APIx sidesteps this entirely** — we only ever collect what is already displayed to consumers. Say this out loud. It's a real advantage over the approach the regulator actually tried.

## 3.6 CPI data — MoSPI

| Resource | Link |
|---|---|
| e-Sankhyiki portal | https://esankhyiki.mospi.gov.in/ |
| CPI direct view | https://esankhyiki.mospi.gov.in/macroindicators?product=cpi |
| Official Python client | `pip install mospi-esankhyiki` |
| CPI Open API | https://api.mospi.gov.in |
| MCP server (no auth) | https://mcp.mospi.gov.in/ |

Key facts: CPI published at **4 PM on the 12th of each month**. Back series Jan 2013 – Dec 2024 on the new base is available. 358 items across 12 Divisions, 43 Groups, 92 Classes, 162 Subclasses, following a UNSD-developed classification. Collection covers 1,465 rural and 1,395 urban markets across 434 towns, plus 12 online markets.

---

# PART 4 — INDEX METHODOLOGY

> **This is the section that wins the competition.** Almost every team will build a scraper and a dashboard. Almost none will be able to answer *"which elementary aggregate formula did you use, and why?"*

## 4.1 Primary source — read this end to end

**Eurostat (2020), *Practical Guidelines on Web Scraping for the HICP***
📄 https://ec.europa.eu/eurostat/documents/272892/12032198/Guidelines-web-scraping-HICP-11-2020.pdf

This document *is* our problem statement, written by people who do it professionally for a national statistics office. It covers legal aspects, technology, item coverage, sampling, classification, validation, and index compilation with scraped data. Eurostat explicitly recommends Selenium (RSelenium or the Python package) for dynamic pages, and notes that online collection reduces manual collection costs and response burden while enabling higher-frequency, higher-volume data.

Citing it reframes our ToS-compliant architecture as **international statistical practice**, not as a compromise.

## 4.2 The three concepts to be able to defend under questioning

### (a) Elementary aggregate formula → **Jevons**

Use the **Jevons index** — the geometric mean of price relatives — at the elementary level.

**Why:** arithmetic means (Carli, Dutot) are destroyed by the 200–400% intraday swings the PS itself describes. Jevons is the standard for scraped price data at ONS and Eurostat.

**One-sentence answer if asked:** *"Jevons, because it's the geometric mean of price relatives — it's invariant to the base period choice and it doesn't blow up on the extreme dispersion you get in dynamically-priced airfares."*

### (b) The CLIP framing → the sophisticated answer

ONS's **Clustering Large datasets Into Price indices** approach assumes that because a consumer may purchase any of a set of relatively homogeneous products, the index should reflect price change across the **whole set**, not a single tracked product. Products are clustered using unsupervised and supervised machine learning, and the index measures change between clusters over time.

**Why this fits us perfectly:** "all fares on DEL–BOM at T+7" is a homogeneous set, not a single product. And CLIP was designed precisely for the case where there is **no continuous time series available for each product** — which is exactly the sold-out-flight problem.

Full paper: https://www.ons.gov.uk/economy/inflationandpriceindices/articles/researchindicesusingwebscrapedpricedata/clusteringlargedatasetsintopriceindicesclip

### (c) Missing prices → **a sold-out flight is a missing price, not a zero price**

Handle with explicit class-mean imputation or documented carry-forward, **flagged in the data model** (`quality_flag = 'sold_out'`).

This is a genuine open problem in scraped-data CPI. Discussing it honestly reads as research, not as a bug.

## 4.3 Airfare-specific rules

**Never mix advance-purchase windows in a comparison.**
T+7 today vs T+7 yesterday. Comparing T+7 against T+30 is a **quality change**, not a price change. Treat the window as a product characteristic.

**Which fare enters the index — and how to defend it.**
BLS runs two different airfare measures, and the distinction is load-bearing:

| Measure | Includes |
|---|---|
| **CPI airline fares** | Prices paid by consumers, **including taxes and all distribution costs paid by the consumer** |
| **ATPI** (experimental) | Includes taxes, but **excludes distribution costs not received by the carrier** (e.g. travel agent fees) |

The CPI also covers trips on foreign carriers; ATPI did not.

→ **For CPI augmentation, APIx uses total fare paid by the consumer, including the OTA convenience fee** — because that's what the Indian traveller actually pays. Being able to say *why*, with a BLS citation, is the difference between a prototype and a proposal.

Source: BLS *Monthly Labor Review*, June 2005 — https://www.bls.gov/opub/mlr/2005/06/art2full.pdf

**Bias is a known, published problem.**
Good, Sickles & Weiher (2008) found an **upward bias in the BLS airfare index** over their sample period, using hedonic adjustment, per-period reweighting and a broader data protocol.

→ This justifies treating advance-purchase window as a quality characteristic, **and** gives us a legitimate research question for the final slide: *does India's CPI airfare collection show similar bias against high-frequency scraped fares?* That question is what a sponsoring ministry actually wants from a hackathon.

## 4.4 Outlier detection — don't invent a z-score

The PS requires "removes outliers." There is a published international review of the outlier detection methodologies national statistical institutes use for alternative data sources, noting that while outlier methods are well established for traditional data, more research is needed for the distinct quality and format of alternative data.

**Cite a method, don't invent one.**
📄 https://www.niesr.ac.uk/wp-content/uploads/2021/10/NIESR-DP-523-4.pdf

## 4.5 Upper-level aggregation

**Chained Laspeyres**, with DGCA passenger weights, and a documented rebasing rule. Accept the basket as an external config file (see §1.6).

## 4.6 Implementation & validation

Python has no index-number library of comparable quality to R's. **That's fine — write our own.** Jevons and chained Laspeyres are ~50 lines total. A small, readable, unit-tested `index/` module is a *better* demo than an opaque library import.

**Do this:** implement in Python → validate against **IndexNumR** (R, CRAN) on a toy dataset → commit that cross-validation test.

When a judge asks *"how do you know your index is correct?"*, point at a passing test that agrees with the R reference implementation to 10 decimal places.

| Library | Language | Use |
|---|---|---|
| IndexNumR | R | Cross-validation reference |
| PriceIndices | R | Multilateral methods, scanner/scraped data |
| eurostat/hicp | R | Implements the HICP Manual — read the vignette |

---

# PART 5 — ENGINEERING STACK

## 5.1 Components

| Layer | Tool | Note |
|---|---|---|
| Browser automation | **Playwright (Python)** | Better than Selenium for JS fare pages. **HAR record/replay makes the demo offline-proof.** |
| Scraping framework | Scrapy | Built-in throttling, retry, pipelines |
| JS + Scrapy | scrapy-playwright | Bridge for dynamic pages |
| robots.txt | Protego, or `urllib.robotparser` | Make compliance a **tested code path** |
| Rate limiting | Scrapy AutoThrottle | Cite as a *compliance* feature |
| Orchestration | Prefect (or Airflow / APScheduler) | Retry semantics + run-history UI |
| Time-series DB | TimescaleDB (Postgres) | Hypertables for fare quotes |
| Analytics DB | DuckDB | Zero-ops alternative for back-testing |
| Data validation | pandera (or Great Expectations) | **Satisfies the "automated testing" deliverable** |
| Testing | pytest + vcrpy | Record HTTP once, replay forever, zero network in CI |
| Public API | FastAPI | Ship an OpenAPI spec for NSO/RBI |
| Dashboard | Streamlit (fast) / Next.js + Recharts (polished) | Heatmaps, elasticity curves |

## 5.2 Repository layout

```
apix/
├── collector/
│   ├── compliance/
│   │   ├── robots.py            # per-host robots.txt, re-checked daily
│   │   ├── rate_limiter.py      # 1 req / 5–10s per host + jitter
│   │   ├── backoff.py           # honours 429/503 and Retry-After
│   │   └── circuit_breaker.py   # block → SOURCE_UNAVAILABLE, disable N hrs
│   ├── adapters/
│   │   ├── base.py              # FareSource interface
│   │   ├── tripjack_api.py
│   │   ├── travelpayouts_api.py
│   │   ├── tariff_sheet.py      # ← §3.3, the legal source
│   │   ├── scraper_indigo.py
│   │   └── cached_replay.py     # HAR replay for demos
│   └── resolver.py              # priority fallback chain per route × window
├── cleaning/
│   ├── outliers.py              # cite NIESR method
│   ├── imputation.py            # sold-out handling
│   └── decomposition.py         # base / tax / UDF / convenience fee
├── index/
│   ├── elementary.py            # Jevons
│   ├── aggregate.py             # chained Laspeyres
│   ├── weights.py               # DGCA passenger weights
│   └── basket.yaml              # externally-supplied config (§1.6)
├── api/                         # FastAPI + OpenAPI spec
├── dashboard/
├── tests/
│   ├── fixtures/                # saved HTML/HAR — never hit the network
│   └── test_index_vs_indexnumr.py   # ← the cross-validation test
└── docs/
```

## 5.3 The volume argument — put this on a slide

```
12 city-pairs × 5 advance-purchase windows × 6 sources
   = 360 requests/day
   = one request every 4 minutes
```

**No rate limiter on earth cares about this.**

Teams get blocked because they hammer an endpoint 200 times an hour while debugging a CSS selector. The fix isn't evasion — it's **fetch once, save the HTML/HAR to disk, and develop the parser against the fixture forever after.** This also hands us the "automated testing" deliverable for free.

## 5.4 Demo safety — non-negotiable

Three layers, all required:

1. **HAR replay** — Playwright records once, replays offline. The demo never touches the network.
2. **Seeded database** — 30–45 days of real collected data, loaded well before finals.
3. **Never live-scrape on stage.** Venue wifi plus a live scraper equals a failed demo. This has killed better projects than ours.

---

# PART 6 — LEGAL, ETHICS & THE ANTI-BOT QUESTION

## 6.1 The contradiction in the PS, and how we resolve it

The PS asks us to handle *"dynamic CAPTCHAs, anti-bot measures, IP rotation"* **and** to remain *"compliant with the robots.txt and terms of service of source websites."*

**These cannot both be satisfied.** Resolve it explicitly and confidently:

> **Hybrid collection framework:** licensed APIs primary → legally-mandated tariff sheets → ethical scraping → imputation. This mirrors how ONS, Statistics Netherlands, DESTATIS and ISTAT actually operate.

Frame it as **rigour**, not as a shortcut. The judges' real question is *"could the government actually run this?"* — and a system built on ToS violation cannot be adopted by a national statistics office.

## 6.2 The ethical-collection module — make it visible

Build it as a **named, tested component**. It's a slide, not a footnote.

- **Identify ourselves.** User-Agent naming the project with a contact URL. This is what statistical agencies do.
- **Rate limit.** 1 request per 5–10 seconds per host, randomised jitter, scheduled off-peak (IST 02:00–05:00).
- **Honour 429/503** and `Retry-After` with exponential backoff.
- **Parse robots.txt** per host, re-checked daily, with a per-source allow/deny registry.
- **★ Treat a CAPTCHA or block as a stop signal, not an obstacle.** Log it, disable that source for N hours, fall through the chain.
- **★ Then put the CAPTCHA-encounter rate on the dashboard as a data-quality metric.**

> That last decision signals more statistical maturity than a working scraper does. It says: *we understand that a data collection system must know, and report, when it is not collecting data.*

## 6.3 Provenance — the field that makes this auditable

Every quote row carries:

```
source_id · collection_method (api|scrape|imputed) · collected_at_utc · quality_flag
```

**This is the actual difference between a hackathon demo and something NSO could pilot.** Without provenance, the output is uncontestable in the wrong way — nobody can check it. With it, the index is auditable.

## 6.4 Legal points — state these precisely

| Point | Detail |
|---|---|
| Commercial re-use | Commercial re-use of scraped IP from internet sources is prohibited. NSIs use scraped data **for official statistics only**, processed in their own secure environment. Our use case is official statistics — say so, and put redistribution of raw quotes out of scope. |
| robots.txt | A **widely observed norm, not a statute.** Saying that accurately — neither over- nor under-claiming — reads as competence. |
| IT Act 2000, §43 | Unauthorised access / downloading from a computer resource. Know what we're avoiding. |
| Indian Contract Act 1872 | Browsewrap vs clickwrap ToS enforceability. |
| DPDP Act 2023 | Not directly binding (fares aren't personal data), but acknowledging it signals maturity. |
| Rule 135(2), Aircraft Rules 1937 | **Our positive legal basis** — tariff sheets are legally required to be public. |

## 6.5 Deployment story for the final slide

A production APIx would run on **data-sharing MoUs with DGCA and the carriers**, exactly as European NSIs operate. **Scraping is the bootstrap, not the destination.**

---

# PART 7 — TIMELINE & OWNERSHIP

## 7.1 Week 1 — non-negotiable

| # | Task | Owner | Why it's week 1 |
|---|---|---|---|
| 1 | **Crude collector writing to DB** | Backend | 30-day back-test is a wall-clock constraint |
| 2 | Send TripJack + TBO emails | Anyone | 1–2 week lead time for integration |
| 3 | Clone `Vonter/india-aviation-traffic`, derive weights | Data | Unblocks basket selection |
| 4 | Download Kaggle 300k panel, build `index/` against it | **Stats** | Index module without waiting for data |
| 5 | Locate tariff sheet pages for 5 carriers | Backend | §3.3 — the hidden legal source |
| 6 | Read Eurostat scraping guidelines end to end | Stats + lead | Everything else depends on this |

> **The week-1 test:** if nobody on the team wants to own the index-construction module, we should pick a different problem statement.

## 7.2 Week 2–3

- Read: CPI Manual (elementary aggregates, missing prices, quality adjustment); Good/Sickles/Weiher; BLS ATPI paper; Expert Group Report (find the air-travel item code)
- Build: cleaning pipeline with pandera schemas; fare decomposition; tariff-sheet adapter
- Build: cross-validation test against IndexNumR
- Collect: continuously, no gaps

## 7.3 Week 4+

- Dashboard, FastAPI + OpenAPI spec
- Back-test against DGCA data — correlation coefficient plus **honest discussion of divergence** (DGCA averages are realised transaction prices; ours are quoted offer prices — that gap is a *finding*, not a failure)
- December 2025 natural experiment analysis (Part 8)
- HAR fixtures for offline demo
- Documentation

## 7.4 Ownership

| Role | Responsible for |
|---|---|
| **Stats / index owner** | Parts 1 & 4, `index/`, `cleaning/`, back-test, the methodology answers |
| **Backend** | `collector/`, `compliance/`, adapters, database, FastAPI |
| **Frontend** | Dashboard, heatmaps, elasticity curves, demo polish |
| **Lead / presenter** | Parts 0–2 & 8, the reframe, outreach emails, documentation |

---

# PART 8 — THE DEMO & THE PITCH

## 8.1 ★ The December 2025 natural experiment — build the demo around this

During the **IndiGo scheduling crisis**, the airline cancelled nearly **4,500 flights over ten days from 2 December 2025**, affecting over **10 lakh passengers**. Fares on other carriers spiked.

On **6 December 2025** the government intervened. The Ministry of Civil Aviation capped airfares in the range of **₹7,500 to ₹18,000 depending on distance**:

| Distance | Cap |
|---|---|
| Up to 500 km | ₹7,500 |
| 500–1,000 km | ₹12,000 |
| 1,000–1,500 km | ₹15,000 |
| Delhi–Mumbai (~1,300 km) | ₹18,000 economy |

The order stated that disruptions had caused capacity constraints and an **unreasonable surge in fares on a number of sectors**, and that the fare limits applied to **all bookings regardless of whether purchased directly through the airline's website or through OTA platforms**. Fares had last been capped during the COVID-19 pandemic in 2020.

### Why this is the perfect demo

**1. The ministry publicly committed to needing exactly our capability.**
MoCA said it would *"continue to closely monitor fare levels through real-time data and active coordination with airlines and online travel platforms."*

**2. Compliance was messy and observable.**
Air India rolled out the caps **progressively** because the process involved third-party system dependencies, and offered **refunds of the differential** to guests who booked above the prescribed caps during the transition. A real-time index would have caught that lag. Manual weekly collection could not.

### The closing slide

> **One chart. Three lines. December 2025.**
>
> 1. What CPI's collection actually recorded
> 2. What APIx would have recorded
> 3. The government's fare caps
>
> Show the gap. **That single chart is the entire argument for the project.**

## 8.2 Third customer — the CCI angle

In **Case No. 32 of 2016** (the Jat Agitation airfare case), the Competition Commission of India analysed price data supplied by five airlines, formed a prima facie view that ticket prices rose on certain routes especially for tickets sold near departure, and ordered investigation of the **pricing algorithms** themselves. It ultimately found no cartel — revenue teams input data but officials made the final pricing decisions.

**The point for us:** CCI had to *request* fare data from the airlines because no independent source existed. APIx would be that source.

📄 https://www.cci.gov.in/images/antitrustorder/en/3220161652248293.pdf

## 8.3 Our honest-limitation slide — do this before a judge does it to us

**Just over 4% of Indians travel by air**, against 37%+ in China and 85%+ in the US. Air travel is a small, urban, higher-income slice of the CPI basket.

Say it ourselves. Then say why it still matters: transport's CPI weight rose from 6.394 to 8.796, air travel penetration is growing from a low base, and the item is unusually volatile — which means it contributes disproportionate *measurement noise* relative to its weight, and that noise is precisely what better collection reduces.

**Also worth noting:** Cleartrip launched a **Price Trends** feature in January 2026, telling users whether a fare is cheaper than usual, typically priced, or higher than usual based on recent pricing patterns for that route and date. The OTAs are already building this intelligence privately. That strengthens the case for a public, methodologically transparent version.

## 8.4 Anticipated questions — prepare answers

| Question | Where the answer lives |
|---|---|
| "Which index formula, and why?" | §4.2(a) |
| "How do you know your index is correct?" | §4.6 — the IndexNumR cross-validation test |
| "What about sold-out flights?" | §4.2(c) |
| "Isn't this scraping illegal?" | §6.1, §6.4, and §3.3 (the legal source) |
| "Could the government actually run this?" | §6.5 |
| "MoSPI already collects this, don't they?" | §1.3 — **and we bring it up first** |
| "Why does airfare matter, it's tiny?" | §8.3 |
| "How do you handle blocks?" | §5.3, §6.2 — treat as data-quality metric |

---

# APPENDIX A — COMPLETE LINK DIRECTORY

## A.1 MoSPI / CPI

| Resource | Link |
|---|---|
| CPI theme page | https://www.mospi.gov.in/themes/product/9-consumer-price-index-cpi |
| e-Sankhyiki portal | https://esankhyiki.mospi.gov.in/ |
| CPI direct view | https://esankhyiki.mospi.gov.in/macroindicators?product=cpi |
| Old CPI warehouse (2012=100) | http://www.cpi.mospi.gov.in |
| CPI Open API | https://api.mospi.gov.in |
| CPI API User Manual (PDF) | https://api.mospi.gov.in/API/CPI%20API%20User%20Manual.pdf |
| ★ Official Python client | https://github.com/nso-india/mospi-esankhyiki |
| PyPI package | https://pypi.org/project/mospi-esankhyiki/ |
| MoSPI MCP server | https://github.com/nso-india/esankhyiki-mcp |
| ★★ **Expert Group Report press note** | https://cpi.mospi.gov.in/PDFile/Press%20note%20on%20release%20of%20Expert%20Group%20Report%20on%20Comprehensive%20Updation%20of%20CPI.pdf |
| ★★ **Expert Group Report (full)** | https://www.mospi.gov.in/uploads/Marquee/doc-0aee0026-bf32-4213-ae4f-c5308088444e.pdf |
| ★★ **Annexure V — FAQs + weights** | https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf |
| National Metadata Structure for CPI | https://www.mospi.gov.in/uploads/governance/governance1773827165694_a1652a6d-80e4-4e64-bc57-cfd41dcd00cb_National_Metadata_Structure_for_CPI_(2).pdf |
| First press release on 2024=100 | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2227012 |
| PIB release on rebasing | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2291051 |
| CPI press release Jan 2026 | https://www.mospi.gov.in/uploads/latestReleases/latest_release_1770891893893_6b458c0a-c327-4fef-a554-41131ea67273_Press_Relase_of_CPI_for_Jan26.pdf |
| CPI press release Mar 2026 | https://mospi.gov.in/uploads/latestreleasesfiles/1776078391571-Press_Release_of_CPI_March_2026.pdf |
| RBI (MPC reports) | https://www.rbi.org.in |

## A.2 Aviation data

| Resource | Link |
|---|---|
| DGCA | https://www.dgca.gov.in |
| ★★ Pre-cleaned DGCA CSVs | https://github.com/Vonter/india-aviation-traffic |
| Airports Authority of India | https://www.aai.aero |
| Ministry of Civil Aviation | https://www.civilaviation.gov.in |
| Open Government Data | https://data.gov.in |
| PIB on TMU + Circular 2 of 2010 | https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1810467 |
| CCI Case No. 32 of 2016 | https://www.cci.gov.in/images/antitrustorder/en/3220161652248293.pdf |

## A.3 Methodology

| Resource | Link |
|---|---|
| ★★ Eurostat web-scraping guidelines (2020) | https://ec.europa.eu/eurostat/documents/272892/12032198/Guidelines-web-scraping-HICP-11-2020.pdf |
| ★ Eurostat/UNECE "How to start" paper | https://unece.org/sites/default/files/2021-05/Session_2_Eurostat_Paper.pdf |
| ★ ONS scraped price indices | https://www.ons.gov.uk/economy/inflationandpriceindices/articles/researchindicesusingwebscrapedpricedata/latest |
| ★ ONS CLIP (full paper) | https://www.ons.gov.uk/economy/inflationandpriceindices/articles/researchindicesusingwebscrapedpricedata/clusteringlargedatasetsintopriceindicesclip |
| ONS alternative data sources plan | https://www.ons.gov.uk/economy/inflationandpriceindices/articles/usingalternativedatasourcesinconsumerpriceindices/may2019 |
| ★ NIESR outlier detection review | https://www.niesr.ac.uk/wp-content/uploads/2021/10/NIESR-DP-523-4.pdf |
| National Academies, Modernizing the CPI, Ch. 2 | https://www.nationalacademies.org/read/26485/chapter/4 |
| Eurostat ESS web scraping conference | https://ec.europa.eu/eurostat/web/european-statistical-system/-/web-scraping-price-collection-and-detailed-average-prices |
| Eurostat CIRCABC use-cases deck | https://circabc.europa.eu/sd/a/5e250346-44a9-471b-87f1-5b5ddb59aa77/1_Big%20Data%20Sources%20part3-Day%201-A%20Use.pdf |
| eurostat/hicp R package | https://github.com/eurostat/hicp · https://cran.r-project.org/package=hicp |
| IndexNumR (R) | https://cran.r-project.org/package=IndexNumR |
| PriceIndices (R) | https://cran.r-project.org/package=PriceIndices |

## A.4 Airfare index literature

| Resource | Link |
|---|---|
| ★ BLS airline fares factsheet | https://www.bls.gov/cpi/factsheets/ |
| ★ BLS ATPI paper (MLR June 2005) | https://www.bls.gov/opub/mlr/2005/06/art2full.pdf |
| BLS TED, ATPI vs CPI divergence | https://www.bls.gov/opub/ted/2005/jun/wk4/art02.txt |
| ★ Good, Sickles & Weiher hedonic index | https://ideas.repec.org/a/bla/revinw/v54y2008i3p438-465.html |
| US airfare CPI historical series | https://www.usinflationcalculator.com/inflation/airfare-inflation/ |
| BLS series CUSR0000SETG01 | https://fred.stlouisfed.org |

## A.5 Fare APIs

| Provider | Link |
|---|---|
| TripJack | https://tripjack.com |
| TBO | https://www.travelboutiqueonline.com/flight_api.aspx |
| Travelpayouts | https://www.travelpayouts.com |
| Duffel | https://duffel.com |
| FlightAPI.io | https://www.flightapi.io |
| Aviationstack | https://aviationstack.com |

## A.6 Datasets

| Dataset | Link |
|---|---|
| ★★ EaseMyTrip 300k panel (with `days_left`) | https://www.kaggle.com/datasets/shubhambathwal/flight-price-prediction |
| PromptCloud EaseMyTrip, Apr–Jun 2020 | https://www.kaggle.com/datasets/promptcloud/easemytrip-flight-fare-travel-listings |
| MakeMyTrip fare sample, Aug 2023 | https://www.kaggle.com/datasets/andrewgeorgeissac/flight-price-data-of-indian-cities-makemytrip |

## A.7 Tooling

Playwright https://playwright.dev/python · Scrapy https://scrapy.org · scrapy-playwright https://github.com/scrapy-plugins/scrapy-playwright · Protego https://github.com/scrapy/protego · AutoThrottle https://docs.scrapy.org/en/latest/topics/autothrottle.html · Prefect https://www.prefect.io · Airflow https://airflow.apache.org · TimescaleDB https://www.timescale.com · DuckDB https://duckdb.org · pandera https://pandera.readthedocs.io · Great Expectations https://greatexpectations.io · pytest https://docs.pytest.org · vcrpy https://vcrpy.readthedocs.io · FastAPI https://fastapi.tiangolo.com · Streamlit https://streamlit.io · Recharts https://recharts.org · Plotly https://plotly.com/python

---

# APPENDIX B — FORMAL BIBLIOGRAPHY

*For the project report.*

### Official statistics — methodology

1. Eurostat (2020). *Harmonised Indices of Consumer Prices: Practical Guidelines on Web Scraping for the HICP.* Directorate C, Unit C-4. European Commission, Luxembourg.
2. Eurostat (2021). *How to Start with Web Scraping in the HICP: Evidence from EU Member States.* UNECE Meeting on the Management of Statistical Information Systems.
3. Eurostat (2017). *HICP: Practical Guide for Processing Supermarket Scanner Data.* European Commission, Luxembourg.
4. Eurostat (2024). *HICP Methodological Manual.* European Commission, Luxembourg.
5. Office for National Statistics (UK). *Research Indices Using Web Scraped Price Data.*
6. Office for National Statistics (UK). *Clustering Large Datasets Into Price Indices (CLIP).*
7. Office for National Statistics (UK) (2019). *Using Alternative Data Sources in Consumer Price Indices.*
8. Boshoff, J., Mao, X. & Young, G. (2020). *Outlier Detection Methodologies for Alternative Data Sources: International Review of Current Practices.* NIESR Discussion Paper 523.
9. National Academies of Sciences, Engineering, and Medicine (2022). *Modernizing the Consumer Price Index for the 21st Century.* Chapter 2. National Academies Press, Washington DC.
10. ILO, IMF, OECD, UNECE, Eurostat & World Bank (2020). *Consumer Price Index Manual: Concepts and Methods.* IMF, Washington DC.
11. ten Bosch, O. & Windmeijer, D. *On the Use of Internet Robots for Official Statistics.* Statistics Netherlands.
12. Krijnen, D., Bot, R. & Lampropoulos, G. *Automated Web Scraping APIs.* Leiden.

### Airfare price indices

13. Good, D. H., Sickles, R. C. & Weiher, J. C. (2008). "A Hedonic Price Index for Airline Travel." *Review of Income and Wealth*, 54(3), 438–465.
14. U.S. Bureau of Labor Statistics (2005). "Developing an Air Travel Price Index." *Monthly Labor Review*, June 2005.
15. U.S. Bureau of Labor Statistics. *Measuring Price Change in the CPI: Airline Fares.* CPI Factsheets.

### Online price measurement

16. Cavallo, A. & Rigobon, R. (2016). "The Billion Prices Project: Using Online Prices for Measurement and Research." *Journal of Economic Perspectives*, 30(2), 151–178.

### Indian official statistics & regulation

17. Ministry of Statistics and Programme Implementation (2026). *Report of the Expert Group on Comprehensive Updation of Consumer Price Index (Base 2024=100).* Government of India.
18. Ministry of Statistics and Programme Implementation (2026). *Frequently Asked Questions on the CPI 2024 Series* (Annexure V). Government of India.
19. Ministry of Statistics and Programme Implementation. *National Metadata Structure (NMDS) for Consumer Price Index.* Government of India.
20. Press Information Bureau (2026). *MoSPI Revises Base Year of the Consumer Price Index from 2012=100 to 2024=100.* Government of India.
21. Directorate General of Civil Aviation. *Air Transport Circular 2 of 2010 — Route-wise Tariff Publication.* Government of India.
22. Government of India. *Aircraft Rules, 1937*, Rule 135 (Sub-Rules 1 and 2).
23. Directorate General of Civil Aviation. *Monthly Statistics — Domestic Air Transport.* Government of India.
24. Competition Commission of India (2021). *Case No. 32 of 2016 — Alleged Cartelisation in the Airlines Industry.*
25. Ministry of Civil Aviation (2025). *Directive on Capping of Economy Class Base Fares*, 6 December 2025.

### Datasets

26. Vonter. *india-aviation-traffic: Dataset of Indian Aviation Traffic, by Carrier and City.* Sourced from DGCA and MoCA. Open Database License (ODbL) v1.0.
27. Bathwal, S. *Flight Price Prediction* [dataset]. Kaggle. 300,261 records scraped from EaseMyTrip, 11 Feb – 31 Mar 2022.
28. National Statistical Office, India. *e-Sankhyiki Portal.*

### Industry / access

29. Crotty, A. (2026, February 9). "Amadeus to Shut Down Self-Service APIs Portal for Developers." *PhocusWire.*

---

# APPENDIX C — DATABASE SCHEMA

```sql
CREATE TABLE fare_quote (
    quote_id            BIGSERIAL PRIMARY KEY,
    collected_at_utc    TIMESTAMPTZ NOT NULL,
    departure_date      DATE        NOT NULL,
    advance_window_days INTEGER     NOT NULL,  -- 1, 7, 15, 30, 45
    origin_iata         CHAR(3)     NOT NULL,
    destination_iata    CHAR(3)     NOT NULL,
    carrier_iata        CHAR(2)     NOT NULL,
    flight_number       TEXT,
    fare_class          TEXT,                  -- Economy / Premium / Business
    fare_brand          TEXT,                  -- Saver / Flexi / Corporate

    -- fare decomposition (see §4.3 for why this matters)
    base_fare_inr       NUMERIC(10,2),
    taxes_inr           NUMERIC(10,2),
    udf_inr             NUMERIC(10,2),         -- User Development Fee
    convenience_fee_inr NUMERIC(10,2),         -- OTA-specific
    total_fare_inr      NUMERIC(10,2) NOT NULL,   -- ← this is what enters APIx

    -- provenance: the field that makes this auditable (§6.3)
    source_id           TEXT        NOT NULL,
    collection_method   TEXT        NOT NULL,  -- api | tariff_sheet | scrape | imputed
    quality_flag        TEXT        NOT NULL,  -- ok | outlier | imputed | sold_out
    raw_payload_hash    TEXT,

    UNIQUE (collected_at_utc, origin_iata, destination_iata,
            carrier_iata, flight_number, fare_brand, source_id)
);

SELECT create_hypertable('fare_quote', 'collected_at_utc');

-- Declared tariff bands from mandated tariff sheets (§3.3).
-- Enables the novel "declared range vs observed quote" compliance analysis.
CREATE TABLE declared_tariff (
    tariff_id           BIGSERIAL PRIMARY KEY,
    filed_month         DATE        NOT NULL,
    carrier_iata        CHAR(2)     NOT NULL,
    origin_iata         CHAR(3)     NOT NULL,
    destination_iata    CHAR(3)     NOT NULL,
    fare_bucket         TEXT        NOT NULL,
    min_fare_inr        NUMERIC(10,2),
    max_fare_inr        NUMERIC(10,2),
    source_url          TEXT        NOT NULL,
    retrieved_at_utc    TIMESTAMPTZ NOT NULL
);
```

**Note on `quality_flag = 'sold_out'`:** a sold-out flight is recorded as an **observation with a missing price** — never as an absent row, never as zero. That distinction is the whole ballgame in scraped-data CPI, and having it in the schema shows we knew it before writing the index module.

---

# APPENDIX D — OUTREACH EMAIL TEMPLATE

Send to TripJack and TBO in week 1. Even a written "no" is a slide. A sandbox key plus a "yes in principle" is a *strong* slide, because it demonstrates the deployment pathway MoSPI would actually need.

---

**Subject:** Read-only API access request — Smart India Hackathon 2026, MoSPI Problem Statement 26056

Dear [Team],

We are a student team selected for Smart India Hackathon 2026, working on a problem statement sponsored by the Ministry of Statistics and Programme Implementation to build a real-time airfare price index for augmenting India's Consumer Price Index.

We are requesting read-only, low-volume search API access — approximately 300 queries per day across 12 domestic city-pairs — for a **non-commercial research prototype**. No bookings, no resale, no redistribution of fare data. We would credit [Company] as the data partner in all documentation and presentations.

We are happy to sign an NDA or accept any usage restrictions you require, and to share our compliance design (rate limiting, robots.txt adherence, data-retention policy) in advance.

Would a 15-minute call be possible this week?

With thanks,
[Names, institution, contact]

---

# APPENDIX E — THINGS THAT CHANGED RECENTLY

**Do not trust tutorials, blog posts, or prior-year SIH repos older than mid-2026 on these points.**

| What changed | When | Impact on us |
|---|---|---|
| **Amadeus Self-Service portal decommissioned** | 17 Jul 2026 | Every "use Amadeus" tutorial is now wrong. Keys deactivated, Enterprise only. |
| **CPI rebased 2012=100 → 2024=100** | Feb 2026 | Transport weight up; 358 items; airfares now collected online. **This is our reframe.** |
| **MoSPI began online airfare collection** | Feb 2026 (CPI 2024) | The PS premise is stale. See Part 1. |
| **MoSPI MCP server launched** | Feb 2026 | Free, no-auth access to official stats. |
| **DGCA TMU expanded to international routes** | Dec 2025 | Second customer, actively growing. |
| **Fare caps imposed during IndiGo crisis** | Dec 2025 | Our natural experiment. First caps since 2020. |
| **Cleartrip launched Price Trends** | Jan 2026 | OTAs building this privately — strengthens our case. |

---

*Compiled September 2026. API availability and government portals change fast — the Amadeus shutdown proves it. Re-verify every access claim in Part 3 before building on it.*
