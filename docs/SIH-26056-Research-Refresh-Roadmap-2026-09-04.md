# SIH PS 26056 APIx Research Refresh & Execution Roadmap

**Research date:** 2026-09-04  
**Project:** APIx, real-time airfare price index for India  
**Repo:** `harshwardhan1507/sih26056`

This refresh updates the September 2026 handbook claims that are most likely to go stale: API access, MoSPI/DGCA portal status, tariff-sheet availability, methodology links, and the historical Kaggle panel.

## 1. Research Refresh

| Area | Current finding | Changed since handbook? | Source/date |
|---|---|---|---|
| TripJack API access | TripJack remains a B2B/approved-supplier integration path rather than a simple public self-serve developer API. Public integration vendors describe approved TripJack credentials, live search, availability, pricing controls, booking workflow, testing, and launch. Treat onboarding as partner/outreach gated. | No reversal found; still start outreach immediately. | SRDV TripJack integration page, crawled 2026-09-04: https://www.srdvtechnologies.com/tripjack-api-integration |
| TripJack cost/onboarding | Public third-party cost signals vary. One 2026 comparison says TripJack has a lower entry barrier than TBO, while another vendor quotes TripJack integration projects around USD 2,000-5,000. These are vendor/integration signals, not official TripJack pricing. | Add uncertainty: do not promise exact pricing without TripJack reply. | FlyBlaze comparison, crawled 2026-09-04: https://flyblaze.com/tbo-vs-tripjack-api/; eWeblink, crawled 2026-09-04: https://www.eweblink.net/tripjack-api-integration.html |
| TBO API access | TBO flight API remains B2B/agency-oriented. Public integration pages describe real-time availability/pricing, registered-airline access, and booking/API integration through travel portals. | No reversal found. | TBO official flight API page, crawled 2026-09-04: https://www.travelboutiqueonline.com/flight_api.aspx; FlightsLogic TBO page, crawled 2026-09-04: https://www.flightslogic.com/travel-boutique-online-flight-api-integration.php |
| TBO cost/onboarding | Public sources do not expose official TBO pricing or approval SLA. A 2026 third-party comparison claims high entry cost with deposits around INR 2 lakh+, but this needs confirmation from TBO. | Add uncertainty: exact price/SLA blocked on outreach. | FlyBlaze comparison, crawled 2026-09-04: https://flyblaze.com/tbo-vs-tripjack-api/ |
| Travelpayouts / Aviasales API | Travelpayouts/Aviasales Data API is still positioned as travel insights, price trends, and popular destination data. Their own guidance recommends cached data and says request counting must be handled by the user. The old Flight Search API version was scheduled to stop on 2026-06-15; new integrations should use the newer version. | Yes: old Flight Search API should not be used for new work. | Aviasales Data API, crawled 2026-09-04: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API; API rate limits, crawled 2026-09-04: https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits; old API notice, crawled 2026-09-04: https://support.travelpayouts.com/hc/en-us/articles/203956173-Aviasales-Flights-Search-API-old-version |
| FlightAPI.io | FlightAPI.io advertises a flight price API with real-time flight-price data, JSON output, multi-vendor comparison, 30-day free trial, no credit card, and 20 free credits on the flight-price API page. Use for demo-scale validation, not 30-day production collection. | No major change found; quota is too small for APIx full collection. | FlightAPI.io flight price page, crawled 2026-09-04: https://www.flightapi.io/flight-price-api/ |
| Aviationstack | Aviationstack still appears to be flight status/schedules/tracking, not a domestic Indian fare-price source. Free plan is 100 requests/month; paid tiers add historical/routes/future flights and commercial use. | No fare-coverage upgrade found. | Aviationstack home/pricing, crawled 2026-09-04: https://aviationstack.com/ and https://aviationstack.com/pricing |
| New API providers | SerpApi Google Flights and newer aviation API comparison posts exist, but no newly launched, official, self-serve Indian domestic real-time fare API was found that cleanly replaces TripJack/TBO. | No clear new primary provider found. | SerpApi Google Flights API, crawled 2026-09-04: https://serpapi.com/google-flights-api; ScrapingBee 2026 API roundup, published 2026-02-10: https://www.scrapingbee.com/blog/top-flights-apis-for-travel-apps/ |
| Amadeus | Amadeus developer site now states the Self-Service portal was decommissioned on 2026-07-17 and the site is for the Enterprise API Portal only. PhocusWire reported the shutdown on 2026-02-09. | Confirmed. Do not use Amadeus Self-Service tutorials. | Amadeus Developers, crawled 2026-09-04: https://developers.amadeus.com/; PhocusWire, 2026-02-09: https://www.phocuswire.com/amadeus-shut-down-self-service-apis-portal-developers |
| MoSPI CPI 2024 methodology | Verified from official Annexure V FAQ & PIB PRID 2243779 (2026-03-23): MoSPI bases CPI on HCES 2023-24 (base 2024=100) using COICOP 2018. Online price collection covers 12 major online markets across 12 >25L towns weekly on identified days/times mapped by Field Operations Division (FOD) regional offices. Q14/Q27 confirm: "price collection for airfare, telephone and OTT are also collected through online platforms." Elementary aggregation uses Jevons formula; higher-level uses Young/Modified Laspeyres. Detailed in docs/data-sources/MOSPI_CPI2024_AIRFARE.md. | Confirmed verbatim quotes & methodology. | MoSPI Annexure V FAQ: https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf; PIB PRID 2243779, 2026-03-23: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2243779&lang=1&reg=3 |
| CPI item-level airfare weight | Verified official PDFs: Annexure V provides Division/Group weights. Combined Transport Division weight increased from 6.394% (2012) to 8.796% (2024) (Rural: 8.644%, Urban: 8.985%). Exact 358 item-level weights are published separately on cpi.mospi.gov.in announcement tab and are not contained in the FAQ PDF. Formally marked UNRESOLVED at decimal item level from PDF; APIx pitch uses Division 07 (Transport: 8.796%) combined with DGCA route-level volume weights. | Unresolved at decimal item level in public FAQ PDF; Transport Division weight is 8.796%. | MoSPI Annexure V FAQ, Question 39, checked 2026-09-04: https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf |
| e-Sankhyiki / API portals | e-Sankhyiki portal is live (200 OK); api.mospi.gov.in is live (200 OK, serving Nginx + Swagger UI 3.24.2); MoSPI Python library page is live (200 OK); `mospi-esankhyiki` PyPI package confirmed live at version `0.1.4` (checked 2026-09-04). | Verified live. | e-Sankhyiki: https://esankhyiki.mospi.gov.in/; API portal: https://api.mospi.gov.in/; MoSPI Python lib: https://www.mospi.gov.in/esankhyiki-python-library; PyPI: https://pypi.org/project/mospi-esankhyiki/ |
| MoSPI alternative data announcements | Confirmed official direction toward CPI framework strengthening and rebasing; no airfare-specific post-September-2026 MoSPI announcement was found during this pass. | No new airfare-specific announcement found. | PIB, posted 2026-03-23: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2243779&lang=1&reg=3 |
| DGCA route-weight data | `Vonter/india-aviation-traffic` is still live under ODbL-1.0. Current repo default branch is `main`; latest commit checked by GitHub API is `42deff1`, dated 2026-07-06. Aggregated domestic city data is now under `aggregated/domestic/city.csv` and extends to May 2026 in the checked CSV. | Yes: path is `aggregated/domestic/city.csv`, not just `domestic/city.csv`. | GitHub API checks run 2026-09-04; repo: https://github.com/Vonter/india-aviation-traffic |
| DGCA TMU | PIB confirms Rule 135 framing and DGCA monthly monitoring of selected routes. December 2025 reporting says government was strengthening the DGCA Tariff Monitoring Unit to prevent opportunistic pricing. | TMU remains pitch-relevant. | PIB, posted 2022-03-28: https://www.pib.gov.in/PressReleasePage.aspx?PRID=1810467; Economic Times/PTI, crawled 2026-09-04: https://hospitality.economictimes.indiatimes.com/news/travel/govt-taking-high-airfares-seriously-strengthening-dgca-tariff-monitoring-unit-aviation-minister/125998430 |
| December 2025 fare caps | MoCA imposed fare-discipline monitoring during the IndiGo disruption on 2025-12-06 and said it would monitor fare levels through real-time data with airlines/OTAs. Public reporting indicates the temporary fare caps were withdrawn effective 2026-03-23 after operations stabilized. | Yes: caps are no longer in force. | PIB, posted 2025-12-06: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2199755; public reporting snippet, crawled 2026-09-04 |
| Rule 135 / Circular 2 of 2010 | Rule 135 basis is still cited by PIB: airlines establish tariffs under Rule 135(1), and established airfares are published on airline websites under Rule 135(2). DGCA site is live and last updated 2026-09-04. | No contradiction found. | PIB, posted 2022-03-28: https://www.pib.gov.in/PressReleasePage.aspx?PRID=1810467; DGCA site, crawled 2026-09-04: https://www.dgca.gov.in/ |
| Airline tariff sheets | Issue #4 research confirmed legal basis: Rule 135(2), Aircraft Rules 1937 is current; ATC 02/2010 is still operative. Verified sources: (1) Air India — direct PDF at https://www.airindia.com/in/en/tariff.html (~1.2 MB, naming pattern TARIFF-SHEET-AS-ON-01{MMM}{YY}.pdf, LOW complexity, first parser target for #11); (2) IndiGo — PDF behind footer link at https://www.goindigo.in/ (MEDIUM, needs browser); (3) Akasa — PDF at https://www.akasaair.com/fare-sheet, CF-protected, CDN path https://assets.akasaair.com/f/159922/x/c1ce86c83e/fare-sheet-akasa-air.pdf (MEDIUM); (4) SpiceJet — PDF at corporate subdomain https://corporate.spicejet.com/Content/pdf/Tariffs.pdf (LOW-MEDIUM). Air India Express UNRESOLVED — /tariff and /en-in/fees-and-charges both return 404; likely URL restructured post-AI merger. Full detail in docs/data-sources/TARIFF_SHEET_SOURCES.md. | Yes: AIX unresolved; AI confirmed as lowest-complexity first parser target. | Issue #4 research, 2026-09-04. |
| Competitive landscape | A public Slideshare deck for SIH26056 “AirIndex” exists. Public GitHub topic/problem-statement repos mostly mirror SIH problem statements, not working airfare-index systems. Differentiation should emphasize MoSPI reframe, Jevons/Laspeyres methodology, DGCA weighting, tariff-sheet stream, and 30-day back-test. | Yes: visible competing decks exist. | Slideshare, crawled 2026-09-04: https://www.slideshare.net/slideshow/airindex-real-time-airfare-price-intelligence-platform-for-india/289488426; GitHub SIH topic, crawled 2026-09-04: https://github.com/topics/sih-2026 |
| Methodology links | Eurostat HICP web-scraping guidelines are still live. NIESR outlier-detection PDF is live. ONS has newer technical guidance on alternative-data elementary aggregates revised 2026-03-25, which should be added to the handbook bibliography. | Yes: add ONS 2026 guidance. | Eurostat HICP publications, crawled 2026-09-04: https://ec.europa.eu/eurostat/web/hicp/publications; NIESR PDF, crawled 2026-09-04: https://niesr.ac.uk/wp-content/uploads/2021/10/NIESR-DP-523-4.pdf; ONS alternative data aggregates, revised 2026-03-25: https://www.ons.gov.uk/economy/inflationandpriceindices/methodologies/alternativedataaggregatesinconsumerprices |
| Kaggle EaseMyTrip dataset | Kaggle dataset `shubhambathwal/flight-price-prediction` is downloadable. The local download produced `Clean_Dataset.csv`, `economy.csv`, and `business.csv`; `Clean_Dataset.csv` has 300,153 records. Kaggle CLI reported license `CC0-1.0`. | Confirmed downloadable; row count differs slightly from the rounded 300k handbook wording. | Kaggle dataset, crawled/downloaded 2026-09-04: https://www.kaggle.com/datasets/shubhambathwal/flight-price-prediction |

