"""
Data cleaning, schema validation, outlier detection, and sold-out flight imputation.
"""

from .schema import (
    ValidationResult,
    validate_fare_quote,
    clean_quote_dict,
    normalize_fare_class,
    VALID_COLLECTION_METHODS,
    VALID_QUALITY_FLAGS,
    VALID_FARE_CLASSES,
    VALID_ADVANCE_WINDOWS,
)
from .deduplication import (
    deduplicate_quotes,
    quote_identity_key,
    quote_precedence_score,
)
from .outliers import (
    detect_outliers,
    identify_outlier_indices_tukey,
    identify_outlier_indices_mad,
)
from .imputation import (
    impute_missing_quotes,
)
from .pipeline import (
    CleaningPipeline,
    CleaningReport,
)

__all__ = [
    "ValidationResult",
    "validate_fare_quote",
    "clean_quote_dict",
    "normalize_fare_class",
    "VALID_COLLECTION_METHODS",
    "VALID_QUALITY_FLAGS",
    "VALID_FARE_CLASSES",
    "VALID_ADVANCE_WINDOWS",
    "deduplicate_quotes",
    "quote_identity_key",
    "quote_precedence_score",
    "detect_outliers",
    "identify_outlier_indices_tukey",
    "identify_outlier_indices_mad",
    "impute_missing_quotes",
    "CleaningPipeline",
    "CleaningReport",
]
