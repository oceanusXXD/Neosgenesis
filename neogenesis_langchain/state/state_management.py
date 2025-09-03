
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - Enhanced State Management for LangChain Integration
为LangChain集成提供增强的状态管理功能
集成：分布式状态、MAB优化、事务管理、持久化存储
"""

import json
import logging
import time
import pickle
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

# 导入第三阶段新组件
try:
    from ..storage.persistent_storage import PersistentStorageEngine, StorageConfig, create_storage_engine
    from .distributed_state import DistributedStateManager, create_distributed_state_manager
    from ..optimization.mab_optimization import AdvancedMABManager, create_mab_manager
    from .state_transactions import TransactionManager, create_transaction_manager
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    PersistentStorageEngine = None
    DistributedStateManager = None
    AdvancedMABManager = None
    TransactionManager = None

logger = logging.getLogger(__name__)

# =============================================================================
# 状态枚举和数据模型
# =============================================================================

class DecisionStage(Enum):
    """决策阶段枚举"""
    THINKING_SEED = "thinking_seed"
    SEED_VERIFICATION = "seed_verification"
    PATH_GENERATION = "path_generation"
    PATH_VERIFICATION = "path_verification"
    MAB_DECISION = "mab_decision"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class StageResult:
    """单个阶段的结果"""
    stage: DecisionStage
    success: bool
    data: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class DecisionState:
    """Neogenesis决策状态"""
    session_id: str
    user_query: str
    current_stage: DecisionStage
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    execution_context: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 中间数据
    thinking_seed: Optional[str] = None
    reasoning_paths: List[Dict[str, Any]] = field(default_factory=list)
    verified_paths: List[Dict[str, Any]] = field(default_factory=list)
    selected_path: Optional[Dict[str, Any]] = None
    
    # 配置
    use_rag_enhancement: bool = True
    max_paths: int = 4
    enable_verification: bool = True
    
    def update_stage(self, stage: DecisionStage, result: StageResult):
        """更新阶段状态"""
        self.current_stage = stage
        self.stage_results[stage.value] = result
        self.updated_at = time.time()
        
        # 更新中间数据
        if stage == DecisionStage.THINKING_SEED and result.success:
            self.thinking_seed = result.data.get("thinking_seed")
        elif stage == DecisionStage.PATH_GENERATION and result.success:
            self.reasoning_paths = result.data.get("reasoning_paths", [])
        elif stage == DecisionStage.PATH_VERIFICATION and result.success:
            self.verified_paths = result.data.get("verified_paths", [])
        elif stage == DecisionStage.MAB_DECISION and result.success:
            self.selected_path = result.data.get("selected_path")
    
    def get_stage_result(self, stage: DecisionStage) -> Optional[StageResult]:
        """获取指定阶段的结果"""
        return self.stage_results.get(stage.value)
    
    def is_stage_completed(self, stage: DecisionStage) -> bool:
        """检查阶段是否完成"""
        result = self.get_stage_result(stage)
        return result is not None and result.success
    
    def get_completion_rate(self) -> float:
        """获取完成率"""
        total_stages = len(DecisionStage) - 2  # 排除COMPLETED和ERROR
        completed_stages = sum(1 for stage in DecisionStage 
                             if stage not in [DecisionStage.COMPLETED, DecisionStage.ERROR]
                             and self.is_stage_completed(stage))
        return completed_stages / total_stages
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举
        data["current_stage"] = self.current_stage.value
        # 转换StageResult对象
        stage_results = {}
        for stage_name, result in self.stage_results.items():
            stage_results[stage_name] = asdict(result)
            stage_results[stage_name]["stage"] = result.stage.value
        data["stage_results"] = stage_results
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionState":
        """从字典创建"""
        # 转换枚举
        data["current_stage"] = DecisionStage(data["current_stage"])
        
        # 转换StageResult对象
        stage_results = {}
        for stage_name, result_data in data.get("stage_results", {}).items():
            result_data["stage"] = DecisionStage(result_data["stage"])
            stage_results[stage_name] = StageResult(**result_data)
        data["stage_results"] = stage_results
        
        return cls(**data)

@dataclass
class MABWeights:
    """MAB权重数据"""
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    strategy_counts: Dict[str, int] = field(default_factory=dict)
    strategy_rewards: Dict[str, List[float]] = field(default_factory=dict)
    total_rounds: int = 0
    last_updated: float = field(default_factory=time.time)
    
    def update_strategy(self, strategy_id: str, reward: float):
        """更新策略权重"""
        if strategy_id not in self.strategy_weights:
            self.strategy_weights[strategy_id] = 0.5
            self.strategy_counts[strategy_id] = 0
            self.strategy_rewards[strategy_id] = []
        
        self.strategy_counts[strategy_id] += 1
        self.strategy_rewards[strategy_id].append(reward)
        
        # 更新权重（简化的UCB算法）
        avg_reward = sum(self.strategy_rewards[strategy_id]) / len(self.strategy_rewards[strategy_id])
        self.strategy_weights[strategy_id] = avg_reward
        
        self.total_rounds += 1
        self.last_updated = time.time()
    
    def get_strategy_confidence(self, strategy_id: str) -> float:
        """获取策略置信度"""
        if strategy_id not in self.strategy_weights:
            return 0.5
        
        count = self.strategy_counts[strategy_id]
        if count == 0:
            return 0.5
        
        # 基于使用次数的置信度
        confidence = min(1.0, count / 10)  # 10次后达到最高置信度
        return confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MABWeights":
        """从字典创建"""
        return cls(**data)

# =============================================================================
# 状态管理器
# =============================================================================

class NeogenesisStateManager:
    """
    Neogenesis状态管理器
    
    功能：
    - 管理决策状态的生命周期
    - 持久化MAB权重
    - 提供状态查询和更新接口
    - 支持多会话管理
    """
    
    def __init__(self, 
                 storage_path: str = "./neogenesis_state",
                 max_sessions: int = 1000,
                 auto_save: bool = True):
        """
        初始化状态管理器
        
        Args:
            storage_path: 存储路径
            max_sessions: 最大会话数
            auto_save: 是否自动保存
        """
        self.storage_path = Path(storage_path)
        self.max_sessions = max_sessions
        self.auto_save = auto_save
        
        # 内存状态
        self.active_sessions: Dict[str, DecisionState] = {}
        self.mab_weights = MABWeights()
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载持久化数据
        self._load_mab_weights()
        
        logger.info(f"🗃️ NeogenesisStateManager 初始化完成: {self.storage_path}")
    
    def create_session(self, 
                      session_id: str,
                      user_query: str,
                      execution_context: Optional[Dict[str, Any]] = None,
                      **kwargs) -> DecisionState:
        """
        创建新的决策会话
        
        Args:
            session_id: 会话ID
            user_query: 用户查询
            execution_context: 执行上下文
            **kwargs: 其他配置
            
        Returns:
            决策状态对象
        """
        # 检查会话限制
        if len(self.active_sessions) >= self.max_sessions:
            self._cleanup_old_sessions()
        
        # 创建新状态
        decision_state = DecisionState(
            session_id=session_id,
            user_query=user_query,
            current_stage=DecisionStage.THINKING_SEED,
            execution_context=execution_context,
            **kwargs
        )
        
        self.active_sessions[session_id] = decision_state
        
        if self.auto_save:
            self._save_session(session_id)
        
        logger.info(f"📝 创建决策会话: {session_id}")
        return decision_state
    
    def get_session(self, session_id: str) -> Optional[DecisionState]:
        """获取决策会话"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # 尝试从磁盘加载
        return self._load_session(session_id)
    
    def update_session_stage(self,
                           session_id: str,
                           stage: DecisionStage,
                           success: bool,
                           data: Dict[str, Any],
                           execution_time: float,
                           error_message: Optional[str] = None) -> bool:
        """
        更新会话阶段
        
        Args:
            session_id: 会话ID
            stage: 决策阶段
            success: 是否成功
            data: 阶段数据
            execution_time: 执行时间
            error_message: 错误消息
            
        Returns:
            是否更新成功
        """
        session = self.get_session(session_id)
        if not session:
            logger.error(f"❌ 会话不存在: {session_id}")
            return False
        
        # 创建阶段结果
        stage_result = StageResult(
            stage=stage,
            success=success,
            data=data,
            execution_time=execution_time,
            error_message=error_message
        )
        
        # 更新会话状态
        session.update_stage(stage, stage_result)
        
        # 如果是MAB决策阶段，更新权重
        if stage == DecisionStage.MAB_DECISION and success:
            selected_path = data.get("selected_path", {})
            strategy_id = selected_path.get("strategy_id")
            if strategy_id:
                # 简化的奖励计算
                reward = 1.0 if success else 0.0
                self.mab_weights.update_strategy(strategy_id, reward)
        
        if self.auto_save:
            self._save_session(session_id)
            self._save_mab_weights()
        
        logger.debug(f"📊 更新会话阶段: {session_id} -> {stage.value}")
        return True
    
    def complete_session(self, session_id: str, final_result: Dict[str, Any]) -> bool:
        """完成决策会话"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.current_stage = DecisionStage.COMPLETED
        session.updated_at = time.time()
        
        if self.auto_save:
            self._save_session(session_id)
        
        logger.info(f"✅ 完成决策会话: {session_id}")
        return True
    
    def get_mab_weights(self) -> MABWeights:
        """获取MAB权重"""
        return self.mab_weights
    
    def get_strategy_recommendation(self, available_strategies: List[str]) -> str:
        """获取策略推荐"""
        if not available_strategies:
            return ""
        
        # 简化的策略选择：选择权重最高的
        best_strategy = available_strategies[0]
        best_weight = self.mab_weights.strategy_weights.get(best_strategy, 0.5)
        
        for strategy in available_strategies[1:]:
            weight = self.mab_weights.strategy_weights.get(strategy, 0.5)
            if weight > best_weight:
                best_strategy = strategy
                best_weight = weight
        
        return best_strategy
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        active_count = len(self.active_sessions)
        
        # 统计阶段分布
        stage_distribution = {}
        for session in self.active_sessions.values():
            stage = session.current_stage.value
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
        
        # 统计完成率
        completion_rates = [session.get_completion_rate() 
                          for session in self.active_sessions.values()]
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0
        
        return {
            "active_sessions": active_count,
            "stage_distribution": stage_distribution,
            "avg_completion_rate": avg_completion_rate,
            "mab_total_rounds": self.mab_weights.total_rounds,
            "mab_strategies": len(self.mab_weights.strategy_weights)
        }
    
    def cleanup_session(self, session_id: str) -> bool:
        """清理会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
            # 删除持久化文件
            session_file = self.storage_path / f"session_{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            logger.info(f"🗑️ 清理会话: {session_id}")
            return True
        return False
    
    def _cleanup_old_sessions(self):
        """清理旧会话"""
        if len(self.active_sessions) < self.max_sessions:
            return
        
        # 按创建时间排序，删除最旧的会话
        sessions = list(self.active_sessions.items())
        sessions.sort(key=lambda x: x[1].created_at)
        
        cleanup_count = len(sessions) - self.max_sessions + 100  # 清理多一些
        for i in range(cleanup_count):
            session_id, _ = sessions[i]
            self.cleanup_session(session_id)
        
        logger.info(f"🧹 清理了 {cleanup_count} 个旧会话")
    
    def _save_session(self, session_id: str):
        """保存会话到磁盘"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        session_file = self.storage_path / f"session_{session_id}.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存会话失败 {session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[DecisionState]:
        """从磁盘加载会话"""
        session_file = self.storage_path / f"session_{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = DecisionState.from_dict(data)
            self.active_sessions[session_id] = session
            return session
        except Exception as e:
            logger.error(f"❌ 加载会话失败 {session_id}: {e}")
            return None
    
    def _save_mab_weights(self):
        """保存MAB权重"""
        weights_file = self.storage_path / "mab_weights.json"
        try:
            with open(weights_file, 'w', encoding='utf-8') as f:
                json.dump(self.mab_weights.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存MAB权重失败: {e}")
    
    def _load_mab_weights(self):
        """加载MAB权重"""
        weights_file = self.storage_path / "mab_weights.json"
        if not weights_file.exists():
            return
        
        try:
            with open(weights_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.mab_weights = MABWeights.from_dict(data)
            logger.info(f"📊 加载MAB权重: {len(self.mab_weights.strategy_weights)}个策略")
        except Exception as e:
            logger.error(f"❌ 加载MAB权重失败: {e}")

# =============================================================================
# 便捷类
# =============================================================================

class MABPersistentWeights:
    """MAB持久化权重管理器（简化版）"""
    
    def __init__(self, storage_path: str = "./mab_weights.pkl"):
        self.storage_path = storage_path
        self.weights = self._load_weights()
    
    def _load_weights(self) -> Dict[str, float]:
        """加载权重"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"❌ 加载权重失败: {e}")
        return {}
    
    def save_weights(self):
        """保存权重"""
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump(self.weights, f)
        except Exception as e:
            logger.error(f"❌ 保存权重失败: {e}")
    
    def update_weight(self, strategy_id: str, reward: float):
        """更新权重"""
        if strategy_id not in self.weights:
            self.weights[strategy_id] = 0.5
        
        # 简单的移动平均
        alpha = 0.1
        self.weights[strategy_id] = (1 - alpha) * self.weights[strategy_id] + alpha * reward
        self.save_weights()
    
    def get_weight(self, strategy_id: str) -> float:
        """获取权重"""
        return self.weights.get(strategy_id, 0.5)

