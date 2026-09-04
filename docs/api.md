# APIx HTTP Data Service API Documentation

**Service:** APIx Data Delivery Layer  
**Base URL:** `http://127.0.0.1:8000`  
**OpenAPI / Interactive Swagger UI:** `http://127.0.0.1:8000/docs`  
**ReDoc UI:** `http://127.0.0.1:8000/redoc`

The APIx API is a read-only HTTP service designed for frontend dashboards, statistical researchers, and regulatory consumers (such as MoSPI and the RBI). It serves data from validated backend artifacts with graceful degradation and uniform error formatting.

> **The OpenAPI spec at `/docs` is authoritative.** It is generated from the
> Pydantic response models, so it cannot drift. This document is a narrative
> companion; where the two disagree, believe `/docs`.

### Dataset selection & provenance

The service serves the **live collection log**
(`data/raw/live_collection/fare_quote_log.csv`) when one exists, and falls back
to the simulated demo artifact (`apix/data/fare_quote.csv`) otherwise.

Every data-bearing response carries a `provenance` block so a consumer never has
to guess what it received:

```json
{
  "dataset_type": "mixed",
  "source_file": "fare_quote_log.csv",
  "is_live_collection": true,
  "total_quotes": 300,
  "observed_quotes": 180,
  "simulated_quotes": 120,
  "simulated_percentage": 40.0,
  "note": "Serving the live collection log."
}
```

`dataset_type` is `production` (no simulated rows), `mixed` (some), or
`synthetic` (all). A real collection run is typically `mixed`: tariff sheets
cover the carriers that publish them, and the simulator fills the rest.

### Time axis

Date filters and index series use the **observation date** — the day a fare was
seen, equal to `departure_date - advance_window_days`. Filtering on departure
date mixes advance windows: a T+1 and a T+45 quote observed on the same day
depart 44 days apart.

---

## 1. Uniform Error Response Schema

Every error condition across all endpoints returns a consistent JSON payload:

```json
{
  "error": "data_unavailable",
  "detail": "Required data file 'fare_quote.csv' is not available."
}
```

| HTTP Status Code | Meaning | Typical Error Code |
|---|---|---|
| `200 OK` | Request succeeded | N/A |
| `400 Bad Request` | Invalid query parameter value | `invalid_parameter` |
| `404 Not Found` | Route or endpoint not found | `not_found` |
| `422 Unprocessable Entity` | Pydantic validation failure (e.g. missing required param) | `validation_error` |
| `503 Service Unavailable` | Backing data file (`fare_quote.csv`, `index_series.csv`) is missing | `data_unavailable` |

---

## 2. Endpoints Reference

### `GET /health`
Liveness probe returning current server health, API version, and UTC timestamp. Never fails due to missing data.

