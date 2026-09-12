"""
External LLM Client Adapter
Provider-agnostic interface communicating with external LLMs across the trust boundary.
"""

from typing import List, Dict, Any


class LLMClient:
    """Dispatches sanitized prompts to configured LLM providers (OpenAI / Mock / etc.)."""

    def __init__(self, provider: str = "openai_mock", api_key: str = "", base_url: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

    async def generate_completion(self, messages: List[Dict[str, str]], model: str = "default") -> str:
        """Sends sanitized messages across trust boundary and returns raw LLM response."""
        # TODO: Implement external LLM HTTP call
        raise NotImplementedError("LLM client adapter is not yet implemented.")
