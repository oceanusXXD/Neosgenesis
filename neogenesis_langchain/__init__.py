#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis LangChain Integration Package

一个完整的、标准化的Python包，将Neogenesis System的核心组件集成到LangChain生态系统中。

这个包提供：
- 基础工具：思维种子生成、RAG种子生成、路径生成、MAB决策等
- 决策链：五阶段决策流程、协调决策链、高级决策链
- 状态管理：本地状态管理、分布式状态、事务管理
- 存储系统：持久化存储引擎，支持多种后端
- 执行系统：智能协调器、执行引擎
- 优化系统：多臂老虎机优化、性能优化
- 适配器：与LangChain的集成适配器
"""

__version__ = "1.0.0"
__author__ = "Neogenesis System Team"
__email__ = "neogenesis@example.com"
__license__ = "MIT"

# 核心工具
try:
    from .tools import (
        NeogenesisThinkingSeedTool,
        NeogenesisRAGSeedTool,
        NeogenesisPathGeneratorTool,
        NeogenesisMABDecisionTool,
        NeogenesisIdeaVerificationTool,
        NeogenesisFiveStageDecisionTool,
        get_all_neogenesis_tools
    )
except ImportError as e:
    print(f"Warning: Tools module import failed: {e}")
    # 提供默认值
    NeogenesisThinkingSeedTool = None
    NeogenesisRAGSeedTool = None
    NeogenesisPathGeneratorTool = None
    NeogenesisMABDecisionTool = None
    NeogenesisIdeaVerificationTool = None
    NeogenesisFiveStageDecisionTool = None
    get_all_neogenesis_tools = None

# 适配器
try:
    from .adapters import (
        NeogenesisAdapter,
        create_neogenesis_agent,
        create_hybrid_agent
    )
except ImportError as e:
    print(f"Warning: Adapters module import failed: {e}")
    NeogenesisAdapter = None
    create_neogenesis_agent = None
    create_hybrid_agent = None

# 链相关
try:
    from .chains import (
        NeogenesisDecisionChain,
        NeogenesisFiveStageChain,
        CoordinatedNeogenesisChain,
        create_enhanced_neogenesis_chain,
        SmartCoordinatedChain,
        HighPerformanceDecisionChain,
        QualityAssuredDecisionChain,
        create_smart_coordinated_chain
    )
except ImportError as e:
    print(f"Warning: Chains module import failed: {e}")
    NeogenesisDecisionChain = None
    NeogenesisFiveStageChain = None
    CoordinatedNeogenesisChain = None
    create_enhanced_neogenesis_chain = None
    SmartCoordinatedChain = None
    HighPerformanceDecisionChain = None
    QualityAssuredDecisionChain = None
    create_smart_coordinated_chain = None

# 状态管理
try:
    from .state import (
    NeogenesisStateManager,
    EnhancedNeogenesisStateManager,
    DecisionState,
    DecisionStage,
    MABPersistentWeights,
    create_enhanced_state_manager,
    DistributedStateManager,
    create_distributed_state_manager,
    TransactionManager,
    create_transaction_manager
    )
except ImportError as e:
    print(f"Warning: State module import failed: {e}")
    # 提供默认值或跳过这些导入
    NeogenesisStateManager = None
    EnhancedNeogenesisStateManager = None
    DecisionState = None
    DecisionStage = None
    MABPersistentWeights = None

# 存储系统  
try:
    from .storage import (
    PersistentStorageEngine,
    StorageConfig,
    StorageBackend,
    create_storage_engine
    )
except ImportError as e:
    print(f"Warning: Storage module import failed: {e}")
    PersistentStorageEngine = None
    StorageConfig = None
    StorageBackend = None
    create_storage_engine = None

# 执行系统
try:
    from .execution import (
        NeogenesisToolCoordinator,
        ExecutionContext,
        ExecutionMode,
        PerformanceOptimizer,
        SmartExecutionEngine,
        IntelligentScheduler,
        DependencyAnalyzer
    )
except ImportError as e:
    print(f"Warning: Execution module import failed: {e}")
    NeogenesisToolCoordinator = None
    ExecutionContext = None
    ExecutionMode = None
    PerformanceOptimizer = None
    SmartExecutionEngine = None
    IntelligentScheduler = None
    DependencyAnalyzer = None

# 优化系统
try:
    from .optimization import (
        AdvancedMABManager,
        MABAlgorithm,
        MABConfig,
        create_mab_manager
    )
except ImportError as e:
    print(f"Warning: Optimization module import failed: {e}")
    AdvancedMABManager = None
    MABAlgorithm = None
    MABConfig = None
    create_mab_manager = None

__all__ = [
    # 核心工具
    "NeogenesisThinkingSeedTool",
    "NeogenesisRAGSeedTool",
    "NeogenesisPathGeneratorTool",
    "NeogenesisMABDecisionTool",
    "NeogenesisIdeaVerificationTool",
    "NeogenesisFiveStageDecisionTool",
    "get_all_neogenesis_tools",
    
    # 适配器
    "NeogenesisAdapter",
    "create_neogenesis_agent", 
    "create_hybrid_agent",
    
    # 决策链
    "NeogenesisDecisionChain",
    "NeogenesisFiveStageChain",
    "CoordinatedNeogenesisChain",
    "create_enhanced_neogenesis_chain",
    "SmartCoordinatedChain",
    "HighPerformanceDecisionChain",
    "QualityAssuredDecisionChain",
    "create_smart_coordinated_chain",
    
    # 状态管理
    "NeogenesisStateManager",
    "EnhancedNeogenesisStateManager",
    "DecisionState",
    "DecisionStage",
    "MABPersistentWeights",
    "create_enhanced_state_manager",
    "DistributedStateManager",
    "create_distributed_state_manager",
    "TransactionManager",
    "create_transaction_manager",
    
    # 存储系统
    "PersistentStorageEngine",
    "StorageConfig",
    "StorageBackend",
    "create_storage_engine",
    
    # 执行系统
    "NeogenesisToolCoordinator",
    "ExecutionContext",
    "ExecutionMode",
    "PerformanceOptimizer",
    "SmartExecutionEngine",
    "IntelligentScheduler",
    "DependencyAnalyzer",
    
    # 优化系统
    "AdvancedMABManager",
    "MABAlgorithm", 
    "MABConfig",
    "create_mab_manager",
]

# 模块信息
__modules__ = {
    "tools": "基础工具集合",
    "adapters": "LangChain适配器",
    "chains": "决策链实现",
    "state": "状态管理系统",
    "storage": "持久化存储系统",
    "execution": "执行协调系统",
    "optimization": "优化算法系统",
    "examples": "使用示例和演示"
}

def get_version():
    """获取包版本"""
    return __version__

def get_info():
    """获取包信息"""
    return {
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "modules": __modules__
    }