**Example Response (`200 OK`):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp_utc": "2026-09-04T12:09:31.625486Z"
}
```

---

### `GET /routes`
Returns the 12-route Indian domestic airfare basket along with Laspeyres passenger traffic expenditure weights and DGCA source attribution. If `route_weights.json` is absent, it returns `200 OK` with `"source": "placeholder"` and baseline weights so frontend development is never blocked.

**Example Response (`200 OK`):**
```json
{
  "source": "Vonter/india-aviation-traffic (https://github.com/Vonter/india-aviation-traffic), licensed ODbL-1.0. Data sourced from DGCA.",
  "coverage_month": "2026-05",
  "generated_date": "2026-09-04",
  "total_basket_pax": 49572263,
  "routes": [
    {
      "route_id": "DEL-BOM",
      "origin": "DEL",
      "destination": "BOM",
      "weight": 0.192173
    },
    {
      "route_id": "DEL-BLR",
      "origin": "DEL",
      "destination": "BLR",
      "weight": 0.135988
    },
    {
      "route_id": "BOM-BLR",
      "origin": "BOM",
      "destination": "BLR",
      "weight": 0.115589
    },
    {
      "route_id": "DEL-HYD",
      "origin": "DEL",
      "destination": "HYD",
      "weight": 0.089441
    },
    {
      "route_id": "DEL-CCU",
      "origin": "DEL",
      "destination": "CCU",
      "weight": 0.081759
    },
    {
      "route_id": "BLR-HYD",
      "origin": "BLR",
      "destination": "HYD",
      "weight": 0.066028
    },
    {
      "route_id": "BOM-CCU",
      "origin": "BOM",
      "destination": "CCU",
      "weight": 0.065517
    },
    {
      "route_id": "DEL-MAA",
      "origin": "DEL",
      "destination": "MAA",
      "weight": 0.065382
    },
    {
      "route_id": "BOM-MAA",
      "origin": "BOM",
      "destination": "MAA",
      "weight": 0.061301
    },
    {
      "route_id": "DEL-GOI",
      "origin": "DEL",
      "destination": "GOI",
      "weight": 0.044817
    },
    {
      "route_id": "BLR-MAA",
      "origin": "BLR",
      "destination": "MAA",
      "weight": 0.042599
    },
    {
      "route_id": "BOM-GOI",
      "origin": "BOM",
      "destination": "GOI",
      "weight": 0.039407
    }
  ]
}
```

---

### `GET /quotes`
Returns collected fare quotes from `fare_quote.csv`. All query filters are optional and combined using logical AND.

**Query Parameters:**
- `origin` (string, optional): Filter by 3-letter origin IATA code (e.g. `DEL`).
- `destination` (string, optional): Filter by 3-letter destination IATA code (e.g. `BOM`).
- `advance_window_days` (int, optional): Filter by advance purchase horizon (`1`, `7`, `15`, `30`, `45`).
- `date_from` (date, optional): Minimum **observation** date (`YYYY-MM-DD`).
- `date_to` (date, optional): Maximum **observation** date (`YYYY-MM-DD`).
- `limit` (int, optional): Maximum quotes to return. `total_matched` reports the unlimited count.

**Example Request:**
```bash
curl "http://127.0.0.1:8000/quotes?origin=DEL&destination=BOM&advance_window_days=7&date_from=2026-01-01&date_to=2026-01-01"
```

**Example Response (`200 OK`):**
```json
{
  "count": 5,
  "quotes": [
    {
      "collected_at_utc": "2026-09-04T11:00:05.581656Z",
      "departure_date": "2026-01-01",
      "advance_window_days": 7,
      "origin_iata": "DEL",
      "destination_iata": "BOM",
      "carrier_iata": "6E",
      "fare_class": "Economy",
      "total_fare_inr": 6225.03,
      "source_id": "simulated_v1",
      "collection_method": "simulated",
      "quality_flag": "ok"
    },
    {
      "collected_at_utc": "2026-09-04T11:00:05.581678Z",
      "departure_date": "2026-01-01",
      "advance_window_days": 7,
      "origin_iata": "DEL",
      "destination_iata": "BOM",
      "carrier_iata": "AI",
      "fare_class": "Economy",
      "total_fare_inr": 7009.51,
      "source_id": "simulated_v1",
      "collection_method": "simulated",
      "quality_flag": "ok"
    },
    {
      "collected_at_utc": "2026-09-04T11:00:05.581691Z",
      "departure_date": "2026-01-01",
      "advance_window_days": 7,
      "origin_iata": "DEL",
      "destination_iata": "BOM",
      "carrier_iata": "QP",
      "fare_class": "Economy",
      "total_fare_inr": 6482.02,
      "source_id": "simulated_v1",
      "collection_method": "simulated",
      "quality_flag": "ok"
    },
    {
      "collected_at_utc": "2026-09-04T11:00:05.581702Z",
      "departure_date": "2026-01-01",
      "advance_window_days": 7,
      "origin_iata": "DEL",
      "destination_iata": "BOM",
      "carrier_iata": "SG",
      "fare_class": "Economy",
      "total_fare_inr": 5866.76,
      "source_id": "simulated_v1",
      "collection_method": "simulated",
      "quality_flag": "ok"
    },
    {
      "collected_at_utc": "2026-09-04T11:00:05.581712Z",
      "departure_date": "2026-01-01",
      "advance_window_days": 7,
      "origin_iata": "DEL",
      "destination_iata": "BOM",
      "carrier_iata": "IX",
      "fare_class": "Economy",
      "total_fare_inr": 5510.0,
      "source_id": "simulated_v1",
      "collection_method": "simulated",
      "quality_flag": "ok"
    }
  ]
}
```

---

### `GET /index/aggregate`
Returns the headline APIx aggregate airfare price index series. Base value is 100.0 at day 0.

Aggregation is a **fixed-base Laspeyres**, not a daily chain — the response's
`methodology` field states which. A daily-chained index of noisy prices is
upward-biased by `exp(sigma^2)` per link and manufactures inflation that is not
there; see [METHODOLOGY_CHAIN_DRIFT.md](METHODOLOGY_CHAIN_DRIFT.md).

Each point carries its calendar `date` and `change_pct` alongside the day index.

**Example Response (`200 OK`):**
```json
{
  "base_value": 100.0,
  "series_length": 45,
  "series": [
    {
      "day": 0,
      "index_value": 100.0
    },
    {
      "day": 1,
      "index_value": 109.625
    },
    {
      "day": 2,
      "index_value": 110.237
    },
    {
      "day": 3,
      "index_value": 111.764
    },
    {
      "day": 4,
      "index_value": 102.495
    }
  ]
}
```

---

### `GET /index/elementary`
Calculates and returns the per-(route, window) chained Jevons elementary index dynamically from `fare_quote.csv` using matched-sample geometric relatives.

**Query Parameters:**
- `origin` (string, required): 3-letter IATA code, e.g. `DEL`.
- `destination` (string, required): 3-letter IATA code, e.g. `BOM`.
- `advance_window_days` (int, required): Advance window, e.g. `7`.
- `date_from` (date, optional): Start date filter (`YYYY-MM-DD`).
- `date_to` (date, optional): End date filter (`YYYY-MM-DD`).

**Example Request:**
```bash
curl "http://127.0.0.1:8000/index/elementary?origin=DEL&destination=BOM&advance_window_days=7"
```

**Example Response (`200 OK`):**
```json
{
  "origin": "DEL",
  "destination": "BOM",
  "advance_window_days": 7,
  "base_value": 100.0,
  "series_length": 45,
  "series": [
    {
      "day": 0,
      "index_value": 100.0,
      "carrier_count": 5
    },
    {
      "day": 1,
      "index_value": 104.864,
      "carrier_count": 5
    },
    {
      "day": 2,
      "index_value": 108.974,
      "carrier_count": 5
    }
  ]
}
```

---

### `GET /routes/summary`
Computes each basket route's current index level, day-over-day change, latest
average observed fare, matched observation count and a down-sampled sparkline —
all derived from the served dataset.

Routes with no observations return `null` values and
`coverage_status: "insufficient"`. Nothing is filled in with a placeholder.

**Example Response (`200 OK`):**
```json
{
  "count": 12,
  "provenance": { "dataset_type": "mixed", "...": "..." },
  "routes": [
    {
      "route_id": "DEL-BOM",
      "origin": "DEL",
      "destination": "BOM",
      "weight": 0.192173,
      "current_index": 100.0,
      "change_pct": null,
      "average_fare": 7661.0,
      "matched_observations": 24,
      "coverage_status": "insufficient",
      "series_length": 1,
      "sparkline": [100.0]
    }
  ]
}
```

---

### `GET /sources/status`
Counts quotes by collection method (`api`, `tariff_sheet`, `scrape`,
`historical_panel`, `simulated`, `imputed`) **and by the adapter that produced
them**, plus the current reliance on simulated fallback. Returns `200 OK` with
zero counts when no data exists.

Only source identifiers that actually contributed rows appear. A source with no
integration is absent, never reported as healthy.

**Example Response (`200 OK`):**
```json
{
  "total_quotes": 300,
  "by_method": {
    "tariff_sheet": 180,
    "simulated": 120
  },
  "by_source_id": {
    "indigo_tariff_v1": 60,
    "air_india_tariff_v1": 60,
    "akasa_tariff_v1": 60,
    "simulated_v1": 120
  },
  "fallback_simulated_percentage": 40.0,
  "provenance": { "dataset_type": "mixed", "...": "..." },
  "status_note": "Counted from fare_quote_log.csv. ..."
}
```

---

### `GET /quality`
Returns data hygiene audit metrics across collected observations (`ok`, `sold_out`, `outlier`, `imputed`). Returns `200 OK` with zero counts if `fare_quote.csv` is absent.

**Example Response (`200 OK`):**
```json
{
  "total_quotes": 13500,
  "by_quality_flag": {
    "ok": 12989,
    "sold_out": 380,
    "outlier": 131
  },
  "ok_count": 12989,
  "sold_out_count": 380,
  "outlier_count": 131,
  "imputed_count": 0
}
```

---

## 3. Running the Server Locally

Start the local development server using `uvicorn`:

```powershell
py -m uvicorn apix.api.main:app --reload --port 8000
```

Once running, interactive documentation is accessible at:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
