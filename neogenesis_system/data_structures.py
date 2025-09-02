#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用数据结构定义 - Universal Data Structures
定义框架级别的核心数据结构，为所有模块提供统一的数据格式

这些数据结构是框架的基础"词汇"，确保所有组件都能以相同的方式理解和交换信息。
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class ActionStatus(Enum):
    """行动状态枚举"""
    PENDING = "pending"       # 等待执行
    EXECUTING = "executing"   # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    SKIPPED = "skipped"       # 跳过执行


class PlanStatus(Enum):
    """计划状态枚举"""
    CREATED = "created"       # 已创建
    EXECUTING = "executing"   # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    CANCELLED = "cancelled"   # 已取消


@dataclass
class Action:
    """
    行动 - 最基本的指令单元
    
    这是框架中最基本的执行单位。每个Action代表一次具体的工具调用，
    清楚地说明了要使用哪个工具以及需要什么输入参数。
    
    Attributes:
        tool_name: 工具名称，必须是已注册的工具
        tool_input: 工具输入参数，字典格式
        action_id: 行动的唯一标识符
        status: 行动状态
        created_at: 创建时间戳
        started_at: 开始执行时间戳
        completed_at: 完成时间戳
        metadata: 附加元数据
    """
    tool_name: str
    tool_input: Dict[str, Any]
    action_id: str = ""
    status: ActionStatus = ActionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理：生成action_id"""
        if not self.action_id:
            timestamp = int(time.time() * 1000)
            self.action_id = f"action_{self.tool_name}_{timestamp}"
    
    def start_execution(self):
        """标记行动开始执行"""
        self.status = ActionStatus.EXECUTING
        self.started_at = time.time()
    
    def complete_execution(self):
        """标记行动执行完成"""
        self.status = ActionStatus.COMPLETED
        self.completed_at = time.time()
    
    def fail_execution(self):
        """标记行动执行失败"""
        self.status = ActionStatus.FAILED
        self.completed_at = time.time()
    
    @property
    def execution_time(self) -> Optional[float]:
        """计算执行时间"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class Plan:
    """
    计划 - 规划器的最终输出
    
    Plan是Planner生成的完整执行方案，包含Agent的思考过程和具体的行动序列。
    如果任务不需要工具就能直接回答，Plan会包含final_answer。
    
    Attributes:
        thought: Agent的思考过程，解释为什么选择这些行动
        actions: 行动列表，按执行顺序排列
        final_answer: 如果不需要工具就能回答，直接提供答案
        plan_id: 计划的唯一标识符
        status: 计划状态
        created_at: 创建时间戳
        metadata: 附加元数据
        confidence: 计划的置信度分数
        estimated_time: 预估执行时间
    """
    thought: str
    actions: List[Action] = field(default_factory=list)
    final_answer: Optional[str] = None
    plan_id: str = ""
    status: PlanStatus = PlanStatus.CREATED
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    estimated_time: Optional[float] = None
    
    def __post_init__(self):
        """初始化后处理：生成plan_id"""
        if not self.plan_id:
            timestamp = int(time.time() * 1000)
            self.plan_id = f"plan_{timestamp}"
    
    def add_action(self, action: Action):
        """添加行动到计划中"""
        self.actions.append(action)
    
    def start_execution(self):
        """标记计划开始执行"""
        self.status = PlanStatus.EXECUTING
    
    def complete_execution(self):
        """标记计划执行完成"""
        self.status = PlanStatus.COMPLETED
    
    def fail_execution(self):
        """标记计划执行失败"""
        self.status = PlanStatus.FAILED
    
    def cancel_execution(self):
        """标记计划已取消"""
        self.status = PlanStatus.CANCELLED
    
    @property
    def is_direct_answer(self) -> bool:
        """判断是否为直接回答（不需要执行工具）"""
        return self.final_answer is not None and len(self.actions) == 0
    
    @property
    def action_count(self) -> int:
        """获取行动数量"""
        return len(self.actions)
    
    @property
    def pending_actions(self) -> List[Action]:
        """获取待执行的行动"""
        return [action for action in self.actions if action.status == ActionStatus.PENDING]
    
    @property
    def completed_actions(self) -> List[Action]:
        """获取已完成的行动"""
        return [action for action in self.actions if action.status == ActionStatus.COMPLETED]


