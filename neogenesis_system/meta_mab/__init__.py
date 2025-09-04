#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Meta MAB Module - 元多臂老虎机模块
Core components for the intelligent decision-making system

包含的组件:
- Controller: 主控制器
- Reasoner: 先验推理器  
- PathGenerator: 路径生成器
- MABConverger: MAB收敛器
- DataStructures: 数据结构定义
- Utils: 工具函数
"""

# 导入核心组件
# from .controller import MainController  # 已废弃，使用 NeogenesisPlanner
from .reasoner import PriorReasoner
from .path_generator import PathGenerator, LLMDrivenDimensionCreator
from .mab_converger import MABConverger
from .rag_seed_generator import RAGSeedGenerator

# 导入数据结构
from .data_structures import (
    ReasoningPath,
    TaskComplexity,
    EnhancedDecisionArm,
    TaskContext,
    DecisionResult,
    PerformanceFeedback,
    LimitationAnalysis,
    AlternativeThinkingSignal,
    FailureAnalysis,
    SuccessPattern,
    SystemStatus
)

# 导入RAG相关数据结构
from .rag_seed_generator import RAGSearchStrategy, RAGInformationSynthesis

# 导入工具
# 适配器模式：使用新的强化客户端
# from .utils.api_caller import DeepSeekAPICaller  # 已弃用
from .utils.common_utils import parse_json_response

__all__ = [
    # 核心组件
    # "MainController",  # 已废弃，使用 NeogenesisPlanner
    "PriorReasoner",
    "PathGenerator", 
    "LLMDrivenDimensionCreator",
    "MABConverger",
    "RAGSeedGenerator",
    
    # 数据结构
    "ReasoningPath",
    "TaskComplexity",
    "EnhancedDecisionArm",
    "TaskContext", 
    "DecisionResult",
    "PerformanceFeedback",
    "LimitationAnalysis",
    "AlternativeThinkingSignal",
    "FailureAnalysis",
    "SuccessPattern",
    "SystemStatus",
    
    # RAG相关数据结构
    "RAGSearchStrategy",
    "RAGInformationSynthesis",
    
    # 工具
    # "DeepSeekAPICaller",  # 已迁移到适配器模式
    "parse_json_response"
]
