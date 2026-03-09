"""
Multi-provider LLM service with unified interface.
Supports OpenAI, Anthropic Claude, Google Gemini, and Grok (xAI).
Includes automatic fallback from Gemini to Grok on rate limits.
"""
from typing import Optional, AsyncGenerator
import structlog
import json
import re

from config import settings

log = structlog.get_logger()


class LLMService:
    """Unified LLM client with provider abstraction and fallback support."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client

        if self.provider == "openai":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "groq":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.XAI_API_KEY, base_url="https://api.groq.com/openai/v1")
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif self.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self._client = genai
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        return self._client

    async def _complete_internal(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        client = self._get_client()

        if self.provider in ("openai", "groq"):
            kwargs = {
                "model": self.model or ("gpt-4o" if self.provider == "openai" else "llama3-8b-8192"),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if json_mode and self.provider in ("openai", "groq"):
                kwargs["response_format"] = {"type": "json_object"}
            resp = await client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content

        elif self.provider == "anthropic":
            resp = await client.messages.create(
                model=self.model or "claude-sonnet-4-5",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return resp.content[0].text

        elif self.provider == "google":
            import google.generativeai as genai
            model = genai.GenerativeModel(
                self.model or "gemini-2.0-flash",
                system_instruction=system_prompt,
            )
            resp = await model.generate_content_async(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return resp.text

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Single completion call with fallback support and retry logic."""
        import asyncio
        for attempt in range(3):
            try:
                return await self._complete_internal(system_prompt, user_prompt, temperature, max_tokens, json_mode)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate limit" in err_str:
                    if attempt < 2:
                        log.warning(f"LLM rate limit hit. Sleeping 4s before retry... Attempt {attempt+1}/3")
                        await asyncio.sleep(4)
                        continue
                if self.provider == "google" and ("429" in err_str or "quota" in err_str or "exhausted" in err_str):
                    if settings.XAI_API_KEY:
                        log.warning("Google API rate limit hit. Falling back to Groq.")
                        self.provider = "groq"
                        self.model = "llama3-8b-8192"
                        self._client = None
                        return await self._complete_internal(system_prompt, user_prompt, temperature, max_tokens, json_mode)
                raise e

    async def complete_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        """Return parsed JSON from LLM."""
        resp = await self.complete(
            system_prompt,
            user_prompt + "\n\nRespond ONLY with valid JSON, no markdown fences.",
            json_mode=(self.provider in ("openai", "groq")),
            **kwargs
        )
        # Strip markdown fences if present
        resp = re.sub(r"```(?:json)?\n?", "", resp).strip().rstrip("```")
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            log.error("Failed to parse JSON from LLM", response=resp)
            raise

    async def _stream_internal(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()

        if self.provider in ("openai", "groq"):
            async with client.chat.completions.stream(
                model=self.model or ("gpt-4o" if self.provider == "openai" else "llama3-8b-8192"),
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            ) as stream:
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        elif self.provider == "anthropic":
            async with client.messages.stream(
                model=self.model or "claude-sonnet-4-5",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        elif self.provider == "google":
            import google.generativeai as genai
            model = genai.GenerativeModel(
                self.model or "gemini-2.0-flash",
                system_instruction=system_prompt,
            )
            resp = await model.generate_content_async(
                user_prompt,
                stream=True,
                generation_config=genai.GenerationConfig(temperature=temperature),
            )
            async for chunk in resp:
                if chunk.text:
                    yield chunk.text

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """Streaming completion for chat interfaces with fallback support."""
        iterator = self._stream_internal(system_prompt, user_prompt, temperature)
        try:
            # Try to get the first chunk to test for rate limits early
            first_chunk = await anext(iterator)
            yield first_chunk
            async for chunk in iterator:
                yield chunk
        except Exception as e:
            err_str = str(e).lower()
            if self.provider == "google" and ("429" in err_str or "quota" in err_str or "exhausted" in err_str):
                if settings.XAI_API_KEY:
                    log.warning("Google API rate limit hit on stream. Falling back to Groq.")
                    self.provider = "groq"
                    self.model = "llama3-8b-8192"
                    self._client = None
                    async for chunk in self._stream_internal(system_prompt, user_prompt, temperature):
                        yield chunk
                    return
            raise e


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
