#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anthropic Claude客户端实现 - 统一LLM接口
Anthropic Claude Client Implementation - Unified LLM Interface
"""

import time
import logging
from typing import List, Optional, Union, Dict, Any

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
from ..llm_base import (
    BaseLLMClient, LLMConfig, LLMResponse, LLMMessage, LLMUsage, 
    LLMProvider, LLMErrorType, create_error_response
)

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """
    Anthropic Claude客户端 - 实现统一LLM接口
    
    支持:
    - Claude 3系列模型
    - 长上下文处理
    - 高质量推理能力
    - 完整的错误处理
    """
    
    def __init__(self, config: LLMConfig):
        """
        初始化Anthropic客户端
        
        Args:
            config: LLM配置对象
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic库未安装。请运行: pip install anthropic")
        
        super().__init__(config)
        
        # 创建Anthropic客户端
        self.client = Anthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout[1],  # 使用读取超时
            max_retries=config.max_retries
        )
        
        logger.info(f"🤖 Anthropic客户端已初始化: {config.model_name}")
    
    def chat_completion(self, 
                       messages: Union[str, List[LLMMessage]], 
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       **kwargs) -> LLMResponse:
        """
        Anthropic聊天完成接口实现
        
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
            
            # 分离系统消息和对话消息
            system_message = ""
            dialogue_messages = []
            
            for msg in prepared_messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    dialogue_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # 如果没有对话消息，创建一个用户消息
            if not dialogue_messages:
                if isinstance(messages, str):
                    dialogue_messages = [{"role": "user", "content": messages}]
                else:
                    dialogue_messages = [{"role": "user", "content": "Hello"}]
            
            # 参数处理
            params = {
                "model": kwargs.get('model') or self.config.model_name,
                "messages": dialogue_messages,
                "max_tokens": max_tokens or self.config.max_tokens,
                "temperature": temperature or self.config.temperature
            }
            
            # 添加系统消息（如果存在）
            if system_message:
                params["system"] = system_message
            
            # 调用Anthropic API
            logger.debug(f"🤖 调用Anthropic API: {params['model']}")
            response = self.client.messages.create(**params)
            
            response_time = time.time() - start_time
            
            # 提取响应内容
            content = ""
            if response.content and len(response.content) > 0:
                content = response.content[0].text
            
            finish_reason = response.stop_reason
            
            # 构建使用统计
            usage = None
            if response.usage:
                usage = LLMUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
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
            
            logger.info(f"✅ Anthropic API调用成功: {content[:50]}...")
            return llm_response
            
        except anthropic.AuthenticationError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.AUTHENTICATION,
                error_message=f"Anthropic认证失败: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Anthropic认证失败: {e}")
            return error_response
            
        except anthropic.RateLimitError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.RATE_LIMIT,
                error_message=f"Anthropic速率限制: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Anthropic速率限制: {e}")
            return error_response
            
        except anthropic.BadRequestError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.INVALID_REQUEST,
                error_message=f"Anthropic请求无效: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Anthropic请求无效: {e}")
            return error_response
            
        except anthropic.InternalServerError as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.SERVER_ERROR,
                error_message=f"Anthropic服务器错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Anthropic服务器错误: {e}")
            return error_response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_response = create_error_response(
                provider=self.provider.value,
                error_type=LLMErrorType.UNKNOWN_ERROR,
                error_message=f"Anthropic未知错误: {str(e)}",
                response_time=response_time
            )
            self._update_stats(error_response)
            logger.error(f"❌ Anthropic未知错误: {e}")
            return error_response
    
    def validate_config(self) -> bool:
        """
        验证Anthropic配置是否有效
        
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
            logger.error(f"❌ Anthropic配置验证失败: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            List[str]: 可用的模型名称列表
        """
        # Anthropic目前支持的模型
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022"
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
            "long_context",  # 支持长上下文
            "reasoning",     # 强推理能力
            "analysis",      # 分析能力
            "creative_writing",  # 创意写作
            "code_analysis", # 代码分析
            "system_messages"
        ]


def create_anthropic_client(api_key: str, model_name: str = "claude-3-sonnet-20240229", **kwargs) -> AnthropicClient:
    """
    创建Anthropic客户端的便捷函数
    
    Args:
        api_key: API密钥
        model_name: 模型名称
        **kwargs: 其他配置参数
        
    Returns:
        AnthropicClient: 客户端实例
    """
    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        api_key=api_key,
        model_name=model_name,
        **kwargs
    )
    return AnthropicClient(config)