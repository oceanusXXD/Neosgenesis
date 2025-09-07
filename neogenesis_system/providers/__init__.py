#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System Providers - 服务提供者层

这个包包含了所有外部服务和资源提供者：
- LLM客户端实现 (impl/)
- RAG种子生成器 (rag_seed_generator.py)
- 知识探索器 (knowledge_explorer.py) 
- 搜索服务客户端 (search_client.py, search_tools.py)
- 客户端管理器和适配器

所有这些组件都遵循依赖注入模式，为系统核心层提供外部能力支持。
"""

__version__ = "1.0.0"
__author__ = "Neogenesis Team"

# 主要导出的类和接口
from .knowledge_explorer import (
    KnowledgeExplorer,
    ExplorationStrategy,
    ExplorationTarget,
    KnowledgeQuality,
    KnowledgeItem,
    ThinkingSeed,
    ExplorationResult
)

from .rag_seed_generator import RAGSeedGenerator
from .search_client import WebSearchClient

try:
    from .llm_manager import LLMManager
    from .llm_base import BaseLLMClient
except ImportError:
    # 某些客户端可能不可用
    LLMManager = None
    BaseLLMClient = None

__all__ = [
    # 知识探索相关
    "KnowledgeExplorer",
    "ExplorationStrategy", 
    "ExplorationTarget",
    "KnowledgeQuality",
    "KnowledgeItem",
    "ThinkingSeed", 
    "ExplorationResult",
    
    # RAG和搜索相关
    "RAGSeedGenerator",
    "WebSearchClient",
    
    # LLM相关（如果可用）
    "LLMManager",
    "BaseLLMClient",
]