# =============================================================================
# 测试和演示
# =============================================================================

# =============================================================================
# 第三阶段增强：企业级状态管理器
# =============================================================================

class EnhancedNeogenesisStateManager:
    """
    增强版Neogenesis状态管理器
    
    集成第三阶段功能：
    - 分布式状态管理
    - MAB权重优化和持久化
    - ACID事务支持
    - 企业级存储引擎
    - 状态快照和恢复
    """
    
    def __init__(self,
                 storage_backend: str = "file_system",
                 storage_path: str = "./neogenesis_enhanced_state",
                 enable_distributed: bool = False,
                 enable_transactions: bool = False,
                 enable_mab_optimization: bool = True,
                 **kwargs):
        """
        初始化增强状态管理器
        
        Args:
            storage_backend: 存储后端类型
            storage_path: 存储路径
            enable_distributed: 是否启用分布式状态管理
            enable_transactions: 是否启用事务支持
            enable_mab_optimization: 是否启用MAB优化
            **kwargs: 其他配置参数
        """
        self.storage_backend = storage_backend
        self.storage_path = storage_path
        self.enable_distributed = enable_distributed and PHASE3_AVAILABLE
        self.enable_transactions = enable_transactions and PHASE3_AVAILABLE
        self.enable_mab_optimization = enable_mab_optimization and PHASE3_AVAILABLE
        
        # 初始化存储引擎
        if PHASE3_AVAILABLE:
            self.storage_engine = create_storage_engine(
                storage_backend, storage_path, **kwargs
            )
        else:
            self.storage_engine = None
        
        # 初始化分布式状态管理器
        if self.enable_distributed:
            self.distributed_state_manager = create_distributed_state_manager(
                storage_backend, f"{storage_path}/distributed", **kwargs
            )
        else:
            self.distributed_state_manager = None
        
        # 初始化事务管理器
        if self.enable_transactions and self.storage_engine:
            self.transaction_manager = create_transaction_manager(
                self.storage_engine, self.distributed_state_manager
            )
        else:
            self.transaction_manager = None
        
        # 初始化MAB管理器
        if self.enable_mab_optimization:
            self.mab_manager = create_mab_manager(
                storage_backend, f"{storage_path}/mab", **kwargs
            )
        else:
            self.mab_manager = None
        
        # 回退到基础状态管理器
        self.basic_state_manager = NeogenesisStateManager(
            storage_path=f"{storage_path}/basic"
        )
        
        logger.info("🚀 增强状态管理器初始化完成")
        logger.info(f"   分布式状态: {self.enable_distributed}")
        logger.info(f"   事务支持: {self.enable_transactions}")
        logger.info(f"   MAB优化: {self.enable_mab_optimization}")
        logger.info(f"   第三阶段功能: {PHASE3_AVAILABLE}")
    
    def create_session(self,
                      session_id: str,
                      user_query: str,
                      execution_context: Optional[Dict[str, Any]] = None,
                      use_transaction: bool = False,
                      **kwargs) -> DecisionState:
        """
        创建决策会话（增强版）
        
        Args:
            session_id: 会话ID
            user_query: 用户查询
            execution_context: 执行上下文
            use_transaction: 是否使用事务
            **kwargs: 其他参数
            
        Returns:
            决策状态对象
        """
        # 如果启用事务，在事务中创建会话
        if use_transaction and self.transaction_manager:
            tx_id = self.transaction_manager.begin_transaction()
            try:
                session = self._create_session_internal(
                    session_id, user_query, execution_context, **kwargs
                )
                
                # 在事务中存储会话
                session_key = f"session:{session_id}"
                self.transaction_manager.write(tx_id, session_key, asdict(session))
                
                # 提交事务
                if self.transaction_manager.commit(tx_id):
                    logger.info(f"📝 会话创建（事务模式）: {session_id}")
                    return session
                else:
                    raise RuntimeError("事务提交失败")
                    
            except Exception as e:
                self.transaction_manager.abort(tx_id)
                logger.error(f"❌ 事务创建会话失败: {e}")
                raise
        else:
            # 非事务模式
            session = self._create_session_internal(
                session_id, user_query, execution_context, **kwargs
            )
            
            # 存储到分布式状态或基础存储
            if self.distributed_state_manager:
                session_key = f"session:{session_id}"
                self.distributed_state_manager.set_state(session_key, asdict(session))
            else:
                # 回退到基础状态管理器
                self.basic_state_manager.create_session(
                    session_id, user_query, execution_context, **kwargs
                )
            
            return session
    
    def _create_session_internal(self,
                               session_id: str,
                               user_query: str,
                               execution_context: Optional[Dict[str, Any]],
                               **kwargs) -> DecisionState:
        """内部会话创建逻辑"""
        session = DecisionState(
            session_id=session_id,
            user_query=user_query,
            current_stage=DecisionStage.THINKING_SEED,
            execution_context=execution_context,
            **kwargs
        )
        return session
    
    def update_session_stage(self,
                           session_id: str,
                           stage: DecisionStage,
                           success: bool,
                           data: Dict[str, Any],
                           execution_time: float,
                           error_message: Optional[str] = None,
                           use_transaction: bool = False) -> bool:
        """
        更新会话阶段（增强版）
        
        Args:
            session_id: 会话ID
            stage: 决策阶段
            success: 是否成功
            data: 阶段数据
            execution_time: 执行时间
            error_message: 错误消息
            use_transaction: 是否使用事务
            
        Returns:
            是否更新成功
        """
        try:
            # 获取会话
            session = self.get_session(session_id)
            if not session:
                logger.error(f"❌ 会话不存在: {session_id}")
                return False
            
            # 创建阶段结果
            stage_result = StageResult(
                stage=stage,
                success=success,
                data=data,
                execution_time=execution_time,
                error_message=error_message
            )
            
            # 更新会话状态
            session.update_stage(stage, stage_result)
            
            # 如果是MAB决策阶段且启用MAB优化，更新MAB权重
            if (stage == DecisionStage.MAB_DECISION and 
                success and 
                self.enable_mab_optimization and 
                self.mab_manager):
                
                self._update_mab_weights(data, execution_time)
            
            # 保存更新后的会话
            if use_transaction and self.transaction_manager:
                tx_id = self.transaction_manager.begin_transaction()
                try:
                    session_key = f"session:{session_id}"
                    self.transaction_manager.write(tx_id, session_key, asdict(session))
                    
                    if self.transaction_manager.commit(tx_id):
                        logger.debug(f"📊 会话阶段更新（事务模式）: {session_id} -> {stage.value}")
                        return True
                    else:
                        return False
                except Exception as e:
                    self.transaction_manager.abort(tx_id)
                    logger.error(f"❌ 事务更新阶段失败: {e}")
                    return False
            else:
                # 非事务模式
                if self.distributed_state_manager:
                    session_key = f"session:{session_id}"
                    success = self.distributed_state_manager.set_state(session_key, asdict(session))
                else:
                    success = self.basic_state_manager.update_session_stage(
                        session_id, stage, success, data, execution_time, error_message
                    )
                
                return success
                
        except Exception as e:
            logger.error(f"❌ 更新会话阶段失败: {session_id} - {e}")
            return False
    
    def _update_mab_weights(self, stage_data: Dict[str, Any], execution_time: float):
        """更新MAB权重"""
        try:
            selected_path = stage_data.get("selected_path", {})
            strategy_id = selected_path.get("strategy_id") or selected_path.get("path_id")
            
            if strategy_id:
                # 计算奖励（基于成功率和执行时间）
                reward = 1.0 if execution_time < 30.0 else 0.5  # 简化的奖励函数
                
                # 更新MAB权重
                self.mab_manager.update_reward(strategy_id, reward)
                logger.debug(f"🎰 MAB权重更新: {strategy_id} = {reward:.3f}")
                
        except Exception as e:
            logger.error(f"❌ MAB权重更新失败: {e}")
    
    def get_session(self, session_id: str) -> Optional[DecisionState]:
        """获取会话（增强版）"""
        try:
            if self.distributed_state_manager:
                session_key = f"session:{session_id}"
                session_data = self.distributed_state_manager.get_state(session_key)
                
                if session_data:
                    return DecisionState.from_dict(session_data)
            
            # 回退到基础状态管理器
            return self.basic_state_manager.get_session(session_id)
            
        except Exception as e:
            logger.error(f"❌ 获取会话失败: {session_id} - {e}")
            return None
    
    def create_state_snapshot(self, snapshot_id: str = None) -> Optional[str]:
        """创建状态快照"""
        if not self.distributed_state_manager:
            logger.warning("⚠️ 分布式状态管理器未启用，无法创建快照")
            return None
        
        try:
            snapshot = self.distributed_state_manager.create_snapshot()
            if snapshot:
                logger.info(f"📸 状态快照创建: {snapshot.snapshot_id}")
                return snapshot.snapshot_id
            
        except Exception as e:
            logger.error(f"❌ 创建状态快照失败: {e}")
        
        return None
    
    def restore_state_snapshot(self, snapshot_id: str) -> bool:
        """恢复状态快照"""
        if not self.distributed_state_manager:
            logger.warning("⚠️ 分布式状态管理器未启用，无法恢复快照")
            return False
        
        try:
            success = self.distributed_state_manager.restore_snapshot(snapshot_id)
            if success:
                logger.info(f"✅ 状态快照恢复: {snapshot_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 恢复状态快照失败: {snapshot_id} - {e}")
            return False
    
    def get_mab_recommendations(self, available_strategies: List[str]) -> List[Tuple[str, float]]:
        """获取MAB策略推荐"""
        if not self.mab_manager:
            logger.warning("⚠️ MAB管理器未启用")
            return []
        
        try:
            # 获取策略排名
            active_engine = self.mab_manager.get_active_engine()
            rankings = active_engine.get_arm_rankings()
            
            # 过滤可用策略
            recommendations = [(arm_id, score) for arm_id, score in rankings 
                             if arm_id in available_strategies]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 获取MAB推荐失败: {e}")
            return []
    
    def execute_in_transaction(self, operations: List[Callable]) -> bool:
        """在事务中执行操作"""
        if not self.transaction_manager:
            logger.warning("⚠️ 事务管理器未启用")
            return False
        
        tx_id = self.transaction_manager.begin_transaction()
        
        try:
            for operation in operations:
                result = operation(self.transaction_manager, tx_id)
                if not result:
                    raise RuntimeError("操作失败")
            
            return self.transaction_manager.commit(tx_id)
            
        except Exception as e:
            self.transaction_manager.abort(tx_id)
            logger.error(f"❌ 事务执行失败: {e}")
            return False
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """获取增强统计信息"""
        stats = {
            "enhanced_features": {
                "distributed_state": self.enable_distributed,
                "transactions": self.enable_transactions,
                "mab_optimization": self.enable_mab_optimization,
                "phase3_available": PHASE3_AVAILABLE
            }
        }
        
        # 基础统计
        try:
            basic_stats = self.basic_state_manager.get_session_statistics()
            stats["basic_stats"] = basic_stats
        except:
            pass
        
        # 分布式状态统计
        if self.distributed_state_manager:
            try:
                distributed_stats = self.distributed_state_manager.get_state_statistics()
                stats["distributed_stats"] = distributed_stats
            except:
                pass
        
        # 事务统计
        if self.transaction_manager:
            try:
                transaction_stats = self.transaction_manager.get_transaction_statistics()
                stats["transaction_stats"] = transaction_stats
            except:
                pass
        
        # MAB统计
        if self.mab_manager:
            try:
                mab_stats = self.mab_manager.get_global_performance_summary()
                stats["mab_stats"] = mab_stats
            except:
                pass
        
        return stats
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理各个组件
            if self.distributed_state_manager:
                self.distributed_state_manager.cleanup()
            
            if self.transaction_manager:
                self.transaction_manager.cleanup()
            
            if self.mab_manager:
                self.mab_manager.cleanup()
            
            if self.storage_engine:
                self.storage_engine.cleanup()
            
            # 清理基础状态管理器
            # basic_state_manager没有cleanup方法，跳过
            
            logger.info("🧹 增强状态管理器清理完成")
            
        except Exception as e:
            logger.error(f"❌ 增强状态管理器清理失败: {e}")

