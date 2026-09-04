"""
Kaggle historical panel real-data loader and adapter for APIx.

Loads EaseMyTrip Clean_Dataset.csv (Bathwal 2022 panel) and normalizes:
  - airline -> canonical name and 2-letter IATA code (e.g., Indigo -> 6E)
  - flight -> standard flight number (e.g., SG-8709)
  - source_city / destination_city -> 3-letter IATA code (e.g., Delhi -> DEL)
  - class -> canonical fare class (Economy / Business)
  - duration -> float hours
  - days_left -> mapped into APIx advance windows (T+1, T+7, T+15, T+30, T+45)
  - price -> total fare in INR

Produces APIx-compatible records convertible to canonical FareQuote instances.
"""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone, timedelta
from io import StringIO
from pathlib import Path
import csv
import re
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from .base import FareQuote, FareSource

# --- Canonical City & Airline IATA Mappings ---

CITY_TO_IATA: Dict[str, str] = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "del": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bom": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "blr": "BLR",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "ccu": "CCU",
    "hyderabad": "HYD",
    "hyd": "HYD",
    "chennai": "MAA",
    "madras": "MAA",
    "maa": "MAA",
    "goa": "GOI",
    "goi": "GOI",
}

IATA_TO_CITY: Dict[str, str] = {
    "DEL": "Delhi",
    "BOM": "Mumbai",
    "BLR": "Bangalore",
    "CCU": "Kolkata",
    "HYD": "Hyderabad",
    "MAA": "Chennai",
    "GOI": "Goa",
}

AIRLINE_TO_IATA: Dict[str, Tuple[str, str]] = {
    "indigo": ("IndiGo", "6E"),
    "6e": ("IndiGo", "6E"),
    "air india": ("Air India", "AI"),
    "air_india": ("Air India", "AI"),
    "airindia": ("Air India", "AI"),
    "ai": ("Air India", "AI"),
    "vistara": ("Vistara", "UK"),
    "uk": ("Vistara", "UK"),
    "spicejet": ("SpiceJet", "SG"),
    "sg": ("SpiceJet", "SG"),
    "airasia": ("AirAsia", "I5"),
    "airasia india": ("AirAsia", "I5"),
    "aix connect": ("AirAsia", "I5"),
    "i5": ("AirAsia", "I5"),
    "go first": ("GO FIRST", "G8"),
    "go_first": ("GO FIRST", "G8"),
    "gofirst": ("GO FIRST", "G8"),
    "go air": ("GO FIRST", "G8"),
    "goair": ("GO FIRST", "G8"),
    "g8": ("GO FIRST", "G8"),
    "akasa": ("Akasa Air", "QP"),
    "akasa air": ("Akasa Air", "QP"),
    "qp": ("Akasa Air", "QP"),
    "air india express": ("Air India Express", "IX"),
    "ix": ("Air India Express", "IX"),
}

# --- APIx Statistical Advance Windows ---

APIX_ADVANCE_WINDOWS: Tuple[int, ...] = (1, 7, 15, 30, 45)

WINDOW_TAGS: Dict[int, str] = {
    1: "T+1",
    7: "T+7",
    15: "T+15",
    30: "T+30",
    45: "T+45",
}

TAG_TO_WINDOW: Dict[str, int] = {
    "T+1": 1,
    "T+7": 7,
    "T+15": 15,
    "T+30": 30,
    "T+45": 45,
    "1": 1,
    "7": 7,
    "15": 15,
    "30": 30,
    "45": 45,
}

# Reference start date of Kaggle panel collection (11 Feb 2022)
KAGGLE_PANEL_BASE_DATE = date(2022, 2, 11)


# --- Normalization Helpers ---

def normalize_city(city: str) -> Tuple[str, str]:
    """
    Normalize city name to canonical (City Name, IATA Code).
    Raises ValueError if city is unmapped.
    """
    cleaned = city.strip().lower()
    iata = CITY_TO_IATA.get(cleaned)
    if not iata:
        raise ValueError(f"Unrecognized city: '{city}'")
    canonical_name = IATA_TO_CITY.get(iata, city.strip().title())
    return canonical_name, iata


def normalize_airline(airline: str) -> Tuple[str, str]:
    """
    Normalize airline name to canonical (Airline Name, IATA Code).
    Raises ValueError if airline is unmapped.
    """
    cleaned = airline.strip().lower()
    mapping = AIRLINE_TO_IATA.get(cleaned)
    if not mapping:
        raise ValueError(f"Unrecognized airline: '{airline}'")
    return mapping


