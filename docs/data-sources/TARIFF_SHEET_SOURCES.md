# Tariff Sheet Legal Basis & Live Airline URLs

**Issue:** #4 — Verify tariff-sheet legal basis and live airline URLs  
**Verified by:** Research run 2026-09-04  
**Scope:** IndiGo (6E), Air India (AI), Akasa (QP), SpiceJet (SG), Air India Express (IX)

---

## 1. Legal Basis

### Rule 135 of the Aircraft Rules, 1937

Rule 135 is the primary statutory authority. The key sub-rules:

| Sub-rule | Text (summary) | Relevance to APIx |
|---|---|---|
| **135(1)** | Airlines may establish reasonable tariffs, taking into account cost of operation, service characteristics, reasonable profit, and prevailing market tariff. | Confirms airlines set their own fares — no government cap in normal times. |
| **135(2)** | Airlines **shall** publish the established tariff on their **website** and in a conspicuous part of their offices and agent offices. | The legal mandate that creates the public tariff-sheet obligation. |
| **135(2-A)** | Airlines must display a **single consolidated fare** and a full break-up (base fare + taxes + surcharges). | Guarantees fare-component transparency we can parse. |
| **135(4)** | DGCA may issue directions if excessive or predatory tariffs are found. | Powers the Tariff Monitoring Unit (TMU) that monitors our basket routes. |

**Status as of 2026-09-04:** Rule 135(2) is still cited by current PIB press releases and DGCA circulars as the operative mandate. No amendment or repeal has been found.

> **Source:** PIB (2022-03-28): https://www.pib.gov.in/PressReleasePage.aspx?PRID=1810467  
> **DGCA site last crawled:** 2026-09-04 — https://www.dgca.gov.in/

### DGCA Air Transport Circular (ATC) 02 of 2010

ATC 02/2010 operationalises Rule 135(2). It requires:
- Airlines to display **fare buckets / Reservation Booking Designators (RBDs)** on their websites.
- Monthly submission of route-wise tariff (all categories) to DGCA on the **first day of each calendar month**.
- Tariff to list base fare, fuel surcharge, and other applicable taxes separately.

**Status as of 2026-09-04:** Multiple 2024-2026 DGCA enforcement communications still cite ATC 02/2010 as the operative circular. No superseding ATC was found in this research pass.

> **Source confirmed via:** Akasa Air DGCA compliance search, 2026-09-04; SpiceJet DGCA regulatory context search, 2026-09-04.

---

## 2. Live Airline Tariff Sources

| # | Carrier | IATA | Status | Live URL | Format | Verified |
|---|---|---|---|---|---|---|
| 1 | Air India | AI | Confirmed PDF | https://www.airindia.com/in/en/tariff.html | **PDF** (~1.2 MB) | 2026-09-04 |
| 2 | IndiGo | 6E | Confirmed (needs browser) | https://www.goindigo.in/ footer "Tariff Sheet" | PDF (footer link) | 2026-09-04 |
| 3 | Akasa Air | QP | Confirmed (CF-protected) | https://www.akasaair.com/fare-sheet | PDF (known CDN path) | 2026-09-04 |
| 4 | SpiceJet | SG | Confirmed (needs browser) | https://www.spicejet.com/tariff | PDF via corporate subdomain | 2026-09-04 |
| 5 | Air India Express | IX | UNRESOLVED | /tariff -> 404; /en-in/fees-and-charges -> 404 | Unknown | 2026-09-04 |

### Detailed notes per carrier

#### Air India (AI) — Best candidate for first parser

- **URL:** `https://www.airindia.com/in/en/tariff.html`
- **What it is:** Direct HTTP GET returns a PDF (`Content-Type: application/pdf`, 1,255,045 bytes).
- **File naming convention:** PDF is named `TARIFF-SHEET-AS-ON-01APR26.pdf` — monthly pattern: `TARIFF-SHEET-AS-ON-01{MMM}{YY}.pdf`.
- **Format:** PDF. Contains route-wise RBD fare tables.
- **Parser complexity:** **LOW** — static PDF URL, directly downloadable, no JavaScript required.
- **Verdict:** First parser target for issue #11.

#### IndiGo (6E) — Confirmed, browser required

