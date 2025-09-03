#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis LangChain - Chains Module
链相关组件：决策链、高级链
"""

# 尝试导入基础链
try:
    from .chains import (
        NeogenesisDecisionChain,
        NeogenesisFiveStageChain,
        CoordinatedNeogenesisChain,
        create_enhanced_neogenesis_chain,
        create_neogenesis_decision_chain,
    )
except ImportError as e:
    print(f"Warning: Cannot import basic chains: {e}")
    NeogenesisDecisionChain = None
    NeogenesisFiveStageChain = None
    CoordinatedNeogenesisChain = None
    create_enhanced_neogenesis_chain = None
    create_neogenesis_decision_chain = None

# 尝试导入高级链
try:
    from .advanced_chains import (
        SmartCoordinatedChain,
        HighPerformanceDecisionChain,
        QualityAssuredDecisionChain,
        create_smart_coordinated_chain,
    )
except ImportError as e:
    print(f"Warning: Cannot import advanced chains: {e}")
    SmartCoordinatedChain = None
    HighPerformanceDecisionChain = None
    QualityAssuredDecisionChain = None
    create_smart_coordinated_chain = None

__all__ = [
    # 基础链
    "NeogenesisDecisionChain",
    "NeogenesisFiveStageChain", 
    "CoordinatedNeogenesisChain",
    "create_enhanced_neogenesis_chain",
    "create_neogenesis_decision_chain",
    
    # 高级链
    "SmartCoordinatedChain",
    "HighPerformanceDecisionChain",
    "QualityAssuredDecisionChain",
    "create_smart_coordinated_chain",
]
