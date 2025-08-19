#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM管理器 - 统一管理多个LLM提供商
LLM Manager - Unified management for multiple LLM providers
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict

from .llm_base import BaseLLMClient, LLMConfig, LLMProvider, LLMResponse, LLMMessage
from .providers import create_llm_client, get_available_providers, is_provider_available
from config import (
    LLM_PROVIDERS_CONFIG, DEFAULT_LLM_CONFIG, LLM_MANAGER_CONFIG, 
    COST_CONTROL_CONFIG, FEATURE_FLAGS
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderStatus:
    """提供商状态"""
    name: str
    enabled: bool
    healthy: bool
    last_check: float
    error_count: int
    success_count: int
    avg_response_time: float
    last_error: Optional[str] = None


class LLMManager:
    """
    LLM管理器 - 统一管理多个LLM提供商
    
    功能：
    - 自动发现和初始化可用的LLM提供商
    - 智能路由和负载均衡
    - 自动回退机制
    - 成本跟踪和控制
    - 健康检查和监控
    """
    
    def __init__(self):
        """初始化LLM管理器"""
        self.providers: Dict[str, BaseLLMClient] = {}
        self.provider_status: Dict[str, ProviderStatus] = {}
        self.config = DEFAULT_LLM_CONFIG.copy()
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_count': 0,
            'provider_usage': defaultdict(int),
            'cost_tracking': defaultdict(float),
            'request_history': []
        }
        
        # 初始化状态
        self.initialized = False
        self.last_health_check = 0
        
        logger.info("🚀 LLM管理器初始化开始")
        self._initialize_providers()
        
    def _initialize_providers(self):
        """初始化可用的提供商"""
        if not FEATURE_FLAGS.get("enable_multi_llm_support", False):
            logger.info("📋 多LLM支持已禁用，仅使用DeepSeek")
            self._initialize_single_provider()
            return
        
        initialized_count = 0
        
        for provider_name, provider_config in LLM_PROVIDERS_CONFIG.items():
            try:
                if not provider_config.get("enabled", False):
                    logger.debug(f"⏭️ 跳过禁用的提供商: {provider_name}")
                    continue
                
                # 检查API密钥
                api_key_env = provider_config.get("api_key_env")
                api_key = ""
                
                if api_key_env:
                    api_key = os.getenv(api_key_env, "")
                    if not api_key:
                        logger.warning(f"⚠️ 未找到{provider_name}的API密钥: {api_key_env}")
                        continue
                
                # 创建LLM配置
                llm_config = self._create_llm_config(provider_name, provider_config, api_key)
                
                # 创建客户端
                client = create_llm_client(llm_config.provider, llm_config)
                
                # 快速健康检查
                if self._quick_health_check(client, provider_name):
                    self.providers[provider_name] = client
                    self.provider_status[provider_name] = ProviderStatus(
                        name=provider_name,
                        enabled=True,
                        healthy=True,
                        last_check=time.time(),
                        error_count=0,
                        success_count=1,
                        avg_response_time=0.0
                    )
                    initialized_count += 1
                    logger.info(f"✅ {provider_name}提供商初始化成功")
                else:
                    logger.warning(f"❌ {provider_name}提供商健康检查失败")
                    
            except Exception as e:
                logger.error(f"❌ 初始化{provider_name}提供商失败: {e}")
                continue
        
        if initialized_count == 0:
            logger.warning("⚠️ 没有可用的LLM提供商，回退到单一提供商模式")
            self._initialize_single_provider()
        else:
            logger.info(f"🎉 LLM管理器初始化完成，可用提供商: {initialized_count}个")
            self.initialized = True
    
    def _initialize_single_provider(self):
        """初始化单一提供商（DeepSeek）"""
        try:
            from .utils.client_adapter import get_or_create_unified_client
            
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                logger.error("❌ 未找到DEEPSEEK_API_KEY环境变量")
                return
            
            client = get_or_create_unified_client(api_key)
            self.providers["deepseek"] = client
            self.provider_status["deepseek"] = ProviderStatus(
                name="deepseek",
                enabled=True,
                healthy=True,
                last_check=time.time(),
                error_count=0,
                success_count=1,
                avg_response_time=0.0
            )
            
            logger.info("✅ 单一提供商模式初始化成功 (DeepSeek)")
            self.initialized = True
            
        except Exception as e:
            logger.error(f"❌ 单一提供商初始化失败: {e}")
    
    def _create_llm_config(self, provider_name: str, provider_config: Dict, api_key: str) -> LLMConfig:
        """创建LLM配置"""
        provider_type = provider_config["provider_type"]
        provider_enum = LLMProvider(provider_type)
        
        # 特殊处理Azure OpenAI
        extra_params = {}
        base_url = provider_config.get("base_url")
        
        if provider_type == "azure_openai":
            azure_endpoint = os.getenv(provider_config.get("azure_endpoint_env", ""), "")
            if azure_endpoint:
                base_url = azure_endpoint
                extra_params["api_version"] = provider_config.get("api_version", "2024-02-15-preview")
        
        return LLMConfig(
            provider=provider_enum,
            api_key=api_key,
            model_name=provider_config["default_model"],
            temperature=provider_config.get("temperature", 0.7),
            max_tokens=provider_config.get("max_tokens", 2000),
            base_url=base_url,
            timeout=tuple(provider_config.get("timeout", (30, 120))),
            max_retries=provider_config.get("max_retries", 3),
            retry_delay_base=provider_config.get("retry_delay_base", 2.0),
            request_interval=provider_config.get("request_interval", 1.0),
            extra_params=extra_params
        )
    
    def _quick_health_check(self, client: BaseLLMClient, provider_name: str) -> bool:
        """快速健康检查"""
        try:
            # 简单的配置验证
            return client.validate_config()
        except Exception as e:
            logger.debug(f"🔍 {provider_name}健康检查失败: {e}")
            return False
    
    def call_api(self, prompt: str, 
                 system_message: Optional[str] = None,
                 temperature: Optional[float] = None,
                 **kwargs) -> str:
        """
        简化的API调用接口 - 兼容现有代码
        
        Args:
            prompt: 用户提示
            system_message: 系统消息
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            str: LLM响应内容
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        try:
            # 构建消息格式
            messages = []
            if system_message:
                messages.append(LLMMessage(role="system", content=system_message))
            messages.append(LLMMessage(role="user", content=prompt))
            
            # 调用chat_completion
            response = self.chat_completion(
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            
            if response.success:
                return response.content
            else:
                raise Exception(f"LLM调用失败: {response.error_message}")
                
        except Exception as e:
            logger.error(f"❌ LLM API调用失败: {e}")
            raise
    
    def chat_completion(self, 
                       messages: Union[str, List[LLMMessage]], 
                       provider_name: Optional[str] = None,
                       temperature: Optional[float] = None,
                       **kwargs) -> LLMResponse:
        """
        聊天完成 - 智能路由到最佳提供商
        
        Args:
            messages: 消息内容
            provider_name: 指定提供商（可选）
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 统一响应
        """
        self.stats['total_requests'] += 1
        
        if not self.initialized or not self.providers:
            return self._create_error_response("没有可用的LLM提供商")
        
        # 处理直接传入字符串的情况
        if isinstance(messages, str):
            messages = [LLMMessage(role="user", content=messages)]
        
        # 选择提供商
        selected_provider = self._select_provider(provider_name)
        if not selected_provider:
            return self._create_error_response("无法选择合适的提供商")
        
        # 添加temperature到kwargs中
        if temperature is not None:
            kwargs['temperature'] = temperature
        
        # 执行请求（带回退机制）
        return self._execute_with_fallback(selected_provider, messages, **kwargs)
    
    def _select_provider(self, preferred_provider: Optional[str] = None) -> Optional[str]:
        """选择提供商"""
        # 如果指定了提供商且可用，直接使用
        if preferred_provider and preferred_provider in self.providers:
            if self.provider_status[preferred_provider].healthy:
                return preferred_provider
        
        # 检查主要提供商设置
        primary = self.config.get("primary_provider", "auto")
        
        if primary == "auto":
            # 自动选择：按首选顺序选择第一个可用的提供商
            preferred_order = self.config.get("preferred_providers", ["deepseek", "openai", "anthropic"])
            for provider_name in preferred_order:
                if provider_name in self.providers and self.provider_status[provider_name].healthy:
                    return provider_name
        else:
            # 使用指定的主要提供商
            if primary in self.providers and self.provider_status[primary].healthy:
                return primary
        
        # 使用第一个健康的提供商
        for name, status in self.provider_status.items():
            if status.healthy and name in self.providers:
                return name
        
        return None
    
    def _execute_with_fallback(self, provider_name: str, messages: Union[str, List[LLMMessage]], **kwargs) -> LLMResponse:
        """执行请求（带回退机制）"""
        providers_to_try = [provider_name]
        
        # 添加回退提供商
        if self.config.get("auto_fallback", True):
            fallback_providers = self.config.get("fallback_providers", [])
            for fallback in fallback_providers:
                if fallback != provider_name and fallback in self.providers:
                    providers_to_try.append(fallback)
        
        last_error = None
        
        for current_provider in providers_to_try:
            try:
                if not self.provider_status[current_provider].healthy:
                    continue
                
                start_time = time.time()
                client = self.providers[current_provider]
                
                logger.info(f"🤖 使用提供商: {current_provider}")
                response = client.chat_completion(messages, **kwargs)
                
                response_time = time.time() - start_time
                
                if response.success:
                    # 更新统计
                    self._update_provider_stats(current_provider, True, response_time)
                    self.stats['successful_requests'] += 1
                    self.stats['provider_usage'][current_provider] += 1
                    
                    # 成本跟踪
                    if response.usage and COST_CONTROL_CONFIG.get("token_usage_tracking", True):
                        self._track_cost(current_provider, response.usage)
                    
                    return response
                else:
                    # 记录失败但继续尝试下一个提供商
                    self._update_provider_stats(current_provider, False, response_time)
                    last_error = response.error_message
                    logger.warning(f"⚠️ {current_provider}请求失败: {last_error}")
                    
                    if len(providers_to_try) > 1:
                        self.stats['fallback_count'] += 1
                        continue
                    else:
                        return response
                        
            except Exception as e:
                self._update_provider_stats(current_provider, False, 0)
                last_error = str(e)
                logger.error(f"❌ {current_provider}执行异常: {e}")
                continue
        
        # 所有提供商都失败
        self.stats['failed_requests'] += 1
        return self._create_error_response(f"所有提供商都不可用: {last_error}")
    
    def _update_provider_stats(self, provider_name: str, success: bool, response_time: float):
        """更新提供商统计"""
        if provider_name not in self.provider_status:
            return
        
        status = self.provider_status[provider_name]
        status.last_check = time.time()
        
        if success:
            status.success_count += 1
            status.error_count = 0  # 重置错误计数
            status.healthy = True
            
            # 更新平均响应时间
            if status.avg_response_time == 0:
                status.avg_response_time = response_time
            else:
                status.avg_response_time = (status.avg_response_time + response_time) / 2
        else:
            status.error_count += 1
            
            # 连续错误过多时标记为不健康
            if status.error_count >= 3:
                status.healthy = False
                logger.warning(f"⚠️ {provider_name}被标记为不健康")
    
    def _track_cost(self, provider_name: str, usage):
        """跟踪成本"""
        try:
            provider_config = LLM_PROVIDERS_CONFIG.get(provider_name, {})
            cost_per_1k = provider_config.get("cost_per_1k_tokens", {})
            
            input_cost = (usage.prompt_tokens / 1000) * cost_per_1k.get("input", 0)
            output_cost = (usage.completion_tokens / 1000) * cost_per_1k.get("output", 0)
            total_cost = input_cost + output_cost
            
            self.stats['cost_tracking'][provider_name] += total_cost
            
            logger.debug(f"💰 {provider_name}成本: ${total_cost:.6f}")
            
        except Exception as e:
            logger.debug(f"❌ 成本跟踪失败: {e}")
    
    def _create_error_response(self, error_message: str) -> LLMResponse:
        """创建错误响应"""
        from .llm_base import LLMErrorType, create_error_response
        return create_error_response(
            provider="llm_manager",
            error_type=LLMErrorType.UNKNOWN_ERROR,
            error_message=error_message
        )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """获取提供商状态"""
        return {
            'initialized': self.initialized,
            'total_providers': len(self.providers),
            'healthy_providers': sum(1 for s in self.provider_status.values() if s.healthy),
            'providers': {name: {
                'enabled': status.enabled,
                'healthy': status.healthy,
                'success_count': status.success_count,
                'error_count': status.error_count,
                'avg_response_time': status.avg_response_time,
                'last_error': status.last_error
            } for name, status in self.provider_status.items()},
            'stats': self.stats.copy()
        }
    
    def get_available_models(self, provider_name: Optional[str] = None) -> Dict[str, List[str]]:
        """获取可用模型"""
        if provider_name:
            if provider_name in self.providers:
                return {provider_name: self.providers[provider_name].get_available_models()}
            else:
                return {}
        
        return {
            name: client.get_available_models() 
            for name, client in self.providers.items()
        }
    
    def switch_primary_provider(self, provider_name: str) -> bool:
        """切换主要提供商"""
        if provider_name in self.providers and self.provider_status[provider_name].healthy:
            self.config["primary_provider"] = provider_name
            logger.info(f"🔄 主要提供商已切换到: {provider_name}")
            return True
        return False
    
    def health_check(self, force: bool = False) -> Dict[str, bool]:
        """健康检查"""
        current_time = time.time()
        check_interval = LLM_MANAGER_CONFIG.get("health_check_interval", 300)
        
        if not force and (current_time - self.last_health_check) < check_interval:
            return {name: status.healthy for name, status in self.provider_status.items()}
        
        logger.info("🔍 执行LLM提供商健康检查")
        results = {}
        
        for name, client in self.providers.items():
            try:
                healthy = self._quick_health_check(client, name)
                self.provider_status[name].healthy = healthy
                results[name] = healthy
                logger.debug(f"🔍 {name}: {'✅' if healthy else '❌'}")
            except Exception as e:
                self.provider_status[name].healthy = False
                results[name] = False
                logger.error(f"🔍 {name}健康检查异常: {e}")
        
        self.last_health_check = current_time
        return results
