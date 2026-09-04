"""
Schema validation and hygiene checks for APIx fare quotes.

Enforces CPI domain constraints:
  - Strict mandatory field validation and type casting
  - 3-letter IATA codes for origin and destination (origin != destination)
  - 2-letter uppercase IATA codes for carriers
  - Standard advance purchase windows (1, 7, 15, 30, 45)
  - The Golden CPI Rule:
      * If quality_flag == "sold_out", total_fare_inr must be None.
      * If total_fare_inr is None, quality_flag must be "sold_out".
      * If total_fare_inr is numeric, it must be strictly positive (> 0.0).
        Zero or negative fares are invalid corruption artifacts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from apix.collector.adapters.base import FareQuote

VALID_COLLECTION_METHODS: Set[str] = {
    "api",
    "tariff_sheet",
    "scrape",
    "simulated",
    "imputed",
}

VALID_QUALITY_FLAGS: Set[str] = {
    "ok",
    "outlier",
    "sold_out",
    "imputed",
}

VALID_FARE_CLASSES: Set[str] = {
    "Economy",
    "Business",
    "Premium",
}

VALID_ADVANCE_WINDOWS: Set[int] = {1, 7, 15, 30, 45}

IATA_AIRPORT_REGEX = re.compile(r"^[A-Z]{3}$")
IATA_CARRIER_REGEX = re.compile(r"^[A-Z0-9]{2}$")


@dataclass
class ValidationResult:
    """Outcome of validating a single fare quote."""
    is_valid: bool
    errors: List[str]
    quote: Optional[FareQuote] = None


def normalize_fare_class(fare_class: str) -> str:
    """Normalize fare class string to canonical title case."""
    cleaned = fare_class.strip().lower()
    if "bus" in cleaned:
        return "Business"
    if "prem" in cleaned:
        return "Premium"
    return "Economy"


def validate_fare_quote(quote: FareQuote, strict_windows: bool = False) -> ValidationResult:
    """
    Validate an existing FareQuote dataclass instance against CPI domain constraints.

    Args:
        quote: FareQuote instance to validate.
        strict_windows: If True, requires advance_window_days in {1, 7, 15, 30, 45}.
                        If False, accepts any positive integer.

    Returns:
        ValidationResult with validation status and list of error messages.
    """
    errors: List[str] = []

    # 1. Airport IATA checks
    origin = quote.origin_iata.strip().upper() if quote.origin_iata else ""
    destination = quote.destination_iata.strip().upper() if quote.destination_iata else ""

    if not IATA_AIRPORT_REGEX.match(origin):
        errors.append(f"Invalid origin_iata: '{quote.origin_iata}' (must be 3 uppercase letters)")
    if not IATA_AIRPORT_REGEX.match(destination):
        errors.append(f"Invalid destination_iata: '{quote.destination_iata}' (must be 3 uppercase letters)")
    if origin and destination and origin == destination:
        errors.append(f"Origin and destination cannot be identical: '{origin}' -> '{destination}'")

    # 2. Carrier IATA checks
    carrier = quote.carrier_iata.strip().upper() if quote.carrier_iata else ""
    if not IATA_CARRIER_REGEX.match(carrier):
        errors.append(f"Invalid carrier_iata: '{quote.carrier_iata}' (must be 2 alphanumeric characters)")

    # 3. Advance window checks
    if quote.advance_window_days is None or quote.advance_window_days <= 0:
        errors.append(f"Invalid advance_window_days: {quote.advance_window_days} (must be > 0)")
    elif strict_windows and quote.advance_window_days not in VALID_ADVANCE_WINDOWS:
        errors.append(
            f"advance_window_days {quote.advance_window_days} not in standard set {VALID_ADVANCE_WINDOWS}"
        )

    # 4. Class and Metadata checks
    norm_class = normalize_fare_class(quote.fare_class) if quote.fare_class else ""
    if norm_class not in VALID_FARE_CLASSES:
        errors.append(f"Invalid fare_class: '{quote.fare_class}'")

    if quote.collection_method not in VALID_COLLECTION_METHODS:
        errors.append(
            f"Invalid collection_method: '{quote.collection_method}' (expected one of {VALID_COLLECTION_METHODS})"
        )

    if quote.quality_flag not in VALID_QUALITY_FLAGS:
        errors.append(
            f"Invalid quality_flag: '{quote.quality_flag}' (expected one of {VALID_QUALITY_FLAGS})"
        )

    # 5. Price & Sold-Out CPI Consistency Constraints
    fare = quote.total_fare_inr

    if quote.quality_flag == "sold_out":
        if fare is not None:
            errors.append(
                f"Sold-out flight must have total_fare_inr=None, found {fare}"
            )
    else:
        if fare is None:
            errors.append(
                f"Missing total_fare_inr must have quality_flag='sold_out', found '{quote.quality_flag}'"
            )
        elif fare <= 0.0:
            errors.append(
                f"Invalid total_fare_inr: {fare} (fares must be strictly positive > 0.0)"
            )

    # 6. Date Consistency
    if quote.collected_at_utc and quote.departure_date:
        col_date = quote.collected_at_utc.date()
        if quote.departure_date < col_date:
            errors.append(
                f"Departure date {quote.departure_date} is before collection date {col_date}"
            )

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, quote=quote if is_valid else None)


def clean_quote_dict(
    raw: Dict[str, Any],
    strict_windows: bool = False,
    auto_repair_sold_out: bool = True,
) -> Tuple[Optional[FareQuote], List[str]]:
    """
    Parse, coerce, and validate a dictionary row into a canonical FareQuote.

    Args:
        raw: Dictionary containing quote attributes (e.g. from CSV or JSON).
        strict_windows: Whether to enforce {1, 7, 15, 30, 45} strictly.
        auto_repair_sold_out: If True, automatically reconciles minor inconsistencies
                              (e.g., None fare becomes quality_flag='sold_out').

    Returns:
        (FareQuote or None, list of validation errors).
    """
    errors: List[str] = []

    try:
        # Parse timestamp
        raw_col = raw.get("collected_at_utc")
        if isinstance(raw_col, datetime):
            collected_at_utc = raw_col
        elif isinstance(raw_col, str) and raw_col.strip():
            collected_at_utc = datetime.fromisoformat(raw_col.strip())
        else:
            collected_at_utc = datetime.now(timezone.utc)

        # Parse departure date
        raw_dep = raw.get("departure_date")
        if isinstance(raw_dep, date):
            departure_date = raw_dep
        elif isinstance(raw_dep, str) and raw_dep.strip():
            departure_date = date.fromisoformat(raw_dep.strip())
        else:
            errors.append("Missing required field: departure_date")
            return None, errors

        # Parse advance window days
        raw_win = raw.get("advance_window_days")
        try:
            advance_window_days = int(raw_win)
        except (ValueError, TypeError):
            errors.append(f"Invalid advance_window_days: {raw_win}")
            return None, errors

        origin_iata = str(raw.get("origin_iata", "")).strip().upper()
        destination_iata = str(raw.get("destination_iata", "")).strip().upper()
        carrier_iata = str(raw.get("carrier_iata", "")).strip().upper()
        fare_class = normalize_fare_class(str(raw.get("fare_class", "Economy")))

        # Parse total_fare_inr
        raw_fare = raw.get("total_fare_inr")
        if raw_fare is None or str(raw_fare).strip() == "" or str(raw_fare).strip().lower() in ("none", "null", "nan"):
            total_fare_inr: Optional[float] = None
        else:
            try:
                total_fare_inr = round(float(raw_fare), 2)
            except (ValueError, TypeError):
                errors.append(f"Could not parse numeric total_fare_inr: {raw_fare}")
                return None, errors

        source_id = str(raw.get("source_id", "unknown")).strip() or "unknown"
        collection_method = str(raw.get("collection_method", "api")).strip().lower()
        quality_flag = str(raw.get("quality_flag", "ok")).strip().lower()

        # Auto-repair sold-out inconsistencies if enabled
        if auto_repair_sold_out:
            if total_fare_inr is None:
                quality_flag = "sold_out"
            elif quality_flag == "sold_out" and total_fare_inr is not None:
                total_fare_inr = None

        quote = FareQuote(
            collected_at_utc=collected_at_utc,
            departure_date=departure_date,
            advance_window_days=advance_window_days,
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            carrier_iata=carrier_iata,
            fare_class=fare_class,
            total_fare_inr=total_fare_inr,
            source_id=source_id,
            collection_method=collection_method,
            quality_flag=quality_flag,
        )

        res = validate_fare_quote(quote, strict_windows=strict_windows)
        if not res.is_valid:
            return None, res.errors

        return quote, []

    except Exception as exc:
        errors.append(f"Unexpected parsing exception: {str(exc)}")
        return None, errors
