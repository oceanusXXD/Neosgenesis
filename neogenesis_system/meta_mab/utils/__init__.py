#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utils Module - 工具模块
Utility functions for the Neogenesis System

包含的工具:
- api_caller: 传统 DeepSeek API调用工具（向后兼容）
- deepseek_client: 强化版 DeepSeek API客户端（推荐使用）
- 其他通用工具函数
"""

# 通用工具函数（从api_caller.py迁移）
from .common_utils import (
    parse_json_response,
    extract_context_factors,
    calculate_similarity,
    validate_api_key,
    format_prompt_with_context
)

# 强化版客户端（推荐使用）
from .deepseek_client import (
    DeepSeekClient,
    ClientConfig,
    ClientMetrics,
    APIResponse,
    APIErrorType,
    create_client,
    quick_chat
)

# 兼容性适配器
from .client_adapter import (
    DeepSeekClientAdapter,
    create_compatible_client,
    get_or_create_client,
    clear_client_cache
)

# 搜索工具客户端
from .search_client import (
    WebSearchClient,
    IdeaVerificationSearchClient,
    SearchResult,
    SearchResponse
)

__all__ = [
    # 通用工具函数（已迁移到独立模块）
    "parse_json_response", 
    "extract_context_factors",
    "calculate_similarity",
    "validate_api_key",
    "format_prompt_with_context",
    
    # 强化版客户端（推荐）
    "DeepSeekClient",
    "ClientConfig", 
    "ClientMetrics",
    "APIResponse",
    "APIErrorType",
    "create_client",
    "quick_chat",
    
    # 兼容性适配器
    "DeepSeekClientAdapter",
    "create_compatible_client",
    "get_or_create_client", 
    "clear_client_cache",
    
    # 搜索工具客户端
    "WebSearchClient",
    "IdeaVerificationSearchClient",
    "SearchResult",
    "SearchResponse"
]