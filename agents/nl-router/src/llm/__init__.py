"""LLM integration module"""

from .llm_client import LLMClient, LLMConfig, get_llm_client
from .prompts import INTENT_CLASSIFICATION_PROMPT, ENTITY_EXTRACTION_PROMPT

__all__ = [
    "LLMClient",
    "LLMConfig",
    "get_llm_client",
    "INTENT_CLASSIFICATION_PROMPT",
    "ENTITY_EXTRACTION_PROMPT",
]
