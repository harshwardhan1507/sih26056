"""
Unified cleaning pipeline and audit reporting for APIx fare quotes.

Orchestrates the four core stages of airfare price data hygiene:
  1. Schema Validation & Coercion (schema.py)
  2. Deduplication with Deterministic Precedence (deduplication.py)
  3. Statistical Outlier Detection on Log Price RELATIVES (outliers.py)
  4. Optional CPI Missing Price Imputation (imputation.py)

Emits cleaned, provenance-audited FareQuotes and an actionable CleaningReport.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from apix.collector.adapters.base import FareQuote
from .schema import clean_quote_dict, validate_fare_quote
from .deduplication import deduplicate_quotes
from .outliers import detect_outliers
from .imputation import impute_missing_quotes


@dataclass
class CleaningReport:
    """Summary metrics of cleaning execution for statistical audit trails."""
    total_input: int
    valid_count: int
    invalid_count: int
    duplicates_dropped: int
    outliers_flagged: int
    sold_out_count: int
    imputed_count: int
    final_count: int

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


class CleaningPipeline:
    """
    Production data cleaning pipeline for APIx fare quotes.
    Accepts raw dictionaries or FareQuote dataclass instances.
    """

    def __init__(
        self,
        strict_windows: bool = False,
        deduplicate: bool = True,
        detect_outliers: bool = True,
        outlier_method: str = "relative",
        outlier_k: float = 2.0,
        outlier_mad_threshold: float = 3.5,
        impute_missing: bool = False,
        imputation_strategy: str = "class_mean",
    ) -> None:
        self.strict_windows = strict_windows
        self.deduplicate = deduplicate
        self.detect_outliers = detect_outliers
        self.outlier_method = outlier_method
        self.outlier_k = outlier_k
        self.outlier_mad_threshold = outlier_mad_threshold
        self.impute_missing = impute_missing
        self.imputation_strategy = imputation_strategy

    def clean_quotes(
        self,
        raw_items: Sequence[Union[FareQuote, Dict[str, Any]]],
    ) -> Tuple[List[FareQuote], CleaningReport]:
        """
        Execute the full cleaning pipeline on input quotes.

        Args:
            raw_items: Sequence of FareQuote objects or raw dict rows.

        Returns:
            (cleaned_quotes, report)
        """
        total_input = len(raw_items)
        valid_quotes: List[FareQuote] = []
        invalid_count = 0

        # Stage 1: Schema Validation
        for item in raw_items:
            if isinstance(item, FareQuote):
                res = validate_fare_quote(item, strict_windows=self.strict_windows)
                if res.is_valid and res.quote is not None:
                    valid_quotes.append(res.quote)
                else:
                    invalid_count += 1
            elif isinstance(item, dict):
                q, errors = clean_quote_dict(item, strict_windows=self.strict_windows)
                if q is not None and len(errors) == 0:
                    valid_quotes.append(q)
                else:
                    invalid_count += 1
            else:
                invalid_count += 1

        valid_count = len(valid_quotes)

        # Stage 2: Deduplication
        duplicates_dropped = 0
        current_quotes = valid_quotes
        if self.deduplicate and len(current_quotes) > 0:
            current_quotes, duplicates_dropped = deduplicate_quotes(current_quotes)

        # Stage 3: Statistical Outlier Detection
        outliers_flagged = 0
        if self.detect_outliers and len(current_quotes) > 0:
            current_quotes, outliers_flagged = detect_outliers(
                current_quotes,
                method=self.outlier_method,
                k=self.outlier_k,
                mad_threshold=self.outlier_mad_threshold,
            )

        # Stage 4: Missing Price / Sold-Out Imputation
        imputed_count = 0
        if self.impute_missing and len(current_quotes) > 0:
            current_quotes, imputed_count = impute_missing_quotes(
                current_quotes,
                strategy=self.imputation_strategy,
            )

        # Count sold-out records
        sold_out_count = sum(1 for q in current_quotes if q.quality_flag == "sold_out")

        report = CleaningReport(
            total_input=total_input,
            valid_count=valid_count,
            invalid_count=invalid_count,
            duplicates_dropped=duplicates_dropped,
            outliers_flagged=outliers_flagged,
            sold_out_count=sold_out_count,
            imputed_count=imputed_count,
            final_count=len(current_quotes),
        )

        return current_quotes, report