# =============================================================================
# 工厂函数
# =============================================================================

def create_enhanced_state_manager(
    storage_backend: str = "file_system",
    storage_path: str = "./neogenesis_enhanced_state",
    enable_all_features: bool = True,
    **kwargs
) -> Union[EnhancedNeogenesisStateManager, NeogenesisStateManager]:
    """
    创建增强状态管理器
    
    Args:
        storage_backend: 存储后端类型
        storage_path: 存储路径
        enable_all_features: 是否启用所有增强功能
        **kwargs: 其他配置参数
        
    Returns:
        增强状态管理器或基础状态管理器
    """
    if PHASE3_AVAILABLE and enable_all_features:
        return EnhancedNeogenesisStateManager(
            storage_backend=storage_backend,
            storage_path=storage_path,
            enable_distributed=True,
            enable_transactions=True,
            enable_mab_optimization=True,
            **kwargs
        )
    else:
        logger.warning("⚠️ 第三阶段功能不可用，使用基础状态管理器")
        return NeogenesisStateManager(storage_path=storage_path)

if __name__ == "__main__":
    # 测试状态管理器
    print("🧪 测试Neogenesis状态管理器...")
    
    if PHASE3_AVAILABLE:
        print("\n🚀 测试增强状态管理器:")
        
        # 创建增强状态管理器
        enhanced_manager = create_enhanced_state_manager(
            storage_backend="memory",
            enable_all_features=True
        )
        
        # 创建会话
        session_id = "enhanced_test_session"
        session = enhanced_manager.create_session(
            session_id=session_id,
            user_query="测试增强功能",
            execution_context={"enhanced": True}
        )
        
        print(f"✅ 增强会话创建: {session.session_id}")
        
        # 更新阶段
        enhanced_manager.update_session_stage(
            session_id=session_id,
            stage=DecisionStage.THINKING_SEED,
            success=True,
            data={"thinking_seed": "增强思维种子"},
            execution_time=2.0
        )
        
        print("✅ 增强阶段更新完成")
        
        # 创建快照
        snapshot_id = enhanced_manager.create_state_snapshot()
        if snapshot_id:
            print(f"📸 状态快照创建: {snapshot_id}")
        
        # 获取增强统计
        enhanced_stats = enhanced_manager.get_enhanced_statistics()
        print(f"📊 增强统计信息:")
        for key, value in enhanced_stats.items():
            print(f"   {key}: {value}")
        
        # 清理
        enhanced_manager.cleanup()
        
    else:
        print("\n⚠️ 第三阶段功能不可用，测试基础功能:")
        
        # 创建基础状态管理器
        state_manager = NeogenesisStateManager(storage_path="./test_state")
        
        # 创建会话
        session_id = "test_session_001"
        session = state_manager.create_session(
            session_id=session_id,
            user_query="测试查询",
            execution_context={"test": True}
        )
        
        print(f"✅ 创建会话: {session.session_id}")
        
        # 更新阶段
        state_manager.update_session_stage(
            session_id=session_id,
            stage=DecisionStage.THINKING_SEED,
            success=True,
            data={"thinking_seed": "测试种子"},
            execution_time=1.5
        )
        
        print(f"✅ 更新阶段: {DecisionStage.THINKING_SEED.value}")
        
        # 获取统计
        stats = state_manager.get_session_statistics()
        print(f"📊 会话统计: {stats}")
        
        # 测试MAB权重
        mab_weights = MABPersistentWeights("./test_mab_weights.pkl")
        mab_weights.update_weight("test_strategy", 0.8)
        weight = mab_weights.get_weight("test_strategy")
        print(f"🎰 MAB权重测试: {weight}")
    
    print("✅ 状态管理器测试完成")
