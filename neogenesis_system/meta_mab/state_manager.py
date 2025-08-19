#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
状态管理器 - 统一管理系统状态和对话上下文
State Manager - Unified management of system state and conversation context
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class TaskPhase(Enum):
    """任务阶段枚举"""
    INITIALIZATION = "initialization"
    ANALYSIS = "analysis"
    TOOL_EXECUTION = "tool_execution"
    SYNTHESIS = "synthesis"
    COMPLETION = "completion"


class GoalStatus(Enum):
    """目标状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIALLY_ACHIEVED = "partially_achieved"
    ACHIEVED = "achieved"
    FAILED = "failed"


@dataclass
class ConversationTurn:
    """对话轮次数据结构"""
    turn_id: str
    timestamp: float
    user_input: str
    llm_response: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    mab_decisions: List[Dict[str, Any]] = field(default_factory=list)
    phase: TaskPhase = TaskPhase.ANALYSIS
    success: bool = True
    error_message: str = ""


@dataclass
class UserGoal:
    """用户目标数据结构"""
    goal_id: str
    original_query: str
    refined_query: str = ""
    goal_type: str = "general"  # search, analysis, generation, comparison, etc.
    priority: int = 1  # 1-10
    status: GoalStatus = GoalStatus.PENDING
    sub_goals: List[str] = field(default_factory=list)
    progress: float = 0.0  # 0.0-1.0
    expected_completion_time: Optional[float] = None
    actual_completion_time: Optional[float] = None


@dataclass
class IntermediateResult:
    """中间结果数据结构"""
    result_id: str
    source: str  # tool_name or "llm_analysis"
    content: Any
    relevance_score: float = 0.0
    quality_score: float = 0.0
    timestamp: float = 0.0
    used_in_final_answer: bool = False


@dataclass
class ExecutionStep:
    """执行步骤数据结构"""
    step_id: str
    step_type: str  # "tool_call", "analysis", "synthesis"
    description: str
    status: str  # "pending", "executing", "completed", "failed"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error_message: str = ""


class StateManager:
    """
    🏗️ 状态管理器 - 统一管理系统状态和对话上下文
    
    职责：
    1. 对话历史管理
    2. 用户目标跟踪
    3. 中间结果存储
    4. 执行步骤记录
    5. 决策历史维护
    6. 状态特征提取（为RL算法准备）
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        
        # 核心状态数据
        self.conversation_history: List[ConversationTurn] = []
        self.user_goals: List[UserGoal] = []
        self.intermediate_results: List[IntermediateResult] = []
        self.execution_steps: List[ExecutionStep] = []
        
        # 当前状态
        self.current_phase: TaskPhase = TaskPhase.INITIALIZATION
        self.current_goal_id: Optional[str] = None
        self.current_turn_id: Optional[str] = None
        
        # 上下文信息
        self.context_metadata: Dict[str, Any] = {
            'start_time': time.time(),
            'total_tokens_used': 0,
            'total_tool_calls': 0,
            'total_mab_decisions': 0,
            'complexity_score': 0.0,
            'user_satisfaction': None
        }
        
        # 决策历史（MAB相关）
        self.mab_decision_history: List[Dict[str, Any]] = []
        self.tool_performance_history: List[Dict[str, Any]] = []
        
        # 状态变化监听器
        self.state_change_listeners: List[callable] = []
        
        logger.info(f"🏗️ StateManager 初始化完成，会话ID: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:16]
    
    # ==================== 🎯 目标管理 ====================
    
    def add_user_goal(self, original_query: str, goal_type: str = "general", 
                     priority: int = 1) -> str:
        """
        添加用户目标
        
        Args:
            original_query: 原始查询
            goal_type: 目标类型
            priority: 优先级
            
        Returns:
            目标ID
        """
        goal_id = f"goal_{len(self.user_goals) + 1}_{int(time.time())}"
        
        goal = UserGoal(
            goal_id=goal_id,
            original_query=original_query,
            goal_type=goal_type,
            priority=priority,
            status=GoalStatus.PENDING
        )
        
        self.user_goals.append(goal)
        self.current_goal_id = goal_id
        
        logger.info(f"🎯 添加用户目标: {goal_id}, 类型: {goal_type}")
        self._notify_state_change("goal_added", {"goal_id": goal_id})
        
        return goal_id
    
    def update_goal_progress(self, goal_id: str, progress: float, 
                           status: Optional[GoalStatus] = None):
        """更新目标进度"""
        goal = self._find_goal_by_id(goal_id)
        if goal:
            goal.progress = max(0.0, min(1.0, progress))
            if status:
                goal.status = status
                
            if goal.status == GoalStatus.ACHIEVED:
                goal.actual_completion_time = time.time()
                
            logger.debug(f"🎯 目标进度更新: {goal_id}, 进度: {progress:.2%}")
            self._notify_state_change("goal_progress", {"goal_id": goal_id, "progress": progress})
    
    def _find_goal_by_id(self, goal_id: str) -> Optional[UserGoal]:
        """根据ID查找目标"""
        return next((goal for goal in self.user_goals if goal.goal_id == goal_id), None)
    
    # ==================== 💬 对话历史管理 ====================
    
    def start_conversation_turn(self, user_input: str) -> str:
        """
        开始新的对话轮次
        
        Args:
            user_input: 用户输入
            
        Returns:
            轮次ID
        """
        turn_id = f"turn_{len(self.conversation_history) + 1}_{int(time.time())}"
        
        turn = ConversationTurn(
            turn_id=turn_id,
            timestamp=time.time(),
            user_input=user_input,
            llm_response="",
            phase=self.current_phase
        )
        
        self.conversation_history.append(turn)
        self.current_turn_id = turn_id
        
        logger.info(f"💬 开始对话轮次: {turn_id}")
        self._notify_state_change("turn_started", {"turn_id": turn_id})
        
        return turn_id
    
    def complete_conversation_turn(self, turn_id: str, llm_response: str, 
                                 success: bool = True, error_message: str = ""):
        """完成对话轮次"""
        turn = self._find_turn_by_id(turn_id)
        if turn:
            turn.llm_response = llm_response
            turn.success = success
            turn.error_message = error_message
            
            logger.info(f"💬 完成对话轮次: {turn_id}, 成功: {success}")
            self._notify_state_change("turn_completed", {"turn_id": turn_id, "success": success})
    
    def add_tool_call_to_turn(self, turn_id: str, tool_call: Dict[str, Any], 
                            tool_result: Any = None):
        """向对话轮次添加工具调用"""
        turn = self._find_turn_by_id(turn_id)
        if turn:
            turn.tool_calls.append(tool_call)
            if tool_result is not None:
                tool_name = tool_call.get('tool_name', 'unknown')
                turn.tool_results[tool_name] = tool_result
                
            self.context_metadata['total_tool_calls'] += 1
            logger.debug(f"🔧 添加工具调用: {turn_id} -> {tool_call.get('tool_name', 'unknown')}")
    
    def add_mab_decision_to_turn(self, turn_id: str, mab_decision: Dict[str, Any]):
        """向对话轮次添加MAB决策"""
        turn = self._find_turn_by_id(turn_id)
        if turn:
            turn.mab_decisions.append(mab_decision)
            self.mab_decision_history.append(mab_decision)
            self.context_metadata['total_mab_decisions'] += 1
            
            logger.debug(f"🎯 记录MAB决策: {turn_id} -> {mab_decision.get('chosen_tool', 'no_tool')}")
    
    def _find_turn_by_id(self, turn_id: str) -> Optional[ConversationTurn]:
        """根据ID查找对话轮次"""
        return next((turn for turn in self.conversation_history if turn.turn_id == turn_id), None)
    
    # ==================== 📊 中间结果管理 ====================
    
    def add_intermediate_result(self, source: str, content: Any, 
                              relevance_score: float = 0.0, 
                              quality_score: float = 0.0) -> str:
        """
        添加中间结果
        
        Args:
            source: 结果来源
            content: 结果内容
            relevance_score: 相关性评分
            quality_score: 质量评分
            
        Returns:
            结果ID
        """
        result_id = f"result_{len(self.intermediate_results) + 1}_{int(time.time())}"
        
        result = IntermediateResult(
            result_id=result_id,
            source=source,
            content=content,
            relevance_score=relevance_score,
            quality_score=quality_score,
            timestamp=time.time()
        )
        
        self.intermediate_results.append(result)
        
        logger.debug(f"📊 添加中间结果: {result_id} from {source}")
        self._notify_state_change("result_added", {"result_id": result_id, "source": source})
        
        return result_id
    
    def mark_result_used(self, result_id: str):
        """标记结果已用于最终答案"""
        result = next((r for r in self.intermediate_results if r.result_id == result_id), None)
        if result:
            result.used_in_final_answer = True
            logger.debug(f"📊 标记结果已使用: {result_id}")
    
    # ==================== 🔄 执行步骤管理 ====================
    
    def add_execution_step(self, step_type: str, description: str) -> str:
        """
        添加执行步骤
        
        Args:
            step_type: 步骤类型
            description: 步骤描述
            
        Returns:
            步骤ID
        """
        step_id = f"step_{len(self.execution_steps) + 1}_{int(time.time())}"
        
        step = ExecutionStep(
            step_id=step_id,
            step_type=step_type,
            description=description,
            status="pending"
        )
        
        self.execution_steps.append(step)
        
        logger.debug(f"🔄 添加执行步骤: {step_id} - {description}")
        return step_id
    
    def start_execution_step(self, step_id: str):
        """开始执行步骤"""
        step = self._find_step_by_id(step_id)
        if step:
            step.status = "executing"
            step.start_time = time.time()
            logger.debug(f"🔄 开始执行步骤: {step_id}")
    
    def complete_execution_step(self, step_id: str, result: Any = None, 
                              success: bool = True, error_message: str = ""):
        """完成执行步骤"""
        step = self._find_step_by_id(step_id)
        if step:
            step.status = "completed" if success else "failed"
            step.end_time = time.time()
            step.result = result
            step.error_message = error_message
            
            logger.debug(f"🔄 完成执行步骤: {step_id}, 成功: {success}")
    
    def _find_step_by_id(self, step_id: str) -> Optional[ExecutionStep]:
        """根据ID查找执行步骤"""
        return next((step for step in self.execution_steps if step.step_id == step_id), None)
    
    # ==================== 📈 状态获取和特征提取 ====================
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        获取当前完整状态
        
        Returns:
            当前状态字典
        """
        current_goal = self._find_goal_by_id(self.current_goal_id) if self.current_goal_id else None
        current_turn = self._find_turn_by_id(self.current_turn_id) if self.current_turn_id else None
        
        state = {
            # 基本信息
            'session_id': self.session_id,
            'current_phase': self.current_phase.value,
            'timestamp': time.time(),
            
            # 当前目标
            'current_goal': {
                'goal_id': current_goal.goal_id if current_goal else None,
                'original_query': current_goal.original_query if current_goal else "",
                'goal_type': current_goal.goal_type if current_goal else "general",
                'progress': current_goal.progress if current_goal else 0.0,
                'status': current_goal.status.value if current_goal else "pending"
            },
            
            # 对话状态
            'conversation': {
                'total_turns': len(self.conversation_history),
                'current_turn_id': self.current_turn_id,
                'last_user_input': current_turn.user_input if current_turn else "",
                'last_llm_response': current_turn.llm_response if current_turn else ""
            },
            
            # 执行状态
            'execution': {
                'total_steps': len(self.execution_steps),
                'completed_steps': len([s for s in self.execution_steps if s.status == "completed"]),
                'failed_steps': len([s for s in self.execution_steps if s.status == "failed"]),
                'current_step': self._get_current_step()
            },
            
            # 结果状态
            'results': {
                'total_results': len(self.intermediate_results),
                'used_results': len([r for r in self.intermediate_results if r.used_in_final_answer]),
                'average_quality': self._calculate_average_quality(),
                'average_relevance': self._calculate_average_relevance()
            },
            
            # MAB状态
            'mab': {
                'total_decisions': len(self.mab_decision_history),
                'recent_tools': self._get_recent_tool_usage(),
                'decision_patterns': self._analyze_decision_patterns()
            },
            
            # 上下文元数据
            'metadata': self.context_metadata.copy()
        }
        
        return state
    
    def get_state_features_for_rl(self) -> Dict[str, float]:
        """
        为RL算法提取状态特征
        
        Returns:
            标准化的状态特征字典
        """
        current_goal = self._find_goal_by_id(self.current_goal_id) if self.current_goal_id else None
        
        # 基础特征
        features = {
            # 任务特征
            'goal_progress': current_goal.progress if current_goal else 0.0,
            'task_complexity': self.context_metadata.get('complexity_score', 0.0),
            'elapsed_time': (time.time() - self.context_metadata['start_time']) / 3600,  # 小时
            
            # 对话特征
            'conversation_length': len(self.conversation_history),
            'average_turn_success': self._calculate_average_turn_success(),
            'tool_usage_rate': self._calculate_tool_usage_rate(),
            
            # 执行特征
            'execution_success_rate': self._calculate_execution_success_rate(),
            'step_completion_rate': self._calculate_step_completion_rate(),
            
            # 结果特征
            'result_quality': self._calculate_average_quality(),
            'result_relevance': self._calculate_average_relevance(),
            'result_utilization': self._calculate_result_utilization(),
            
            # MAB特征
            'mab_exploration_rate': self._calculate_mab_exploration_rate(),
            'tool_diversity': self._calculate_tool_diversity(),
            'decision_consistency': self._calculate_decision_consistency()
        }
        
        # 标准化特征值到0-1范围
        normalized_features = {}
        for key, value in features.items():
            if isinstance(value, (int, float)):
                normalized_features[key] = max(0.0, min(1.0, float(value)))
            else:
                normalized_features[key] = 0.0
        
        return normalized_features
    
    # ==================== 🔧 辅助方法 ====================
    
    def _get_current_step(self) -> Optional[str]:
        """获取当前执行步骤"""
        executing_steps = [s for s in self.execution_steps if s.status == "executing"]
        return executing_steps[0].step_id if executing_steps else None
    
    def _calculate_average_quality(self) -> float:
        """计算平均质量分数"""
        if not self.intermediate_results:
            return 0.0
        return sum(r.quality_score for r in self.intermediate_results) / len(self.intermediate_results)
    
    def _calculate_average_relevance(self) -> float:
        """计算平均相关性分数"""
        if not self.intermediate_results:
            return 0.0
        return sum(r.relevance_score for r in self.intermediate_results) / len(self.intermediate_results)
    
    def _get_recent_tool_usage(self, limit: int = 5) -> List[str]:
        """获取最近使用的工具"""
        recent_decisions = self.mab_decision_history[-limit:] if self.mab_decision_history else []
        return [d.get('chosen_tool', 'no_tool') for d in recent_decisions]
    
    def _analyze_decision_patterns(self) -> Dict[str, Any]:
        """分析决策模式"""
        if not self.mab_decision_history:
            return {'total': 0, 'patterns': {}}
        
        tool_counts = {}
        for decision in self.mab_decision_history:
            tool = decision.get('chosen_tool', 'no_tool')
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        return {
            'total': len(self.mab_decision_history),
            'tool_distribution': tool_counts,
            'most_used_tool': max(tool_counts.items(), key=lambda x: x[1])[0] if tool_counts else None
        }
    
    def _calculate_average_turn_success(self) -> float:
        """计算平均对话成功率"""
        if not self.conversation_history:
            return 0.0
        successful_turns = sum(1 for turn in self.conversation_history if turn.success)
        return successful_turns / len(self.conversation_history)
    
    def _calculate_tool_usage_rate(self) -> float:
        """计算工具使用率"""
        if not self.conversation_history:
            return 0.0
        turns_with_tools = sum(1 for turn in self.conversation_history if turn.tool_calls)
        return turns_with_tools / len(self.conversation_history)
    
    def _calculate_execution_success_rate(self) -> float:
        """计算执行成功率"""
        if not self.execution_steps:
            return 0.0
        successful_steps = sum(1 for step in self.execution_steps if step.status == "completed")
        total_finished = sum(1 for step in self.execution_steps if step.status in ["completed", "failed"])
        return successful_steps / total_finished if total_finished > 0 else 0.0
    
    def _calculate_step_completion_rate(self) -> float:
        """计算步骤完成率"""
        if not self.execution_steps:
            return 0.0
        completed_steps = sum(1 for step in self.execution_steps if step.status == "completed")
        return completed_steps / len(self.execution_steps)
    
    def _calculate_result_utilization(self) -> float:
        """计算结果利用率"""
        if not self.intermediate_results:
            return 0.0
        used_results = sum(1 for result in self.intermediate_results if result.used_in_final_answer)
        return used_results / len(self.intermediate_results)
    
    def _calculate_mab_exploration_rate(self) -> float:
        """计算MAB探索率"""
        # 这里需要根据具体的MAB算法实现来计算
        # 简单示例：不同工具的使用分布
        if not self.mab_decision_history:
            return 0.0
        
        tool_set = set(d.get('chosen_tool', 'no_tool') for d in self.mab_decision_history)
        return len(tool_set) / max(len(self.mab_decision_history), 1)
    
    def _calculate_tool_diversity(self) -> float:
        """计算工具多样性"""
        recent_tools = self._get_recent_tool_usage(10)
        if not recent_tools:
            return 0.0
        return len(set(recent_tools)) / len(recent_tools)
    
    def _calculate_decision_consistency(self) -> float:
        """计算决策一致性"""
        # 在相似状态下的决策一致性（简化实现）
        if len(self.mab_decision_history) < 2:
            return 1.0
        
        # 简单的一致性度量：连续决策的相似度
        consistent_decisions = 0
        for i in range(1, len(self.mab_decision_history)):
            if (self.mab_decision_history[i].get('chosen_tool') == 
                self.mab_decision_history[i-1].get('chosen_tool')):
                consistent_decisions += 1
        
        return consistent_decisions / (len(self.mab_decision_history) - 1)
    
    # ==================== 🔔 状态变化通知 ====================
    
    def add_state_change_listener(self, listener: callable):
        """添加状态变化监听器"""
        self.state_change_listeners.append(listener)
        logger.debug(f"🔔 添加状态变化监听器: {listener.__name__}")
    
    def _notify_state_change(self, event_type: str, event_data: Dict[str, Any]):
        """通知状态变化"""
        for listener in self.state_change_listeners:
            try:
                listener(event_type, event_data, self)
            except Exception as e:
                logger.error(f"❌ 状态变化监听器错误: {e}")
    
    # ==================== 📊 状态序列化和持久化 ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """将状态序列化为字典"""
        return {
            'session_id': self.session_id,
            'current_phase': self.current_phase.value,
            'current_goal_id': self.current_goal_id,
            'current_turn_id': self.current_turn_id,
            'conversation_history': [self._serialize_turn(turn) for turn in self.conversation_history],
            'user_goals': [self._serialize_goal(goal) for goal in self.user_goals],
            'intermediate_results': [self._serialize_result(result) for result in self.intermediate_results],
            'execution_steps': [self._serialize_step(step) for step in self.execution_steps],
            'context_metadata': self.context_metadata,
            'mab_decision_history': self.mab_decision_history
        }
    
    def _serialize_turn(self, turn: ConversationTurn) -> Dict[str, Any]:
        """序列化对话轮次"""
        return {
            'turn_id': turn.turn_id,
            'timestamp': turn.timestamp,
            'user_input': turn.user_input,
            'llm_response': turn.llm_response,
            'tool_calls': turn.tool_calls,
            'tool_results': turn.tool_results,
            'mab_decisions': turn.mab_decisions,
            'phase': turn.phase.value,
            'success': turn.success,
            'error_message': turn.error_message
        }
    
    def _serialize_goal(self, goal: UserGoal) -> Dict[str, Any]:
        """序列化用户目标"""
        return {
            'goal_id': goal.goal_id,
            'original_query': goal.original_query,
            'refined_query': goal.refined_query,
            'goal_type': goal.goal_type,
            'priority': goal.priority,
            'status': goal.status.value,
            'sub_goals': goal.sub_goals,
            'progress': goal.progress,
            'expected_completion_time': goal.expected_completion_time,
            'actual_completion_time': goal.actual_completion_time
        }
    
    def _serialize_result(self, result: IntermediateResult) -> Dict[str, Any]:
        """序列化中间结果"""
        return {
            'result_id': result.result_id,
            'source': result.source,
            'content': str(result.content),  # 简化处理
            'relevance_score': result.relevance_score,
            'quality_score': result.quality_score,
            'timestamp': result.timestamp,
            'used_in_final_answer': result.used_in_final_answer
        }
    
    def _serialize_step(self, step: ExecutionStep) -> Dict[str, Any]:
        """序列化执行步骤"""
        return {
            'step_id': step.step_id,
            'step_type': step.step_type,
            'description': step.description,
            'status': step.status,
            'start_time': step.start_time,
            'end_time': step.end_time,
            'result': str(step.result) if step.result else None,
            'error_message': step.error_message
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        current_goal = self._find_goal_by_id(self.current_goal_id) if self.current_goal_id else None
        
        return {
            'session_id': self.session_id,
            'duration': time.time() - self.context_metadata['start_time'],
            'phase': self.current_phase.value,
            'goal_progress': current_goal.progress if current_goal else 0.0,
            'total_turns': len(self.conversation_history),
            'total_tool_calls': self.context_metadata['total_tool_calls'],
            'total_mab_decisions': self.context_metadata['total_mab_decisions'],
            'success_rate': self._calculate_average_turn_success(),
            'result_quality': self._calculate_average_quality(),
            'completion_status': current_goal.status.value if current_goal else "unknown"
        }
