# MoSPI CPI 2024=100 Airfare Methodology & Item Weight Verification

**Document Status:** Verified & Documented  
**Checked Date:** 2026-09-04  
**Primary Source 1:** MoSPI Official Annexure V — *Frequently Asked Questions (FAQs) on CPI 2024 Series* ([Official PDF](https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf))  
**Primary Source 2:** PIB Delhi Press Release ([PRID 2243779](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2243779&lang=1&reg=3), posted 2026-03-23)  
**Portal Sources:** [e-Sankhyiki Data Portal](https://esankhyiki.mospi.gov.in/), [MoSPI API Portal](https://api.mospi.gov.in/), [mospi-esankhyiki Python Library (PyPI)](https://pypi.org/project/mospi-esankhyiki/)

---

## 1. Executive Summary & Pitch Significance

> [!IMPORTANT]
> **Why this matters for the SIH26056 pitch:**  
> The traditional problem statement assumes airfare price collection is entirely manual, disconnected, or unmonitored. In reality, **MoSPI has already formally integrated online weekly airfare collection** into the CPI 2024=100 base revision.  
> **APIx's value proposition is scaling this existing MoSPI institutional workflow**: transitioning from manual/weekly snapshot polling by regional FOD offices to an automated, daily high-frequency index engine using Jevons elementary aggregation and Laspeyres higher-level aggregation with DGCA passenger route weighting.

---

## 2. Exact Quotes & Methodology References

### A. MoSPI Annexure V FAQ (CPI 2024 Series)
*Source: `https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf` (7-page official FAQ)*

1. **Airfare Online Platform Collection (Question 14 & Question 27):**
   - **Q14 (Page 2, Line 79-82):**  
     > *"Have online markets been included in the CPI 2024 series?"*  
     > **Ans:** *"Twelve online markets have been added across 12 towns with a population of more than 25 lakh to capture price variations of items sold on e-commerce and online platforms. In addition, price collection for airfare, telephone and OTT are also collected through online platforms."*
   - **Q27 (Page 3, Line 122-124):**  
     > *"How the prices for airfares are collected in the CPI 2024 series?"*  
     > **Ans:** *"Airfares are collected through well-known online platforms."*

2. **Collection Frequency (Question 8):**
   - **Q8 (Page 1, Line 42-44):**  
     > *"How often is price data collected for CPI?"*  
     > **Ans:** *"Price data are collected monthly from rural and urban markets. Online prices are collected on weekly basis."*

3. **Field Operations Division (FOD) Role (Question 16):**
   - **Q16 (Page 2, Line 86-87):**  
     > *"Which organization collects CPI price data for MoSPI?"*  
     > **Ans:** *"Field Operations Division of National Sample Survey (NSS), MoSPI collects monthly price data for CPI."*

4. **Index Compilation Formula (Questions 20 & 21):**
   - **Q20 (Page 3, Line 101-102):**  
     > *"Which method is used for elementary index compilation in the CPI 2024 series?"*  
     > **Ans:** *"The Jevons index (Short index formula) is used for compiling elementary indices in the CPI 2024 series."*
   - **Q21 (Page 3, Line 103-104):**  
     > *"Which method is used for higher level index compilation in the CPI 2024 series?"*  
     > **Ans:** *"The Young/Modified Laspeyres’ index is used for compiling higher level indices in the CPI 2024 series."*

5. **COICOP 2018 Classification Hierarchy (Question 19):**
   - **Q19 (Page 3, Line 99-100):**  
     > *"What is the hierarchical structure of CPI 2024 after adopting COICOP 2018?"*  
     > **Ans:** *"CPI 2024 has 12 Divisions, 43 Groups, 92 Classes, and 162 Sub-classes as per COICOP 2018."*

---

### B. PIB Press Release (PRID 2243779, 2026-03-23)
*Source: `https://www.pib.gov.in/PressReleasePage.aspx?PRID=2243779&lang=1&reg=3` (Rajya Sabha unstarred/starred reply by MoS Rao Inderjit Singh)*

> *"The Ministry of Statistics & Programme Implementation (MoSPI) has strengthened the measurement framework of the Consumer Price Index (CPI) through a comprehensive base revision from 2012=100 to 2024=100, using the latest Household Consumption Expenditure Survey (HCES) 2023–24 to update the CPI item basket and weights."*
>
> *"The prices of items are collected through online/e-commerce platforms on weekly basis. All items of CPI baskets are mapped with the corresponding most popular e-commerce platform for price collection by the respective regional offices of Field Operations Division (FOD) of MoSPI. Keeping in view the volatility of prices on e-commerce platforms, prices are collected in all four weeks on identified days and time slot. A monthly average price using these weekly transaction price observations are used in CPI compilation."*

---

## 3. CPI 2024 Division & Group Weights (Transport)

From Annexure V, Question 39:

### Division-Wise Weights (COICOP 2018 Framework — CPI 2024 Structure)
| Division | Rural (2012) | Rural (2024) | Urban (2012) | Urban (2024) | Combined (2012) | Combined (2024) |
|---|---|---|---|---|---|---|
| **Transport** | **5.645%** | **8.644%** | **7.129%** | **8.985%** | **6.394%** | **8.796%** |
| *Food and beverages* | 50.922% | 41.983% | 32.811% | 30.251% | 42.617% | 36.753% |
| *Housing, water, electricity, gas & fuels* | 7.983% | 11.764% | 27.294% | 25.000% | 16.888% | 17.665% |
| *Health* | 6.839% | 6.764% | 4.820% | 5.275% | 5.900% | 6.100% |
| *Information & communication* | 2.818% | 3.647% | 3.906% | 3.563% | 3.323% | 3.609% |
| *Education Services* | 2.468% | 2.383% | 4.720% | 4.515% | 3.513% | 3.333% |

> [!NOTE]
> **Transport weight surge:** The Combined weight of the **Transport Division** increased significantly from **6.394%** (in 2012 series) to **8.796%** (in 2024 series), reflecting higher mobility expenditure in HCES 2023-24.

---

## 4. Item-Level Airfare Weight Status

> [!WARNING]
> **Status: UNRESOLVED AT ITEM LEVEL (Documented via Official PDFs)**
> 
> - **Findings from Annexure V:** Annexure V publishes Division-level and Group-level weights (e.g., Division 07 Transport = 8.796% Combined), but does **not** include the granular 358 individual item-level weights table in its 7 pages.
> - **Guidance in Annexure V (Q12):** States that full item-wise weights are published on `cpi.mospi.gov.in` under the announcements tab.
> - **Pitch Guidance:** State clearly:
>   - **Transport Division weight (Combined):** `8.796%` (CPI 2024=100) vs `6.394%` (CPI 2012=100).
>   - **Airfare item-level weight:** Contained within Division 07 (Transport) -> Passenger Transport by Air under COICOP class 07.3.3. Exact item decimal is not released in the FAQ summary PDF; APIx utilizes DGCA passenger seat-kilometer / OD traffic matrix (`aggregated/domestic/city.csv`) for route-level Laspeyres basket weighting.

---

## 5. Portal & Package Verification (Checked 2026-09-04)

| Endpoint / Artifact | URL | Status | Verified Version / Details |
|---|---|---|---|
| **e-Sankhyiki Data Platform** | `https://esankhyiki.mospi.gov.in` | **200 OK** (Live) | Primary dissemination platform for CPI 2024 (`/macroindicators?product=cpi`). |
| **MoSPI API Gateway** | `https://api.mospi.gov.in` | **200 OK** (Live) | Nginx reverse proxy serving React + Swagger UI (`swagger-ui/3.24.2`) for official data APIs. Note: Python urllib fails due to legacy renegotiation SSL handshake; works via standard modern TLS/curl. |
| **MoSPI Python Library Guide** | `https://www.mospi.gov.in/esankhyiki-python-library` | **200 OK** (Live) | Official MoSPI documentation for `mospi-esankhyiki`. |
| **PyPI Package (`mospi-esankhyiki`)** | `https://pypi.org/project/mospi-esankhyiki/` | **Live** | Version `0.1.4` (releases `0.1.0` through `0.1.4` confirmed via PyPI JSON API). Summary: *"Python client for India's National Statistical Office (NSO/MoSPI) data portal"*. |
| **CPI Dedicated Portal** | `https://www.cpi.mospi.gov.in` | Intermittent | Cited in Annexure V Q12 for granular announcements. |

---

## 6. Synthesis for APIx Architecture & Pitch

1. **Methodological Harmony with MoSPI:**
   - MoSPI explicitly adopted **Jevons index** for elementary aggregation (Question 20) and **Modified Laspeyres index** for higher levels (Question 21).
   - APIx implements identical mathematical foundations: `Jevons` at elementary flight route-class level and `Laspeyres` across nationwide passenger volumes.
2. **Operational Scaling:**
   - MoSPI FOD conducts **weekly** manual/semi-automated collection across 12 major urban online markets.
   - APIx executes **daily automated resolution** across 12 top domestic routes, providing real-time high-frequency visibility into dynamic fare shifts.
