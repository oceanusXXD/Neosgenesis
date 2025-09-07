#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
客户端适配器 - 统一LLM接口的向后兼容层
Client Adapter - Backward compatibility layer for unified LLM interface

这个适配器已简化为直接使用统一的BaseLLMClient接口，
主要提供向后兼容性以及便捷的工厂方法。
"""

import logging
from typing import Optional, Union

from .impl.deepseek_client import DeepSeekClient, ClientConfig, create_llm_client
from .llm_base import BaseLLMClient, LLMConfig, LLMProvider
try:
    from neogenesis_system.config import API_CONFIG
except ImportError:
    try:
        from ..config import API_CONFIG
    except ImportError:
        API_CONFIG = {}

logger = logging.getLogger(__name__)


class DeepSeekClientAdapter(DeepSeekClient):
    """
    DeepSeek客户端适配器 - 简化版
    
    现在主要作为向后兼容层存在，内部使用统一的LLM接口。
    推荐直接使用BaseLLMClient或其具体实现。
    """
    
    def __init__(self, api_key: str = ""):
        """
        初始化适配器 - 兼容原有接口
        
        Args:
            api_key: LLM API密钥（默认为DeepSeek）
        """
        # 创建统一的LLM配置
        llm_config = LLMConfig(
            provider=LLMProvider.DEEPSEEK,
            api_key=api_key,
            model_name="deepseek-chat",
            timeout=API_CONFIG.get("timeout", (30, 180)),
            max_retries=API_CONFIG.get("max_retries", 3),
            retry_delay_base=API_CONFIG.get("retry_delay_base", 2.0),
            temperature=API_CONFIG.get("temperature", 0.7),
            max_tokens=API_CONFIG.get("max_tokens", 2000),
            proxies=API_CONFIG.get("proxies"),
            request_interval=API_CONFIG.get("request_interval", 1.0)
        )
        
        # 调用父类构造函数
        super().__init__(llm_config)
        logger.info("🔄 DeepSeek客户端适配器已初始化（统一接口模式）")
    
    # call_api方法已经在BaseLLMClient中实现，无需重复定义


def create_compatible_client(api_key: str) -> DeepSeekClientAdapter:
    """
    创建兼容性客户端
    
    Args:
        api_key: API密钥
        
    Returns:
        兼容性客户端实例
    """
    return DeepSeekClientAdapter(api_key)


def create_unified_client(api_key: str, **kwargs) -> BaseLLMClient:
    """
    创建统一LLM客户端 - 推荐使用
    
    Args:
        api_key: API密钥
        **kwargs: 其他配置参数
        
    Returns:
        BaseLLMClient实例
    """
    return create_llm_client(api_key, **kwargs)


# 全局客户端实例缓存
_client_cache = {}
_unified_client_cache = {}

def get_or_create_client(api_key: str) -> DeepSeekClientAdapter:
    """
    获取或创建客户端实例（带缓存） - 向后兼容
    
    Args:
        api_key: API密钥
        
    Returns:
        客户端实例
    """
    if api_key not in _client_cache:
        _client_cache[api_key] = create_compatible_client(api_key)
    
    return _client_cache[api_key]


def get_or_create_unified_client(api_key: str, **kwargs) -> BaseLLMClient:
    """
    获取或创建统一客户端实例（带缓存） - 推荐使用
    
    Args:
        api_key: API密钥
        **kwargs: 其他配置参数
        
    Returns:
        BaseLLMClient实例
    """
    cache_key = f"{api_key}_{hash(frozenset(kwargs.items()) if kwargs else frozenset())}"
    
    if cache_key not in _unified_client_cache:
        _unified_client_cache[cache_key] = create_unified_client(api_key, **kwargs)
    
    return _unified_client_cache[cache_key]


def clear_client_cache():
    """清理客户端缓存"""
    global _client_cache, _unified_client_cache
    
    # 清理旧版缓存
    for client in _client_cache.values():
        try:
            client.session.close()
        except:
            pass
    _client_cache.clear()
    
    # 清理统一客户端缓存
    for client in _unified_client_cache.values():
        try:
            if hasattr(client, 'session'):
                client.session.close()
        except:
            pass
    _unified_client_cache.clear()
    
    logger.info("🧹 所有客户端缓存已清理")
