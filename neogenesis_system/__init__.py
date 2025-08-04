#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - 智能决策系统
A modular intelligent decision-making system powered by DeepSeek and MAB algorithms

主要组件:
- MainController: 主控制器，协调所有组件
- PriorReasoner: 先验推理器，任务理解和置信度评估
- PathGenerator: 路径生成器，维度生成和路径规划
- MABConverger: MAB收敛器，多臂老虎机算法决策
"""

__version__ = "1.0.0"
__author__ = "Neogenesis Team"
__email__ = "team@neogenesis.ai"

# 导入核心组件
from .meta_mab.controller import MainController
from .meta_mab.reasoner import PriorReasoner
from .meta_mab.path_generator import PathGenerator, DeepSeekDrivenDimensionCreator
from .meta_mab.mab_converger import MABConverger

# 导入数据结构
from .meta_mab.data_structures import (
    ReasoningPath,
    TaskComplexity,
    EnhancedDecisionArm,
    TaskContext,
    DecisionResult,
    PerformanceFeedback,
    SystemStatus
)

# 导入工具（已迁移到适配器模式）
# from .meta_mab.utils.api_caller import DeepSeekAPICaller  # 已弃用，使用 DeepSeekClientAdapter

# 导入配置
from .config import (
    DEEPSEEK_API_BASE,
    DEEPSEEK_MODEL,
    API_CONFIG,
    MAB_CONFIG,
    SYSTEM_LIMITS,
    EVALUATION_CONFIG,
    PROMPT_TEMPLATES,
    FEATURE_FLAGS,
    PERFORMANCE_CONFIG
)

__all__ = [
    # 核心组件
    "MainController",
    "PriorReasoner", 
    "PathGenerator",
    "DeepSeekDrivenDimensionCreator",
    "MABConverger",
    
        # 数据结构
    "ReasoningPath",
    "TaskComplexity",
    "EnhancedDecisionArm",
    "TaskContext",
    "DecisionResult",
    "PerformanceFeedback",
    "SystemStatus",
    
    # 工具（已迁移到适配器模式）
    # "DeepSeekAPICaller",  # 已弃用，使用 DeepSeekClientAdapter
    
    # 配置
    "DEEPSEEK_API_BASE",
    "DEEPSEEK_MODEL",
    "API_CONFIG",
    "MAB_CONFIG", 
    "SYSTEM_LIMITS",
    "EVALUATION_CONFIG",
    "PROMPT_TEMPLATES",
    "FEATURE_FLAGS",
    "PERFORMANCE_CONFIG"
]


def create_system(api_key: str, config: dict = None) -> MainController:
    """
    创建Neogenesis智能决策系统实例
    
    Args:
        api_key: DeepSeek API密钥
        config: 系统配置字典
        
    Returns:
        MainController实例
        
    Example:
        >>> system = create_system("your_api_key")
        >>> result = system.make_decision("查询最近上映的电影")
        >>> print(result['selected_dimensions'])
    """
    return MainController(api_key, config)


def get_version() -> str:
    """获取系统版本号"""
    return __version__


def get_system_info() -> dict:
    """获取系统信息"""
    return {
        "name": "Neogenesis System",
        "version": __version__,
        "description": "智能决策系统 - DeepSeek驱动的多臂老虎机决策框架",
        "author": __author__,
        "components": [
            "MainController",
            "PriorReasoner", 
            "PathGenerator",
            "MABConverger"
        ],
        "features": [
            "AI驱动的动态维度创建",
            "多臂老虎机算法优化",
            "强化学习反馈机制",
            "组件化架构设计",
            "DeepSeek智能推理集成"
        ]
    }