"""
Text Normalization & Offset Mapping
Implements Unicode NFC normalization and controlled whitespace collapsing (PIIShield.md §5).
"""

from typing import Tuple, List, Dict
from pydantic import BaseModel


class NormalizedTextResult(BaseModel):
    normalized_text: str
    # Map from index in normalized_text -> index in original_text
    offset_map: List[int]


def normalize_text(original_text: str) -> NormalizedTextResult:
    """
    Applies Unicode NFC normalization + controlled whitespace collapsing.
    Constructs an offset mapping to project detected normalized spans back to original offsets.
    """
    # TODO: Implement normalization and offset map construction
    raise NotImplementedError("Text normalizer is not yet implemented.")


def map_span_to_original(start: int, end: int, offset_map: List[int]) -> Tuple[int, int]:
    """Converts start and end offsets from normalized space back to original space."""
    # TODO: Implement offset conversion logic
    raise NotImplementedError("Offset mapping logic is not yet implemented.")
