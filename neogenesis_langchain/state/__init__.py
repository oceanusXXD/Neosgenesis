#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis LangChain - State Management Module
状态管理组件：状态管理器、分布式状态、事务管理
"""

# 尝试逐个导入，避免导入错误
try:
    from .state_management import DecisionStage
except ImportError as e:
    print(f"Warning: Cannot import DecisionStage: {e}")
    DecisionStage = None

try:
    from .state_management import NeogenesisStateManager
except ImportError as e:
    print(f"Warning: Cannot import NeogenesisStateManager: {e}")
    NeogenesisStateManager = None

try:
    from .state_management import DecisionState
except ImportError as e:
    print(f"Warning: Cannot import DecisionState: {e}")
    DecisionState = None

try:
    from .state_management import MABPersistentWeights
except ImportError as e:
    print(f"Warning: Cannot import MABPersistentWeights: {e}")
    MABPersistentWeights = None

# 分布式状态管理 - 可选导入
try:
    from .distributed_state import DistributedStateManager
except ImportError as e:
    print(f"Warning: Cannot import DistributedStateManager: {e}")
    DistributedStateManager = None

# 事务管理 - 可选导入  
try:
    from .state_transactions import TransactionManager
except ImportError as e:
    print(f"Warning: Cannot import TransactionManager: {e}")
    TransactionManager = None

__all__ = [
    "DecisionStage",
    "NeogenesisStateManager",
    "DecisionState", 
    "MABPersistentWeights",
    "DistributedStateManager",
    "TransactionManager",
]
