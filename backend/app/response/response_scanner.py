"""
Response Scanner
Scans raw LLM responses before any de-pseudonymization occurs (PIIShield.md §7).
"""

from typing import List
from app.detection.models import RawDetectedEntity


class ResponseScanner:
    """Runs detection passes on raw LLM responses."""

    def __init__(self):
        # TODO: Initialize detection pipeline for response scanning
        pass

    def scan_response(self, response_text: str) -> List[RawDetectedEntity]:
        """
        Detects entities present in the response text before placeholder restoration.
        Fails closed on scanning errors (PIIShield.md §2).
        """
        # TODO: Implement detection pass over response text
        raise NotImplementedError("Response scanning is not yet implemented.")
