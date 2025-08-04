#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
强化版 DeepSeek API 客户端
Enhanced DeepSeek API Client with advanced features

特性:
- 使用 requests.Session 提高性能
- 配置化的重试逻辑和超时控制
- 精细的错误处理和结构化日志
- 自动 JSON 解析和响应验证
- 流式响应支持
- 请求缓存机制
- 性能监控和统计
"""

import json
import time
import hashlib
import logging
import requests
from typing import Optional, Dict, Any, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

from config import API_CONFIG, DEEPSEEK_CHAT_ENDPOINT, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)


class APIErrorType(Enum):
    """API错误类型枚举"""
    AUTHENTICATION = "authentication_error"
    RATE_LIMIT = "rate_limit_error" 
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    PARSE_ERROR = "parse_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class APIResponse:
    """API响应数据结构"""
    success: bool
    content: str = ""
    raw_response: Optional[Dict[str, Any]] = None
    error_type: Optional[APIErrorType] = None
    error_message: str = ""
    status_code: int = 0
    response_time: float = 0.0
    tokens_used: int = 0
    model_used: str = ""


@dataclass  
class ClientConfig:
    """客户端配置"""
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = DEEPSEEK_MODEL
    timeout: tuple = (30, 180)
    max_retries: int = 3
    retry_delay_base: float = 2.0
    temperature: float = 0.7
    max_tokens: int = 2000
    enable_cache: bool = True
    cache_ttl: int = 300  # 缓存时间(秒)
    enable_metrics: bool = True
    proxies: Optional[Dict[str, str]] = None
    request_interval: float = 1.0  # 🔧 新增：请求间隔时间(秒)


@dataclass
class ClientMetrics:
    """客户端性能指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    total_tokens_used: int = 0
    cache_hits: int = 0
    error_counts: Dict[APIErrorType, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """平均响应时间"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests


class DeepSeekClient:
    """
    强化版 DeepSeek API 客户端
    
    特性:
    - 高性能会话复用
    - 智能重试机制
    - 请求缓存
    - 性能监控
    - 结构化错误处理
    """
    
    def __init__(self, config: ClientConfig):
        """
        初始化客户端
        
        Args:
            config: 客户端配置
        """
        self.config = config
        self.metrics = ClientMetrics()
        
        # 初始化 requests.Session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Neogenesis-System/1.0'
        })
        
        # 配置代理
        if config.proxies:
            self.session.proxies.update(config.proxies)
        
        # 请求缓存
        self._cache: Dict[str, tuple] = {}  # key -> (response, timestamp)
        
        # 🔧 新增：请求频率控制
        self._last_request_time = 0
        self._request_interval = getattr(config, 'request_interval', 1.0)  # 默认1秒间隔
        
        logger.info(f"🚀 DeepSeekClient 初始化完成")
        logger.info(f"   模型: {config.model}")
        logger.info(f"   缓存: {'启用' if config.enable_cache else '禁用'}")
        logger.info(f"   指标: {'启用' if config.enable_metrics else '禁用'}")
        logger.info(f"   请求间隔: {self._request_interval}s")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        system_message: Optional[str] = None,
        enable_cache: Optional[bool] = None
    ) -> APIResponse:
        """
        聊天完成API调用
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            model: 模型名称
            system_message: 系统消息（会自动添加到messages开头）
            enable_cache: 是否启用缓存
            
        Returns:
            API响应对象
        """
        start_time = time.time()
        
        # 参数处理
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        model = model or self.config.model
        enable_cache = enable_cache if enable_cache is not None else self.config.enable_cache
        
        # 添加系统消息
        if system_message:
            messages = [{"role": "system", "content": system_message}] + messages
        
        # 构建请求数据
        request_data = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        # 检查缓存
        cache_key = self._generate_cache_key(request_data)
        if enable_cache and self._is_cache_valid(cache_key):
            cached_response, _ = self._cache[cache_key]
            self.metrics.cache_hits += 1
            logger.debug(f"📋 使用缓存响应: {cache_key[:16]}...")
            return cached_response
        
        # 执行API调用
        response = self._execute_request(request_data, start_time)
        
        # 更新缓存
        if enable_cache and response.success:
            self._cache[cache_key] = (response, time.time())
            self._cleanup_cache()
        
        # 更新指标
        if self.config.enable_metrics:
            self._update_metrics(response)
        
        return response
    
    def simple_chat(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        简化的聊天接口
        
        Args:
            prompt: 用户提示
            system_message: 系统消息
            **kwargs: 其他参数
            
        Returns:
            API响应对象
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(
            messages=messages,
            system_message=system_message,
            **kwargs
        )
    
    def _execute_request(self, request_data: Dict[str, Any], start_time: float) -> APIResponse:
        """
        执行API请求（包含重试逻辑）
        
        Args:
            request_data: 请求数据
            start_time: 开始时间
            
        Returns:
            API响应对象
        """
        # 🔧 请求频率控制 - 确保两次请求之间有足够间隔
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._request_interval:
            wait_time = self._request_interval - time_since_last
            logger.debug(f"⏱️ 请求间隔控制，等待 {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
        
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"🤖 API调用尝试 {attempt + 1}/{self.config.max_retries}")
                
                response = self.session.post(
                    f"{self.config.base_url}/chat/completions",
                    json=request_data,
                    timeout=self.config.timeout
                )
                
                response_time = time.time() - start_time
                
                # 处理成功响应
                if response.status_code == 200:
                    return self._process_success_response(response, response_time)
                
                # 处理错误响应
                error_response = self._process_error_response(response, response_time)
                
                # 决定是否重试
                if not self._should_retry(error_response.error_type, attempt):
                    return error_response
                
                # 计算等待时间并重试
                wait_time = self._calculate_retry_delay(error_response.error_type, attempt)
                logger.warning(f"🔄 等待 {wait_time:.1f}s 后重试...")
                time.sleep(wait_time)
                last_error = error_response
                
            except requests.exceptions.Timeout as e:
                response_time = time.time() - start_time
                last_error = APIResponse(
                    success=False,
                    error_type=APIErrorType.TIMEOUT_ERROR,
                    error_message=f"请求超时: {str(e)}",
                    response_time=response_time
                )
                
                if attempt < self.config.max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"⏱️ 超时重试，等待 {wait_time}s...")
                    time.sleep(wait_time)
                
            except requests.exceptions.ConnectionError as e:
                response_time = time.time() - start_time
                last_error = APIResponse(
                    success=False,
                    error_type=APIErrorType.NETWORK_ERROR,
                    error_message=f"网络连接错误: {str(e)}",
                    response_time=response_time
                )
                
                if attempt < self.config.max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    logger.warning(f"🌐 网络错误重试，等待 {wait_time}s...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                last_error = APIResponse(
                    success=False,
                    error_type=APIErrorType.UNKNOWN_ERROR,
                    error_message=f"未知错误: {str(e)}",
                    response_time=response_time
                )
                
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"❌ 未知错误重试，等待 3s...")
                    time.sleep(3)
        
        # 所有重试失败
        logger.error(f"❌ API调用失败: 所有 {self.config.max_retries} 次重试均失败")
        return last_error or APIResponse(
            success=False,
            error_type=APIErrorType.UNKNOWN_ERROR,
            error_message="所有重试尝试均失败"
        )
    
    def _process_success_response(self, response: requests.Response, response_time: float) -> APIResponse:
        """处理成功响应"""
        try:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # 提取token使用信息
            tokens_used = 0
            if 'usage' in data:
                tokens_used = data['usage'].get('total_tokens', 0)
            
            logger.info(f"✅ API调用成功 ({response_time:.2f}s, {tokens_used} tokens)")
            
            return APIResponse(
                success=True,
                content=content,
                raw_response=data,
                status_code=response.status_code,
                response_time=response_time,
                tokens_used=tokens_used,
                model_used=data.get('model', self.config.model)
            )
            
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"❌ 响应解析失败: {str(e)}")
            return APIResponse(
                success=False,
                error_type=APIErrorType.PARSE_ERROR,
                error_message=f"响应解析失败: {str(e)}",
                status_code=response.status_code,
                response_time=response_time
            )
    
    def _process_error_response(self, response: requests.Response, response_time: float) -> APIResponse:
        """处理错误响应"""
        error_type = APIErrorType.UNKNOWN_ERROR
        error_message = f"HTTP {response.status_code}"
        
        # 根据状态码分类错误
        if response.status_code == 401:
            error_type = APIErrorType.AUTHENTICATION
            error_message = "API密钥认证失败"
        elif response.status_code == 429:
            error_type = APIErrorType.RATE_LIMIT
            error_message = "API调用频率限制"
        elif response.status_code in [500, 502, 503, 504]:
            error_type = APIErrorType.SERVER_ERROR
            error_message = f"服务器错误 {response.status_code}"
        
        # 尝试提取详细错误信息
        try:
            error_data = response.json()
            if 'error' in error_data:
                error_message = error_data['error'].get('message', error_message)
        except:
            pass
        
        logger.error(f"❌ API错误: {error_message} ({response.status_code})")
        
        return APIResponse(
            success=False,
            error_type=error_type,
            error_message=error_message,
            status_code=response.status_code,
            response_time=response_time
        )
    
    def _should_retry(self, error_type: APIErrorType, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.max_retries - 1:
            return False
        
        # 不重试的错误类型
        non_retryable = {
            APIErrorType.AUTHENTICATION,
            APIErrorType.PARSE_ERROR
        }
        
        return error_type not in non_retryable
    
    def _calculate_retry_delay(self, error_type: APIErrorType, attempt: int) -> float:
        """计算重试延迟时间"""
        base_delay = self.config.retry_delay_base
        
        if error_type == APIErrorType.RATE_LIMIT:
            # 限流错误使用指数退避
            return base_delay ** (attempt + 1) * 2
        elif error_type == APIErrorType.SERVER_ERROR:
            # 服务器错误使用线性增长
            return 5 * (attempt + 1)
        else:
            # 其他错误使用基础延迟
            return base_delay * (attempt + 1)
    
    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 将请求数据序列化并生成哈希
        cache_string = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False
        
        _, timestamp = self._cache[cache_key]
        return time.time() - timestamp < self.config.cache_ttl
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.config.cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"🧹 清理了 {len(expired_keys)} 个过期缓存项")
    
    def _update_metrics(self, response: APIResponse):
        """更新性能指标"""
        self.metrics.total_requests += 1
        
        if response.success:
            self.metrics.successful_requests += 1
            self.metrics.total_response_time += response.response_time
            self.metrics.total_tokens_used += response.tokens_used
        else:
            self.metrics.failed_requests += 1
            if response.error_type:
                self.metrics.error_counts[response.error_type] = \
                    self.metrics.error_counts.get(response.error_type, 0) + 1
    
    def get_metrics(self) -> ClientMetrics:
        """获取客户端性能指标"""
        return self.metrics
    
    def reset_metrics(self):
        """重置性能指标"""
        self.metrics = ClientMetrics()
        logger.info("📊 性能指标已重置")
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("🧹 缓存已清空")
    
    @contextmanager
    def batch_mode(self):
        """批量模式上下文管理器（可以添加批量优化逻辑）"""
        logger.debug("🔄 进入批量模式")
        try:
            yield self
        finally:
            logger.debug("✅ 退出批量模式")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """清理资源"""
        self.session.close()
        logger.debug("🔄 DeepSeekClient 资源已清理")


# 工厂函数和便捷接口
def create_client(api_key: str, **kwargs) -> DeepSeekClient:
    """
    创建 DeepSeek 客户端的工厂函数
    
    Args:
        api_key: API密钥
        **kwargs: 其他配置参数
        
    Returns:
        DeepSeekClient 实例
    """
    config = ClientConfig(api_key=api_key, **kwargs)
    return DeepSeekClient(config)


def quick_chat(api_key: str, prompt: str, system_message: Optional[str] = None) -> str:
    """
    快速聊天便捷函数
    
    Args:
        api_key: API密钥
        prompt: 用户提示
        system_message: 系统消息
        
    Returns:
        AI响应内容
        
    Raises:
        Exception: API调用失败时抛出异常
    """
    with create_client(api_key) as client:
        response = client.simple_chat(prompt, system_message)
        if response.success:
            return response.content
        else:
            raise Exception(f"API调用失败: {response.error_message}")