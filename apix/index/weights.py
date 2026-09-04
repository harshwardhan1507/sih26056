"""
Route weight loader for the APIx aggregate index.

Weights are stored in an external JSON file so that PSD/MoSPI-supplied weights
can replace the DGCA-derived defaults without touching any source code.
See handbook §1.6, §3.2, and docs/data-sources/dgca-route-weights.md for the
design rationale, legal compliance (ODbL-1.0), and derivation methodology.
Run `scripts/derive_weights.py` to regenerate weights from DGCA city-pair traffic.

Weight file schema:
    {
        "source":         "<attribution string>",
        "coverage_month": "YYYY-MM",
        "generated_date": "YYYY-MM-DD",
        "weights": {
            "DEL-BOM": 0.1922,
            ...   (keys are canonical IATA route strings, values sum to 1.0)
        }
    }

The top-level keys "source", "coverage_month", and "generated_date" are
required; any extra keys are ignored, so future fields can be added freely.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

# Default weight file shipped with the package.
# Override by passing an explicit path to load_weights().
DEFAULT_WEIGHT_FILE: Path = Path(__file__).resolve().parent.parent / "data" / "route_weights.json"

# Basket routes in canonical direction (matches backfill_demo.py ROUTES list).
# Used only for validation; callers are free to supply a different basket.
BASKET_ROUTES: tuple[str, ...] = (
    "DEL-BOM", "DEL-BLR", "DEL-CCU", "DEL-MAA", "DEL-HYD",
    "BOM-BLR", "BOM-MAA", "BOM-CCU",
    "BLR-HYD", "BLR-MAA",
    "DEL-GOI", "BOM-GOI",
)


def load_weights(
    path: Optional[Path | str] = None,
    *,
    required_routes: Optional[tuple[str, ...]] = BASKET_ROUTES,
    sum_tolerance: float = 1e-4,
) -> dict[str, float]:
    """
    Load route weights from a JSON file and return them as a plain dict.

    Parameters
    ----------
    path:
        Path to the JSON weight file.  Defaults to ``DEFAULT_WEIGHT_FILE``.
    required_routes:
        If given, raises ``KeyError`` if any of these route keys are absent
        from the loaded weight dict.  Pass ``None`` to skip this check.
    sum_tolerance:
        Acceptable deviation from 1.0 for the weight sum.  Raises
        ``ValueError`` if ``abs(sum(weights) - 1.0) > sum_tolerance``.

    Returns
    -------
    dict[str, float]
        ``{"DEL-BOM": 0.1922, ...}`` — keys are IATA route strings.

    Raises
    ------
    FileNotFoundError
        If the weight file does not exist at the resolved path.
    KeyError
        If a required route key is missing from the weight dict.
    ValueError
        If weights do not sum to approximately 1.0.
    """
    resolved = Path(path) if path is not None else DEFAULT_WEIGHT_FILE
    if not resolved.exists():
        raise FileNotFoundError(
            f"Route weight file not found: {resolved}\n"
            "Run scripts/derive_weights.py to regenerate it, or supply a "
            "MoSPI/PSD-provided weight file."
        )

    with open(resolved, encoding="utf-8") as fh:
        payload = json.load(fh)

    weights: dict[str, float] = {
        str(k): float(v) for k, v in payload["weights"].items()
    }

    # Validate required routes are present
    if required_routes:
        missing = [r for r in required_routes if r not in weights]
        if missing:
            raise KeyError(
                f"Weight file {resolved} is missing required routes: {missing}"
            )

    # Validate weight sum
    total = sum(weights.values())
    if not math.isclose(total, 1.0, abs_tol=sum_tolerance):
        raise ValueError(
            f"Weights in {resolved} sum to {total:.8f}, expected 1.0 "
            f"(tolerance ±{sum_tolerance}). Normalise and regenerate the file."
        )

    return weights


def weight_file_metadata(path: Optional[Path | str] = None) -> dict:
    """
    Return the metadata fields from the weight file (source, coverage_month,
    generated_date) without validating the weights themselves.  Useful for
    logging and API provenance headers.
    """
    resolved = Path(path) if path is not None else DEFAULT_WEIGHT_FILE
    with open(resolved, encoding="utf-8") as fh:
        payload = json.load(fh)
    return {
        k: payload[k]
        for k in ("source", "coverage_month", "generated_date")
        if k in payload
    }
