from enum import Enum
from typing import Optional
from langchain_core.language_models import BaseChatModel
from app.core.config import settings


class ModelRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    COMPACTOR = "compactor"


# 各供应商的模型配置（模型名 + 默认参数）
PROVIDER_CONFIG = {
    "anthropic": {
        ModelRole.ORCHESTRATOR: {"model": "claude-sonnet-4-6", "temperature": 0.3, "max_tokens": 1024},
        ModelRole.WORKER: {"model": "claude-haiku-4-5-20251001", "temperature": 0.2, "max_tokens": 512},
        ModelRole.COMPACTOR: {"model": "claude-haiku-4-5-20251001", "temperature": 0.1, "max_tokens": 256},
    },
    "openai": {
        ModelRole.ORCHESTRATOR: {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 1024},
        ModelRole.WORKER: {"model": "gpt-4o-mini", "temperature": 0.2, "max_tokens": 512},
        ModelRole.COMPACTOR: {"model": "gpt-4o-mini", "temperature": 0.1, "max_tokens": 256},
    },
    "qwen": {
        ModelRole.ORCHESTRATOR: {"model": "qwen-plus", "temperature": 0.3, "max_tokens": 1024},
        ModelRole.WORKER: {"model": "qwen-turbo", "temperature": 0.2, "max_tokens": 512},
        ModelRole.COMPACTOR: {"model": "qwen-turbo", "temperature": 0.1, "max_tokens": 256},
    },
}


class LLMFactory:
    _cache: dict[str, BaseChatModel] = {}

    @classmethod
    def create(
        cls,
        role: ModelRole,
        provider: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> BaseChatModel:
        """
        创建 LLM 实例
        
        Args:
            role: 模型角色 (orchestrator/worker/compactor)
            provider: 供应商，默认从 settings.LLM_PROVIDER 读取
            use_cache: 是否缓存实例复用
            **kwargs: 覆盖默认参数
        """
        provider = provider or settings.LLM_PROVIDER
        
        cache_key = f"{provider}:{role.value}"
        if use_cache and not kwargs and cache_key in cls._cache:
            return cls._cache[cache_key]
        
        llm = cls._create_llm(provider, role, **kwargs)
        
        if use_cache and not kwargs:
            cls._cache[cache_key] = llm
        return llm

    @classmethod
    def _create_llm(cls, provider: str, role: ModelRole, **kwargs) -> BaseChatModel:
        if provider not in PROVIDER_CONFIG:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDER_CONFIG.keys())}")
        
        config = {**PROVIDER_CONFIG[provider][role], **kwargs}
        
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(api_key=settings.ANTHROPIC_API_KEY, **config)
        
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(api_key=settings.OPENAI_API_KEY, **config)
        
        elif provider == "qwen":
            from langchain_community.chat_models import ChatTongyi
            config.pop("max_tokens", None)  # Tongyi 用 max_output_tokens
            return ChatTongyi(
                api_key=settings.DASHSCOPE_API_KEY,
                **config
            )
        
        raise ValueError(f"Provider {provider} not implemented")

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()
