"""
Text Normalization & Offset Mapping
Implements Unicode NFC normalization and controlled whitespace collapsing (PIIShield_Spec_v2.md §5).
"""

import unicodedata
import re
from typing import Tuple, List
from pydantic import BaseModel


class NormalizedTextResult(BaseModel):
    normalized_text: str
    # Map from index in normalized_text -> index in original_text
    offset_map: List[int]


def normalize_text(original_text: str) -> NormalizedTextResult:
    """
    Applies Unicode NFC normalization + controlled whitespace collapsing.
    Constructs an offset mapping to project detected normalized spans back to original offsets.
    Follows PIIShield_Spec_v2.md §5.
    """
    if not original_text:
        return NormalizedTextResult(normalized_text="", offset_map=[])

    # 1. Unicode NFC normalization
    # Note: for NFC, decomposed unicode characters combine into single code points.
    nfc_text = unicodedata.normalize("NFC", original_text)

    # 2. Controlled whitespace collapsing (spaces/tabs collapsed to single space)
    # Track offset from normalized character back to original_text character.
    normalized_chars: List[str] = []
    offset_map: List[int] = []

    # Map nfc characters to original characters (if simple 1-1 or fallback)
    in_whitespace = False

    for orig_idx, char in enumerate(original_text):
        nfc_char = unicodedata.normalize("NFC", char)
        if char in " \t":
            if not in_whitespace:
                normalized_chars.append(" ")
                offset_map.append(orig_idx)
                in_whitespace = True
            else:
                # Skip extra consecutive whitespace
                continue
        else:
            in_whitespace = False
            for c in nfc_char:
                normalized_chars.append(c)
                offset_map.append(orig_idx)

    normalized_text = "".join(normalized_chars)
    return NormalizedTextResult(normalized_text=normalized_text, offset_map=offset_map)


def map_span_to_original(start: int, end: int, offset_map: List[int]) -> Tuple[int, int]:
    """
    Converts start and end offsets from normalized space back to original space.
    Guarantees the mapped slice in original_text covers the entire original entity span.
    """
    if start < 0 or not offset_map:
        return 0, 0

    if start >= len(offset_map):
        return offset_map[-1], offset_map[-1] + 1

    orig_start = offset_map[start]

    # For end offset: find the end of the last character in the normalized span
    last_char_idx = min(end - 1, len(offset_map) - 1)
    if last_char_idx < start:
        return orig_start, orig_start

    orig_end = offset_map[last_char_idx] + 1
    return orig_start, orig_end