## 2. Roadmap

| Phase | Task | Owner | Depends on | Status | Maps to |
|---|---|---|---|---|---|
| Week 1 | Send TripJack and TBO read-only access outreach; record pricing/SLA replies | Lead/Presenter | none | not started | a |
| Week 1 | Download EaseMyTrip 300k panel and document local files/license | Backend + Data | none | done | b / c |
| Week 1 | Build Kaggle panel loader with route, carrier, class, `days_left`, and price normalization | Stats/Index | dataset download | not started | c |
| Week 1 | Create DGCA route-weight script from `aggregated/domestic/city.csv` | Stats/Index | DGCA CSV | not started | c / back-test |
| Week 1 | Implement `resolver.py` source priority: API, tariff sheet, polite scrape, simulated | Backend | adapter contract | not started | a |
| Week 2 | Implement cleaning pipeline: schema validation, outliers, sold-out/missing handling, imputation | Backend + Data | FareQuote schema, Kaggle loader | not started | b |
| Week 2 | Locate/parse first tariff-sheet source, starting with PDF extraction for Air India/Akasa/SpiceJet | Backend | tariff URLs | not started | a / b |
| Week 2 | Cross-check Jevons/Laspeyres outputs on Kaggle panel and simulated data | Stats/Index | loader, cleaning | not started | c |
| Week 2 | Start crude daily collection/back-test clock even if adapters are imperfect | Everyone | resolver skeleton | not started | 30-day back-test |
| Week 3 | Build quote/index storage layer and exportable audit trail | Backend | cleaning + resolver | not started | b / d |
| Week 3 | Add FastAPI endpoints for route basket, quotes, elementary index, aggregate index, and source status | Backend | storage layer | not started | d |
| Week 3 | Build dashboard views: trend, route heatmap, provenance, data-quality flags | Frontend | API endpoints | not started | d |
| Week 4+ | Back-test against DGCA passenger/route data and document quoted-vs-realized fare differences | Stats/Index | 30-day collection | not started | 30-day back-test |
| Week 4+ | Finalize risk register, pitch reframe, two-minute brief, and demo fallback fixtures | Lead/Presenter | research refresh + working demo | not started | all |

