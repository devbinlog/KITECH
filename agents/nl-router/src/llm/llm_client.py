"""LLM Client for Claude API integration"""

import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMConfig(BaseSettings):
    """LLM configuration."""

    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.0

    model_config = SettingsConfigDict(
        env_prefix="NL_ROUTER_",
        env_file=".env",
        extra="ignore",  # 다른 NL_ROUTER_ 환경변수 무시
    )


class LLMClient:
    """Client for Claude API with structured output support"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Anthropic client"""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package is required. Install with: pip install anthropic"
                )
        return self._client

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
    ) -> T | str | Dict[str, Any]:
        """
        Complete a prompt with optional structured output

        Args:
            prompt: User prompt
            system: System prompt
            response_schema: Pydantic model for structured response

        Returns:
            Parsed response (Pydantic model if schema provided, else str/dict)
        """
        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system or "",
                messages=messages,
            )

            content = response.content[0].text

            # Parse JSON if schema provided
            if response_schema:
                try:
                    # Try to extract JSON from response
                    json_str = self._extract_json(content)
                    data = json.loads(json_str)
                    return response_schema.model_validate(data)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse structured response: {e}")
                    return content

            # Try to parse as JSON dict
            try:
                return json.loads(self._extract_json(content))
            except (json.JSONDecodeError, ValueError):
                return content

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    async def complete_with_tools(
        self,
        prompt: str,
        tools: list[Dict[str, Any]],
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete with tool use for structured extraction

        Args:
            prompt: User prompt
            tools: Tool definitions
            system: System prompt

        Returns:
            Tool use result or text response
        """
        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system or "",
                messages=messages,
                tools=tools,
            )

            # Process response
            for block in response.content:
                if block.type == "tool_use":
                    return {
                        "tool_name": block.name,
                        "tool_input": block.input,
                    }
                elif block.type == "text":
                    return {"text": block.text}

            return {"text": ""}

        except Exception as e:
            logger.error(f"LLM API call with tools failed: {e}")
            raise

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text (handles markdown code blocks)"""
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find JSON object directly
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return text[start:end]

        return text


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