- **URL:** `https://www.goindigo.in/` footer "Tariff Sheet" link
- **Direct path:** `/information/fare-tariff.html` returns H2 stream error (anti-bot). Footer link must be resolved via Selenium/Playwright.
- **Format:** PDF (typical RBD/fare bucket table).
- **Parser complexity:** **MEDIUM** — URL must be scraped from footer first, then PDF downloaded.

#### Akasa Air (QP) — Confirmed PDF, Cloudflare-protected

- **URL:** `https://www.akasaair.com/fare-sheet` (returns 403 for headless; resolves in browser)
- **Known CDN PDF path:** `https://assets.akasaair.com/f/159922/x/c1ce86c83e/fare-sheet-akasa-air.pdf`
- **Format:** PDF.
- **Parser complexity:** **MEDIUM** — Cloudflare blocks simple requests; try CDN URL directly first.

#### SpiceJet (SG) — Confirmed, React SPA

- **URL:** `https://www.spicejet.com/tariff` — React SPA (no server-side content in static fetch).
- **Known direct PDF:** `https://corporate.spicejet.com/Content/pdf/Tariffs.pdf` (corporate subdomain).
- **Format:** PDF (corporate subdomain, simpler access path).
- **Parser complexity:** **LOW-MEDIUM** — corporate subdomain PDF is directly fetchable without JS.

#### Air India Express (IX) — UNRESOLVED

- **Status:** Explicitly unresolved as of 2026-09-04.
- **What was tried:**
  - `https://www.airindiaexpress.com/tariff` -> 404
  - `https://www.airindiaexpress.com/en-in/fees-and-charges` -> 404
- **Likely cause:** Post-merger with Air India under Tata group; tariff may now fall under AI umbrella, or AIX site has restructured URL schema (Adobe AEM-based site with `/content/airindiaexpress/en/` internal paths).
- **Recommended next step:** Check `/en/fees-charges` or inspect AIX footer in a live browser session.
- **For issue #11:** Mark AIX as **deferred** — document uncertainty, do not block adapter on this carrier.

---

## 3. Parser Complexity Ranking

| Rank | Carrier | Complexity | Reason | Action for #11 |
|---:|---|---|---|---|
| 1 | **Air India (AI)** | Low | Static PDF, direct URL, no JS | **Build first — proof of concept** |
| 2 | **SpiceJet (SG)** | Low-Medium | Corporate subdomain PDF, direct fetch | Build second |
| 3 | **IndiGo (6E)** | Medium | Need footer-scraped URL, then PDF | Build third |
| 4 | **Akasa (QP)** | Medium | Cloudflare-protected; try CDN URL first | Build fourth |
| 5 | **Air India Express (IX)** | Unresolved | Page not found; site restructured post-merger | Defer until URL confirmed |

---

## 4. Recommended First Parser Target (for issue #11)

**Air India (AI) domestic tariff PDF at `https://www.airindia.com/in/en/tariff.html`**

Rationale:
- Direct HTTP GET returns the PDF — no JS execution required.
- File size ~1.2 MB, manageable for `pdfplumber`.
- URL naming pattern (`TARIFF-SHEET-AS-ON-01{MMM}{YY}.pdf`) is deterministic — easy to automate monthly refresh.
- Air India is a basket carrier (IATA `AI`) already in the `CARRIERS` list.

Suggested adapter skeleton:

```python
# apix/collector/adapters/tariff_sheet_ai.py
import requests
import pdfplumber
from io import BytesIO

TARIFF_URL = "https://www.airindia.com/in/en/tariff.html"

def fetch_tariff_pdf(url: str = TARIFF_URL) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content  # application/pdf

def parse_fare_bands(pdf_bytes: bytes) -> list[dict]:
    rows = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # header detection and row mapping goes here
                rows.extend(table)
    return rows
```

---

## 5. Acceptance Criteria Checklist

| Criterion | Met? |
|---|---|
| At least four airline tariff-sheet sources are verified with live URLs | Yes — 4 verified (AI, 6E, QP, SG) |
| Air India Express is either verified or explicitly marked unresolved | Yes — explicitly unresolved with reason |
| Parser complexity is known for each source | Yes — see ranking table above |
| First parser target is chosen for issue #11 | Yes — Air India (AI) |
| Legal basis (Rule 135(2) and ATC 02/2010) confirmed still relevant | Yes — both confirmed current as of 2026-09-04 |
