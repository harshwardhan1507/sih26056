# Kaggle Historical Panel Real-Data Loader (#7)

## Overview

This module implements real-data ingestion from the public Kaggle EaseMyTrip historical flight price dataset (`Clean_Dataset.csv` by Shubham Bathwal, 2022 panel). It normalizes raw scraped flight records into canonical APIx domain entities, maps booking lead times (`days_left`) into APIx statistical advance-purchase horizons ($T+1, T+7, T+15, T+30, T+45$), and exposes a `FareSource` adapter that feeds directly into the elementary price index calculation.

## Implemented Components

### 1. Normalization Engine (`apix.collector.adapters.kaggle`)

- **City & Route Normalization (`normalize_city`)**:
  - Maps 6 major Indian domestic metro cities to their official 3-letter IATA airport codes:
    - Delhi / New Delhi $\rightarrow$ `DEL`
    - Mumbai / Bombay $\rightarrow$ `BOM`
    - Bangalore / Bengaluru $\rightarrow$ `BLR`
    - Kolkata / Calcutta $\rightarrow$ `CCU`
    - Hyderabad $\rightarrow$ `HYD`
    - Chennai / Madras $\rightarrow$ `MAA`
  - Case-insensitive, strips trailing/leading whitespace, and handles pre-existing IATA codes.

- **Airline & Carrier Normalization (`normalize_airline`)**:
  - Maps domestic airline names and variants to canonical titles and 2-letter IATA codes:
    - IndiGo / Indigo $\rightarrow$ `6E`
    - Air India / Air_India $\rightarrow$ `AI`
    - Vistara $\rightarrow$ `UK`
    - SpiceJet $\rightarrow$ `SG`
    - AirAsia / AirAsia India / AIX Connect $\rightarrow$ `I5`
    - GO FIRST / GoAir / Go First $\rightarrow$ `G8`
    - Akasa Air $\rightarrow$ `QP`
    - Air India Express $\rightarrow$ `IX`

- **Class & Flight Number Normalization (`normalize_class`, `normalize_flight_number`)**:
  - Canonicalizes travel classes into `"Economy"`, `"Business"`, and `"Premium"`.
  - Normalizes flight number strings (e.g. `6E 2053` $\rightarrow$ `6E-2053`).

- **Advance Purchase Window Mapping (`map_days_left_to_window`)**:
  - Maps booking lead days (`days_left`) to APIx advance horizons ($1, 7, 15, 30, 45$):
    - `exact`: Retains observations strictly matching the 5 target windows ($1, 7, 15, 30, 45$).
    - `nearest`: Assigns each observation to the nearest window anchor.
    - `bucket`: Maps observations into statistical bins:
      - $[1, 3] \rightarrow T+1$
      - $[4, 10] \rightarrow T+7$
      - $[11, 22] \rightarrow T+15$
      - $[23, 37] \rightarrow T+30$
      - $[38, \infty) \rightarrow T+45$
  - Helper functions `window_to_tag` and `tag_to_window` provide conversions between integers and labels (`T+1`, `T+7`, etc.).

### 2. APIx Data Model Compatibility (`KaggleFlightRecord`)

- Dataclass encapsulating all raw and normalized attributes.
- Provides `.to_fare_quote(as_of_date=...)` producing canonical `FareQuote` instances:
  - `source_id = "kaggle_easemytrip_v1"`
  - `collection_method = "scrape"`
  - `quality_flag = "ok"`
- Provides `.to_row()` and `.to_dict()` serializations compatible with Appendix C schema.

### 3. Streaming Loader & FareSource Adapter

- **`KaggleDatasetLoader`**:
  - `stream_records()`: Memory-efficient line-by-line streaming using standard library `csv.DictReader` (~0 additional RAM overhead for 300k rows).
  - `load_records()`: Bulk loader with route and class filtering.
  - `to_daily_carrier_prices()`: Formats carrier prices grouped by flight date for direct consumption by `build_elementary_index()`.
- **`KaggleFareSource`**:
  - Implements `FareSource.get_quotes(origin, destination, as_of_date, advance_window_days, carriers) -> list[FareQuote]`.
  - Indexes quotes in-memory for instant lookup.

## Verification

### Automated Tests
Run unit tests with Python standard library:
```powershell
python tests/test_kaggle_loader.py
python tests/test_index.py
```

### Test Coverage
- `test_normalize_airline`: Validates all 6 carriers, aliases, and error rejection on invalid airlines.
- `test_normalize_city`: Validates all 6 cities, aliases, and error rejection on invalid cities.
- `test_normalize_class`: Validates economy, business, and premium variations.
- `test_normalize_flight_number`: Validates spacing and carrier code prefixing.
- `test_map_days_left_exact`, `test_map_days_left_nearest`, `test_map_days_left_bucket`: Validates mapping logic and boundary behavior.
- `test_window_tags`: Validates conversions between `int` and `T+` tags.
- `test_load_records_exact_strategy`, `test_load_records_nearest_and_bucket`: Validates CSV loading and strategy differences.
- `test_stream_filter_by_class_and_route`: Validates filtered streaming.
- `test_to_fare_quote_conversion`: Validates `FareQuote` generation.
- `test_kaggle_fare_source_get_quotes`: Validates integration with `FareSource` contract.
- `test_kaggle_daily_prices_to_elementary_index`: Validates integration with Jevons index formula.
- `test_corrupted_rows_handling`: Validates resilience against malformed rows.