@dataclass
class Observation:
    """
    观察 - 执行行动后的结果
    
    Observation记录了执行某个Action后得到的具体结果，包括成功输出或错误信息。
    这是Agent学习和调整策略的重要数据来源。
    
    Attributes:
        action: 执行的行动对象
        output: 工具返回的输出结果
        success: 执行是否成功
        error_message: 如果失败，错误信息
        execution_time: 执行耗时
        timestamp: 观察记录的时间戳
        metadata: 附加元数据
    """
    action: Action
    output: str
    success: bool = True
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def action_id(self) -> str:
        """获取关联的行动ID"""
        return self.action.action_id
    
    @property
    def tool_name(self) -> str:
        """获取使用的工具名称"""
        return self.action.tool_name
    
    def is_successful(self) -> bool:
        """判断执行是否成功"""
        return self.success and self.error_message is None


@dataclass
class ExecutionContext:
    """
    执行上下文 - 记录完整的执行过程
    
    ExecutionContext跟踪一个完整的任务执行过程，包括计划、所有观察结果和最终状态。
    这为系统提供了完整的执行历史和学习数据。
    
    Attributes:
        plan: 执行的计划
        observations: 所有观察结果
        final_result: 最终执行结果
        total_time: 总执行时间
        context_id: 上下文的唯一标识符
        created_at: 创建时间戳
        metadata: 附加元数据
    """
    plan: Plan
    observations: List[Observation] = field(default_factory=list)
    final_result: Optional[str] = None
    total_time: Optional[float] = None
    context_id: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理：生成context_id"""
        if not self.context_id:
            timestamp = int(time.time() * 1000)
            self.context_id = f"ctx_{timestamp}"
    
    def add_observation(self, observation: Observation):
        """添加观察结果"""
        self.observations.append(observation)
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if not self.observations:
            return 0.0
        successful = sum(1 for obs in self.observations if obs.is_successful())
        return successful / len(self.observations)
    
    @property
    def failed_observations(self) -> List[Observation]:
        """获取失败的观察结果"""
        return [obs for obs in self.observations if not obs.is_successful()]
    
    @property
    def successful_observations(self) -> List[Observation]:
        """获取成功的观察结果"""
        return [obs for obs in self.observations if obs.is_successful()]


@dataclass
class AgentState:
    """
    Agent状态 - 记录Agent的当前状态和历史
    
    AgentState维护Agent的完整状态信息，包括当前执行的任务、历史记录和性能统计。
    
    Attributes:
        current_context: 当前执行上下文
        execution_history: 历史执行记录
        memory_state: 内存状态快照
        performance_metrics: 性能指标
        state_id: 状态的唯一标识符
        last_updated: 最后更新时间
        metadata: 附加元数据
    """
    current_context: Optional[ExecutionContext] = None
    execution_history: List[ExecutionContext] = field(default_factory=list)
    memory_state: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    state_id: str = ""
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理：生成state_id"""
        if not self.state_id:
            timestamp = int(time.time() * 1000)
            self.state_id = f"state_{timestamp}"
    
    def update_context(self, context: ExecutionContext):
        """更新当前执行上下文"""
        if self.current_context:
            self.execution_history.append(self.current_context)
        self.current_context = context
        self.last_updated = time.time()
    
    def complete_current_task(self):
        """完成当前任务"""
        if self.current_context:
            self.execution_history.append(self.current_context)
            self.current_context = None
            self.last_updated = time.time()
    
    @property
    def total_executions(self) -> int:
        """获取总执行次数"""
        return len(self.execution_history)
    
    @property
    def average_success_rate(self) -> float:
        """计算平均成功率"""
        if not self.execution_history:
            return 0.0
        total_rate = sum(ctx.success_rate for ctx in self.execution_history)
        return total_rate / len(self.execution_history)
