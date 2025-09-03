#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - MAB Optimization & Persistent Learning
多臂老虎机优化与持久化学习：高级权重管理和智能策略选择
"""

import json
import logging
import math
import time
import threading
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import uuid

from .persistent_storage import PersistentStorageEngine, StorageConfig
from .distributed_state import DistributedStateManager

logger = logging.getLogger(__name__)

# =============================================================================
# MAB配置和枚举
# =============================================================================

class MABAlgorithm(Enum):
    """多臂老虎机算法类型"""
    EPSILON_GREEDY = "epsilon_greedy"
    UCB1 = "ucb1"
    THOMPSON_SAMPLING = "thompson_sampling"
    SOFTMAX = "softmax"
    ADAPTIVE_GREEDY = "adaptive_greedy"

class RewardType(Enum):
    """奖励类型"""
    BINARY = "binary"           # 0或1
    CONTINUOUS = "continuous"   # 连续值
    CATEGORICAL = "categorical" # 分类奖励
    CUSTOM = "custom"          # 自定义奖励函数

class LearningMode(Enum):
    """学习模式"""
    ONLINE = "online"           # 在线学习
    BATCH = "batch"            # 批量学习
    HYBRID = "hybrid"          # 混合学习

@dataclass
class MABArm:
    """多臂老虎机臂"""
    arm_id: str
    name: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    total_pulls: int = 0
    total_reward: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    
    # 高级统计
    reward_history: List[float] = field(default_factory=list)
    pull_timestamps: List[float] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    
    # 算法相关参数
    confidence_radius: float = 0.0
    thompson_alpha: float = 1.0
    thompson_beta: float = 1.0
    
    @property
    def average_reward(self) -> float:
        """平均奖励"""
        return self.total_reward / max(self.total_pulls, 1)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total_attempts = self.success_count + self.failure_count
        return self.success_count / max(total_attempts, 1)
    
    @property
    def confidence_interval(self) -> Tuple[float, float]:
        """置信区间"""
        if self.total_pulls == 0:
            return (0.0, 1.0)
        
        mean = self.average_reward
        std_error = math.sqrt(self.confidence_radius / self.total_pulls)
        return (max(0.0, mean - 1.96 * std_error), min(1.0, mean + 1.96 * std_error))

@dataclass
class MABContext:
    """MAB上下文信息"""
    context_id: str
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class MABAction:
    """MAB动作记录"""
    action_id: str
    arm_id: str
    context: MABContext
    timestamp: float = field(default_factory=time.time)
    reward: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MABConfiguration:
    """MAB配置"""
    algorithm: MABAlgorithm = MABAlgorithm.UCB1
    epsilon: float = 0.1              # ε-贪心参数
    temperature: float = 1.0          # Softmax温度参数
    ucb_c: float = 1.0               # UCB置信参数
    learning_rate: float = 0.01       # 学习率
    decay_factor: float = 0.99        # 衰减因子
    
    # 持久化设置
    auto_save_interval: float = 60.0  # 自动保存间隔（秒）
    max_history_length: int = 1000    # 最大历史长度
    enable_contextual: bool = False   # 是否启用上下文感知
    enable_cold_start: bool = True    # 是否启用冷启动优化

# =============================================================================
# 智能MAB算法实现
# =============================================================================

class IntelligentMABEngine:
    """智能多臂老虎机引擎"""
    
    def __init__(self,
                 config: MABConfiguration = None,
                 storage_engine: PersistentStorageEngine = None):
        """
        初始化智能MAB引擎
        
        Args:
            config: MAB配置
            storage_engine: 存储引擎
        """
        self.config = config or MABConfiguration()
        self.storage_engine = storage_engine
        
        # MAB状态
        self.arms: Dict[str, MABArm] = {}
        self.actions_history: deque = deque(maxlen=self.config.max_history_length)
        self.total_rounds: int = 0
        
        # 上下文感知
        self.contextual_models = {}
        self.feature_importance = defaultdict(float)
        
        # 性能统计
        self.performance_stats = {
            "total_actions": 0,
            "total_reward": 0.0,
            "cumulative_regret": 0.0,
            "algorithm_switches": 0,
            "cold_start_actions": 0
        }
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 自动保存
        self.auto_save_timer = None
        if self.storage_engine and self.config.auto_save_interval > 0:
            self._start_auto_save()
        
        logger.info(f"🎰 智能MAB引擎初始化: {self.config.algorithm.value}")
    
    def add_arm(self, arm: MABArm) -> bool:
        """添加臂"""
        with self._lock:
            if arm.arm_id in self.arms:
                logger.warning(f"⚠️ 臂已存在: {arm.arm_id}")
                return False
            
            self.arms[arm.arm_id] = arm
            logger.info(f"➕ 添加MAB臂: {arm.arm_id} ({arm.name})")
            
            # 如果启用了冷启动，给新臂一些初始探索机会
            if self.config.enable_cold_start:
                arm.total_pulls = 1
                arm.total_reward = 0.5  # 中性初始奖励
            
            return True
    
    def remove_arm(self, arm_id: str) -> bool:
        """移除臂"""
        with self._lock:
            if arm_id not in self.arms:
                logger.warning(f"⚠️ 臂不存在: {arm_id}")
                return False
            
            del self.arms[arm_id]
            logger.info(f"➖ 移除MAB臂: {arm_id}")
            return True
    
    def select_arm(self, context: MABContext = None) -> Optional[str]:
        """
        选择臂
        
        Args:
            context: 上下文信息
            
        Returns:
            选择的臂ID
        """
        with self._lock:
            if not self.arms:
                logger.warning("⚠️ 没有可用的臂")
                return None
            
            # 根据算法选择臂
            if self.config.algorithm == MABAlgorithm.EPSILON_GREEDY:
                selected_arm = self._epsilon_greedy_selection()
            elif self.config.algorithm == MABAlgorithm.UCB1:
                selected_arm = self._ucb1_selection()
            elif self.config.algorithm == MABAlgorithm.THOMPSON_SAMPLING:
                selected_arm = self._thompson_sampling_selection()
            elif self.config.algorithm == MABAlgorithm.SOFTMAX:
                selected_arm = self._softmax_selection()
            else:
                selected_arm = self._adaptive_greedy_selection()
            
            # 记录动作
            if selected_arm:
                action = MABAction(
                    action_id=f"action_{uuid.uuid4().hex[:8]}",
                    arm_id=selected_arm,
                    context=context or MABContext(f"ctx_{uuid.uuid4().hex[:8]}")
                )
                self.actions_history.append(action)
                
                # 更新统计
                self.performance_stats["total_actions"] += 1
                if self.arms[selected_arm].total_pulls == 0:
                    self.performance_stats["cold_start_actions"] += 1
            
            logger.debug(f"🎯 选择臂: {selected_arm}")
            return selected_arm
    
    def update_reward(self, arm_id: str, reward: float, context: MABContext = None) -> bool:
        """
        更新奖励
        
        Args:
            arm_id: 臂ID
            reward: 奖励值
            context: 上下文信息
            
        Returns:
            是否更新成功
        """
        with self._lock:
            if arm_id not in self.arms:
                logger.warning(f"⚠️ 臂不存在: {arm_id}")
                return False
            
            arm = self.arms[arm_id]
            current_time = time.time()
            
            # 更新臂统计
            arm.total_pulls += 1
            arm.total_reward += reward
            arm.reward_history.append(reward)
            arm.pull_timestamps.append(current_time)
            arm.last_updated = current_time
            
            # 更新成功/失败计数（二元奖励）
            if reward > 0.5:  # 简化的成功判定
                arm.success_count += 1
            else:
                arm.failure_count += 1
            
            # 更新Thompson Sampling参数
            arm.thompson_alpha += reward
            arm.thompson_beta += (1.0 - reward)
            
            # 计算置信半径
            arm.confidence_radius = math.log(self.total_rounds + 1) / max(arm.total_pulls, 1)
            
            # 限制历史长度
            max_history = self.config.max_history_length
            if len(arm.reward_history) > max_history:
                arm.reward_history = arm.reward_history[-max_history:]
                arm.pull_timestamps = arm.pull_timestamps[-max_history:]
            
            # 更新全局统计
            self.total_rounds += 1
            self.performance_stats["total_reward"] += reward
            
            # 更新最近动作的奖励
            if self.actions_history:
                last_action = self.actions_history[-1]
                if last_action.arm_id == arm_id and last_action.reward is None:
                    last_action.reward = reward
                    last_action.context = context or last_action.context
            
            logger.debug(f"📊 更新奖励: {arm_id} = {reward:.3f}")
            return True
    
    def _epsilon_greedy_selection(self) -> str:
        """ε-贪心选择"""
        if np.random.random() < self.config.epsilon:
            # 探索：随机选择
            return np.random.choice(list(self.arms.keys()))
        else:
            # 利用：选择最高平均奖励的臂
            best_arm = max(self.arms.keys(), key=lambda x: self.arms[x].average_reward)
            return best_arm
    
    def _ucb1_selection(self) -> str:
        """UCB1选择"""
        if self.total_rounds == 0:
            return np.random.choice(list(self.arms.keys()))
        
        def ucb1_value(arm: MABArm) -> float:
            if arm.total_pulls == 0:
                return float('inf')  # 未拉过的臂优先
            
            confidence_term = self.config.ucb_c * math.sqrt(
                math.log(self.total_rounds) / arm.total_pulls
            )
            return arm.average_reward + confidence_term
        
        best_arm = max(self.arms.keys(), key=lambda x: ucb1_value(self.arms[x]))
        return best_arm
    
    def _thompson_sampling_selection(self) -> str:
        """Thompson采样选择"""
        arm_scores = {}
        
        for arm_id, arm in self.arms.items():
            # 从Beta分布采样
            score = np.random.beta(arm.thompson_alpha, arm.thompson_beta)
            arm_scores[arm_id] = score
        
        best_arm = max(arm_scores.keys(), key=lambda x: arm_scores[x])
        return best_arm
    
    def _softmax_selection(self) -> str:
        """Softmax选择"""
        if not self.arms:
            return None
        
        # 计算softmax概率
        arm_ids = list(self.arms.keys())
        values = [self.arms[arm_id].average_reward for arm_id in arm_ids]
        
        # 防止数值溢出
        max_value = max(values)
        exp_values = [math.exp((v - max_value) / self.config.temperature) for v in values]
        sum_exp = sum(exp_values)
        
        probabilities = [exp_v / sum_exp for exp_v in exp_values]
        
        # 根据概率选择
        selected_idx = np.random.choice(len(arm_ids), p=probabilities)
        return arm_ids[selected_idx]
    
    def _adaptive_greedy_selection(self) -> str:
        """自适应贪心选择"""
        # 动态调整探索率
        if self.total_rounds < 100:
            epsilon = 0.3  # 早期高探索
        elif self.total_rounds < 1000:
            epsilon = 0.1  # 中期适度探索
        else:
            epsilon = 0.05  # 后期低探索
        
        if np.random.random() < epsilon:
            return np.random.choice(list(self.arms.keys()))
        else:
            # 考虑置信区间的选择
            def adaptive_value(arm: MABArm) -> float:
                if arm.total_pulls == 0:
                    return 1.0
                
                lower_bound, upper_bound = arm.confidence_interval
                # 乐观估计：使用置信区间上界
                return upper_bound
            
            best_arm = max(self.arms.keys(), key=lambda x: adaptive_value(self.arms[x]))
            return best_arm
    
    def get_arm_rankings(self) -> List[Tuple[str, float]]:
        """获取臂排名"""
        with self._lock:
            rankings = [(arm_id, arm.average_reward) for arm_id, arm in self.arms.items()]
            rankings.sort(key=lambda x: x[1], reverse=True)
            return rankings
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            total_actions = self.performance_stats["total_actions"]
            
            # 计算累积后悔
            if total_actions > 0:
                best_possible_reward = max(arm.average_reward for arm in self.arms.values()) if self.arms else 0
                actual_average_reward = self.performance_stats["total_reward"] / total_actions
                cumulative_regret = (best_possible_reward - actual_average_reward) * total_actions
            else:
                cumulative_regret = 0
            
            # 计算探索利用比率
            exploration_actions = sum(1 for action in self.actions_history 
                                    if self._is_exploration_action(action))
            exploration_rate = exploration_actions / max(total_actions, 1)
            
            return {
                "total_rounds": self.total_rounds,
                "total_actions": total_actions,
                "average_reward": self.performance_stats["total_reward"] / max(total_actions, 1),
                "cumulative_regret": cumulative_regret,
                "exploration_rate": exploration_rate,
                "cold_start_actions": self.performance_stats["cold_start_actions"],
                "algorithm": self.config.algorithm.value,
                "arms_count": len(self.arms),
                "active_arms": len([arm for arm in self.arms.values() if arm.total_pulls > 0])
            }
    
    def _is_exploration_action(self, action: MABAction) -> bool:
        """判断是否为探索动作"""
        if not self.arms or action.arm_id not in self.arms:
            return True
        
        arm = self.arms[action.arm_id]
        rankings = self.get_arm_rankings()
        
        # 如果选择的不是当前最佳臂，则认为是探索
        best_arm_id = rankings[0][0] if rankings else None
        return action.arm_id != best_arm_id
    
    def save_state(self, key: str = "mab_state") -> bool:
        """保存MAB状态"""
        if not self.storage_engine:
            logger.warning("⚠️ 没有存储引擎，无法保存状态")
            return False
        
        try:
            with self._lock:
                state_data = {
                    "config": asdict(self.config),
                    "arms": {arm_id: asdict(arm) for arm_id, arm in self.arms.items()},
                    "total_rounds": self.total_rounds,
                    "performance_stats": self.performance_stats,
                    "actions_history": [asdict(action) for action in list(self.actions_history)[-100:]],  # 只保存最近100个
                    "saved_at": time.time()
                }
                
                success = self.storage_engine.store(key, state_data)
                if success:
                    logger.info(f"💾 MAB状态保存成功: {key}")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ MAB状态保存失败: {e}")
            return False
    
    def load_state(self, key: str = "mab_state") -> bool:
        """加载MAB状态"""
        if not self.storage_engine:
            logger.warning("⚠️ 没有存储引擎，无法加载状态")
            return False
        
        try:
            state_data = self.storage_engine.retrieve(key)
            if not state_data:
                logger.info("ℹ️ 没有找到MAB状态数据")
                return False
            
            with self._lock:
                # 恢复配置
                if "config" in state_data:
                    config_data = state_data["config"]
                    config_data["algorithm"] = MABAlgorithm(config_data["algorithm"])
                    self.config = MABConfiguration(**config_data)
                
                # 恢复臂
                if "arms" in state_data:
                    self.arms = {}
                    for arm_id, arm_data in state_data["arms"].items():
                        self.arms[arm_id] = MABArm(**arm_data)
                
                # 恢复统计信息
                self.total_rounds = state_data.get("total_rounds", 0)
                self.performance_stats = state_data.get("performance_stats", {})
                
                # 恢复动作历史
                if "actions_history" in state_data:
                    self.actions_history.clear()
                    for action_data in state_data["actions_history"]:
                        context_data = action_data["context"]
                        action_data["context"] = MABContext(**context_data)
                        self.actions_history.append(MABAction(**action_data))
                
                saved_at = state_data.get("saved_at", 0)
                logger.info(f"📥 MAB状态加载成功: {key} (保存于: {time.ctime(saved_at)})")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ MAB状态加载失败: {e}")
            return False
    
    def _start_auto_save(self):
        """启动自动保存"""
        def auto_save_loop():
            while True:
                try:
                    time.sleep(self.config.auto_save_interval)
                    self.save_state()
                except Exception as e:
                    logger.error(f"❌ 自动保存失败: {e}")
        
        auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        auto_save_thread.start()
        logger.info(f"⏰ 自动保存已启动: 间隔 {self.config.auto_save_interval}s")
    
    def reset(self):
        """重置MAB状态"""
        with self._lock:
            for arm in self.arms.values():
                arm.total_pulls = 0
                arm.total_reward = 0.0
                arm.success_count = 0
                arm.failure_count = 0
                arm.reward_history.clear()
                arm.pull_timestamps.clear()
                arm.thompson_alpha = 1.0
                arm.thompson_beta = 1.0
            
            self.actions_history.clear()
            self.total_rounds = 0
            self.performance_stats = {
                "total_actions": 0,
                "total_reward": 0.0,
                "cumulative_regret": 0.0,
                "algorithm_switches": 0,
                "cold_start_actions": 0
            }
            
            logger.info("🔄 MAB状态已重置")
    
    def cleanup(self):
        """清理资源"""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        # 最后保存一次
        if self.storage_engine:
            self.save_state()
        
        logger.info("🧹 智能MAB引擎清理完成")

# =============================================================================
# 高级MAB管理器
# =============================================================================

class AdvancedMABManager:
    """
    高级MAB管理器
    
    功能：
    - 多MAB引擎管理
    - 策略自动切换
    - A/B测试支持
    - 性能对比分析
    """
    
    def __init__(self,
                 storage_engine: PersistentStorageEngine = None,
                 distributed_state_manager: DistributedStateManager = None):
        """
        初始化高级MAB管理器
        
        Args:
            storage_engine: 存储引擎
            distributed_state_manager: 分布式状态管理器
        """
        self.storage_engine = storage_engine
        self.distributed_state_manager = distributed_state_manager
        
        # MAB引擎管理
        self.mab_engines: Dict[str, IntelligentMABEngine] = {}
        self.active_engine_id: str = "default"
        
        # A/B测试
        self.ab_test_configs = {}
        self.ab_test_results = defaultdict(list)
        
        # 性能监控
        self.performance_history = deque(maxlen=1000)
        self.algorithm_performance = defaultdict(list)
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 创建默认引擎
        self._create_default_engine()
        
        logger.info("🎰 高级MAB管理器初始化完成")
    
    def _create_default_engine(self):
        """创建默认MAB引擎"""
        default_config = MABConfiguration(
            algorithm=MABAlgorithm.UCB1,
            enable_cold_start=True,
            auto_save_interval=300.0  # 5分钟自动保存
        )
        
        default_engine = IntelligentMABEngine(
            config=default_config,
            storage_engine=self.storage_engine
        )
        
        self.mab_engines["default"] = default_engine
        self.active_engine_id = "default"
    
    def create_engine(self, 
                     engine_id: str,
                     config: MABConfiguration,
                     arms: List[MABArm] = None) -> bool:
        """创建新的MAB引擎"""
        with self._lock:
            if engine_id in self.mab_engines:
                logger.warning(f"⚠️ MAB引擎已存在: {engine_id}")
                return False
            
            engine = IntelligentMABEngine(
                config=config,
                storage_engine=self.storage_engine
            )
            
            # 添加臂
            if arms:
                for arm in arms:
                    engine.add_arm(arm)
            
            self.mab_engines[engine_id] = engine
            logger.info(f"➕ 创建MAB引擎: {engine_id}")
            
            return True
    
    def switch_engine(self, engine_id: str) -> bool:
        """切换活跃引擎"""
        with self._lock:
            if engine_id not in self.mab_engines:
                logger.warning(f"⚠️ MAB引擎不存在: {engine_id}")
                return False
            
            old_engine_id = self.active_engine_id
            self.active_engine_id = engine_id
            
            logger.info(f"🔄 切换MAB引擎: {old_engine_id} -> {engine_id}")
            return True
    
    def get_active_engine(self) -> IntelligentMABEngine:
        """获取活跃引擎"""
        return self.mab_engines[self.active_engine_id]
    
    def select_arm(self, context: MABContext = None, engine_id: str = None) -> Optional[str]:
        """选择臂"""
        engine = self.mab_engines.get(engine_id or self.active_engine_id)
        if not engine:
            logger.warning(f"⚠️ MAB引擎不存在: {engine_id}")
            return None
        
        return engine.select_arm(context)
    
    def update_reward(self, 
                     arm_id: str, 
                     reward: float, 
                     context: MABContext = None,
                     engine_id: str = None) -> bool:
        """更新奖励"""
        engine = self.mab_engines.get(engine_id or self.active_engine_id)
        if not engine:
            logger.warning(f"⚠️ MAB引擎不存在: {engine_id}")
            return False
        
        success = engine.update_reward(arm_id, reward, context)
        
        # 记录性能历史
        if success:
            performance_record = {
                "timestamp": time.time(),
                "engine_id": engine_id or self.active_engine_id,
                "arm_id": arm_id,
                "reward": reward,
                "algorithm": engine.config.algorithm.value
            }
            self.performance_history.append(performance_record)
            self.algorithm_performance[engine.config.algorithm.value].append(reward)
        
        return success
    
    def run_ab_test(self,
                   test_name: str,
                   engines: List[str],
                   duration: float = 3600.0,
                   traffic_split: List[float] = None) -> Dict[str, Any]:
        """
        运行A/B测试
        
        Args:
            test_name: 测试名称
            engines: 参与测试的引擎ID列表
            duration: 测试持续时间（秒）
            traffic_split: 流量分配比例
            
        Returns:
            A/B测试结果
        """
        if traffic_split is None:
            traffic_split = [1.0 / len(engines)] * len(engines)
        
        if len(engines) != len(traffic_split) or abs(sum(traffic_split) - 1.0) > 0.01:
            logger.error("❌ 引擎数量与流量分配不匹配")
            return {}
        
        # 配置A/B测试
        ab_config = {
            "test_name": test_name,
            "engines": engines,
            "traffic_split": traffic_split,
            "start_time": time.time(),
            "duration": duration,
            "status": "running"
        }
        
        self.ab_test_configs[test_name] = ab_config
        
        logger.info(f"🧪 A/B测试开始: {test_name} ({len(engines)} 个引擎)")
        
        # 注意：实际的A/B测试执行需要在select_arm方法中实现流量分配逻辑
        # 这里只是配置测试参数
        
        return ab_config
    
    def get_ab_test_results(self, test_name: str) -> Dict[str, Any]:
        """获取A/B测试结果"""
        if test_name not in self.ab_test_configs:
            return {}
        
        config = self.ab_test_configs[test_name]
        results = {}
        
        for engine_id in config["engines"]:
            if engine_id in self.mab_engines:
                engine = self.mab_engines[engine_id]
                metrics = engine.get_performance_metrics()
                results[engine_id] = metrics
        
        return {
            "test_config": config,
            "engine_results": results,
            "generated_at": time.time()
        }
    
    def get_global_performance_summary(self) -> Dict[str, Any]:
        """获取全局性能摘要"""
        with self._lock:
            total_actions = len(self.performance_history)
            if total_actions == 0:
                return {"total_actions": 0}
            
            # 算法性能对比
            algorithm_stats = {}
            for algorithm, rewards in self.algorithm_performance.items():
                if rewards:
                    algorithm_stats[algorithm] = {
                        "avg_reward": np.mean(rewards),
                        "std_reward": np.std(rewards),
                        "total_actions": len(rewards),
                        "best_reward": max(rewards),
                        "worst_reward": min(rewards)
                    }
            
            # 引擎性能对比
            engine_stats = {}
            for engine_id, engine in self.mab_engines.items():
                engine_stats[engine_id] = engine.get_performance_metrics()
            
            # 最近性能趋势
            recent_performance = list(self.performance_history)[-100:]  # 最近100个动作
            recent_avg_reward = np.mean([r["reward"] for r in recent_performance]) if recent_performance else 0
            
            return {
                "total_actions": total_actions,
                "active_engine": self.active_engine_id,
                "engines_count": len(self.mab_engines),
                "recent_avg_reward": recent_avg_reward,
                "algorithm_performance": algorithm_stats,
                "engine_performance": engine_stats,
                "active_ab_tests": len([config for config in self.ab_test_configs.values() 
                                      if config["status"] == "running"])
            }
    
    def auto_optimize_algorithm(self) -> str:
        """自动优化算法选择"""
        if len(self.algorithm_performance) < 2:
            logger.info("ℹ️ 算法数据不足，无法进行自动优化")
            return self.get_active_engine().config.algorithm.value
        
        # 计算各算法的性能
        best_algorithm = None
        best_performance = -float('inf')
        
        for algorithm, rewards in self.algorithm_performance.items():
            if len(rewards) >= 10:  # 至少需要10个样本
                performance = np.mean(rewards[-50:])  # 使用最近50个样本
                if performance > best_performance:
                    best_performance = performance
                    best_algorithm = algorithm
        
        if best_algorithm and best_algorithm != self.get_active_engine().config.algorithm.value:
            # 创建新的优化引擎
            optimized_config = MABConfiguration(algorithm=MABAlgorithm(best_algorithm))
            optimized_engine_id = f"optimized_{best_algorithm}_{int(time.time())}"
            
            if self.create_engine(optimized_engine_id, optimized_config):
                # 复制当前引擎的臂
                current_engine = self.get_active_engine()
                optimized_engine = self.mab_engines[optimized_engine_id]
                
                for arm_id, arm in current_engine.arms.items():
                    optimized_engine.add_arm(arm)
                
                logger.info(f"🎯 自动优化: 切换到算法 {best_algorithm}")
                return best_algorithm
        
        return self.get_active_engine().config.algorithm.value
    
    def save_all_states(self) -> bool:
        """保存所有引擎状态"""
        success_count = 0
        total_count = len(self.mab_engines)
        
        for engine_id, engine in self.mab_engines.items():
            if engine.save_state(f"mab_engine_{engine_id}"):
                success_count += 1
        
        # 保存管理器状态
        manager_state = {
            "active_engine_id": self.active_engine_id,
            "ab_test_configs": self.ab_test_configs,
            "performance_history": list(self.performance_history)[-100:],  # 只保存最近100个
            "saved_at": time.time()
        }
        
        if self.storage_engine:
            if self.storage_engine.store("mab_manager_state", manager_state):
                success_count += 1
                total_count += 1
        
        logger.info(f"💾 保存MAB状态: {success_count}/{total_count} 成功")
        return success_count == total_count
    
    def load_all_states(self) -> bool:
        """加载所有引擎状态"""
        # 加载管理器状态
        if self.storage_engine:
            manager_state = self.storage_engine.retrieve("mab_manager_state")
            if manager_state:
                self.active_engine_id = manager_state.get("active_engine_id", "default")
                self.ab_test_configs = manager_state.get("ab_test_configs", {})
                
                # 恢复性能历史
                history_data = manager_state.get("performance_history", [])
                self.performance_history.clear()
                self.performance_history.extend(history_data)
                
                logger.info("📥 MAB管理器状态加载成功")
        
        # 加载引擎状态
        success_count = 0
        for engine_id, engine in self.mab_engines.items():
            if engine.load_state(f"mab_engine_{engine_id}"):
                success_count += 1
        
        logger.info(f"📥 加载MAB引擎状态: {success_count}/{len(self.mab_engines)} 成功")
        return success_count > 0
    
    def cleanup(self):
        """清理资源"""
        # 保存所有状态
        self.save_all_states()
        
        # 清理所有引擎
        for engine in self.mab_engines.values():
            engine.cleanup()
        
        logger.info("🧹 高级MAB管理器清理完成")

# =============================================================================
# 工厂函数
# =============================================================================

def create_mab_manager(
    storage_backend: str = "file_system",
    storage_path: str = "./neogenesis_mab",
    algorithm: str = "ucb1",
    **kwargs
) -> AdvancedMABManager:
    """
    创建MAB管理器
    
    Args:
        storage_backend: 存储后端类型
        storage_path: 存储路径
        algorithm: 默认算法
        **kwargs: 其他配置参数
        
    Returns:
        高级MAB管理器实例
    """
    from .persistent_storage import create_storage_engine
    
    storage_engine = create_storage_engine(storage_backend, storage_path, **kwargs)
    manager = AdvancedMABManager(storage_engine=storage_engine)
    
    # 配置默认引擎
    if algorithm != "ucb1":
        default_engine = manager.get_active_engine()
        default_engine.config.algorithm = MABAlgorithm(algorithm)
    
    return manager

# =============================================================================
# 测试和演示
# =============================================================================

if __name__ == "__main__":
    # 测试MAB优化系统
    print("🧪 测试MAB优化与持久化系统...")
    
    # 创建MAB管理器
    manager = create_mab_manager("memory", algorithm="ucb1")
    
    # 添加测试臂
    arms = [
        MABArm("strategy_analytical", "分析型策略", "系统性分析方法"),
        MABArm("strategy_creative", "创新型策略", "创造性思维方法"),
        MABArm("strategy_practical", "实用型策略", "实践导向方法"),
        MABArm("strategy_research", "研究型策略", "深度研究方法")
    ]
    
    active_engine = manager.get_active_engine()
    for arm in arms:
        active_engine.add_arm(arm)
    
    print(f"✅ 添加 {len(arms)} 个策略臂")
    
    # 模拟MAB学习过程
    print("\n🎰 模拟MAB学习过程:")
    for round_num in range(50):
        # 选择策略
        context = MABContext(f"context_{round_num}", {"round": round_num})
        selected_arm = manager.select_arm(context)
        
        if selected_arm:
            # 模拟奖励（不同策略有不同的期望奖励）
            if selected_arm == "strategy_analytical":
                reward = np.random.beta(8, 3)  # 高奖励策略
            elif selected_arm == "strategy_creative":
                reward = np.random.beta(6, 4)  # 中等奖励策略
            elif selected_arm == "strategy_practical":
                reward = np.random.beta(7, 4)  # 中高奖励策略
            else:
                reward = np.random.beta(5, 5)  # 平均奖励策略
            
            # 更新奖励
            manager.update_reward(selected_arm, reward, context)
            
            if round_num % 10 == 9:
                rankings = active_engine.get_arm_rankings()
                best_arm = rankings[0]
                print(f"   轮次 {round_num+1}: 最佳策略 = {best_arm[0]} (奖励: {best_arm[1]:.3f})")
    
    # 获取最终性能
    print("\n📊 最终性能分析:")
    rankings = active_engine.get_arm_rankings()
    for i, (arm_id, avg_reward) in enumerate(rankings):
        arm = active_engine.arms[arm_id]
        print(f"   排名 {i+1}: {arm.name} - 平均奖励: {avg_reward:.3f} (拉取次数: {arm.total_pulls})")
    
    # 获取性能指标
    metrics = active_engine.get_performance_metrics()
    print(f"\n📈 性能指标:")
    print(f"   总轮次: {metrics['total_rounds']}")
    print(f"   平均奖励: {metrics['average_reward']:.3f}")
    print(f"   探索率: {metrics['exploration_rate']:.3f}")
    print(f"   累积后悔: {metrics['cumulative_regret']:.3f}")
    
    # 测试状态保存和加载
    print("\n💾 测试状态持久化:")
    save_success = manager.save_all_states()
    print(f"✅ 状态保存: {'成功' if save_success else '失败'}")
    
    # 重置并加载
    active_engine.reset()
    load_success = manager.load_all_states()
    print(f"✅ 状态加载: {'成功' if load_success else '失败'}")
    
    # 验证恢复
    if load_success:
        restored_rankings = active_engine.get_arm_rankings()
        print(f"✅ 状态恢复验证: 最佳策略 = {restored_rankings[0][0]}")
    
    # 清理
    manager.cleanup()
    
    print("✅ MAB优化与持久化系统测试完成")
