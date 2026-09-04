"""
APIx Data Collection Adapters.
"""

from .base import FareQuote, FareSource
from .simulated import SimulatedFareSource, BASE_FARE
from .kaggle import (
    KaggleFlightRecord,
    KaggleDatasetLoader,
    KaggleFareSource,
    normalize_airline,
    normalize_city,
    normalize_class,
    normalize_flight_number,
    map_days_left_to_window,
    window_to_tag,
    tag_to_window,
    APIX_ADVANCE_WINDOWS,
    WINDOW_TAGS,
    CITY_TO_IATA,
    AIRLINE_TO_IATA,
)

from .tariff_sheet import IndiGoTariffSheetSource, TariffBand
from .tariff_carriers import AirIndiaTariffSheetSource, AkasaTariffSheetSource
from .har_replay_scraper import HarReplayScraperSource

__all__ = [
    "FareQuote",
    "FareSource",
    "SimulatedFareSource",
    "BASE_FARE",
    "IndiGoTariffSheetSource",
    "AirIndiaTariffSheetSource",
    "AkasaTariffSheetSource",
    "HarReplayScraperSource",
    "TariffBand",
    "KaggleFlightRecord",
    "KaggleDatasetLoader",
    "KaggleFareSource",
    "normalize_airline",
    "normalize_city",
    "normalize_class",
    "normalize_flight_number",
    "map_days_left_to_window",
    "window_to_tag",
    "tag_to_window",
    "APIX_ADVANCE_WINDOWS",
    "WINDOW_TAGS",
    "CITY_TO_IATA",
    "AIRLINE_TO_IATA",
]
