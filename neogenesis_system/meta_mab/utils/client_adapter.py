#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
客户端适配器 - 提供向后兼容的接口
Client Adapter - provides backward compatibility interface

这个适配器允许现有代码无缝使用强化版 DeepSeekClient，
同时保持与原 DeepSeekAPICaller 相同的接口。
"""

import logging
from typing import Optional

from .deepseek_client import DeepSeekClient, ClientConfig, APIResponse
from config import API_CONFIG

logger = logging.getLogger(__name__)


class DeepSeekClientAdapter(DeepSeekClient):
    """
    DeepSeek客户端适配器
    
    提供与原 DeepSeekAPICaller 兼容的接口，
    但底层使用强化版 DeepSeekClient 实现。
    """
    
    def __init__(self, api_key: str = ""):
        """
        初始化适配器
        
        Args:
            api_key: DeepSeek API密钥
        """
        # 从现有配置创建客户端配置
        config = ClientConfig(
            api_key=api_key,
            timeout=API_CONFIG.get("timeout", (30, 180)),
            max_retries=API_CONFIG.get("max_retries", 3),
            retry_delay_base=API_CONFIG.get("retry_delay_base", 2.0),
            temperature=API_CONFIG.get("temperature", 0.7),
            max_tokens=API_CONFIG.get("max_tokens", 2000),
            proxies=API_CONFIG.get("proxies"),
            request_interval=API_CONFIG.get("request_interval", 1.0)  # 🔧 新增请求间隔配置
        )
        
        super().__init__(config)
        logger.info("🔄 DeepSeek客户端适配器已初始化（兼容模式）")
    
    def call_api(self, prompt: str, temperature: float = None, 
                 system_message: str = None) -> str:
        """
        兼容原 DeepSeekAPICaller.call_api 接口
        
        Args:
            prompt: 用户提示
            temperature: 温度参数
            system_message: 系统消息
            
        Returns:
            API响应内容
            
        Raises:
            ConnectionError: 所有重试失败后抛出
        """
        # 使用默认系统消息（与原版保持一致）
        if system_message is None:
            system_message = "你是一个智能决策维度分析师。请分析给定任务，识别关键决策维度。"
        
        logger.info(f"🤖 开始DeepSeek API调用: {prompt[:30]}...")
        
        # 调用强化版客户端
        response = self.simple_chat(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature
        )
        
        # 兼容原版的异常处理
        if response.success:
            logger.info("✅ DeepSeek API调用成功")
            return response.content
        else:
            logger.error("❌ DeepSeek API调用失败: 所有重试尝试均失败")
            raise ConnectionError("DeepSeek API调用失败: 所有重试尝试均失败")


def create_compatible_client(api_key: str) -> DeepSeekClientAdapter:
    """
    创建兼容性客户端
    
    Args:
        api_key: API密钥
        
    Returns:
        兼容性客户端实例
    """
    return DeepSeekClientAdapter(api_key)


# 全局客户端实例缓存
_client_cache = {}

def get_or_create_client(api_key: str) -> DeepSeekClientAdapter:
    """
    获取或创建客户端实例（带缓存）
    
    Args:
        api_key: API密钥
        
    Returns:
        客户端实例
    """
    if api_key not in _client_cache:
        _client_cache[api_key] = create_compatible_client(api_key)
    
    return _client_cache[api_key]


def clear_client_cache():
    """清理客户端缓存"""
    global _client_cache
    for client in _client_cache.values():
        try:
            client.session.close()
        except:
            pass
    _client_cache.clear()
    logger.info("🧹 客户端缓存已清理")