"""
SimulatedFareSource — Tier 4 stand-in until real API/scrape access lands.

This is NOT a random-number generator. It encodes the fare behaviour the
index module needs to be tested against before real data exists:
  - advance-purchase decay (T+1 costs more than T+45)
  - weekend departure surcharge
  - carrier price spread (full-service vs LCC)
  - occasional sold-out flights (missing price, never zero — see §4.2c)
  - occasional genuine outliers (for the outlier-detection module to catch)

IMPORTANT: BASE_FARE below is a rough placeholder. Once you download the
Kaggle EaseMyTrip panel (§3.4 in the handbook), replace these numbers with
actual median fares per route so the simulation is calibrated to reality,
not vibes.
"""

import hashlib
import random
from datetime import date, datetime, timezone

from .base import FareQuote, FareSource

# Rough placeholder economy base fares (INR) at T+30, one price per route.
# origin, destination -> base fare
BASE_FARE = {
    ("DEL", "BOM"): 5500, ("BOM", "DEL"): 5500,
    ("DEL", "BLR"): 6000, ("BLR", "DEL"): 6000,
    ("DEL", "CCU"): 6500, ("CCU", "DEL"): 6500,
    ("DEL", "MAA"): 7000, ("MAA", "DEL"): 7000,
    ("DEL", "HYD"): 5800, ("HYD", "DEL"): 5800,
    ("BOM", "BLR"): 4500, ("BLR", "BOM"): 4500,
    ("BOM", "MAA"): 5500, ("MAA", "BOM"): 5500,
    ("BOM", "CCU"): 7500, ("CCU", "BOM"): 7500,
    ("BLR", "HYD"): 4000, ("HYD", "BLR"): 4000,
    ("BLR", "MAA"): 3500, ("MAA", "BLR"): 3500,
    ("DEL", "GOI"): 6800, ("GOI", "DEL"): 6800,
    ("BOM", "GOI"): 3500, ("GOI", "BOM"): 3500,
}

# Carrier price multiplier relative to base (full-service costs more than LCC)
CARRIER_MULTIPLIER = {
    "6E": 1.00,  # IndiGo — market leader, roughly the reference price
    "AI": 1.15,  # Air India — full service
    "QP": 0.95,  # Akasa
    "SG": 0.90,  # SpiceJet
    "IX": 0.85,  # Air India Express
}

# Advance-purchase decay: shorter window -> higher last-minute premium
WINDOW_MULTIPLIER = {45: 0.80, 30: 0.90, 15: 1.05, 7: 1.30, 1: 1.70}

SOLD_OUT_PROB = 0.03
OUTLIER_PROB = 0.01


def _seeded_random(*parts: str) -> random.Random:
    """Deterministic per-(route, carrier, date, window) RNG so re-runs are reproducible."""
    key = "|".join(parts)
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


class SimulatedFareSource(FareSource):
    source_id = "simulated_v1"
    collection_method = "simulated"

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        base = BASE_FARE.get((origin, destination))
        if base is None:
            return []

        departure_date = as_of_date  # caller offsets this by the window if needed
        weekend_mult = 1.10 if departure_date.weekday() in (4, 5, 6) else 1.0
        window_mult = WINDOW_MULTIPLIER.get(advance_window_days, 1.0)

        quotes = []
        for carrier in carriers:
            rng = _seeded_random(origin, destination, carrier,
                                  as_of_date.isoformat(), str(advance_window_days))

            if rng.random() < SOLD_OUT_PROB:
                quotes.append(FareQuote(
                    collected_at_utc=datetime.now(timezone.utc),
                    departure_date=departure_date,
                    advance_window_days=advance_window_days,
                    origin_iata=origin, destination_iata=destination,
                    carrier_iata=carrier, fare_class="Economy",
                    total_fare_inr=None,
                    source_id=self.source_id,
                    collection_method=self.collection_method,
                    quality_flag="sold_out",
                ))
                continue

            noise = rng.lognormvariate(0, 0.08)  # ~+/-8% typical day-to-day noise
            price = base * CARRIER_MULTIPLIER.get(carrier, 1.0) * window_mult * weekend_mult * noise

            quality_flag = "ok"
            if rng.random() < OUTLIER_PROB:
                price *= rng.uniform(2.0, 4.0)
                quality_flag = "outlier"

            quotes.append(FareQuote(
                collected_at_utc=datetime.now(timezone.utc),
                departure_date=departure_date,
                advance_window_days=advance_window_days,
                origin_iata=origin, destination_iata=destination,
                carrier_iata=carrier, fare_class="Economy",
                total_fare_inr=round(price, 2),
                source_id=self.source_id,
                collection_method=self.collection_method,
                quality_flag=quality_flag,
            ))
        return quotes
