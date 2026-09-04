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
from datetime import date, datetime, timedelta
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
    collection_method: str            # api | tariff_sheet | scrape | historical_panel
                                      #   | simulated | imputed
    quality_flag: str                 # ok | outlier | imputed | sold_out

    @property
    def observation_date(self) -> date:
        """
        The day this fare was OBSERVED, i.e. departure minus the advance window.

        A price index compares the T+7 fare seen today against the T+7 fare
        seen yesterday, so the index's time axis is the observation date.
        Consumers that grouped on ``departure_date`` only worked by accident:
        within one window it is a constant shift, but it silently misaligns
        the moment two windows share a calendar.
        """
        return self.departure_date - timedelta(days=self.advance_window_days)

    def to_row(self) -> dict:
        d = asdict(self)
        d["collected_at_utc"] = self.collected_at_utc.isoformat()
        d["departure_date"] = self.departure_date.isoformat()
        d["observation_date"] = self.observation_date.isoformat()
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
