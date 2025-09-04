#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MAB收敛器 - 阶段三：思维路径选择器
负责从多个思维路径中选择最优路径的多臂老虎机算法
MAB Converger - Stage 3: Reasoning Path Selector
Responsible for selecting optimal reasoning path from multiple paths using MAB algorithms
"""

import time
import logging
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass

from .data_structures import EnhancedDecisionArm, ReasoningPath
try:
    from neogenesis_system.config import MAB_CONFIG
except ImportError:
    try:
        from ..config import MAB_CONFIG
    except ImportError:
        MAB_CONFIG = {
            "convergence_threshold": 0.95,
            "min_samples": 10
        }

logger = logging.getLogger(__name__)


@dataclass
class MABConverger:
    """MAB收敛器 - 阶段三：思维路径选择器"""
    
    def __init__(self):
        # 改为存储路径级别的决策臂：path_id -> EnhancedDecisionArm
        self.path_arms: Dict[str, EnhancedDecisionArm] = {}
        self.convergence_threshold = MAB_CONFIG["convergence_threshold"]  # 收敛阈值
        self.min_samples = MAB_CONFIG["min_samples"]  # 最小样本数
        
        # 🔧 新增：工具级别的决策臂存储：tool_id -> EnhancedDecisionArm
        self.tool_arms: Dict[str, EnhancedDecisionArm] = {}
        self.tool_selection_history = []  # 工具选择历史
        self.total_tool_selections = 0  # 总工具选择次数
        
        # 算法选择策略
        self.algorithm_preferences = {
            'thompson_sampling': 0.4,
            'ucb_variant': 0.35,
            'epsilon_greedy': 0.25
        }
        
        # 路径级别的性能统计
        self.algorithm_performance = defaultdict(lambda: {'successes': 0, 'total': 0})
        self.path_selection_history = []  # 路径选择历史
        self.total_path_selections = 0  # 总路径选择次数
        
        # 🔧 新增：工具级别的性能统计
        self.tool_algorithm_performance = defaultdict(lambda: {'successes': 0, 'total': 0})
        
        # 🏆 黄金决策模板系统
        self.golden_templates: Dict[str, Dict[str, any]] = {}  # 存储黄金模板
        self.golden_template_config = {
            'success_rate_threshold': 0.90,  # 成功率阈值90%
            'min_samples_required': 20,      # 最小样本数20次
            'confidence_threshold': 0.95,    # 置信度阈值
            'stability_check_window': 10,    # 稳定性检查窗口
            'max_golden_templates': 50       # 最大黄金模板数量
        }
        self.template_usage_stats = defaultdict(int)  # 黄金模板使用统计
        self.template_match_history = []  # 模板匹配历史
        
        # 🔧 改进方案：采用动态创建策略，在需要时自动创建决策臂
        
        logger.info("🎰 MABConverger 已初始化 - 双层学习模式：思维路径 + 工具选择")
        logger.info("🏆 黄金决策模板系统已启用")
        logger.info("🔧 工具选择MAB系统已就绪")
    
    def _create_strategy_arm_if_missing(self, strategy_id: str, path_type: str = None) -> EnhancedDecisionArm:
        """
        动态创建策略决策臂（如果不存在）
        
        Args:
            strategy_id: 策略ID
            path_type: 路径类型（可选，如果未提供则自动推断）
            
        Returns:
            对应的决策臂
        """
        if strategy_id not in self.path_arms:
            if path_type is None:
                # 自动推断路径类型
                path_type = self._infer_path_type_from_strategy_id(strategy_id)
            
            self.path_arms[strategy_id] = EnhancedDecisionArm(
                path_id=strategy_id,
                option=path_type
            )
            logger.debug(f"🆕 动态创建策略决策臂: {strategy_id} ({path_type})")
        
        return self.path_arms[strategy_id]
    
    def _create_tool_arm_if_missing(self, tool_id: str, tool_name: str = None) -> EnhancedDecisionArm:
        """
        动态创建工具决策臂（如果不存在）
        
        Args:
            tool_id: 工具ID
            tool_name: 工具名称（可选，如果未提供则使用tool_id）
            
        Returns:
            对应的工具决策臂
        """
        if tool_id not in self.tool_arms:
            if tool_name is None:
                tool_name = tool_id  # 默认使用tool_id作为工具名称
            
            self.tool_arms[tool_id] = EnhancedDecisionArm(
                path_id=tool_id,
                option=tool_name
            )
            logger.debug(f"🔧 动态创建工具决策臂: {tool_id} ({tool_name})")
        
        return self.tool_arms[tool_id]
    
    def select_best_path(self, paths: List[ReasoningPath], algorithm: str = 'auto') -> ReasoningPath:
        """
        阶段三核心方法：从思维路径列表中选择最优路径（集成黄金模板系统）
        
        Args:
            paths: 思维路径列表
            algorithm: 使用的算法 ('thompson_sampling', 'ucb_variant', 'epsilon_greedy', 'auto')
            
        Returns:
            选择的最优思维路径
        """
        if not paths:
            raise ValueError("路径列表不能为空")
        
        if len(paths) == 1:
            logger.info(f"🎯 只有一个路径，直接选择: {paths[0].path_type}")
            return paths[0]
        
        self.total_path_selections += 1
        logger.info(f"🛤️ 开始第 {self.total_path_selections} 次路径选择，候选路径: {len(paths)}个")
        
        # 🏆 黄金模板优先检查：在MAB算法前先检查是否有匹配的黄金模板
        golden_match = self._check_golden_template_match(paths)
        if golden_match:
            selected_path = golden_match['path']
            template_id = golden_match['template_id']
            match_score = golden_match['match_score']
            
            # 更新黄金模板使用统计
            self.template_usage_stats[template_id] += 1
            
            # 记录模板匹配历史
            self.template_match_history.append({
                'template_id': template_id,
                'path_id': selected_path.path_id,
                'path_type': selected_path.path_type,
                'match_score': match_score,
                'timestamp': time.time(),
                'selection_round': self.total_path_selections
            })
            
            logger.info(f"🏆 黄金模板匹配成功！")
            logger.info(f"   模板ID: {template_id}")
            logger.info(f"   匹配路径: {selected_path.path_type}")
            logger.info(f"   匹配分数: {match_score:.3f}")
            logger.info(f"   跳过MAB算法，直接使用黄金模板")
            
            return selected_path
        
        # 🔧 动态创建策略：在选择路径时确保所有策略决策臂都存在
        available_arms = []
        strategy_to_path_mapping = {}  # 策略ID到路径实例的映射
        
        for path in paths:
            strategy_id = path.strategy_id
            strategy_to_path_mapping[strategy_id] = path  # 记录映射关系
            
            # 🔧 动态创建：确保策略决策臂存在
            arm = self._create_strategy_arm_if_missing(strategy_id, path.path_type)
            available_arms.append(arm)
            
            logger.debug(f"✅ 策略决策臂就绪: {strategy_id} ({path.path_type})")
            logger.debug(f"   对应实例: {path.instance_id}")
        
        # 自动选择算法
        if algorithm == 'auto':
            algorithm = self._select_best_algorithm_for_paths()
        
        # 根据选择的算法进行决策
        try:
            if algorithm == 'thompson_sampling':
                best_arm = self._thompson_sampling_for_paths(available_arms)
            elif algorithm == 'ucb_variant':
                best_arm = self._ucb_variant_for_paths(available_arms)
            elif algorithm == 'epsilon_greedy':
                best_arm = self._epsilon_greedy_for_paths(available_arms)
            else:
                logger.warning(f"⚠️ 未知算法 {algorithm}，使用Thompson采样")
                best_arm = self._thompson_sampling_for_paths(available_arms)
            
            # 更新使用时间和激活次数
            best_arm.last_used = time.time()
            best_arm.activation_count += 1
            
            # 🎯 修复：基于策略ID找到对应的路径实例
            selected_path = strategy_to_path_mapping.get(best_arm.path_id)
            
            if selected_path is None:
                # 兼容性：如果映射失败，尝试其他方式
                logger.warning(f"⚠️ 策略映射失败: {best_arm.path_id}")
                for path in paths:
                    strategy_id = getattr(path, 'strategy_id', None)
                    if strategy_id == best_arm.path_id:
                        selected_path = path
                        break
                
                if selected_path is None:
                    logger.error(f"❌ 无法找到对应的路径策略: {best_arm.path_id}")
                    selected_path = paths[0]  # 回退到第一个路径
            
            # 记录选择历史
            self.path_selection_history.append({
                'path_id': best_arm.path_id,
                'path_type': selected_path.path_type,
                'algorithm': algorithm,
                'timestamp': time.time(),
                'selection_round': self.total_path_selections
            })
            
            logger.info(f"🎯 使用 {algorithm} 选择路径: {selected_path.path_type} (ID: {best_arm.path_id})")
            return selected_path
            
        except Exception as e:
            logger.error(f"❌ MAB路径选择算法执行失败: {e}")
            # 回退到随机选择
            selected_path = np.random.choice(paths)
            logger.info(f"🔄 回退到随机选择路径: {selected_path.path_type}")
            return selected_path
    
    def select_best_tool(self, available_tools: List[str], algorithm: str = 'auto') -> str:
        """
        🔧 新增：从可用工具列表中选择最优工具
        
        Args:
            available_tools: 可用工具名称列表
            algorithm: 使用的算法 ('thompson_sampling', 'ucb_variant', 'epsilon_greedy', 'auto')
            
        Returns:
            选择的最优工具名称
        """
        if not available_tools:
            raise ValueError("工具列表不能为空")
        
        if len(available_tools) == 1:
            logger.info(f"🔧 只有一个工具，直接选择: {available_tools[0]}")
            return available_tools[0]
        
        self.total_tool_selections += 1
        logger.info(f"🔧 开始第 {self.total_tool_selections} 次工具选择，候选工具: {len(available_tools)}个")
        
        # 🔧 动态创建：确保所有工具的决策臂都存在
        available_arms = []
        tool_to_arm_mapping = {}  # 工具名称到决策臂的映射
        
        for tool_name in available_tools:
            tool_id = tool_name  # 使用工具名称作为ID
            tool_to_arm_mapping[tool_name] = tool_id
            
            # 🔧 动态创建：确保工具决策臂存在
            arm = self._create_tool_arm_if_missing(tool_id, tool_name)
            available_arms.append(arm)
            
            logger.debug(f"✅ 工具决策臂就绪: {tool_id} ({tool_name})")
        
        # 自动选择算法
        if algorithm == 'auto':
            algorithm = self._select_best_algorithm_for_tools()
        
        # 根据选择的算法进行决策
        try:
            if algorithm == 'thompson_sampling':
                best_arm = self._thompson_sampling_for_tools(available_arms)
            elif algorithm == 'ucb_variant':
                best_arm = self._ucb_variant_for_tools(available_arms)
            elif algorithm == 'epsilon_greedy':
                best_arm = self._epsilon_greedy_for_tools(available_arms)
            else:
                logger.warning(f"⚠️ 未知算法 {algorithm}，使用Thompson采样")
                best_arm = self._thompson_sampling_for_tools(available_arms)
            
            # 更新使用时间和激活次数
            best_arm.last_used = time.time()
            best_arm.activation_count += 1
            
            # 🎯 找到对应的工具名称
            selected_tool = best_arm.option  # 工具名称存储在option字段中
            
            # 记录选择历史
            self.tool_selection_history.append({
                'tool_id': best_arm.path_id,
                'tool_name': selected_tool,
                'algorithm': algorithm,
                'timestamp': time.time(),
                'selection_round': self.total_tool_selections
            })
            
            logger.info(f"🔧 使用 {algorithm} 选择工具: {selected_tool} (ID: {best_arm.path_id})")
            return selected_tool
            
        except Exception as e:
            logger.error(f"❌ MAB工具选择算法执行失败: {e}")
            # 回退到随机选择
            selected_tool = np.random.choice(available_tools)
            logger.info(f"🔄 回退到随机选择工具: {selected_tool}")
            return selected_tool
    
    def is_tool_cold(self, tool_name: str) -> Dict[str, any]:
        """
        🔍 判断工具是否处于冷启动状态
        
        这个方法是MABConverger的"自我认知"能力，当MainController询问时，
        它能明确回答："我推荐的这个工具，我自己熟不熟？"
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Dict包含详细的冷启动分析结果:
            {
                'is_cold_start': bool,      # 是否处于冷启动状态
                'cold_score': float,        # 冷启动得分 (0-1, 越高越"冷")
                'confidence': float,        # 经验可信度 (0-1, 越高越可信)
                'analysis': {
                    'usage_count': int,     # 使用次数
                    'reliability_score': float,  # 可靠性分数
                    'idle_hours': float,    # 空闲时间(小时)
                    'sample_size': int      # 样本数量
                },
                'recommendation': str,      # 推荐模式 ('experience'/'exploration')
                'reason': str              # 判断理由
            }
        """
        logger.debug(f"🔍 开始冷启动检测: 工具 '{tool_name}'")
        
        # 获取冷启动配置
        cold_start_config = MAB_CONFIG["cold_start_threshold"]
        detection_weights = cold_start_config["detection_weights"]
        
        # 获取工具的决策臂
        tool_arm = self.tool_arms.get(tool_name)
        
        if not tool_arm:
            # 完全未使用的工具 - 绝对冷启动
            logger.debug(f"🆕 工具 '{tool_name}' 从未使用过，判定为冷启动")
            return {
                'is_cold_start': True,
                'cold_score': 1.0,
                'confidence': 0.0,
                'analysis': {
                    'usage_count': 0,
                    'reliability_score': 0.0,
                    'idle_hours': float('inf'),
                    'sample_size': 0
                },
                'recommendation': 'exploration',
                'reason': '工具从未被使用过，无任何经验数据'
            }
        
        # 计算各个冷启动因子
        analysis = self._calculate_cold_start_factors(tool_arm, cold_start_config)
        
        # 计算加权冷启动得分
        cold_score = (
            analysis['usage_factor'] * detection_weights['usage_frequency'] +
            analysis['reliability_factor'] * detection_weights['reliability'] +
            analysis['recency_factor'] * detection_weights['recency'] +
            analysis['sample_factor'] * detection_weights['sample_sufficiency']
        )
        
        # 判定是否冷启动
        exploration_threshold = cold_start_config["exploration_trigger_threshold"]
        is_cold = cold_score > exploration_threshold
        
        # 生成判断理由
        reason = self._generate_cold_start_reason(analysis, cold_score, exploration_threshold)
        
        result = {
            'is_cold_start': is_cold,
            'cold_score': round(cold_score, 3),
            'confidence': round(1.0 - cold_score, 3),
            'analysis': {
                'usage_count': analysis['usage_count'],
                'reliability_score': round(analysis['reliability_score'], 3),
                'idle_hours': round(analysis['idle_hours'], 2),
                'sample_size': analysis['sample_size']
            },
            'recommendation': 'exploration' if is_cold else 'experience',
            'reason': reason
        }
        
        logger.info(f"🔍 冷启动检测完成: {tool_name} -> "
                   f"{'冷启动' if is_cold else '经验丰富'} "
                   f"(得分: {cold_score:.3f}, 置信度: {result['confidence']:.3f})")
        
        return result
    
    def _calculate_cold_start_factors(self, tool_arm: EnhancedDecisionArm, 
                                    cold_start_config: Dict[str, any]) -> Dict[str, any]:
        """
        计算冷启动各个因子
        
        Args:
            tool_arm: 工具决策臂
            cold_start_config: 冷启动配置
            
        Returns:
            包含各个因子的分析结果
        """
        current_time = time.time()
        
        # 1. 使用频率因子 (使用次数越少，分数越高)
        usage_count = tool_arm.activation_count
        min_usage = cold_start_config["min_usage_count"]
        usage_factor = max(0.0, 1.0 - usage_count / max(min_usage, 1))
        
        # 2. 可靠性因子 (成功率不稳定或样本少时分数高)
        total_samples = tool_arm.success_count + tool_arm.failure_count
        if total_samples >= 3:
            reliability_score = tool_arm.success_rate
            # 样本数调整：样本越少，可靠性越低
            sample_adjustment = min(1.0, total_samples / 10.0)  # 10个样本视为充足
            adjusted_reliability = reliability_score * sample_adjustment
        else:
            adjusted_reliability = 0.0  # 样本太少，不可靠
        
        min_reliability = cold_start_config["min_reliability_score"]
        reliability_factor = max(0.0, 1.0 - adjusted_reliability / max(min_reliability, 0.1))
        
        # 3. 最近使用因子 (时间越久，分数越高)
        if tool_arm.last_used > 0:
            idle_hours = (current_time - tool_arm.last_used) / 3600
        else:
            idle_hours = float('inf')
        
        max_idle = cold_start_config["max_idle_hours"]
        recency_factor = min(1.0, idle_hours / max(max_idle, 1))
        
        # 4. 样本充足性因子 (样本越少，分数越高)
        min_samples = cold_start_config["min_sample_size"]
        sample_factor = max(0.0, 1.0 - total_samples / max(min_samples, 1))
        
        return {
            'usage_count': usage_count,
            'usage_factor': usage_factor,
            'reliability_score': adjusted_reliability,
            'reliability_factor': reliability_factor,
            'idle_hours': idle_hours if idle_hours != float('inf') else -1,
            'recency_factor': recency_factor,
            'sample_size': total_samples,
            'sample_factor': sample_factor
        }
    
    def _generate_cold_start_reason(self, analysis: Dict[str, any], 
                                   cold_score: float, threshold: float) -> str:
        """
        生成冷启动判断的详细理由
        
        Args:
            analysis: 分析结果
            cold_score: 冷启动得分
            threshold: 判定阈值
            
        Returns:
            判断理由字符串
        """
        reasons = []
        
        # 使用频率分析
        if analysis['usage_factor'] > 0.7:
            reasons.append(f"使用次数过少({analysis['usage_count']}次)")
        elif analysis['usage_factor'] > 0.3:
            reasons.append(f"使用经验有限({analysis['usage_count']}次)")
        
        # 可靠性分析
        if analysis['reliability_factor'] > 0.6:
            reasons.append(f"性能数据不可靠(可靠性:{analysis['reliability_score']:.2f})")
        elif analysis['reliability_factor'] > 0.3:
            reasons.append(f"性能数据不够稳定")
        
        # 最近使用分析
        if analysis['idle_hours'] > 72:
            reasons.append(f"长时间未使用({analysis['idle_hours']:.1f}小时)")
        elif analysis['idle_hours'] > 24:
            reasons.append(f"较长时间未使用")
        
        # 样本数分析
        if analysis['sample_factor'] > 0.7:
            reasons.append(f"样本数据不足({analysis['sample_size']}个)")
        
        if not reasons:
            if cold_score > threshold:
                reasons.append("综合评估显示缺乏足够经验")
            else:
                reasons.append("具有充足的使用经验和可靠数据")
        
        # 组合理由
        if cold_score > threshold:
            return f"冷启动状态: {'; '.join(reasons)} (得分:{cold_score:.3f} > {threshold})"
        else:
            return f"经验丰富: {'; '.join(reasons)} (得分:{cold_score:.3f} ≤ {threshold})"
    
    def _thompson_sampling_for_paths(self, arms: List[EnhancedDecisionArm]) -> EnhancedDecisionArm:
        """针对思维路径的Thompson采样算法"""
        if not arms:
            raise ValueError("没有可用的路径决策臂")
        
        best_arm = None
        best_score = -1
        
        logger.debug(f"🎲 Thompson采样路径选择，候选路径: {len(arms)}个")
        
        for arm in arms:
            # 使用Beta分布进行Thompson采样
            alpha = arm.success_count + 1
            beta = arm.failure_count + 1
            
            # 从Beta分布中采样
            sampled_value = np.random.beta(alpha, beta)
            
            # 路径级别的奖励考虑
            if arm.rl_reward_history:
                avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history)
                # 将奖励调整到0-1范围
                normalized_reward = max(0, min(1, (avg_reward + 1) / 2))
                sampled_value = sampled_value * 0.8 + normalized_reward * 0.2
            
            # 路径多样性考虑：减少过度依赖单一路径
            usage_penalty = min(0.1, arm.activation_count / (self.total_path_selections + 1) * 0.2)
            sampled_value = max(0, sampled_value - usage_penalty)
            
            logger.debug(f"   路径 {arm.path_id}: sampled={sampled_value:.3f}, α={alpha}, β={beta}")
            
            if sampled_value > best_score:
                best_score = sampled_value
                best_arm = arm
        
        logger.debug(f"🏆 Thompson采样选择: {best_arm.path_id} (得分: {best_score:.3f})")
        return best_arm
    
    def _ucb_variant_for_paths(self, arms: List[EnhancedDecisionArm]) -> EnhancedDecisionArm:
        """针对思维路径的UCB (Upper Confidence Bound) 变种算法"""
        if not arms:
            raise ValueError("没有可用的路径决策臂")
        
        total_rounds = sum(arm.activation_count for arm in arms)
        if total_rounds == 0:
            # 第一轮随机选择
            selected_arm = np.random.choice(arms)
            logger.debug(f"🎲 UCB首轮随机选择路径: {selected_arm.path_id}")
            return selected_arm
        
        best_arm = None
        best_ucb_value = -float('inf')
        
        logger.debug(f"📊 UCB路径选择，总轮数: {total_rounds}")
        
        for arm in arms:
            if arm.activation_count == 0:
                # 未尝试过的路径优先选择
                logger.debug(f"🆕 优先选择未使用路径: {arm.path_id}")
                return arm
            
            # 计算UCB值
            confidence_bound = np.sqrt(2 * np.log(total_rounds) / arm.activation_count)
            
            # 基础成功率
            base_value = arm.success_rate
            
            # 路径级别的RL奖励考虑
            if arm.rl_reward_history:
                avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history)
                normalized_reward = max(0, min(1, (avg_reward + 1) / 2))
                base_value = base_value * 0.7 + normalized_reward * 0.3
            
            # 路径探索奖励：鼓励尝试不同思维方式
            exploration_bonus = confidence_bound * 1.2  # 增强探索
            ucb_value = base_value + exploration_bonus
            
            logger.debug(f"   路径 {arm.path_id}: UCB={ucb_value:.3f}, base={base_value:.3f}, conf={confidence_bound:.3f}")
            
            if ucb_value > best_ucb_value:
                best_ucb_value = ucb_value
                best_arm = arm
        
        logger.debug(f"🏆 UCB选择路径: {best_arm.path_id} (UCB值: {best_ucb_value:.3f})")
        return best_arm
    
    def _epsilon_greedy_for_paths(self, arms: List[EnhancedDecisionArm]) -> EnhancedDecisionArm:
        """针对思维路径的Epsilon-Greedy算法"""
        if not arms:
            raise ValueError("没有可用的路径决策臂")
        
        # 路径级别的动态epsilon值，鼓励思维多样性
        total_activations = sum(arm.activation_count for arm in arms)
        epsilon = max(0.1, 0.4 / (1 + total_activations * 0.008))  # 比传统更高的探索率
        
        logger.debug(f"🎯 Epsilon-Greedy路径选择，ε={epsilon:.3f}")
        
        # 使用epsilon决定是否探索
        if np.random.random() < epsilon:
            # 探索：随机选择路径，鼓励思维多样性
            selected_arm = np.random.choice(arms)
            logger.debug(f"🔍 探索模式选择路径: {selected_arm.path_id}")
            return selected_arm
        else:
            # 利用：选择当前最好的路径
            best_arm = None
            best_score = -float('inf')
            
            for arm in arms:
                # 路径级别的综合评分
                score = arm.success_rate
                
                # RL奖励权重
                if arm.rl_reward_history:
                    avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history)
                    normalized_reward = max(0, min(1, (avg_reward + 1) / 2))
                    score = score * 0.6 + normalized_reward * 0.4
                
                # 路径使用频率平衡：避免过度依赖单一思维模式
                usage_ratio = arm.activation_count / (total_activations + 1)
                if usage_ratio > 0.5:  # 如果某路径使用过于频繁，稍微降低评分
                    score *= 0.95
                
                logger.debug(f"   路径 {arm.path_id}: score={score:.3f}, usage_ratio={usage_ratio:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_arm = arm
            
            logger.debug(f"🏆 利用模式选择路径: {best_arm.path_id} (得分: {best_score:.3f})")
            return best_arm if best_arm else arms[0]
    
    def _select_best_algorithm_for_paths(self) -> str:
        """
        为路径选择选择最佳算法
        
        Returns:
            最佳算法名称
        """
        # 如果样本太少，使用Thompson采样进行探索
        if self.total_path_selections < 15:
            logger.debug("📊 样本较少，选择Thompson采样")
            return 'thompson_sampling'
        
        # 计算路径级别的收敛水平
        if not self.path_arms:
            return 'thompson_sampling'
        
        arms_list = list(self.path_arms.values())
        convergence_level = self._calculate_path_convergence_level(arms_list)
        
        # 考虑思维多样性：路径选择需要更多探索
        if convergence_level < 0.4:
            # 低收敛，使用探索性强的算法
            logger.debug(f"📊 低收敛({convergence_level:.3f})，选择Thompson采样")
            return 'thompson_sampling'
        elif convergence_level < 0.7:
            # 中等收敛，使用平衡的算法
            logger.debug(f"📊 中等收敛({convergence_level:.3f})，选择UCB")
            return 'ucb_variant'
        else:
            # 高收敛，但仍需保持一定探索（思维多样性重要）
            logger.debug(f"📊 高收敛({convergence_level:.3f})，选择Epsilon-Greedy")
            return 'epsilon_greedy'
    
    def _calculate_path_convergence_level(self, arms: List[EnhancedDecisionArm]) -> float:
        """
        计算路径级别的收敛水平
        
        Args:
            arms: 路径决策臂列表
            
        Returns:
            收敛水平 (0.0-1.0)
        """
        if len(arms) < 2:
            return 0.0
        
        # 计算路径成功率方差
        success_rates = []
        for arm in arms:
            total = arm.success_count + arm.failure_count
            if total > 0:
                success_rates.append(arm.success_count / total)
        
        if len(success_rates) < 2:
            return 0.0
        
        variance = np.var(success_rates)
        # 将方差转换为收敛水平（方差越小，收敛水平越高）
        # 对于思维路径，我们希望保持一定的多样性，所以收敛标准稍微宽松
        convergence_level = max(0.0, 1.0 - variance * 3.5)
        
        return convergence_level
    
    # ==================== 🔧 工具选择MAB算法实现 ====================
    
    def _select_best_algorithm_for_tools(self) -> str:
        """
        为工具选择选择最佳算法
        
        Returns:
            最佳算法名称
        """
        # 如果样本太少，使用Thompson采样进行探索
        if self.total_tool_selections < 10:
            logger.debug("📊 工具选择样本较少，选择Thompson采样")
            return 'thompson_sampling'
        
        # 计算工具级别的收敛水平
        if not self.tool_arms:
            return 'thompson_sampling'
        
        arms_list = list(self.tool_arms.values())
        convergence_level = self._calculate_tool_convergence_level(arms_list)
        
        # 工具选择倾向于更快收敛到最优工具
        if convergence_level < 0.3:
            # 低收敛，使用探索性强的算法
            logger.debug(f"📊 工具选择低收敛({convergence_level:.3f})，选择Thompson采样")
            return 'thompson_sampling'
        elif convergence_level < 0.6:
            # 中等收敛，使用平衡的算法
            logger.debug(f"📊 工具选择中等收敛({convergence_level:.3f})，选择UCB")
            return 'ucb_variant'
        else:
            # 高收敛，使用利用型算法
            logger.debug(f"📊 工具选择高收敛({convergence_level:.3f})，选择Epsilon-Greedy")
            return 'epsilon_greedy'
    
    def _calculate_tool_convergence_level(self, arms: List[EnhancedDecisionArm]) -> float:
        """
        计算工具级别的收敛水平
        
        Args:
            arms: 工具决策臂列表
            
        Returns:
            收敛水平 (0.0-1.0)
        """
        if len(arms) < 2:
            return 0.0
        
        # 计算工具成功率方差
        success_rates = []
        for arm in arms:
            total = arm.success_count + arm.failure_count
            if total > 0:
                success_rates.append(arm.success_count / total)
        
        if len(success_rates) < 2:
            return 0.0
        
        variance = np.var(success_rates)
        # 工具选择可以更快收敛，收敛标准相对严格
        convergence_level = max(0.0, 1.0 - variance * 2.5)
        
        return convergence_level
    
    def _thompson_sampling_for_tools(self, arms: List[EnhancedDecisionArm]) -> EnhancedDecisionArm:
        """针对工具选择的Thompson采样算法"""
        if not arms:
            raise ValueError("没有可用的工具决策臂")
        
        best_arm = None
        best_score = -1
        
        logger.debug(f"🔧 Thompson采样工具选择，候选工具: {len(arms)}个")
        
        for arm in arms:
            # 使用Beta分布进行Thompson采样
            alpha = arm.success_count + 1
            beta = arm.failure_count + 1
            
            # 从Beta分布中采样
            sampled_value = np.random.beta(alpha, beta)
            
            # 工具级别的奖励考虑
            if arm.rl_reward_history:
                avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history)
                # 将奖励调整到0-1范围
                normalized_reward = max(0, min(1, (avg_reward + 1) / 2))
                sampled_value = sampled_value * 0.7 + normalized_reward * 0.3
            
            logger.debug(f"   工具 {arm.path_id}: sampled={sampled_value:.3f}, α={alpha}, β={beta}")
            
            if sampled_value > best_score:
                best_score = sampled_value
                best_arm = arm
        
        logger.debug(f"🏆 Thompson采样选择工具: {best_arm.path_id} (得分: {best_score:.3f})")
        return best_arm
    
    def _ucb_variant_for_tools(self, arms: List[EnhancedDecisionArm]) -> EnhancedDecisionArm:
        """针对工具选择的UCB (Upper Confidence Bound) 变种算法"""
        if not arms:
            raise ValueError("没有可用的工具决策臂")
        
        total_rounds = sum(arm.activation_count for arm in arms)
        if total_rounds == 0:
            # 第一轮随机选择
            selected_arm = np.random.choice(arms)
            logger.debug(f"🔧 UCB首轮随机选择工具: {selected_arm.path_id}")
            return selected_arm
        
        best_arm = None
        best_ucb_value = -float('inf')
        
        logger.debug(f"📊 UCB工具选择，总轮数: {total_rounds}")
        
        for arm in arms:
            if arm.activation_count == 0:
                # 未尝试过的工具优先选择
                logger.debug(f"🆕 优先选择未使用工具: {arm.path_id}")
                return arm
            
            # 计算UCB值
            confidence_bound = np.sqrt(2 * np.log(total_rounds) / arm.activation_count)
            
            # 基础成功率
            base_value = arm.success_rate
            
            # 工具级别的RL奖励考虑
            if arm.rl_reward_history:
                avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history)
                normalized_reward = max(0, min(1, (avg_reward + 1) / 2))
                base_value = base_value * 0.6 + normalized_reward * 0.4
            
            # 工具探索奖励
            exploration_bonus = confidence_bound * 1.0  # 标准探索
            ucb_value = base_value + exploration_bonus
            
            logger.debug(f"   工具 {arm.path_id}: UCB={ucb_value:.3f}, base={base_value:.3f}, conf={confidence_bound:.3f}")
            
            if ucb_value > best_ucb_value:
                best_ucb_value = ucb_value
                best_arm = arm
        
        logger.debug(f"🏆 UCB选择工具: {best_arm.path_id} (UCB值: {best_ucb_value:.3f})")
        return best_arm
    
    def _epsilon_greedy_for_tools(self, arms: List[EnhancedDecisionArm]) -> EnhancedDecisionArm:
        """针对工具选择的Epsilon-Greedy算法"""
        if not arms:
            raise ValueError("没有可用的工具决策臂")
        
        # 工具级别的动态epsilon值
        total_activations = sum(arm.activation_count for arm in arms)
        epsilon = max(0.05, 0.3 / (1 + total_activations * 0.01))  # 比路径选择更低的探索率
        
        logger.debug(f"🔧 Epsilon-Greedy工具选择，ε={epsilon:.3f}")
        
        # 使用epsilon决定是否探索
        if np.random.random() < epsilon:
            # 探索：随机选择工具
            selected_arm = np.random.choice(arms)
            logger.debug(f"🔍 探索模式选择工具: {selected_arm.path_id}")
            return selected_arm
        else:
            # 利用：选择当前最好的工具
            best_arm = None
            best_score = -float('inf')
            
            for arm in arms:
                # 工具级别的综合评分
                score = arm.success_rate
                
                # RL奖励权重
                if arm.rl_reward_history:
                    avg_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history)
                    normalized_reward = max(0, min(1, (avg_reward + 1) / 2))
                    score = score * 0.5 + normalized_reward * 0.5
                
                logger.debug(f"   工具 {arm.path_id}: score={score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_arm = arm
            
            logger.debug(f"🏆 利用模式选择工具: {best_arm.path_id} (得分: {best_score:.3f})")
            return best_arm if best_arm else arms[0]
    
    # ==================== 📊 更新性能反馈方法 ====================
    
    def update_path_performance(self, path_id: str, success: bool, reward: float = 0.0):
        """
        🔧 双层学习：更新路径或工具的性能反馈 - 通用性反馈更新方法
        
        Args:
            path_id: 路径ID或工具ID（由调用方决定是路径还是工具）
            success: 执行是否成功
            reward: RL奖励值
        """
        # 🎯 智能识别：检查是路径反馈还是工具反馈
        if path_id in self.path_arms:
            # 路径反馈处理
            target_arm = self.path_arms[path_id]
            
            # 更新路径算法性能统计
            if self.path_selection_history:
                last_selection = self.path_selection_history[-1]
                if last_selection['path_id'] == path_id:
                    algorithm = last_selection['algorithm']
                    self.algorithm_performance[algorithm]['total'] += 1
                    if success:
                        self.algorithm_performance[algorithm]['successes'] += 1
                        
        elif path_id in self.tool_arms:
            # 工具反馈处理
            target_arm = self.tool_arms[path_id]
            
            # 更新工具算法性能统计
            if self.tool_selection_history:
                last_selection = self.tool_selection_history[-1]
                if last_selection['tool_id'] == path_id:
                    algorithm = last_selection['algorithm']
                    self.tool_algorithm_performance[algorithm]['total'] += 1
                    if success:
                        self.tool_algorithm_performance[algorithm]['successes'] += 1
                        
        else:
            # 动态创建决策臂（默认作为路径处理，保持向后兼容）
            target_arm = self._create_strategy_arm_if_missing(path_id)
            logger.debug(f"🔧 为未知ID {path_id} 创建路径决策臂（向后兼容）")
        
        # 使用增强的性能更新方法
        target_arm.update_performance(success, reward)
        
        # 记录更新日志
        arm_type = "工具" if path_id in self.tool_arms else "路径"
        logger.info(f"📊 更新{arm_type}性能: {path_id} -> 成功率:{target_arm.success_rate:.3f}, 奖励:{reward:.3f}")
        logger.debug(f"   详细: 成功{target_arm.success_count}次, 失败{target_arm.failure_count}次, 激活{target_arm.activation_count}次")
        
        # 🏆 黄金模板识别逻辑：检查是否符合黄金模板条件（仅对路径应用）
        if path_id in self.path_arms:
            self._check_and_promote_to_golden_template(path_id, target_arm)
    
    # 保留向后兼容的方法（标记为过时）
    def update_arm_performance(self, dimension_name: str, option: str, 
                             success: bool, reward: float = 0.0):
        """
        更新决策臂的性能 - 已过时，请使用 update_path_performance
        
        Args:
            dimension_name: 维度名称
            option: 选项名称
            success: 是否成功
            reward: RL奖励值
        """
        logger.warning("⚠️ update_arm_performance 已过时，请使用 update_path_performance")
        path_id = f"{dimension_name}_{option}"  # 临时转换
        self.update_path_performance(path_id, success, reward)
    
    def check_path_convergence(self) -> bool:
        """
        检查路径选择是否收敛
        
        Returns:
            是否收敛
        """
        if len(self.path_arms) < 2:
            return False
            
        # 检查是否有足够的样本
        total_samples = sum(arm.success_count + arm.failure_count for arm in self.path_arms.values())
        if total_samples < self.min_samples:
            return False
            
        # 计算路径成功率方差，判断是否收敛
        success_rates = []
        for arm in self.path_arms.values():
            total = arm.success_count + arm.failure_count
            if total > 0:
                success_rates.append(arm.success_count / total)
                
        if len(success_rates) < 2:
            return False
            
        variance = np.var(success_rates)
        # 对于思维路径，使用稍微宽松的收敛标准，保持多样性
        adjusted_threshold = self.convergence_threshold * 1.2
        is_converged = variance < adjusted_threshold
        
        if is_converged:
            logger.info(f"✅ 路径选择已收敛 (方差:{variance:.4f}, 阈值:{adjusted_threshold:.4f})")
        
        return is_converged
    
    # 保留向后兼容的方法（标记为过时）
    def check_convergence(self, dimension_name: str) -> bool:
        """
        检查指定维度是否收敛 - 已过时，请使用 check_path_convergence
        """
        logger.warning("⚠️ check_convergence 已过时，请使用 check_path_convergence")
        return self.check_path_convergence()
    
    def get_path_statistics(self) -> Dict[str, Dict[str, any]]:
        """
        获取所有路径的统计信息（包含黄金模板状态）
        
        Returns:
            路径统计数据
        """
        statistics = {}
        
        for path_id, arm in self.path_arms.items():
            # 检查是否为黄金模板
            is_golden_template = path_id in self.golden_templates
            golden_template_info = None
            
            if is_golden_template:
                template_data = self.golden_templates[path_id]
                golden_template_info = {
                    'created_timestamp': template_data['created_timestamp'],
                    'last_updated': template_data['last_updated'],
                    'stability_score': template_data['stability_score'],
                    'usage_as_template': self.template_usage_stats.get(path_id, 0),
                    'promotion_reason': template_data['promotion_reason']
                }
            
            # 计算路径特定的统计
            statistics[path_id] = {
                'path_type': arm.option,  # 路径类型
                'path_id': path_id,
                'activation_count': arm.activation_count,
                'success_count': arm.success_count,
                'failure_count': arm.failure_count,
                'success_rate': arm.success_rate,
                'total_reward': arm.total_reward,
                'average_reward': sum(arm.rl_reward_history) / len(arm.rl_reward_history) if arm.rl_reward_history else 0.0,
                'last_used': arm.last_used,
                'recent_trend': self._calculate_recent_trend(arm),
                'consecutive_successes': self._calculate_consecutive_successes(arm),
                'usage_ratio': arm.activation_count / max(self.total_path_selections, 1),
                
                # 🏆 黄金模板相关信息
                'is_golden_template': is_golden_template,
                'golden_template_info': golden_template_info,
                'meets_golden_criteria': self._check_golden_criteria(arm),
                'stability_score': self._calculate_stability_score(arm) if arm.activation_count >= 10 else 0.0
            }
        
        return statistics
    
    def _check_golden_criteria(self, arm: EnhancedDecisionArm) -> bool:
        """
        检查路径是否符合黄金模板的基本条件（不包括稳定性检查）
        
        Args:
            arm: 决策臂对象
            
        Returns:
            是否符合基本条件
        """
        config = self.golden_template_config
        return (arm.success_rate >= config['success_rate_threshold'] and 
                arm.activation_count >= config['min_samples_required'])
    
    def get_system_path_summary(self) -> Dict[str, any]:
        """
        获取路径选择系统的整体摘要
        
        Returns:
            系统摘要数据
        """
        if not self.path_arms:
            return {
                'total_paths': 0,
                'total_selections': self.total_path_selections,
                'is_converged': False,
                'convergence_level': 0.0,
                'most_used_path': None,
                'best_performing_path': None
            }
        
        # 最常用路径
        most_used_arm = max(self.path_arms.values(), key=lambda a: a.activation_count)
        
        # 最佳性能路径
        best_performing_arm = max(self.path_arms.values(), key=lambda a: a.success_rate)
        
        # 算法性能统计
        algorithm_stats = {}
        for algo, stats in self.algorithm_performance.items():
            if stats['total'] > 0:
                algorithm_stats[algo] = {
                    'success_rate': stats['successes'] / stats['total'],
                    'total_uses': stats['total']
                }
        
        return {
            'total_paths': len(self.path_arms),
            'total_selections': self.total_path_selections,
            'is_converged': self.check_path_convergence(),
            'convergence_level': self._calculate_path_convergence_level(list(self.path_arms.values())),
            'most_used_path': {
                'path_id': most_used_arm.path_id,
                'path_type': most_used_arm.option,
                'usage_count': most_used_arm.activation_count
            },
            'best_performing_path': {
                'path_id': best_performing_arm.path_id,
                'path_type': best_performing_arm.option,
                'success_rate': best_performing_arm.success_rate
            },
            'algorithm_performance': algorithm_stats,
            'total_samples': sum(arm.success_count + arm.failure_count for arm in self.path_arms.values())
        }
    
    # 保留向后兼容的方法（标记为过时）
    def get_dimension_statistics(self) -> Dict[str, Dict[str, any]]:
        """
        获取所有维度的统计信息 - 已过时，请使用 get_path_statistics
        """
        logger.warning("⚠️ get_dimension_statistics 已过时，请使用 get_path_statistics")
        return self.get_path_statistics()
    
    def get_path_details(self, path_id: str = None) -> Dict[str, any]:
        """
        获取指定路径的详细信息
        
        Args:
            path_id: 路径ID，如果为None则返回所有路径的详细信息
            
        Returns:
            路径详细信息
        """
        if path_id is not None:
            if path_id not in self.path_arms:
                logger.warning(f"⚠️ 路径 {path_id} 不存在")
                return {}
            
            arm = self.path_arms[path_id]
            return {
                'path_id': path_id,
                'path_type': arm.option,
                'success_count': arm.success_count,
                'failure_count': arm.failure_count,
                'success_rate': arm.success_rate,
                'total_reward': arm.total_reward,
                'average_reward': sum(arm.rl_reward_history) / len(arm.rl_reward_history) if arm.rl_reward_history else 0.0,
                'activation_count': arm.activation_count,
                'last_used': arm.last_used,
                'recent_trend': self._calculate_recent_trend(arm),
                'consecutive_successes': self._calculate_consecutive_successes(arm),
                'rl_reward_history': arm.rl_reward_history.copy(),
                'recent_results': arm.recent_results.copy()
            }
        else:
            # 返回所有路径的详细信息
            all_details = {}
            for pid, arm in self.path_arms.items():
                all_details[pid] = self.get_path_details(pid)
            
            # 按成功率排序
            sorted_paths = sorted(all_details.items(), 
                                key=lambda x: x[1]['success_rate'], 
                                reverse=True)
            return dict(sorted_paths)
    
    def get_selection_history(self, limit: int = 10) -> List[Dict[str, any]]:
        """
        获取路径选择历史
        
        Args:
            limit: 返回的历史记录数量限制
            
        Returns:
            选择历史列表
        """
        return self.path_selection_history[-limit:] if self.path_selection_history else []
    
    # 保留向后兼容的方法（标记为过时）
    def get_arm_details(self, dimension_name: str) -> List[Dict[str, any]]:
        """
        获取指定维度的所有决策臂详细信息 - 已过时，请使用 get_path_details
        """
        logger.warning("⚠️ get_arm_details 已过时，请使用 get_path_details")
        return list(self.get_path_details().values())
    
    def reset_path(self, path_id: str):
        """
        重置指定路径的所有数据
        
        Args:
            path_id: 路径ID
        """
        if path_id in self.path_arms:
            del self.path_arms[path_id]
            logger.info(f"🔄 路径 {path_id} 已重置")
        
        # 清理选择历史中的相关记录
        self.path_selection_history = [
            record for record in self.path_selection_history 
            if record['path_id'] != path_id
        ]
    
    def reset_all_paths(self):
        """
        重置所有路径数据，完全清空学习历史
        """
        self.path_arms.clear()
        self.path_selection_history.clear()
        self.total_path_selections = 0
        self.algorithm_performance.clear()
        logger.info("🔄 所有路径数据已重置")
    
    def get_system_status(self) -> Dict[str, any]:
        """
        获取MAB路径选择系统的整体状态
        
        Returns:
            系统状态信息
        """
        total_paths = len(self.path_arms)
        is_converged = self.check_path_convergence()
        
        # 计算活跃路径数（最近使用过的）
        current_time = time.time()
        active_paths = sum(
            1 for arm in self.path_arms.values() 
            if arm.last_used > 0 and (current_time - arm.last_used) < 3600  # 1小时内使用过
        )
        
        # 最受欢迎的路径类型
        path_type_usage = {}
        for arm in self.path_arms.values():
            path_type = arm.option
            path_type_usage[path_type] = path_type_usage.get(path_type, 0) + arm.activation_count
        
        most_popular_type = max(path_type_usage.items(), key=lambda x: x[1])[0] if path_type_usage else None
        
        # 获取黄金模板统计
        golden_stats = self.get_golden_template_stats()
        
        return {
            'mode': 'path_selection',  # 新增：标识当前为路径选择模式
            'total_paths': total_paths,
            'active_paths': active_paths,
            'total_selections': self.total_path_selections,
            'is_converged': is_converged,
            'convergence_level': self._calculate_path_convergence_level(list(self.path_arms.values())) if self.path_arms else 0.0,
            'convergence_threshold': self.convergence_threshold,
            'min_samples': self.min_samples,
            'most_popular_path_type': most_popular_type,
            'path_type_distribution': path_type_usage,
            'algorithm_performance': dict(self.algorithm_performance),
            
            # 🏆 黄金模板系统状态
            'golden_template_system': {
                'enabled': True,
                'total_templates': golden_stats['total_templates'],
                'avg_success_rate': golden_stats['avg_success_rate'],
                'total_usage_count': golden_stats['total_usage_count'],
                'most_used_template': golden_stats['most_used_template'],
                'match_history_count': golden_stats['match_history_count'],
                'config': self.golden_template_config
            }
        }
    
    # 保留向后兼容的方法（标记为过时）
    def reset_dimension(self, dimension_name: str):
        """
        重置指定维度的所有数据 - 已过时，请使用 reset_path 或 reset_all_paths
        """
        logger.warning("⚠️ reset_dimension 已过时，请使用 reset_path 或 reset_all_paths")
        # 不执行任何操作，避免意外清除路径数据
    
    # ==================== 🏆 黄金决策模板系统实现 ====================
    
    def _check_golden_template_match(self, paths: List[ReasoningPath]) -> Optional[Dict[str, any]]:
        """
        检查当前路径列表是否与已有黄金模板匹配 - 🎯 修复版：基于策略ID匹配
        
        Args:
            paths: 候选思维路径列表
            
        Returns:
            匹配结果字典，包含匹配的模板和路径信息，如果无匹配则返回None
        """
        if not self.golden_templates:
            return None
        
        best_match = None
        best_score = 0.0
        match_threshold = 0.85  # 匹配阈值
        
        logger.debug(f"🏆 检查 {len(self.golden_templates)} 个黄金模板")
        
        for template_id, template_data in self.golden_templates.items():
            template_path_type = template_data['path_type']
            
            # 🎯 根源修复：直接使用路径的策略ID，无需推导
            for path in paths:
                # 直接使用路径的策略ID
                path_strategy_id = path.strategy_id
                
                # 检查是否匹配：策略ID匹配或路径类型匹配
                is_strategy_match = (template_id == path_strategy_id)
                is_type_match = (template_path_type == path.path_type)
                
                if is_strategy_match or is_type_match:
                    # 计算匹配分数
                    match_score = self._calculate_template_match_score(template_data, path)
                    
                    # 策略ID匹配给额外分数
                    if is_strategy_match:
                        match_score += 0.1  # 策略ID匹配奖励
                    
                    logger.debug(f"   模板 {template_id} vs 路径策略 {path_strategy_id}: 匹配分数 {match_score:.3f}")
                    logger.debug(f"      策略匹配: {is_strategy_match}, 类型匹配: {is_type_match}")
                    
                    if match_score > match_threshold and match_score > best_score:
                        best_match = {
                            'template_id': template_id,
                            'path': path,
                            'match_score': match_score,
                            'template_data': template_data,
                            'strategy_match': is_strategy_match
                        }
                        best_score = match_score
        
        if best_match:
            match_type = "策略ID" if best_match['strategy_match'] else "路径类型"
            logger.debug(f"🏆 找到最佳匹配: 模板 {best_match['template_id']} (分数: {best_score:.3f}, 匹配类型: {match_type})")
        else:
            logger.debug("🏆 未找到符合条件的黄金模板匹配")
        
        return best_match
    
    def _calculate_template_match_score(self, template_data: Dict[str, any], path: ReasoningPath) -> float:
        """
        计算模板与路径的匹配分数 - 🎯 修复版：基于策略ID匹配
        
        Args:
            template_data: 黄金模板数据
            path: 候选路径
            
        Returns:
            匹配分数 (0.0-1.0)
        """
        score = 0.0
        
        # 🎯 根源修复：直接使用路径的策略ID
        path_strategy_id = path.strategy_id
        
        # 1. 策略ID完全匹配 (基础分数60%)
        template_strategy_id = template_data.get('strategy_id', template_data.get('path_id', ''))
        if template_strategy_id == path_strategy_id:
            score += 0.6
        # 1b. 路径类型匹配作为备选 (基础分数40%)
        elif template_data['path_type'] == path.path_type:
            score += 0.4
        
        # 2. 描述相似性 (额外20%)
        desc_similarity = self._calculate_description_similarity(
            template_data.get('description', ''), path.description
        )
        score += desc_similarity * 0.2
        
        # 3. 历史性能奖励 (额外20%)
        performance_bonus = min(template_data['success_rate'] - 0.8, 0.2) * 1.0  # 超过80%的部分转换为奖励
        score += performance_bonus
        
        logger.debug(f"🎯 匹配分数详情:")
        logger.debug(f"   模板策略ID: {template_strategy_id}")
        logger.debug(f"   路径策略ID: {path_strategy_id}")
        logger.debug(f"   策略匹配: {template_strategy_id == path_strategy_id}")
        logger.debug(f"   描述相似性: {desc_similarity:.3f}")
        logger.debug(f"   性能奖励: {performance_bonus:.3f}")
        logger.debug(f"   总分: {score:.3f}")
        
        return min(score, 1.0)
    
    def _calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """
        计算两个描述文本的相似度（简单实现）
        
        Args:
            desc1: 描述文本1
            desc2: 描述文本2
            
        Returns:
            相似度分数 (0.0-1.0)
        """
        if not desc1 or not desc2:
            return 0.0
        
        # 简单的关键词匹配算法
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _check_and_promote_to_golden_template(self, path_id: str, arm: EnhancedDecisionArm):
        """
        检查路径是否符合黄金模板条件，如果符合则提升为黄金模板
        
        Args:
            path_id: 路径ID
            arm: 决策臂对象
        """
        config = self.golden_template_config
        
        # 检查基本条件
        if (arm.success_rate >= config['success_rate_threshold'] and 
            arm.activation_count >= config['min_samples_required']):
            
            # 检查稳定性（最近N次的表现）
            if self._check_path_stability(arm):
                # 检查是否已经是黄金模板
                if path_id not in self.golden_templates:
                    self._promote_to_golden_template(path_id, arm)
                else:
                    # 更新已有黄金模板
                    self._update_golden_template(path_id, arm)
    
    def _check_path_stability(self, arm: EnhancedDecisionArm) -> bool:
        """
        检查路径的稳定性（最近表现是否持续良好）
        
        Args:
            arm: 决策臂对象
            
        Returns:
            是否稳定
        """
        window_size = self.golden_template_config['stability_check_window']
        
        # 获取最近的结果
        recent_results = arm.recent_results[-window_size:] if len(arm.recent_results) >= window_size else arm.recent_results
        
        if len(recent_results) < window_size:
            return False  # 样本不足
        
        # 计算最近窗口的成功率
        recent_successes = sum(1 for result in recent_results if result)
        recent_success_rate = recent_successes / len(recent_results)
        
        # 稳定性要求：最近表现不低于整体表现的95%
        stability_threshold = arm.success_rate * 0.95
        
        return recent_success_rate >= stability_threshold
    
    def _promote_to_golden_template(self, strategy_id: str, arm: EnhancedDecisionArm):
        """
        将策略提升为黄金模板 - 🎯 修复版：基于策略ID
        
        Args:
            strategy_id: 策略ID（而非实例ID）
            arm: 决策臂对象
        """
        # 检查模板数量限制
        if len(self.golden_templates) >= self.golden_template_config['max_golden_templates']:
            # 移除表现最差的模板
            self._remove_worst_golden_template()
        
        # 🎯 修复：基于策略ID创建黄金模板
        template_data = {
            'strategy_id': strategy_id,        # 策略ID（用于匹配）
            'path_id': strategy_id,           # 兼容性字段
            'path_type': arm.option,          # 路径类型
            'description': getattr(arm, 'description', ''),
            'success_rate': arm.success_rate,
            'total_activations': arm.activation_count,
            'average_reward': sum(arm.rl_reward_history) / len(arm.rl_reward_history) if arm.rl_reward_history else 0.0,
            'created_timestamp': time.time(),
            'last_updated': time.time(),
            'promotion_reason': 'high_performance',
            'stability_score': self._calculate_stability_score(arm),
            'usage_count': 0  # 作为模板被使用的次数
        }
        
        # 使用策略ID作为模板键
        self.golden_templates[strategy_id] = template_data
        
        logger.info(f"🏆 新黄金模板诞生！")
        logger.info(f"   策略ID: {strategy_id}")
        logger.info(f"   路径类型: {arm.option}")
        logger.info(f"   成功率: {arm.success_rate:.1%}")
        logger.info(f"   激活次数: {arm.activation_count}")
        avg_rl_reward = sum(arm.rl_reward_history) / len(arm.rl_reward_history) if arm.rl_reward_history else 0.0
        logger.info(f"   平均奖励: {avg_rl_reward:.3f}")
        logger.info(f"   当前黄金模板总数: {len(self.golden_templates)}")
    
    def _update_golden_template(self, strategy_id: str, arm: EnhancedDecisionArm):
        """
        更新已有的黄金模板数据 - 🎯 修复版：基于策略ID
        
        Args:
            strategy_id: 策略ID（而非实例ID）
            arm: 决策臂对象
        """
        if strategy_id in self.golden_templates:
            template = self.golden_templates[strategy_id]
            template.update({
                'success_rate': arm.success_rate,
                'total_activations': arm.activation_count,
                'average_reward': sum(arm.rl_reward_history) / len(arm.rl_reward_history) if arm.rl_reward_history else 0.0,
                'last_updated': time.time(),
                'stability_score': self._calculate_stability_score(arm)
            })
            
            logger.debug(f"🏆 更新黄金模板: {strategy_id} -> 成功率:{arm.success_rate:.1%}")
    
    def _calculate_stability_score(self, arm: EnhancedDecisionArm) -> float:
        """
        计算路径的稳定性分数
        
        Args:
            arm: 决策臂对象
            
        Returns:
            稳定性分数 (0.0-1.0)
        """
        if arm.activation_count < 10:
            return 0.0
        
        # 计算成功率的方差（越小越稳定）
        recent_results = arm.recent_results[-20:] if len(arm.recent_results) >= 20 else arm.recent_results
        
        if len(recent_results) < 5:
            return 0.5  # 样本不足，给中等分数
        
        # 计算滑动窗口成功率的方差
        window_size = 5
        success_rates = []
        
        for i in range(len(recent_results) - window_size + 1):
            window = recent_results[i:i + window_size]
            window_success_rate = sum(window) / len(window)
            success_rates.append(window_success_rate)
        
        if len(success_rates) < 2:
            return 0.5
        
        # 方差越小，稳定性越高
        variance = np.var(success_rates)
        stability_score = max(0.0, 1.0 - variance * 4)  # 将方差转换为稳定性分数
        
        return stability_score
    
    def _remove_worst_golden_template(self):
        """
        移除表现最差的黄金模板
        """
        if not self.golden_templates:
            return
        
        # 按综合分数排序，移除最差的
        worst_template_id = min(self.golden_templates.keys(), 
                               key=lambda tid: self._calculate_template_quality_score(self.golden_templates[tid]))
        
        removed_template = self.golden_templates.pop(worst_template_id)
        
        logger.info(f"🗑️ 移除表现较差的黄金模板: {worst_template_id}")
        logger.info(f"   原因: 为新模板腾出空间")
        logger.info(f"   被移除模板成功率: {removed_template['success_rate']:.1%}")
    
    def _calculate_template_quality_score(self, template_data: Dict[str, any]) -> float:
        """
        计算模板的质量分数
        
        Args:
            template_data: 模板数据
            
        Returns:
            质量分数
        """
        # 综合考虑成功率、使用次数、稳定性等因素
        success_score = template_data['success_rate'] * 0.4
        usage_score = min(template_data.get('usage_count', 0) / 10, 1.0) * 0.3  # 使用次数标准化
        stability_score = template_data.get('stability_score', 0.5) * 0.2
        recency_score = self._calculate_recency_score(template_data) * 0.1
        
        return success_score + usage_score + stability_score + recency_score
    
    def _calculate_recency_score(self, template_data: Dict[str, any]) -> float:
        """
        计算模板的新近性分数
        
        Args:
            template_data: 模板数据
            
        Returns:
            新近性分数 (0.0-1.0)
        """
        current_time = time.time()
        last_updated = template_data.get('last_updated', template_data.get('created_timestamp', current_time))
        
        # 计算距离上次更新的时间（小时）
        hours_since_update = (current_time - last_updated) / 3600
        
        # 24小时内更新得满分，超过7天开始衰减
        if hours_since_update <= 24:
            return 1.0
        elif hours_since_update <= 168:  # 7天
            return 1.0 - (hours_since_update - 24) / 144  # 线性衰减
        else:
            return 0.0
    
    # ==================== 🏆 黄金模板管理接口 ====================
    
    def get_golden_templates(self) -> Dict[str, Dict[str, any]]:
        """
        获取所有黄金模板
        
        Returns:
            黄金模板字典
        """
        return self.golden_templates.copy()
    
    def get_golden_template_stats(self) -> Dict[str, any]:
        """
        获取黄金模板系统统计信息
        
        Returns:
            统计信息字典
        """
        if not self.golden_templates:
            return {
                'total_templates': 0,
                'avg_success_rate': 0.0,
                'total_usage_count': 0,
                'most_used_template': None,
                'template_usage_stats': {},
                'match_history_count': len(self.template_match_history) if hasattr(self, 'template_match_history') else 0
            }
        
        success_rates = [t['success_rate'] for t in self.golden_templates.values()]
        usage_counts = [self.template_usage_stats.get(tid, 0) for tid in self.golden_templates.keys()]
        
        most_used_template_id = max(self.template_usage_stats.keys(), 
                                   key=self.template_usage_stats.get) if self.template_usage_stats else None
        
        return {
            'total_templates': len(self.golden_templates),
            'avg_success_rate': sum(success_rates) / len(success_rates),
            'total_usage_count': sum(usage_counts),
            'most_used_template': {
                'template_id': most_used_template_id,
                'usage_count': self.template_usage_stats.get(most_used_template_id, 0),
                'template_data': self.golden_templates.get(most_used_template_id)
            } if most_used_template_id else None,
            'template_usage_stats': dict(self.template_usage_stats),
            'match_history_count': len(self.template_match_history)
        }
    
    def remove_golden_template(self, template_id: str) -> bool:
        """
        手动移除指定的黄金模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            是否成功移除
        """
        if template_id in self.golden_templates:
            removed_template = self.golden_templates.pop(template_id)
            logger.info(f"🗑️ 手动移除黄金模板: {template_id}")
            logger.info(f"   模板类型: {removed_template['path_type']}")
            return True
        else:
            logger.warning(f"⚠️ 黄金模板 {template_id} 不存在")
            return False
    
    def clear_golden_templates(self):
        """
        清空所有黄金模板
        """
        count = len(self.golden_templates)
        self.golden_templates.clear()
        self.template_usage_stats.clear()
        self.template_match_history.clear()
        
        logger.info(f"🗑️ 已清空所有黄金模板 (共 {count} 个)")
    
    def export_golden_templates(self) -> str:
        """
        导出黄金模板数据（JSON格式）
        
        Returns:
            JSON字符串
        """
        import json
        export_data = {
            'golden_templates': self.golden_templates,
            'template_usage_stats': dict(self.template_usage_stats),
            'template_match_history': self.template_match_history[-50:],  # 只导出最近50条匹配历史
            'export_timestamp': time.time(),
            'config': self.golden_template_config
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def import_golden_templates(self, json_data: str) -> bool:
        """
        导入黄金模板数据
        
        Args:
            json_data: JSON字符串
            
        Returns:
            是否成功导入
        """
        try:
            import json
            data = json.loads(json_data)
            
            # 验证数据格式
            if 'golden_templates' not in data:
                logger.error("❌ 导入数据格式错误：缺少golden_templates字段")
                return False
            
            # 导入模板
            imported_count = 0
            for template_id, template_data in data['golden_templates'].items():
                if len(self.golden_templates) < self.golden_template_config['max_golden_templates']:
                    self.golden_templates[template_id] = template_data
                    imported_count += 1
                else:
                    break
            
            # 导入使用统计
            if 'template_usage_stats' in data:
                for template_id, count in data['template_usage_stats'].items():
                    if template_id in self.golden_templates:
                        self.template_usage_stats[template_id] = count
            
            logger.info(f"✅ 成功导入 {imported_count} 个黄金模板")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导入黄金模板失败: {e}")
            return False
    
    # ==================== 🏆 黄金模板使用示例 ====================
    
    def demo_golden_template_workflow(self):
        """
        演示黄金模板系统的完整工作流程
        
        这是一个示例方法，展示了黄金模板系统的核心功能
        """
        logger.info("🏆 开始黄金模板系统演示")
        
        # 1. 显示当前状态
        stats = self.get_golden_template_stats()
        logger.info(f"当前黄金模板数量: {stats['total_templates']}")
        
        # 2. 显示配置
        config = self.golden_template_config
        logger.info(f"黄金模板配置:")
        logger.info(f"  - 成功率阈值: {config['success_rate_threshold']:.1%}")
        logger.info(f"  - 最小样本数: {config['min_samples_required']}")
        logger.info(f"  - 最大模板数: {config['max_golden_templates']}")
        
        # 3. 显示现有黄金模板
        if self.golden_templates:
            logger.info("🏆 现有黄金模板:")
            for template_id, template_data in self.golden_templates.items():
                logger.info(f"  - {template_id}: {template_data['path_type']} "
                           f"(成功率: {template_data['success_rate']:.1%}, "
                           f"使用次数: {self.template_usage_stats.get(template_id, 0)})")
        else:
            logger.info("📝 暂无黄金模板")
        
        # 4. 显示候选路径
        candidate_paths = []
        for path_id, arm in self.path_arms.items():
            if self._check_golden_criteria(arm) and path_id not in self.golden_templates:
                candidate_paths.append((path_id, arm))
        
        if candidate_paths:
            logger.info("⭐ 符合黄金模板条件的候选路径:")
            for path_id, arm in candidate_paths:
                stability = self._calculate_stability_score(arm)
                logger.info(f"  - {path_id}: {arm.option} "
                           f"(成功率: {arm.success_rate:.1%}, "
                           f"样本: {arm.activation_count}, "
                           f"稳定性: {stability:.2f})")
        else:
            logger.info("📝 暂无符合条件的候选路径")
        
        logger.info("🏆 黄金模板系统演示完成")
    
    # ==================== 💡 Aha-Moment决策支持系统 ====================
    
    def get_path_confidence(self, strategy_id: str) -> float:
        """
        获取指定策略的置信度分数
        
        Args:
            strategy_id: 策略ID（注意：这里应该传递strategy_id而不是path_id实例ID）
            
        Returns:
            置信度分数 (0.0-1.0)，1.0表示非常有信心，0.0表示完全没有信心
        """
        # 🔧 动态创建：如果策略不存在，则动态创建（置信度为最低）
        arm = self._create_strategy_arm_if_missing(strategy_id)
        
        # 如果样本数不足，置信度较低
        if arm.activation_count < 5:
            base_confidence = 0.2  # 基础信心很低
        elif arm.activation_count < 10:
            base_confidence = 0.4
        elif arm.activation_count < 20:
            base_confidence = 0.6
        else:
            base_confidence = 0.8  # 充足样本的基础信心
        
        # 基于成功率调整置信度
        success_factor = arm.success_rate
        
        # 基于稳定性调整置信度
        stability_factor = self._calculate_stability_score(arm) if arm.activation_count >= 10 else 0.5
        
        # 基于最近表现调整置信度
        recent_performance_factor = self._calculate_recent_performance_factor(arm)
        
        # 综合计算置信度
        confidence = (
            base_confidence * 0.3 +          # 样本量贡献30%
            success_factor * 0.4 +           # 成功率贡献40%
            stability_factor * 0.2 +         # 稳定性贡献20%
            recent_performance_factor * 0.1  # 最近表现贡献10%
        )
        
        return min(max(confidence, 0.0), 1.0)  # 确保在[0,1]范围内
    
    def _calculate_recent_performance_factor(self, arm: EnhancedDecisionArm) -> float:
        """
        计算最近表现因子
        
        Args:
            arm: 决策臂对象
            
        Returns:
            最近表现因子 (0.0-1.0)
        """
        if not arm.recent_results or len(arm.recent_results) < 3:
            return 0.5  # 默认中等
        
        # 计算最近5次的成功率
        recent_window = arm.recent_results[-5:]
        recent_success_rate = sum(recent_window) / len(recent_window)
        
        return recent_success_rate
    
    def get_all_paths_confidence(self) -> Dict[str, float]:
        """
        获取所有路径的置信度
        
        Returns:
            路径ID到置信度的映射
        """
        confidence_map = {}
        for path_id in self.path_arms.keys():
            confidence_map[path_id] = self.get_path_confidence(path_id)
        
        return confidence_map
    
    def check_low_confidence_scenario(self, threshold: float = 0.3) -> bool:
        """
        检查是否处于低置信度场景（所有路径表现都很差）
        
        Args:
            threshold: 置信度阈值，低于此值认为是低置信度
            
        Returns:
            是否所有路径都处于低置信度状态
        """
        if not self.path_arms:
            return True  # 没有路径数据，认为是低置信度场景
        
        confidence_scores = self.get_all_paths_confidence()
        
        if not confidence_scores:
            return True
        
        # 检查是否所有路径的置信度都低于阈值
        max_confidence = max(confidence_scores.values())
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
        
        logger.debug(f"💡 置信度检查: 最高置信度={max_confidence:.3f}, 平均置信度={avg_confidence:.3f}, 阈值={threshold}")
        
        # 如果最高置信度都低于阈值，则认为需要绕道思考
        return max_confidence < threshold
    
    def get_confidence_analysis(self) -> Dict[str, any]:
        """
        获取置信度分析报告
        
        Returns:
            置信度分析数据
        """
        confidence_scores = self.get_all_paths_confidence()
        
        if not confidence_scores:
            return {
                'total_paths': 0,
                'max_confidence': 0.0,
                'min_confidence': 0.0,
                'avg_confidence': 0.0,
                'low_confidence_paths': 0,
                'high_confidence_paths': 0,
                'confidence_distribution': {}
            }
        
        values = list(confidence_scores.values())
        low_confidence_count = sum(1 for conf in values if conf < 0.3)
        high_confidence_count = sum(1 for conf in values if conf > 0.7)
        
        # 置信度分布统计
        distribution = {
            'very_low (0.0-0.2)': sum(1 for conf in values if 0.0 <= conf < 0.2),
            'low (0.2-0.4)': sum(1 for conf in values if 0.2 <= conf < 0.4),
            'medium (0.4-0.6)': sum(1 for conf in values if 0.4 <= conf < 0.6),
            'high (0.6-0.8)': sum(1 for conf in values if 0.6 <= conf < 0.8),
            'very_high (0.8-1.0)': sum(1 for conf in values if 0.8 <= conf <= 1.0)
        }
        
        return {
            'total_paths': len(confidence_scores),
            'max_confidence': max(values),
            'min_confidence': min(values),
            'avg_confidence': sum(values) / len(values),
            'low_confidence_paths': low_confidence_count,
            'high_confidence_paths': high_confidence_count,
            'confidence_distribution': distribution,
            'detailed_scores': confidence_scores
        }
    
    # ==================== 🔧 辅助计算方法 ====================
    
    def _calculate_recent_trend(self, arm: EnhancedDecisionArm) -> str:
        """
        计算路径的最近性能趋势
        
        Args:
            arm: 决策臂对象
            
        Returns:
            趋势字符串: 'improving', 'declining', 'stable', 'insufficient_data'
        """
        if len(arm.recent_results) < 4:
            return 'insufficient_data'
        
        # 取最近的结果，分为两半进行比较
        recent = arm.recent_results[-10:] if len(arm.recent_results) >= 10 else arm.recent_results
        mid_point = len(recent) // 2
        
        if mid_point < 2:
            return 'insufficient_data'
        
        # 计算前半段和后半段的成功率
        earlier_half = recent[:mid_point]
        later_half = recent[mid_point:]
        
        earlier_rate = sum(earlier_half) / len(earlier_half)
        later_rate = sum(later_half) / len(later_half)
        
        # 判断趋势
        if later_rate > earlier_rate + 0.1:  # 10%的改善视为improving
            return 'improving'
        elif later_rate < earlier_rate - 0.1:  # 10%的下降视为declining
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_consecutive_successes(self, arm: EnhancedDecisionArm) -> int:
        """
        计算连续成功次数
        
        Args:
            arm: 决策臂对象
            
        Returns:
            连续成功次数
        """
        if not arm.recent_results:
            return 0
        
        consecutive_count = 0
        # 从最近的结果开始往前数
        for result in reversed(arm.recent_results):
            if result:  # 如果是成功
                consecutive_count += 1
            else:  # 如果失败了，就停止计数
                break
        
        return consecutive_count
    
    # ==================== 🎯 根源修复完成：移除复杂解析逻辑 ====================
    # 注意：_resolve_strategy_id 方法已移除，因为数据源头现在直接提供正确的策略ID
    
    def _infer_path_type_from_strategy_id(self, strategy_id: str) -> str:
        """
        从策略ID推断路径类型
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            推断的路径类型
        """
        # 策略ID到路径类型的映射表
        strategy_to_type_mapping = {
            'systematic_analytical': '系统分析型',
            'creative_innovative': '创新突破型',
            'critical_questioning': '批判质疑型',
            'practical_pragmatic': '实用务实型',
            'holistic_comprehensive': '整体综合型',
            'exploratory_investigative': '探索调研型',
            'collaborative_consultative': '协作咨询型',
            'adaptive_flexible': '适应灵活型',
            
            # 兼容性映射（中文路径类型）
            '系统分析': '系统分析型',
            '创新突破': '创新突破型',
            '批判质疑': '批判质疑型',
            '实用务实': '实用务实型',
            '整体综合': '整体综合型',
            '探索调研': '探索调研型',
            '协作咨询': '协作咨询型',
            '适应灵活': '适应灵活型'
        }
        
        # 直接匹配
        if strategy_id in strategy_to_type_mapping:
            return strategy_to_type_mapping[strategy_id]
        
        # 模糊匹配
        strategy_lower = strategy_id.lower()
        for key, value in strategy_to_type_mapping.items():
            if key.lower() in strategy_lower or strategy_lower in key.lower():
                logger.debug(f"🔍 模糊匹配策略类型: {strategy_id} -> {value}")
                return value
        
        # 基于关键词推断
        if 'systematic' in strategy_lower or 'analytical' in strategy_lower or '系统' in strategy_id:
            return '系统分析型'
        elif 'creative' in strategy_lower or 'innovative' in strategy_lower or '创新' in strategy_id:
            return '创新突破型'
        elif 'critical' in strategy_lower or 'questioning' in strategy_lower or '批判' in strategy_id:
            return '批判质疑型'
        elif 'practical' in strategy_lower or 'pragmatic' in strategy_lower or '实用' in strategy_id:
            return '实用务实型'
        elif 'holistic' in strategy_lower or 'comprehensive' in strategy_lower or '整体' in strategy_id:
            return '整体综合型'
        elif 'exploratory' in strategy_lower or 'investigative' in strategy_lower or '探索' in strategy_id:
            return '探索调研型'
        elif 'collaborative' in strategy_lower or 'consultative' in strategy_lower or '协作' in strategy_id:
            return '协作咨询型'
        elif 'adaptive' in strategy_lower or 'flexible' in strategy_lower or '适应' in strategy_id:
            return '适应灵活型'
        
        # 默认返回
        logger.debug(f"⚠️ 无法推断路径类型，使用默认: {strategy_id} -> 通用方法型")
        return '通用方法型'
