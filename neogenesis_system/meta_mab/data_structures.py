#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据结构定义 - 存放所有数据类和类型定义
Data Structures - contains all data classes and type definitions
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ReasoningPath:
    """代表一个完整且独特的思考范式"""
    path_id: str  # 路径的唯一标识，例如 'systematic_methodical_v1'
    path_type: str  # 路径类型，如 '系统方法型', '创新直觉型', '批判质疑型'
    description: str  # 对这条思维路径的详细描述
    prompt_template: str  # 执行该路径时，用于生成最终提示的核心模板
    
    # 🎯 MAB学习修复：新增策略级别固定ID用于MAB学习
    strategy_id: str = ""  # 策略级别的固定ID，用于MAB学习（如'systematic_analytical'）
    instance_id: str = ""  # 实例级别的唯一ID，用于会话追踪（如'systematic_analytical_v1_1703123456789_1234'）
    
    def __post_init__(self):
        """初始化后处理：简化版，数据源头现在保证ID正确性"""
        # 🎯 根源修复：PathGenerator现在直接提供正确的ID，简化后处理逻辑
        # 只做基本的兼容性检查
        if not self.strategy_id:
            # 后备方案：使用path_id（向后兼容）
            self.strategy_id = self.path_id
            
        if not self.instance_id:
            # 后备方案：使用path_id（向后兼容）
            self.instance_id = self.path_id


@dataclass 
class TaskComplexity:
    """任务复杂度"""
    overall_score: float = 0.5
    factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class EnhancedDecisionArm:
    """决策臂 - 追踪思维路径的性能"""
    path_id: str  # 关联的思维路径ID
    option: str = ""  # 路径类型/选项 (兼容性字段)
    
    # 基础性能追踪
    success_count: int = 0
    failure_count: int = 0
    total_reward: float = 0.0
    
    # 历史记录（限制长度避免内存膨胀）
    recent_rewards: List[float] = field(default_factory=list)  # 最近的奖励记录
    rl_reward_history: List[float] = field(default_factory=list)  # RL奖励历史
    recent_results: List[bool] = field(default_factory=list)  # 最近的执行结果
    
    # 使用统计
    activation_count: int = 0
    last_used: float = 0.0
    
    def update_performance(self, success: bool, reward: float):
        """更新性能数据"""
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            
        self.total_reward += reward
        self.recent_rewards.append(reward)
        self.rl_reward_history.append(reward)  # 添加到RL奖励历史
        self.recent_results.append(success)  # 添加到结果历史
        
        # 限制历史长度
        if len(self.recent_rewards) > 20:
            self.recent_rewards = self.recent_rewards[-10:]
        if len(self.rl_reward_history) > 50:
            self.rl_reward_history = self.rl_reward_history[-25:]
        if len(self.recent_results) > 50:
            self.recent_results = self.recent_results[-25:]
            
        self.activation_count += 1
        self.last_used = time.time()
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / max(total, 1)
    
    @property
    def average_reward(self) -> float:
        """平均奖励"""
        if not self.recent_rewards:
            return 0.0
        return sum(self.recent_rewards) / len(self.recent_rewards)
    
    @property
    def total_uses(self) -> int:
        """总使用次数"""
        return self.success_count + self.failure_count


@dataclass
class TaskContext:
    """任务上下文"""
    user_query: str
    task_type: str = "general"
    complexity_score: float = 0.5
    deepseek_confidence: float = 0.5
    real_time_requirements: bool = False
    domain_tags: List[str] = field(default_factory=list)
    execution_context: Optional[Dict] = None
    dynamic_classification: Optional[Dict] = None


@dataclass
class DecisionResult:
    """决策结果数据结构"""
    timestamp: float
    round_number: int
    user_query: str
    selected_dimensions: Dict[str, str]
    confidence_scores: Dict[str, float]
    task_confidence: float
    complexity_analysis: Dict[str, Any]
    mab_decisions: Dict[str, Dict[str, Any]]
    reasoning: str
    fallback_used: bool
    component_architecture: bool = True
    
    # 可选字段
    overall_confidence: Optional[float] = None
    algorithm_used: Optional[str] = None
    dimension_count: Optional[int] = None
    bypass_reason: Optional[str] = None
    direct_response: Optional[str] = None


@dataclass
class PerformanceFeedback:
    """性能反馈数据结构"""
    timestamp: float
    execution_success: bool
    execution_time: float
    user_satisfaction: float
    rl_reward: float
    task_completion_score: float = 0.0
    error_details: Optional[str] = None
    output_quality_score: Optional[float] = None


@dataclass
class LimitationAnalysis:
    """局限性分析结果"""
    type: str
    severity: float
    description: str
    specific_context: str
    impact: str
    confidence: float
    compensation_strategy: List[str]
    source: str
    timestamp: float


@dataclass
class AlternativeThinkingSignal:
    """替代思考信号"""
    timestamp: float
    user_query: str
    reason: str
    suggested_reassessment: bool
    creative_approaches_needed: bool
    environmental_exploration: bool


@dataclass
class FailureAnalysis:
    """失败分析结果"""
    timestamp: float
    user_query: str
    failed_dimensions: Dict[str, str]
    rl_reward: float
    failure_severity: float
    consecutive_failures: int
    context_change_needed: bool
    alternative_strategies: List[str]


@dataclass
class SuccessPattern:
    """成功模式数据结构"""
    pattern_id: str
    dimension_combination: Dict[str, str]
    success_contexts: List[str]
    quality_score: float
    replication_count: int
    confidence: float
    last_used: float
    
    
@dataclass
class SystemStatus:
    """系统状态数据结构"""
    total_rounds: int
    component_architecture: bool
    prior_reasoner_assessments: int
    path_generator_cache_size: int
    mab_converger_arms: int
    convergence_status: Dict[str, bool]
    recent_decisions: int
    
    # 性能指标
    avg_decision_time: Optional[float] = None
    success_rate: Optional[float] = None
    exploration_rate: Optional[float] = None