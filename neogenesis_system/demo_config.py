#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示专用配置文件
Demo-specific configuration for AI thinking visualization
"""

# ==================== 演示模式配置 ====================

# 演示场景配置
DEMO_SCENARIOS = {
    'standard_decision': {
        'name': '标准元认知决策',
        'description': '观察完整的五阶段决策流程',
        'query': '如何构建一个高性能的网络爬虫系统？',
        'expected_complexity': 0.8,
        'expected_confidence': 0.75,
        'icon': '🎯'
    },
    'aha_moment': {
        'name': 'Aha-Moment灵感迸发',
        'description': '观察系统如何创造性地解决问题', 
        'query': '设计一个能够自我进化的AI算法框架',
        'expected_complexity': 0.9,
        'expected_confidence': 0.4,
        'icon': '💡'
    },
    'golden_template': {
        'name': '经验成金智慧沉淀',
        'description': '观察黄金模板的形成和复用',
        'query': '优化分布式系统的性能瓶颈',
        'expected_complexity': 0.7,
        'expected_confidence': 0.8,
        'icon': '🏆'
    }
}

# 可视化配置
VISUALIZATION_CONFIG = {
    'pause_duration': 0.5,  # 自动暂停时长
    'step_delay': 0.2,      # 步骤间延迟
    'animation_enabled': True,
    'color_output': True,
    'detailed_logging': True
}

# 模拟数据配置
SIMULATION_CONFIG = {
    'mock_thinking_seeds': {
        'technical': "这是一个复杂的技术问题，需要考虑系统架构、性能优化、可扩展性等多个方面。基于问题的特征，我需要从系统设计、技术选型、实施策略等角度进行深入分析...",
        'innovative': "这个问题需要突破传统思维框架，探索创新的解决方案。我需要跳出常规技术限制，考虑前沿技术的应用可能性，同时保持方案的实用性...",
        'practical': "这是一个需要实用导向的问题，我应该优先考虑可行性、成本效益和实施难度。基于已有经验和最佳实践，我需要提供稳定可靠的解决方案..."
    },
    
    'mock_reasoning_paths': [
        {
            'path_type': '系统分析型',
            'description': '从系统架构角度分析问题，考虑组件设计、数据流、接口规范等技术细节',
            'confidence': 0.85
        },
        {
            'path_type': '创新突破型',
            'description': '跳出传统思路，探索新兴技术和创新方法来解决问题',
            'confidence': 0.65
        },
        {
            'path_type': '实用务实型', 
            'description': '注重实际可行性，优先选择成熟稳定的技术方案',
            'confidence': 0.75
        },
        {
            'path_type': '批判质疑型',
            'description': '深度质疑现有方案，识别潜在问题和风险点',
            'confidence': 0.55
        },
        {
            'path_type': '整体综合型',
            'description': '从全局角度平衡各种因素，寻找最佳的综合解决方案',
            'confidence': 0.70
        }
    ],
    
    'mock_verification_results': {
        'high_feasibility': [
            {'path_type': '系统分析型', 'feasibility_score': 0.85, 'is_feasible': True},
            {'path_type': '实用务实型', 'feasibility_score': 0.78, 'is_feasible': True},
            {'path_type': '整体综合型', 'feasibility_score': 0.72, 'is_feasible': True}
        ],
        'low_feasibility': [
            {'path_type': '系统分析型', 'feasibility_score': 0.25, 'is_feasible': False},
            {'path_type': '创新突破型', 'feasibility_score': 0.20, 'is_feasible': False},
            {'path_type': '实用务实型', 'feasibility_score': 0.15, 'is_feasible': False}
        ],
        'mixed_feasibility': [
            {'path_type': '系统分析型', 'feasibility_score': 0.85, 'is_feasible': True},
            {'path_type': '创新突破型', 'feasibility_score': 0.35, 'is_feasible': False},
            {'path_type': '实用务实型', 'feasibility_score': 0.75, 'is_feasible': True}
        ]
    }
}

# MAB算法配置（演示用）
MAB_CONFIG = {
    "convergence_threshold": 0.05,
    "min_samples": 10,
    "algorithm_preferences": {
        'thompson_sampling': 0.4,
        'ucb_variant': 0.35,
        'epsilon_greedy': 0.25
    }
}

# 提示模板（简化版）
PROMPT_TEMPLATES = {
    "thinking_seed": """
作为AI助手，请分析以下任务：{user_query}

请从以下角度思考：
1. 问题的核心要求是什么？
2. 主要的挑战和难点在哪里？
3. 可能的解决思路有哪些？
4. 需要考虑的约束条件？

请生成一个思维种子来指导后续分析。
""",

    "dimension_creation": """
基于用户问题：{user_query}

请创建多个思维维度来全面分析这个问题：
{context_info}

历史洞察：{historical_insights}

请返回JSON格式的维度建议。
""",

    "path_selection": """
从以下思维路径中选择最适合的：
{available_paths}

考虑因素：
- 问题复杂度：{complexity}
- 预期置信度：{confidence}
- 任务特征：{task_features}

请选择最优路径并说明理由。
"""
}

# RAG配置（演示用）
RAG_CONFIG = {
    "max_search_results": 5,
    "enable_parallel_search": False,  # 演示模式关闭并行
    "max_search_workers": 2,
    "search_timeout": 10
}

# 性能配置（演示用）
PERFORMANCE_CONFIG = {
    "enable_performance_optimization": False,  # 演示模式关闭优化
    "enable_parallel_path_verification": False,
    "enable_intelligent_caching": True,
    "enable_adaptive_path_count": False,
    "enable_early_termination": False,
    "max_concurrent_verifications": 2,
    "cache_ttl_seconds": 300,
    "path_consistency_threshold": 0.8
}

# 功能特性开关
FEATURE_FLAGS = {
    "enable_performance_optimization": False,
    "enable_rag_seed_generation": True,
    "enable_real_time_verification": True,
    "enable_aha_moment_system": True,
    "enable_golden_template_system": True,
    "demo_mode": True  # 标识为演示模式
}

# 系统限制
SYSTEM_LIMITS = {
    "max_decision_history": 50,
    "max_reasoning_paths": 6,
    "max_thinking_seed_length": 1000,
    "max_path_description_length": 500
}

# 演示消息模板
DEMO_MESSAGES = {
    'welcome': """
🎭 欢迎来到AI的"内心世界"！

您即将观察到：
• 🧠 AI如何分析和理解问题
• 🛤️ AI如何生成多种解决思路
• 🎰 AI如何智能选择最优路径
• 🔬 AI如何验证想法并学习
• 💡 AI如何在困境中创新突破
• 🏆 AI如何积累和复用智慧

准备好观察AI的思考过程了吗？
""",

    'thinking_start': "🧠 AI开始思考中...",
    'thinking_complete': "✅ 思考完成！",
    'learning_update': "📚 经验已更新到知识库",
    'aha_moment': "💡 Aha-Moment！创新思考启动...",
    'golden_template': "🏆 发现黄金模板，智慧复用中...",
    
    'stage_names': {
        1: "思维种子萌发",
        2: "多路径思维展开", 
        3: "智能路径选择",
        4: "实时验证学习",
        5: "智慧决策诞生"
    }
}

# 演示统计信息
DEMO_STATS = {
    'total_demo_runs': 0,
    'successful_demonstrations': 0,
    'user_satisfaction_scores': [],
    'most_popular_scenario': '',
    'average_demo_duration': 0.0
}