#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAI客户端实现 - 统一LLM接口
OpenAI Client Implementation - Unified LLM Interface
"""

import time
import logging
from typing import List, Optional, Union, Dict, Any

try:
    import openai
    from openai import OpenAI, AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
from ..llm_base import (
    BaseLLMClient, LLMConfig, LLMResponse, LLMMessage, LLMUsage, 
    LLMProvider, LLMErrorType, create_error_response
)

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    OpenAI客户端 - 实现统一LLM接口
    
    支持:
    - OpenAI GPT模型
    - Azure OpenAI服务
    - 完整的聊天完成功能
    - 错误处理和重试机制
    """
    
    def __init__(self, config: LLMConfig):
        """
        初始化OpenAI客户端
        
        Args:
            config: LLM配置对象
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI库未安装。请运行: pip install openai")
        
        super().__init__(config)
        
        # 根据提供商类型创建客户端
        if config.provider == LLMProvider.AZURE_OPENAI:
            # Azure OpenAI配置
            azure_endpoint = config.base_url or config.extra_params.get('azure_endpoint')
            api_version = config.extra_params.get('api_version', '2024-02-15-preview')
            
            if not azure_endpoint:
                raise ValueError("Azure OpenAI需要提供base_url或azure_endpoint")
            
            self.client = AzureOpenAI(
                api_key=config.api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                timeout=config.timeout[1]  # 使用读取超时
            )
            logger.info(f"🤖 Azure OpenAI客户端已初始化: {azure_endpoint}")
            
        else:
            # 标准OpenAI配置
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout[1],
                max_retries=config.max_retries
            )
            logger.info(f"🤖 OpenAI客户端已初始化: {config.model_name}")
    
    def chat_completion(self, 
                       messages: Union[str, List[LLMMessage]], 
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       **kwargs) -> LLMResponse:
        """
        OpenAI聊天完成接口实现
        
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
            
            # 转换为OpenAI API格式
            openai_messages = []
            for msg in prepared_messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 参数处理
            params = {
                "model": kwargs.get('model') or self.config.model_name,
                "messages": openai_messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "top_p": kwargs.get('top_p') or self.config.top_p,
                "frequency_penalty": kwargs.get('frequency_penalty') or self.config.frequency_penalty,
                "presence_penalty": kwargs.get('presence_penalty') or self.config.presence_penalty
            }
            
            # 调用OpenAI API
            logger.debug(f"🤖 调用OpenAI API: {params['model']}")
            response = self.client.chat.completions.create(**params)
            
            response_time = time.time() - start_time
            
            # 提取响应内容
            content = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            
            # 构建使用统计
            usage = None
            if response.usage:
                usage = LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens
                )
            
            # 构建响应对象
            llm_response = LLMResponse(
                success=True,
                content=content,
                provider=self.provider.value,
                model=response.model,
                response_time=response_time,
                usage=usage,
                finish_reason=finish_reason,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
            # 更新统计
            self._update_stats(llm_response)
            
            logger.info(f"✅ OpenAI API调用成功: {content[:50]}...")
            return llm_response
            
        except openai.AuthenticationError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.AUTHENTICATION,
                error_message=f"OpenAI认证失败: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ OpenAI认证失败: {e}")
            return error_response
            
        except openai.RateLimitError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.RATE_LIMIT,
                error_message=f"OpenAI速率限制: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ OpenAI速率限制: {e}")
            return error_response
            
        except openai.BadRequestError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.INVALID_REQUEST,
                error_message=f"OpenAI请求无效: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ OpenAI请求无效: {e}")
            return error_response
            
        except openai.InternalServerError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.SERVER_ERROR,
                error_message=f"OpenAI服务器错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ OpenAI服务器错误: {e}")
            return error_response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.UNKNOWN_ERROR,
                error_message=f"OpenAI未知错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ OpenAI未知错误: {e}")
            return error_response
    
    def validate_config(self) -> bool:
        """
        验证OpenAI配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 简单测试API连通性
            response = self.chat_completion(
                messages="Hello",
                max_tokens=5
            )
            return response.success
            
        except Exception as e:
            logger.error(f"❌ OpenAI配置验证失败: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            List[str]: 可用的模型名称列表
        """
        try:
            models_response = self.client.models.list()
            return [model.id for model in models_response.data]
            
        except Exception as e:
            logger.error(f"❌ 获取OpenAI模型列表失败: {e}")
            # 返回常见的模型
            if self.config.provider == LLMProvider.AZURE_OPENAI:
                return ["gpt-35-turbo", "gpt-4", "gpt-4-32k"]
            else:
                return [
                    "gpt-3.5-turbo", 
                    "gpt-3.5-turbo-16k",
                    "gpt-4", 
                    "gpt-4-turbo-preview",
                    "gpt-4o",
                    "gpt-4o-mini"
                ]
    
    def get_supported_features(self) -> List[str]:
        """
        获取支持的功能列表
        
        Returns:
            List[str]: 支持的功能
        """
        features = [
            "chat_completion", 
            "text_generation",
            "function_calling",
            "streaming",
            "vision",  # 部分模型支持
            "json_mode",
            "system_messages"
        ]
        
        if self.config.provider == LLMProvider.AZURE_OPENAI:
            features.append("azure_integration")
            
        return features


def create_openai_client(api_key: str, model_name: str = "gpt-3.5-turbo", **kwargs) -> OpenAIClient:
    """
    创建OpenAI客户端的便捷函数
    
    Args:
        api_key: API密钥
        model_name: 模型名称
        **kwargs: 其他配置参数
        
    Returns:
        OpenAIClient: 客户端实例
    """
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=api_key,
        model_name=model_name,
        **kwargs
    )
    return OpenAIClient(config)


def create_azure_openai_client(api_key: str, azure_endpoint: str, 
                              model_name: str = "gpt-35-turbo", **kwargs) -> OpenAIClient:
    """
    创建Azure OpenAI客户端的便捷函数
    
    Args:
        api_key: API密钥
        azure_endpoint: Azure端点
        model_name: 模型名称
        **kwargs: 其他配置参数
        
    Returns:
        OpenAIClient: 客户端实例
    """
    config = LLMConfig(
        provider=LLMProvider.AZURE_OPENAI,
        api_key=api_key,
        model_name=model_name,
        base_url=azure_endpoint,
        extra_params={"azure_endpoint": azure_endpoint},
        **kwargs
    )
    return OpenAIClient(config)