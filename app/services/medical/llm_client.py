"""
LLM Client Service

This module provides a client for interfacing with Groq LLM provider.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import httpx
from groq import AsyncGroq
from loguru import logger

from app.config import settings
from app.core.exceptions import LLMServiceError
from app.utils.metrics import record_llm_metrics

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    LOCAL = "local"

@dataclass
class LLMRequest:
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    model: Optional[str] = None

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, Any]
    finish_reason: Optional[str]
    response_time: float
    provider: str

class LLMClient:
    async def health_check(self) -> dict:
        """Dummy health check for LLMClient."""
        return {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "provider": str(self.provider)
        }
    """
    Client for interfacing with Groq LLM provider.
    """
    def __init__(self):
        self.provider = LLMProvider(settings.LLM_PROVIDER) if not isinstance(settings.LLM_PROVIDER, LLMProvider) else settings.LLM_PROVIDER
        self.clients: Dict[LLMProvider, Any] = {}
        self.models: Dict[LLMProvider, str] = {
            LLMProvider.GROQ: settings.GROQ_MODEL,
            LLMProvider.LOCAL: settings.LOCAL_MODEL
        }
        self._initialize_clients()

    def _initialize_clients(self):
        try:
            if settings.GROQ_API_KEY:
                self.clients[LLMProvider.GROQ] = AsyncGroq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq client initialized")
            if settings.LOCAL_MODEL_ENDPOINT:
                self.clients[LLMProvider.LOCAL] = settings.LOCAL_MODEL_ENDPOINT
                logger.info("Local model client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM clients: {e}")
            raise LLMServiceError(
                f"LLM client initialization failed: {e}",
                provider=str(self.provider)
            ) from e

    async def generate(
        self, 
        request: LLMRequest,
        provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        provider = LLMProvider(provider) if provider and not isinstance(provider, LLMProvider) else (provider or self.provider)
        start_time = time.time()
        try:
            if provider == LLMProvider.GROQ:
                response = await self._generate_groq(request)
            elif provider == LLMProvider.LOCAL:
                response = await self._generate_local(request)
            else:
                raise LLMServiceError(
                    f"Unsupported provider: {provider}",
                    provider=str(provider)
                )
            response_time = time.time() - start_time
            response.response_time = response_time
            # Record LLM metrics
            tokens_used = response.usage.get("total_tokens", 0)
            await record_llm_metrics(
                request_id="llm",
                model=request.model or self.models[provider],
                provider=provider.value,
                duration=response_time,
                success=True,
                tokens_used=tokens_used
            )
            logger.info(f"LLM generation completed in {response_time:.2f}s using {provider}")
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMServiceError(
                f"LLM generation failed: {e}",
                provider=str(provider)
            ) from e

    async def streaming_generate(
        self,
        request: LLMRequest,
        provider: Optional[LLMProvider] = None
    ):
        """Stream LLM response chunks. Only supported for Groq."""
        provider = LLMProvider(provider) if provider and not isinstance(provider, LLMProvider) else (provider or self.provider)
        
        if provider != LLMProvider.GROQ:
            raise LLMServiceError(f"Streaming not supported for provider: {provider}")
        
        try:
            client = self.clients[LLMProvider.GROQ]
            model = request.model or self.models[LLMProvider.GROQ]
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise LLMServiceError(
                f"Streaming generation failed: {e}",
                provider=str(provider)
            ) from e

    async def _generate_groq(self, request: LLMRequest) -> LLMResponse:
        client = self.clients[LLMProvider.GROQ]
        model = request.model or self.models[LLMProvider.GROQ]
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stream=request.stream
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=response.choices[0].finish_reason,
            response_time=0.0,
            provider=LLMProvider.GROQ.value
        )

    async def _generate_local(self, request: LLMRequest) -> LLMResponse:
        endpoint = self.clients[LLMProvider.LOCAL]
        model = request.model or self.models[LLMProvider.LOCAL]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system_prompt} if request.system_prompt else None,
                {"role": "user", "content": request.prompt}
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stop": request.stop_sequences,
            "stream": request.stream
        }
        payload["messages"] = [msg for msg in payload["messages"] if msg is not None]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/v1/chat/completions",
                json=payload,
                timeout=settings.LLM_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            usage=data["usage"],
            finish_reason=data["choices"][0]["finish_reason"],
            response_time=0.0,
            provider=LLMProvider.LOCAL.value
        )