def normalize_class(fare_class: str) -> str:
    """
    Normalize fare class to 'Economy' | 'Business' | 'Premium'.
    """
    cleaned = fare_class.strip().lower()
    if "bus" in cleaned:
        return "Business"
    if "prem" in cleaned:
        return "Premium"
    return "Economy"


def normalize_flight_number(flight: str, carrier_iata: str = "") -> str:
    """
    Standardize flight code format (e.g. 'SG-8709' or '6E 2053' -> '6E-2053').
    """
    cleaned = flight.strip().upper()
    cleaned = re.sub(r"\s+", "-", cleaned)
    if carrier_iata and not cleaned.startswith(f"{carrier_iata}-") and not cleaned.startswith(carrier_iata):
        cleaned = f"{carrier_iata}-{cleaned}"
    return cleaned


def map_days_left_to_window(days_left: int, strategy: str = "exact") -> Optional[int]:
    """
    Map raw days_left integer into an APIx advance window (1, 7, 15, 30, 45).

    Strategies:
      - 'exact': Only maps if days_left in (1, 7, 15, 30, 45), else None.
      - 'nearest': Maps to the closest anchor in APIX_ADVANCE_WINDOWS.
      - 'bucket': Maps into statistical intervals:
          * 1: [1, 3]
          * 7: [4, 10]
          * 15: [11, 22]
          * 30: [23, 37]
          * 45: [38, inf)
    """
    if days_left < 1:
        return None

    if strategy == "exact":
        return days_left if days_left in APIX_ADVANCE_WINDOWS else None

    if strategy == "nearest":
        return min(APIX_ADVANCE_WINDOWS, key=lambda w: abs(days_left - w))

    if strategy == "bucket":
        if days_left <= 3:
            return 1
        elif days_left <= 10:
            return 7
        elif days_left <= 22:
            return 15
        elif days_left <= 37:
            return 30
        else:
            return 45

    raise ValueError(f"Unknown advance window mapping strategy: '{strategy}'")


def window_to_tag(window_days: int) -> str:
    """Convert window days integer (1, 7, ...) to APIx tag ('T+1', 'T+7', ...)."""
    return WINDOW_TAGS.get(window_days, f"T+{window_days}")


def tag_to_window(tag: str) -> int:
    """Convert APIx tag ('T+1', 'T+7', ...) or string integer to window days int."""
    cleaned = tag.strip().upper()
    if cleaned in TAG_TO_WINDOW:
        return TAG_TO_WINDOW[cleaned]
    if cleaned.startswith("T+"):
        return int(cleaned[2:])
    return int(cleaned)


# --- Record Model ---