## 3. Critical Path

Start these even before the rest of the system is polished:

| Critical item | Why it gates the project | Immediate action |
|---|---|---|
| TripJack/TBO outreach | Approval and commercial replies take wall-clock time. | Send outreach now; even a rejection is evidence for fallback design. |
| 30-day back-test | Cannot be compressed at the end. | Start crude collection as soon as resolver skeleton exists. |
| Kaggle historical panel | Lets the index/cleaning owners work before live data arrives. | Downloaded locally; build loader next. |
| Tariff-sheet parser | PDF formats vary and can break extraction. | Build one carrier parser early, then generalize. |
| DGCA weights | Route basket legitimacy depends on official traffic weighting. | Use `Vonter/india-aviation-traffic` May 2026 domestic city data immediately. |

## 4. Risk Register

| Risk | Impact | Probability | Mitigation | Owner |
|---|---:|---:|---|---|
| Late data start | High | High | Start crude collection/back-test before adapters are complete. | Backend |
| Scraper-and-dashboard-only trap | High | Medium | Keep Jevons/Laspeyres, DGCA weights, data-quality flags, and audit trail central. | Stats/Index |
| Anti-bot arms race | High | Medium | Prefer APIs, tariff sheets, cached fixtures, and polite scraping; treat blocks as data-quality flags. | Backend |
| API access unavailable or expensive | High | High | Start outreach; maintain tariff-sheet and simulated fallback; document provider constraints. | Lead/Backend |
| Kaggle raw data accidentally committed | Medium | Low | Keep `data/raw/` ignored and verify `git status` before commits. | Backend |
| CPI item-level air-travel weight unresolved | Medium | Medium | Assign explicit MoSPI PDF extraction task; do not guess in pitch. | Stats/Index |
| DGCA repo path drift | Medium | Low | Use current `aggregated/domestic/city.csv` path and pin commit/date in docs. | Stats/Index |
| Tariff sheets are PDFs with inconsistent layout | Medium | High | Build carrier-specific extractors with fixtures and parser tests. | Backend |
| Temporary fare-cap story becomes stale | Low | Medium | State exact dates: imposed 2025-12-06, reportedly lifted 2026-03-23. | Presenter |

## 5. Stand-Up Summary

**Done:** Core simulated source, FareSource/FareQuote contract, elementary Jevons index, aggregate Laspeyres index, tests on simulated 45-day panel, research refresh, GitHub planning structure.

**Blocked:** Exact CPI item-level air-travel weight needs direct MoSPI PDF extraction before final slides.

**Next 7 days:** load the EaseMyTrip panel, derive DGCA route weights, send TripJack/TBO outreach, implement resolver skeleton, and start the crude collection clock.

**Pitch focus:** “MoSPI already collects airfares online weekly; APIx scales that into daily automated collection with official-style index methodology and full provenance.”
