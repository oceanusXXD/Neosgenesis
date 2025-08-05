#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM提供商模块 - 支持多种LLM服务提供商
LLM Providers Module - Support for multiple LLM service providers
"""

from ..llm_base import BaseLLMClient, LLMConfig, LLMProvider

# 导入具体的提供商实现
try:
    from .openai_client import OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .anthropic_client import AnthropicClient
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from .ollama_client import OllamaClient
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# 从deepseek_client导入
from ..utils.deepseek_client import DeepSeekClient

# 提供商注册表
PROVIDER_REGISTRY = {
    LLMProvider.DEEPSEEK: DeepSeekClient,
}

# 根据可用性注册提供商
if OPENAI_AVAILABLE:
    PROVIDER_REGISTRY[LLMProvider.OPENAI] = OpenAIClient
    PROVIDER_REGISTRY[LLMProvider.AZURE_OPENAI] = OpenAIClient

if ANTHROPIC_AVAILABLE:
    PROVIDER_REGISTRY[LLMProvider.ANTHROPIC] = AnthropicClient

if OLLAMA_AVAILABLE:
    PROVIDER_REGISTRY[LLMProvider.OLLAMA] = OllamaClient


def create_llm_client(provider: LLMProvider, config: LLMConfig) -> BaseLLMClient:
    """
    创建LLM客户端的工厂函数
    
    Args:
        provider: LLM提供商
        config: LLM配置
        
    Returns:
        BaseLLMClient: 客户端实例
        
    Raises:
        ValueError: 当提供商不支持时
    """
    if provider not in PROVIDER_REGISTRY:
        available_providers = list(PROVIDER_REGISTRY.keys())
        raise ValueError(f"不支持的LLM提供商: {provider.value}. 可用提供商: {[p.value for p in available_providers]}")
    
    client_class = PROVIDER_REGISTRY[provider]
    return client_class(config)


def get_available_providers() -> list[LLMProvider]:
    """
    获取可用的LLM提供商列表
    
    Returns:
        list[LLMProvider]: 可用的提供商列表
    """
    return list(PROVIDER_REGISTRY.keys())


def is_provider_available(provider: LLMProvider) -> bool:
    """
    检查提供商是否可用
    
    Args:
        provider: LLM提供商
        
    Returns:
        bool: 是否可用
    """
    return provider in PROVIDER_REGISTRY


__all__ = [
    'BaseLLMClient',
    'LLMConfig', 
    'LLMProvider',
    'create_llm_client',
    'get_available_providers',
    'is_provider_available',
    'PROVIDER_REGISTRY'
]