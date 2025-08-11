#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - LangChain Integration Module
将Neogenesis System的核心组件抽象为LangChain工具

这个模块实现了方案一：渐进式工具化
- 第一阶段：基础工具抽象
- 第二阶段：决策链协调
- 第三阶段：状态管理
- 第四阶段：混合模式
"""

from .tools import (
    NeogenesisThinkingSeedTool,
    NeogenesisRAGSeedTool,
    NeogenesisPathGeneratorTool,
    NeogenesisMABDecisionTool,
    NeogenesisIdeaVerificationTool,
    NeogenesisFiveStageDecisionTool,
    get_all_neogenesis_tools
)

from .chains import (
    NeogenesisDecisionChain,
    NeogenesisFiveStageChain,
    CoordinatedNeogenesisChain,
    create_enhanced_neogenesis_chain
)

from .state_management import (
    NeogenesisStateManager,
    DecisionState,
    MABPersistentWeights
)

from .adapters import (
    NeogenesisAdapter,
    create_neogenesis_agent,
    create_hybrid_agent
)

# 第二阶段新增组件
try:
    from .coordinators import (
        NeogenesisToolCoordinator,
        ExecutionContext,
        ExecutionMode,
        PerformanceOptimizer
    )
    from .advanced_chains import (
        SmartCoordinatedChain,
        HighPerformanceDecisionChain,
        QualityAssuredDecisionChain,
        create_smart_coordinated_chain
    )
    from .execution_engines import (
        SmartExecutionEngine,
        IntelligentScheduler,
        DependencyAnalyzer
    )
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False

# 第三阶段新增组件
try:
    from .persistent_storage import (
        PersistentStorageEngine,
        StorageConfig,
        create_storage_engine
    )
    from .distributed_state import (
        DistributedStateManager,
        create_distributed_state_manager
    )
    from .mab_optimization import (
        AdvancedMABManager,
        create_mab_manager
    )
    from .state_transactions import (
        TransactionManager,
        create_transaction_manager
    )
    from .state_management import (
        EnhancedNeogenesisStateManager,
        create_enhanced_state_manager
    )
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False

# 第四阶段新增组件 (混合模式架构)
# 注意：第四阶段模块已被删除，暂时不可用
PHASE4_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "Neogenesis System Team"

__all__ = [
    # 基础工具
    "NeogenesisThinkingSeedTool",
    "NeogenesisRAGSeedTool", 
    "NeogenesisPathGeneratorTool",
    "NeogenesisMABDecisionTool",
    "NeogenesisIdeaVerificationTool",
    "NeogenesisFiveStageDecisionTool",
    "get_all_neogenesis_tools",
    
    # 决策链
    "NeogenesisDecisionChain",
    "NeogenesisFiveStageChain",
    "CoordinatedNeogenesisChain",
    "create_enhanced_neogenesis_chain",
    
    # 状态管理
    "NeogenesisStateManager",
    "DecisionState",
    "MABPersistentWeights",
    
    # 适配器
    "NeogenesisAdapter",
    "create_neogenesis_agent",
    "create_hybrid_agent"
]

# 第二阶段组件动态添加到__all__
if PHASE2_AVAILABLE:
    __all__.extend([
        # 协调器
        "NeogenesisToolCoordinator",
        "ExecutionContext", 
        "ExecutionMode",
        "PerformanceOptimizer",
        
        # 高级链
        "SmartCoordinatedChain",
        "HighPerformanceDecisionChain",
        "QualityAssuredDecisionChain",
        "create_smart_coordinated_chain",
        
        # 执行引擎
        "SmartExecutionEngine",
        "IntelligentScheduler",
        "DependencyAnalyzer"
    ])

# 第三阶段组件动态添加到__all__
if PHASE3_AVAILABLE:
    __all__.extend([
        # 持久化存储
        "PersistentStorageEngine",
        "StorageConfig",
        "create_storage_engine",
        
        # 分布式状态管理
        "DistributedStateManager",
        "create_distributed_state_manager",
        
        # MAB优化
        "AdvancedMABManager",
        "create_mab_manager",
        
        # 事务管理
        "TransactionManager",
        "create_transaction_manager",
        
        # 增强状态管理
        "EnhancedNeogenesisStateManager",
        "create_enhanced_state_manager"
    ])

# 第四阶段组件动态添加到__all__
# 注意：第四阶段组件暂时不可用
if PHASE4_AVAILABLE:
    __all__.extend([
        # 独立模式
        "NeogenesisStandalone",
        "NeogenesisStandaloneDecisionInterface", 
        "quick_decision",
        "create_standalone_system",
        
        # LangChain插件模式
        "NeogenesisLangChainPlugin",
        "create_neogenesis_plugin",
        "get_neogenesis_tools",
        "create_neogenesis_agent",
        
        # 混合框架
        "NeogenesisHybridFramework",
        "create_hybrid_framework",
        
        # 配置管理
        "ConfigurationManager",
        "FrameworkMode",
        "create_configuration_manager",
        
        # 兼容性层
        "check_compatibility",
        "detect_optimal_mode", 
        "get_recommendation_report"
    ])
