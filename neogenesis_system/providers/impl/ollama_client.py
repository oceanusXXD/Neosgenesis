#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ollama客户端实现 - 统一LLM接口
Ollama Client Implementation - Unified LLM Interface for local models
"""

import time
import logging
import requests
import json
import asyncio
import aiohttp
from typing import List, Optional, Union, Dict, Any

from ..llm_base import (
    BaseLLMClient, LLMConfig, LLMResponse, LLMMessage, LLMUsage, 
    LLMProvider, LLMErrorType, create_error_response
)

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """
    Ollama客户端 - 实现统一LLM接口
    
    支持:
    - 本地运行的开源模型
    - Llama、Mistral、CodeLlama等
    - 快速本地推理
    - 离线使用
    """
    
    def __init__(self, config: LLMConfig):
        """
        初始化Ollama客户端
        
        Args:
            config: LLM配置对象
        """
        super().__init__(config)
        
        # 设置Ollama服务器地址
        self.base_url = config.base_url or "http://localhost:11434"
        self.session = requests.Session()
        
        # 设置超时
        self.timeout = config.timeout[1] if isinstance(config.timeout, tuple) else config.timeout
        
        logger.info(f"🤖 Ollama客户端已初始化: {config.model_name} @ {self.base_url}")
    
    def chat_completion(self, 
                       messages: Union[str, List[LLMMessage]], 
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       **kwargs) -> LLMResponse:
        """
        Ollama聊天完成接口实现
        
        Args:
            messages: 消息内容
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 统一的响应对象
        """
        start_time = time.time()
        
        try:
            # 准备消息格式
            prepared_messages = self._prepare_messages(messages)
            
            # 转换为Ollama API格式
            ollama_messages = []
            for msg in prepared_messages:
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 构建请求参数
            request_data = {
                "model": kwargs.get('model') or self.config.model_name,
                "messages": ollama_messages,
                "stream": False,  # 不使用流式响应
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens
                }
            }
            
            # 调用Ollama API
            logger.debug(f"🤖 调用Ollama API: {request_data['model']}")
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=request_data,
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            # 检查响应状态
            if response.status_code != 200:
                return self._handle_error_response(response, response_time)
            
            # 解析响应
            response_data = response.json()
            content = response_data.get("message", {}).get("content", "")
            
            # 构建使用统计（Ollama通常不返回详细的token统计）
            usage = None
            if "usage" in response_data:
                usage_data = response_data["usage"]
                usage = LLMUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0)
                )
            
            # 构建响应对象
            llm_response = LLMResponse(
                success=True,
                content=content,
                provider=self.provider.value,
                model=request_data["model"],
                response_time=response_time,
                usage=usage,
                finish_reason=response_data.get("done_reason"),
                raw_response=response_data
            )
            
            # 更新统计
            self._update_stats(llm_response)
            
            logger.info(f"✅ Ollama API调用成功: {content[:50]}...")
            return llm_response
            
        except requests.exceptions.ConnectionError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.NETWORK_ERROR,
                error_message=f"无法连接到Ollama服务器: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama连接失败: {e}")
            return error_response
            
        except requests.exceptions.Timeout as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.TIMEOUT_ERROR,
                error_message=f"Ollama请求超时: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama请求超时: {e}")
            return error_response
            
        except json.JSONDecodeError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.PARSE_ERROR,
                error_message=f"Ollama响应解析失败: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama响应解析失败: {e}")
            return error_response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.UNKNOWN_ERROR,
                error_message=f"Ollama未知错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama未知错误: {e}")
            return error_response
    
    async def achat_completion(self, 
                              messages: Union[str, List[LLMMessage]], 
                              temperature: Optional[float] = None,
                              max_tokens: Optional[int] = None,
                              **kwargs) -> LLMResponse:
        """
        Ollama异步聊天完成接口实现
        
        Args:
            messages: 消息内容
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 统一的响应对象
        """
        start_time = time.time()
        
        try:
            # 准备消息格式
            prepared_messages = self._prepare_messages(messages)
            
            # 转换为Ollama API格式
            ollama_messages = []
            for msg in prepared_messages:
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 构建请求参数
            request_data = {
                "model": kwargs.get('model') or self.config.model_name,
                "messages": ollama_messages,
                "stream": False,  # 不使用流式响应
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens
                }
            }
            
            # 异步调用Ollama API
            logger.debug(f"🤖 异步调用Ollama API: {request_data['model']}")
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=request_data
                ) as response:
                    response_time = time.time() - start_time
                    
                    # 检查响应状态
                    if response.status != 200:
                        return await self._handle_async_error_response(response, response_time)
                    
                    # 解析响应
                    response_data = await response.json()
                    content = response_data.get("message", {}).get("content", "")
                    
                    # 构建使用统计（Ollama通常不返回详细的token统计）
                    usage = None
                    if "usage" in response_data:
                        usage_data = response_data["usage"]
                        usage = LLMUsage(
                            prompt_tokens=usage_data.get("prompt_tokens", 0),
                            completion_tokens=usage_data.get("completion_tokens", 0),
                            total_tokens=usage_data.get("total_tokens", 0)
                        )
                    
                    # 构建响应对象
                    llm_response = LLMResponse(
                        success=True,
                        content=content,
                        provider=self.provider.value,
                        model=request_data["model"],
                        response_time=response_time,
                        usage=usage,
                        finish_reason=response_data.get("done_reason"),
                        raw_response=response_data
                    )
                    
                    # 更新统计
                    self._update_stats(llm_response)
                    
                    logger.info(f"✅ Ollama异步API调用成功: {content[:50]}...")
                    return llm_response
            
        except asyncio.TimeoutError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.TIMEOUT_ERROR,
                error_message=f"Ollama异步请求超时: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama异步请求超时: {e}")
            return error_response
            
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.NETWORK_ERROR,
                error_message=f"Ollama异步网络错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama异步网络错误: {e}")
            return error_response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.UNKNOWN_ERROR,
                error_message=f"Ollama异步未知错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Ollama异步未知错误: {e}")
            return error_response
    
    async def _handle_async_error_response(self, response: aiohttp.ClientResponse, response_time: float) -> LLMResponse:
        """处理异步错误响应"""
        error_type = LLMErrorType.UNKNOWN_ERROR
        
        if response.status == 404:
            error_type = LLMErrorType.MODEL_ERROR
            error_message = f"模型未找到: {self.config.model_name}"
        elif response.status == 400:
            error_type = LLMErrorType.INVALID_REQUEST
            error_message = "请求参数无效"
        elif response.status >= 500:
            error_type = LLMErrorType.SERVER_ERROR
            error_message = f"Ollama服务器错误: {response.status}"
        else:
            error_message = f"HTTP错误: {response.status}"
        
        try:
            error_data = await response.json()
            if "error" in error_data:
                error_message = error_data["error"]
        except:
            pass
        
        return create_error_response(
            provider=self.provider.value,
            error_type=error_type,
            error_message=error_message,
            response_time=response_time
        )
    
    def _handle_error_response(self, response: requests.Response, response_time: float) -> LLMResponse:
        """处理错误响应"""
        error_type = LLMErrorType.UNKNOWN_ERROR
        
        if response.status_code == 404:
            error_type = LLMErrorType.MODEL_ERROR
            error_message = f"模型未找到: {self.config.model_name}"
        elif response.status_code == 400:
            error_type = LLMErrorType.INVALID_REQUEST
            error_message = "请求参数无效"
        elif response.status_code >= 500:
            error_type = LLMErrorType.SERVER_ERROR
            error_message = f"Ollama服务器错误: {response.status_code}"
        else:
            error_message = f"HTTP错误: {response.status_code}"
        
        try:
            error_data = response.json()
            if "error" in error_data:
                error_message = error_data["error"]
        except:
            pass
        
        return create_error_response(
            provider=self.provider.value,
            error_type=error_type,
            error_message=error_message,
            response_time=response_time
        )
    
    def validate_config(self) -> bool:
        """
        验证Ollama配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 基础配置验证 - 不进行实际网络调用
            if not hasattr(self.config, 'model_name') or not self.config.model_name:
                logger.debug("❌ Ollama模型名称未设置")
                return False
            
            # 检查base_url格式
            base_url = getattr(self, 'base_url', None) or getattr(self.config, 'base_url', None)
            if base_url:
                if not (base_url.startswith('http://') or base_url.startswith('https://')):
                    logger.debug("❌ Ollama base_url格式无效")
                    return False
            
            logger.debug("✅ Ollama基础配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ollama配置验证失败: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            List[str]: 可用的模型名称列表
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                logger.error(f"❌ 获取Ollama模型列表失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取Ollama模型列表失败: {e}")
            # 返回常见的模型名称
            return [
                "deepseek-r1:7b", "deepseek-r1:latest",    # DeepSeek系列（优先推荐）
                "llama2", "llama2:7b", "llama2:13b",
                "mistral", "mistral:7b",
                "codellama", "codellama:7b",
                "phi", "phi:2.7b",
                "neural-chat", "neural-chat:7b"
            ]
    
    def get_supported_features(self) -> List[str]:
        """
        获取支持的功能列表
        
        Returns:
            List[str]: 支持的功能
        """
        return [
            "chat_completion", 
            "text_generation",
            "local_inference",  # 本地推理
            "offline_usage",    # 离线使用
            "open_source",      # 开源模型
            "customizable",     # 可定制
            "privacy_focused"   # 隐私保护
        ]


def create_ollama_client(model_name: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434", **kwargs) -> OllamaClient:
    """
    创建Ollama客户端的便捷函数
    
    Args:
        model_name: 模型名称
        base_url: Ollama服务器地址
        **kwargs: 其他配置参数
        
    Returns:
        OllamaClient: 客户端实例
    """
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        api_key="",  # Ollama通常不需要API密钥
        model_name=model_name,
        base_url=base_url,
        **kwargs
    )
    return OllamaClient(config)
