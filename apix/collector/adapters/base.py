"""
FareSource interface — the contract every data adapter must satisfy.

Why this exists: resolver.py (Tier 1 API -> Tier 2 tariff sheet -> Tier 3
scrape -> Tier 4 simulated/cached) never needs to know HOW a quote was
obtained. Today only SimulatedFareSource exists. When TripJack access
comes through, you add TripJackFareSource with the same interface and
resolver.py doesn't change at all.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional


@dataclass
class FareQuote:
    collected_at_utc: datetime
    departure_date: date
    advance_window_days: int          # 1, 7, 15, 30, 45
    origin_iata: str
    destination_iata: str
    carrier_iata: str
    fare_class: str                   # Economy | Premium | Business
    total_fare_inr: Optional[float]   # None when quality_flag == "sold_out"
    source_id: str
    collection_method: str            # api | tariff_sheet | scrape | imputed | simulated
    quality_flag: str                 # ok | outlier | imputed | sold_out

    def to_row(self) -> dict:
        d = asdict(self)
        d["collected_at_utc"] = self.collected_at_utc.isoformat()
        d["departure_date"] = self.departure_date.isoformat()
        return d


class FareSource(ABC):
    """Every adapter (real or simulated) implements this."""

    source_id: str
    collection_method: str

    @abstractmethod
    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        """Return one FareQuote per carrier for this route/window/day."""
        raise NotImplementedError