@dataclass
class KaggleFlightRecord:
    """
    Normalized flight record from the Kaggle historical panel.
    Fully compatible with APIx schema and converts to FareQuote.
    """
    flight_number: str
    airline: str
    carrier_iata: str
    source_city: str
    origin_iata: str
    destination_city: str
    destination_iata: str
    fare_class: str                    # Economy | Business | Premium
    duration_hours: float
    days_left: int
    advance_window_days: int           # 1, 7, 15, 30, 45
    advance_window_tag: str            # T+1, T+7, T+15, T+30, T+45
    price_inr: float
    departure_time: str = ""
    stops: str = ""
    arrival_time: str = ""
    collected_at_utc: Optional[datetime] = None
    departure_date: Optional[date] = None
    source_id: str = "kaggle_easemytrip_v1"
    collection_method: str = "historical_panel"
    quality_flag: str = "ok"

    @property
    def observation_date(self) -> Optional[date]:
        """
        The day the fare was OBSERVED (the panel's `date` column), as
        distinct from the day it departs.

        An airfare index compares the T+7 price seen today against the T+7
        price seen yesterday, so the time axis is the observation date.
        Keying on departure_date instead only happens to work within a
        single window (it is a constant shift) and breaks the moment two
        windows are placed on a shared calendar.
        """
        if self.collected_at_utc is not None:
            return self.collected_at_utc.date()
        if self.departure_date is not None:
            return self.departure_date - timedelta(days=self.advance_window_days)
        return None

    def to_fare_quote(self, as_of_date: Optional[date] = None) -> FareQuote:
        """
        Convert this normalized record to a canonical APIx FareQuote dataclass.
        """
        now_utc = self.collected_at_utc or datetime.now(timezone.utc)
        base_dep_date = self.departure_date
        if base_dep_date is None:
            anchor = as_of_date or KAGGLE_PANEL_BASE_DATE
            base_dep_date = anchor + timedelta(days=self.advance_window_days)

        return FareQuote(
            collected_at_utc=now_utc,
            departure_date=base_dep_date,
            advance_window_days=self.advance_window_days,
            origin_iata=self.origin_iata,
            destination_iata=self.destination_iata,
            carrier_iata=self.carrier_iata,
            fare_class=self.fare_class,
            total_fare_inr=round(self.price_inr, 2),
            source_id=self.source_id,
            collection_method=self.collection_method,
            quality_flag=self.quality_flag,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a complete dictionary with all normalized fields."""
        d = asdict(self)
        if self.collected_at_utc:
            d["collected_at_utc"] = self.collected_at_utc.isoformat()
        if self.departure_date:
            d["departure_date"] = self.departure_date.isoformat()
        return d

    def to_row(self) -> Dict[str, Any]:
        """Convert record to row representation matching APIx CSV export schema."""
        fq = self.to_fare_quote()
        row = fq.to_row()
        row["flight_number"] = self.flight_number
        row["duration_hours"] = self.duration_hours
        row["days_left"] = self.days_left
        row["advance_window_tag"] = self.advance_window_tag
        return row


# --- Row Normalization ---

def normalize_row(
    row: Dict[str, str],
    window_strategy: str = "exact",
    as_of_date: Optional[date] = None,
) -> Optional[KaggleFlightRecord]:
    """
    Parse and normalize a single raw CSV row from Clean_Dataset.csv.
    Returns KaggleFlightRecord if valid and within the advance window strategy, else None.
    """
    try:
        airline_name, carrier_iata = normalize_airline(row["airline"])
        src_city, origin_iata = normalize_city(row["source_city"])
        dest_city, dest_iata = normalize_city(row["destination_city"])
        fare_class = normalize_class(row.get("class", "Economy"))

        flight_num = normalize_flight_number(row.get("flight", ""), carrier_iata)
        duration = float(row.get("duration", 0.0))
        days_left = int(row.get("days_left", 0))
        price = float(row.get("price", 0.0))

        if price <= 0 or duration < 0:
            return None

        window = map_days_left_to_window(days_left, strategy=window_strategy)
        if window is None:
            return None

        window_tag = window_to_tag(window)
        if "date" in row and row["date"].strip():
            try:
                anchor_date = date.fromisoformat(row["date"].strip())
            except ValueError:
                anchor_date = as_of_date or KAGGLE_PANEL_BASE_DATE
        else:
            anchor_date = as_of_date or KAGGLE_PANEL_BASE_DATE

        if "departure_date" in row and row["departure_date"].strip():
            try:
                departure_date = date.fromisoformat(row["departure_date"].strip())
            except ValueError:
                departure_date = anchor_date + timedelta(days=days_left)
        else:
            departure_date = anchor_date + timedelta(days=days_left)

        collected_at = datetime.combine(anchor_date, datetime.min.time(), tzinfo=timezone.utc)

        return KaggleFlightRecord(
            flight_number=flight_num,
            airline=airline_name,
            carrier_iata=carrier_iata,
            source_city=src_city,
            origin_iata=origin_iata,
            destination_city=dest_city,
            destination_iata=dest_iata,
            fare_class=fare_class,
            duration_hours=duration,
            days_left=days_left,
            advance_window_days=window,
            advance_window_tag=window_tag,
            price_inr=price,
            departure_time=row.get("departure_time", "").strip(),
            stops=row.get("stops", "").strip(),
            arrival_time=row.get("arrival_time", "").strip(),
            collected_at_utc=collected_at,
            departure_date=departure_date,
            source_id="kaggle_easemytrip_v1",
            collection_method="historical_panel",
            quality_flag="ok",
        )
    except (ValueError, KeyError):
        return None


# --- Dataset Loader ---

class KaggleDatasetLoader:
    """
    High-performance, streaming reader for Clean_Dataset.csv.
    Processes rows without requiring heavy external dependencies.
    """

    DEFAULT_CANDIDATE_PATHS = (
        Path("data/raw/kaggle/easemytrip-flight-price-prediction/Clean_Dataset.csv"),
        Path("data/Clean_Dataset.csv"),
        Path("apix/data/Clean_Dataset.csv"),
        Path("tests/fixtures/sample_clean_dataset.csv"),
    )

    @classmethod
    def resolve_path(cls, path: Optional[Union[str, Path]] = None) -> Path:
        """Locate the dataset file among specified or standard locations."""
        if path is not None:
            p = Path(path)
            if p.exists():
                return p
            raise FileNotFoundError(f"Kaggle dataset file not found at: {path}")

        for candidate in cls.DEFAULT_CANDIDATE_PATHS:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            "Clean_Dataset.csv not found in standard paths. "
            "Please specify the path or download the dataset."
        )

    @staticmethod
    def stream_records(
        source: Union[str, Path, StringIO],
        window_strategy: str = "exact",
        fare_class: Optional[str] = None,
        origin_iata: Optional[str] = None,
        destination_iata: Optional[str] = None,
        as_of_date: Optional[date] = None,
    ) -> Iterator[KaggleFlightRecord]:
        """
        Stream KaggleFlightRecords row-by-row with optional filtering.
        Memory-efficient iterator suitable for 300,000+ records.
        """
        target_class = normalize_class(fare_class) if fare_class else None
        target_orig = origin_iata.strip().upper() if origin_iata else None
        target_dest = destination_iata.strip().upper() if destination_iata else None

        if isinstance(source, StringIO):
            f = source
            reader = csv.DictReader(f)
            for row in reader:
                rec = normalize_row(row, window_strategy=window_strategy, as_of_date=as_of_date)
                if rec is None:
                    continue
                if target_class and rec.fare_class != target_class:
                    continue
                if target_orig and rec.origin_iata != target_orig:
                    continue
                if target_dest and rec.destination_iata != target_dest:
                    continue
                yield rec
        else:
            path = Path(source)
            with open(path, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rec = normalize_row(row, window_strategy=window_strategy, as_of_date=as_of_date)
                    if rec is None:
                        continue
                    if target_class and rec.fare_class != target_class:
                        continue
                    if target_orig and rec.origin_iata != target_orig:
                        continue
                    if target_dest and rec.destination_iata != target_dest:
                        continue
                    yield rec

    @classmethod
    def load_records(
        cls,
        source: Optional[Union[str, Path, StringIO]] = None,
        window_strategy: str = "exact",
        fare_class: Optional[str] = None,
        origin_iata: Optional[str] = None,
        destination_iata: Optional[str] = None,
        as_of_date: Optional[date] = None,
    ) -> List[KaggleFlightRecord]:
        """Load all matching records into a list."""
        src = source if isinstance(source, StringIO) else cls.resolve_path(source)
        return list(cls.stream_records(
            source=src,
            window_strategy=window_strategy,
            fare_class=fare_class,
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            as_of_date=as_of_date,
        ))

    @staticmethod
    def to_daily_carrier_prices(
        records: Sequence[KaggleFlightRecord],
        origin_iata: str,
        destination_iata: str,
        window_days: int,
        fare_class: str = "Economy",
        agg_func: str = "min",
    ) -> List[Dict[str, float]]:
        """
        Aggregate records into a daily price series for index compilation.
        Returns list of {carrier_iata: price} dictionaries grouped by flight departure date.
        """
        target_orig = origin_iata.strip().upper()
        target_dest = destination_iata.strip().upper()
        target_class = normalize_class(fare_class)

        # Group by departure_date -> carrier_iata -> list of prices
        grouped: Dict[date, Dict[str, List[float]]] = {}
        for rec in records:
            if (rec.origin_iata == target_orig and
                rec.destination_iata == target_dest and
                rec.advance_window_days == window_days and
                rec.fare_class == target_class):
                
                dep = rec.departure_date or KAGGLE_PANEL_BASE_DATE
                if dep not in grouped:
                    grouped[dep] = {}
                grouped[dep].setdefault(rec.carrier_iata, []).append(rec.price_inr)

        daily_series: List[Dict[str, float]] = []
        for dep in sorted(grouped.keys()):
            carrier_map: Dict[str, float] = {}
            for carrier, prices in grouped[dep].items():
                if agg_func == "min":
                    carrier_map[carrier] = min(prices)
                elif agg_func == "median":
                    sorted_p = sorted(prices)
                    mid = len(sorted_p) // 2
                    carrier_map[carrier] = sorted_p[mid] if len(sorted_p) % 2 != 0 else (sorted_p[mid-1] + sorted_p[mid]) / 2.0
                else:
                    carrier_map[carrier] = sum(prices) / len(prices)
            daily_series.append(carrier_map)

        return daily_series

    @staticmethod
    def to_dated_carrier_prices(
        records: Sequence[KaggleFlightRecord],
        origin_iata: str,
        destination_iata: str,
        window_days: int,
        fare_class: str = "Economy",
        agg_func: str = "min",
    ) -> Dict[date, Dict[str, float]]:
        """
        Same aggregation as ``to_daily_carrier_prices`` but keyed by calendar
        date instead of collapsed into a dense list.

        The list form silently loses which days are missing, so two
        (route, window) strata with different coverage produce series of
        different lengths that cannot be aggregated together. Callers that
        aggregate across strata must build a common date axis, which needs
        the dates.
        """
        target_orig = origin_iata.strip().upper()
        target_dest = destination_iata.strip().upper()
        target_class = normalize_class(fare_class)

        grouped: Dict[date, Dict[str, List[float]]] = {}
        for rec in records:
            if (rec.origin_iata == target_orig and
                rec.destination_iata == target_dest and
                rec.advance_window_days == window_days and
                rec.fare_class == target_class):

                obs = rec.observation_date or KAGGLE_PANEL_BASE_DATE
                grouped.setdefault(obs, {}).setdefault(rec.carrier_iata, []).append(rec.price_inr)

        dated: Dict[date, Dict[str, float]] = {}
        for obs, carriers in grouped.items():
            carrier_map: Dict[str, float] = {}
            for carrier, prices in carriers.items():
                if agg_func == "min":
                    carrier_map[carrier] = min(prices)
                elif agg_func == "median":
                    sorted_p = sorted(prices)
                    mid = len(sorted_p) // 2
                    carrier_map[carrier] = (
                        sorted_p[mid] if len(sorted_p) % 2 != 0
                        else (sorted_p[mid - 1] + sorted_p[mid]) / 2.0
                    )
                else:
                    carrier_map[carrier] = sum(prices) / len(prices)
            dated[obs] = carrier_map

        return dated


# --- FareSource Adapter for APIx Pipeline ---

class KaggleFareSource(FareSource):
    """
    FareSource adapter backed by the historical Kaggle EaseMyTrip panel.
    Integrates directly with FareResolver and index pipelines.
    """

    source_id = "kaggle_easemytrip_v1"
    # Retrospective panel (2022 observations), NOT a live scrape. Mislabelling
    # it "scrape" made /sources/status report stale history as live collection.
    collection_method = "historical_panel"

    def __init__(
        self,
        records_or_source: Optional[Union[Sequence[KaggleFlightRecord], str, Path, StringIO]] = None,
        window_strategy: str = "exact",
        fare_class: str = "Economy",
        price_agg: str = "min",
    ) -> None:
        """
        Initialize KaggleFareSource.

        Args:
            records_or_source: Pre-parsed records, path to CSV, or None to auto-resolve.
            window_strategy: Mapping method for days_left ('exact', 'nearest', 'bucket').
            fare_class: Travel class to query ('Economy', 'Business').
            price_agg: How to aggregate multiple flights per carrier ('min', 'median', 'mean').
        """
        self.window_strategy = window_strategy
        self.fare_class = normalize_class(fare_class)
        self.price_agg = price_agg

        if isinstance(records_or_source, (list, tuple)):
            self.records = list(records_or_source)
        else:
            self.records = KaggleDatasetLoader.load_records(
                source=records_or_source,
                window_strategy=window_strategy,
                fare_class=self.fare_class,
            )

        # Index records: (origin_iata, destination_iata, window_days) -> carrier_iata -> list[price]
        self._index: Dict[Tuple[str, str, int], Dict[str, List[float]]] = {}
        for rec in self.records:
            if rec.fare_class != self.fare_class:
                continue
            key = (rec.origin_iata, rec.destination_iata, rec.advance_window_days)
            if key not in self._index:
                self._index[key] = {}
            self._index[key].setdefault(rec.carrier_iata, []).append(rec.price_inr)

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        """
        Return one FareQuote per carrier for this route/window/day.
        Follows FareSource contract from base.py.
        """
        key = (origin.upper(), destination.upper(), advance_window_days)
        carrier_prices = self._index.get(key, {})

        quotes: List[FareQuote] = []
        dep_date = as_of_date + timedelta(days=advance_window_days)
        now_utc = datetime.combine(as_of_date, datetime.min.time(), tzinfo=timezone.utc)

        for carrier in carriers:
            carrier_upper = carrier.upper()
            prices = carrier_prices.get(carrier_upper)

            if not prices:
                # Carrier unavailable on this route / window
                continue

            if self.price_agg == "min":
                fare = min(prices)
            elif self.price_agg == "median":
                sorted_p = sorted(prices)
                mid = len(sorted_p) // 2
                fare = sorted_p[mid] if len(sorted_p) % 2 != 0 else (sorted_p[mid-1] + sorted_p[mid]) / 2.0
            else:
                fare = sum(prices) / len(prices)

            quotes.append(FareQuote(
                collected_at_utc=now_utc,
                departure_date=dep_date,
                advance_window_days=advance_window_days,
                origin_iata=origin.upper(),
                destination_iata=destination.upper(),
                carrier_iata=carrier_upper,
                fare_class=self.fare_class,
                total_fare_inr=round(fare, 2),
                source_id=self.source_id,
                collection_method=self.collection_method,
                quality_flag="ok",
            ))

        return quotes
