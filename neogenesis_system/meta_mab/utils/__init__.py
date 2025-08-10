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

# 🔧 新增：统一工具抽象接口
from .tool_abstraction import (
    BaseTool,
    AsyncBaseTool,
    BatchProcessingTool,
    ToolCategory,
    ToolResult,
    ToolCapability,
    ToolStatus,
    ToolRegistry,
    global_tool_registry,
    # 工具管理函数
    register_tool,
    unregister_tool,
    get_tool,
    execute_tool,
    list_available_tools,
    search_tools,
    get_tools_by_category,
    disable_tool,
    enable_tool,
    get_tool_info,
    get_registry_stats,
    health_check,
    export_registry_config
)

# 🔧 新增：搜索工具（Tool接口封装）
from .search_tools import (
    WebSearchTool,
    IdeaVerificationTool,
    create_and_register_search_tools,
    quick_web_search,
    quick_idea_verification
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
    
    # 搜索工具客户端（原有）
    "WebSearchClient",
    "IdeaVerificationSearchClient",
    "SearchResult",
    "SearchResponse",
    
    # 🔧 新增：统一工具抽象接口
    "BaseTool",
    "AsyncBaseTool", 
    "BatchProcessingTool",
    "ToolCategory",
    "ToolResult",
    "ToolCapability",
    "ToolStatus",
    "ToolRegistry",
    "global_tool_registry",
    # 工具管理函数
    "register_tool",
    "unregister_tool",
    "get_tool",
    "execute_tool",
    "list_available_tools",
    "search_tools",
    "get_tools_by_category",
    "disable_tool",
    "enable_tool",
    "get_tool_info",
    "get_registry_stats",
    "health_check",
    "export_registry_config",
    
    # 🔧 新增：搜索工具（Tool接口封装）
    "WebSearchTool",
    "IdeaVerificationTool", 
    "create_and_register_search_tools",
    "quick_web_search",
    "quick_idea_verification"
]
