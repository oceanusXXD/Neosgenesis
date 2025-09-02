#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis智能规划器 - 基于Meta MAB的高级规划系统
将MainController的五阶段智能决策逻辑重构为符合框架标准的规划器组件

核心特性:
1. 五阶段智能验证-学习决策流程
2. 依赖注入式组件协作
3. 标准Plan输出格式
4. 智能决策结果翻译
"""

import time
import logging
from typing import Dict, List, Optional, Any

# 导入框架核心
try:
    from ..abstractions import BasePlanner
    from ..data_structures import Plan, Action
except ImportError:
    from neogenesis_system.abstractions import BasePlanner
    from neogenesis_system.data_structures import Plan, Action

# 导入Meta MAB组件
from ..meta_mab.reasoner import PriorReasoner
from ..meta_mab.path_generator import PathGenerator
from ..meta_mab.mab_converger import MABConverger
from ..meta_mab.data_structures import DecisionResult, ReasoningPath
from ..meta_mab.state_manager import StateManager

# 导入工具系统
from ..meta_mab.utils.tool_abstraction import (
    ToolRegistry, 
    global_tool_registry,
    execute_tool,
    ToolResult
)

logger = logging.getLogger(__name__)


class NeogenesisPlanner(BasePlanner):
    """
    Neogenesis智能规划器
    
    将MainController的五阶段决策逻辑重构为标准规划器组件：
    1. 思维种子生成 (PriorReasoner)
    2. 种子验证检查 (idea_verification)
    3. 思维路径生成 (PathGenerator)
    4. 路径验证学习 (核心创新)
    5. 智能最终决策 (升级版MAB)
    """
    
    def __init__(self, 
                 prior_reasoner: PriorReasoner,
                 path_generator: PathGenerator,
                 mab_converger: MABConverger,
                 tool_registry: Optional[ToolRegistry] = None,
                 state_manager: Optional[StateManager] = None,
                 config: Optional[Dict] = None):
        """
        依赖注入式初始化
        
        Args:
            prior_reasoner: 先验推理器实例
            path_generator: 路径生成器实例  
            mab_converger: MAB收敛器实例
            tool_registry: 工具注册表（可选，默认使用全局注册表）
            state_manager: 状态管理器（可选）
            config: 配置字典（可选）
        """
        super().__init__(
            name="NeogenesisPlanner",
            description="基于Meta MAB的五阶段智能规划器"
        )
        
        # 依赖注入的核心组件
        self.prior_reasoner = prior_reasoner
        self.path_generator = path_generator
        self.mab_converger = mab_converger
        
        # 可选组件
        self.tool_registry = tool_registry or global_tool_registry
        self.state_manager = state_manager
        self.config = config or {}
        
        # 内部状态
        self.total_rounds = 0
        self.decision_history = []
        self.performance_stats = {
            'total_decisions': 0,
            'avg_decision_time': 0.0,
            'component_performance': {
                'prior_reasoner': {'calls': 0, 'avg_time': 0.0},
                'path_generator': {'calls': 0, 'avg_time': 0.0},
                'mab_converger': {'calls': 0, 'avg_time': 0.0}
            }
        }
        
        logger.info(f"🧠 NeogenesisPlanner 初始化完成")
        logger.info(f"   组件: PriorReasoner, PathGenerator, MABConverger")
        logger.info(f"   工具注册表: {len(self.tool_registry.tools) if self.tool_registry else 0} 个工具")
    
    def create_plan(self, query: str, memory: Any, context: Optional[Dict[str, Any]] = None) -> Plan:
        """
        创建执行计划 - 实现BasePlanner接口
        
        这是规划器的主要入口点，调用内部的五阶段决策逻辑，
        然后将结果翻译为标准的Plan格式。
        
        Args:
            query: 用户查询
            memory: Agent的记忆对象
            context: 可选的执行上下文
            
        Returns:
            Plan: 标准格式的执行计划
        """
        logger.info(f"🎯 开始创建计划: {query[:50]}...")
        start_time = time.time()
        
        try:
            # 🚀 调用内部五阶段决策逻辑
            decision_result = self._make_decision_logic(
                user_query=query,
                deepseek_confidence=context.get('confidence', 0.5) if context else 0.5,
                execution_context=context
            )
            
            # 🔄 将决策结果翻译为标准Plan格式
            plan = self._convert_decision_to_plan(decision_result, query)
            
            # 📊 更新性能统计
            execution_time = time.time() - start_time
            self._update_planner_stats(True, execution_time)
            
            logger.info(f"✅ 计划创建完成: {plan.action_count} 个行动, 耗时 {execution_time:.3f}s")
            return plan
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_planner_stats(False, execution_time)
            
            logger.error(f"❌ 计划创建失败: {e}")
            
            # 返回错误回退计划
            return Plan(
                thought=f"规划过程中出现错误: {str(e)}",
                final_answer=f"抱歉，我在处理您的请求时遇到了问题: {str(e)}"
            )
    
    def validate_plan(self, plan: Plan) -> bool:
        """
        验证计划的有效性
        
        Args:
            plan: 要验证的计划
            
        Returns:
            bool: 计划是否有效
        """
        try:
            # 检查基本结构
            if not plan.thought:
                return False
            
            # 直接回答模式
            if plan.is_direct_answer:
                return plan.final_answer is not None and len(plan.final_answer.strip()) > 0
            
            # 工具执行模式
            if not plan.actions:
                return False
            
            # 验证所有行动
            for action in plan.actions:
                if not action.tool_name or not isinstance(action.tool_input, dict):
                    return False
                
                # 检查工具是否存在
                if self.tool_registry and not self.tool_registry.has_tool(action.tool_name):
                    logger.warning(f"⚠️ 工具 '{action.tool_name}' 未在注册表中找到")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 计划验证失败: {e}")
            return False
    
    def _make_decision_logic(self, user_query: str, deepseek_confidence: float = 0.5, 
                           execution_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        五阶段智能验证-学习决策逻辑（从MainController迁移）
        
        这是原MainController.make_decision方法的核心逻辑，
        几乎原封不动地保留了所有功能。
        """
        start_time = time.time()
        self.total_rounds += 1
        
        logger.info(f"🚀 开始第 {self.total_rounds} 轮五阶段智能验证-学习决策")
        logger.info(f"   查询: {user_query[:50]}...")
        logger.info(f"   置信度: {deepseek_confidence:.2f}")
        
        try:
            # 🧠 阶段一：先验推理 - 生成思维种子
            reasoner_start = time.time()
            thinking_seed = self.prior_reasoner.get_thinking_seed(user_query, execution_context)
            
            # 兼容性：获取旧格式数据
            task_confidence = self.prior_reasoner.assess_task_confidence(user_query, execution_context)
            complexity_info = self.prior_reasoner.analyze_task_complexity(user_query)
            
            reasoner_time = time.time() - reasoner_start
            self._update_component_performance('prior_reasoner', reasoner_time)
            
            logger.info(f"🧠 阶段一完成: 思维种子生成 (长度: {len(thinking_seed)} 字符)")
            
            # 🔍 阶段二：验证思维种子
            seed_verification_start = time.time()
            seed_verification_result = self._verify_idea_feasibility(
                idea_text=thinking_seed,
                context={
                    'stage': 'thinking_seed',
                    'domain': 'strategic_planning',
                    'query': user_query,
                    **(execution_context if execution_context else {})
                }
            )
            seed_verification_time = time.time() - seed_verification_start
            
            # 分析种子验证结果
            seed_feasibility = seed_verification_result.get('feasibility_analysis', {}).get('feasibility_score', 0.5)
            seed_reward = seed_verification_result.get('reward_score', 0.0)
            
            logger.info(f"🔍 阶段二完成: 思维种子验证 (可行性: {seed_feasibility:.2f}, 奖励: {seed_reward:+.3f})")
            
            # 🛤️ 阶段三：路径生成
            generator_start = time.time()
            all_reasoning_paths = self.path_generator.generate_paths(
                thinking_seed=thinking_seed, 
                task=user_query,
                max_paths=6  # 限制路径数量以提高性能
            )
            generator_time = time.time() - generator_start
            self._update_component_performance('path_generator', generator_time)
            
            logger.info(f"🛤️ 阶段三完成: 生成了 {len(all_reasoning_paths)} 条思维路径")
            
            # 🚀 阶段四：路径验证学习
            path_verification_start = time.time()
            verified_paths = []
            all_infeasible = True
            
            logger.info(f"🔬 阶段四开始: 验证思维路径")
            
            # 简化版路径验证（避免复杂的并行处理）
            for i, path in enumerate(all_reasoning_paths, 1):
                logger.debug(f"🔬 验证路径 {i}/{len(all_reasoning_paths)}: {path.path_type}")
                
                # 验证单个路径
                path_verification_result = self._verify_idea_feasibility(
                    idea_text=f"{path.path_type}: {path.description}",
                    context={
                        'stage': 'reasoning_path',
                        'path_id': path.path_id,
                        'path_type': path.path_type,
                        'query': user_query,
                        **(execution_context if execution_context else {})
                    }
                )
                
                # 提取验证结果
                path_feasibility = path_verification_result.get('feasibility_analysis', {}).get('feasibility_score', 0.5)
                path_reward = path_verification_result.get('reward_score', 0.0)
                verification_success = not path_verification_result.get('fallback', False)
                
                # 💡 即时学习：立即将验证结果反馈给MAB系统
                if verification_success and path_feasibility > 0.3:
                    # 可行的路径 - 正面学习信号
                    self.mab_converger.update_path_performance(
                        path_id=path.strategy_id,
                        success=True,
                        reward=path_reward
                    )
                    all_infeasible = False
                    logger.debug(f"✅ 路径 {path.path_type} 验证通过: 可行性={path_feasibility:.2f}")
                else:
                    # 不可行的路径 - 负面学习信号
                    self.mab_converger.update_path_performance(
                        path_id=path.strategy_id,
                        success=False,
                        reward=path_reward
                    )
                    logger.debug(f"❌ 路径 {path.path_type} 验证失败: 可行性={path_feasibility:.2f}")
                
                # 记录验证结果
                verified_paths.append({
                    'path': path,
                    'verification_result': path_verification_result,
                    'feasibility_score': path_feasibility,
                    'reward_score': path_reward,
                    'is_feasible': path_feasibility > 0.3
                })
            
            path_verification_time = time.time() - path_verification_start
            feasible_count = sum(1 for vp in verified_paths if vp['is_feasible'])
            
            logger.info(f"🔬 阶段四完成: {feasible_count}/{len(all_reasoning_paths)} 条路径可行")
            
            # 🎯 阶段五：智能最终决策
            final_decision_start = time.time()
            
            if all_infeasible:
                # 🚨 所有路径都不可行 - 触发智能绕道思考
                logger.warning("🚨 所有思维路径都被验证为不可行，触发智能绕道思考")
                chosen_path = self._execute_intelligent_detour_thinking(
                    user_query, thinking_seed, all_reasoning_paths
                )
                selection_algorithm = 'intelligent_detour'
            else:
                # ✅ 至少有可行路径 - 使用增强的MAB选择
                logger.info("✅ 发现可行路径，使用验证增强的MAB决策")
                chosen_path = self.mab_converger.select_best_path(all_reasoning_paths)
                selection_algorithm = 'verification_enhanced_mab'
            
            final_decision_time = time.time() - final_decision_start
            total_mab_time = path_verification_time + final_decision_time
            self._update_component_performance('mab_converger', total_mab_time)
            
            # 计算总体决策时间
            total_decision_time = time.time() - start_time
            
            # 构建决策结果
            decision_result = {
                # 基本信息
                'timestamp': time.time(),
                'round_number': self.total_rounds,
                'user_query': user_query,
                'deepseek_confidence': deepseek_confidence,
                'execution_context': execution_context,
                
                # 五阶段决策结果
                'thinking_seed': thinking_seed,
                'seed_verification': seed_verification_result,
                'chosen_path': chosen_path,
                'available_paths': all_reasoning_paths,
                'verified_paths': verified_paths,
                
                # 决策元信息
                'reasoning': f"五阶段智能验证-学习决策: {chosen_path.path_type} - {chosen_path.description}",
                'path_count': len(all_reasoning_paths),
                'feasible_path_count': feasible_count,
                'selection_algorithm': selection_algorithm,
                'architecture_version': '5-stage-verification',
                'verification_enabled': True,
                'instant_learning_enabled': True,
                
                # 验证统计
                'verification_stats': {
                    'seed_feasibility': seed_feasibility,
                    'seed_reward': seed_reward,
                    'paths_verified': len(verified_paths),
                    'feasible_paths': feasible_count,
                    'infeasible_paths': len(verified_paths) - feasible_count,
                    'all_paths_infeasible': all_infeasible,
                    'average_path_feasibility': sum(vp['feasibility_score'] for vp in verified_paths) / len(verified_paths) if verified_paths else 0.0,
                    'total_verification_time': seed_verification_time + path_verification_time
                },
                
                # 性能指标
                'performance_metrics': {
                    'total_time': total_decision_time,
                    'stage1_reasoner_time': reasoner_time,
                    'stage2_seed_verification_time': seed_verification_time,
                    'stage3_generator_time': generator_time,
                    'stage4_path_verification_time': path_verification_time,
                    'stage5_final_decision_time': final_decision_time,
                }
            }
            
            # 记录决策历史
            self.decision_history.append(decision_result)
            
            # 限制历史记录长度
            max_history = 100  # 简化的限制
            if len(self.decision_history) > max_history:
                self.decision_history = self.decision_history[-max_history//2:]
            
            logger.info(f"🎉 五阶段智能验证-学习决策完成:")
            logger.info(f"   🎯 最终选择: {chosen_path.path_type}")
            logger.info(f"   ⏱️ 总耗时: {total_decision_time:.3f}s")
            
            return decision_result
            
        except Exception as e:
            logger.error(f"❌ 决策过程失败: {e}")
            # 返回错误决策结果
            return self._create_error_decision_result(user_query, str(e), time.time() - start_time)
    
    def _convert_decision_to_plan(self, decision_result: Dict[str, Any], query: str) -> Plan:
        """
        翻译层：将Neogenesis决策结果转换为标准Plan格式
        
        这是适配新架构最关键的一步，将复杂的决策结果翻译成
        整个Agent框架都能理解的标准化Plan对象。
        
        Args:
            decision_result: 五阶段决策的完整结果
            query: 原始用户查询
            
        Returns:
            Plan: 标准格式的执行计划
        """
        try:
            chosen_path = decision_result.get('chosen_path')
            thinking_seed = decision_result.get('thinking_seed', '')
            reasoning = decision_result.get('reasoning', '')
            
            if not chosen_path:
                # 没有选中路径，返回直接回答
                return Plan(
                    thought="决策过程未能选择有效路径",
                    final_answer="抱歉，我无法为您的查询制定合适的执行计划。"
                )
            
            # 构建思考过程
            thought_parts = [
                f"基于五阶段智能决策，我选择了'{chosen_path.path_type}'策略",
                f"思维种子: {thinking_seed[:100]}..." if len(thinking_seed) > 100 else f"思维种子: {thinking_seed}",
                f"选择理由: {chosen_path.description}"
            ]
            thought = "\n".join(thought_parts)
            
            # 🔄 智能路径分析 - 判断需要什么行动
            actions = self._analyze_path_actions(chosen_path, query, decision_result)
            
            if not actions:
                # 如果没有生成行动，返回直接回答
                direct_answer = self._generate_direct_answer(chosen_path, query, thinking_seed)
                return Plan(
                    thought=thought,
                    final_answer=direct_answer
                )
            
            # 返回包含行动的计划
            plan = Plan(
                thought=thought,
                actions=actions
            )
            
            # 添加元数据
            plan.metadata.update({
                'neogenesis_decision': decision_result,
                'chosen_path_type': chosen_path.path_type,
                'path_id': chosen_path.path_id,
                'verification_stats': decision_result.get('verification_stats', {}),
                'performance_metrics': decision_result.get('performance_metrics', {})
            })
            
            logger.info(f"🔄 决策翻译完成: {len(actions)} 个行动，策略 '{chosen_path.path_type}'")
            return plan
            
        except Exception as e:
            logger.error(f"❌ 决策翻译失败: {e}")
            return Plan(
                thought=f"翻译决策结果时出现错误: {str(e)}",
                final_answer="抱歉，我在处理您的查询时遇到了技术问题。"
            )
    
    def _analyze_path_actions(self, chosen_path: ReasoningPath, query: str, 
                            decision_result: Dict[str, Any]) -> List[Action]:
        """
        智能路径分析 - 根据选中的思维路径生成具体行动
        
        这个方法分析chosen_path的特征，判断应该使用什么工具。
        """
        actions = []
        path_type = chosen_path.path_type.lower()
        path_description = chosen_path.description.lower()
        
        # 🔍 搜索类路径识别
        search_keywords = ['搜索', 'search', '查找', '信息收集', '调研', '探索', '资料']
        if any(keyword in path_type or keyword in path_description for keyword in search_keywords):
            # 生成搜索行动
            search_query = self._extract_search_query(query, chosen_path)
            actions.append(Action(
                tool_name="web_search",
                tool_input={"query": search_query}
            ))
            logger.debug(f"🔍 识别为搜索路径: {search_query}")
        
        # 🔬 验证类路径识别
        verification_keywords = ['验证', 'verify', '确认', '检查', '核实', '审查']
        if any(keyword in path_type or keyword in path_description for keyword in verification_keywords):
            # 生成验证行动
            idea_to_verify = self._extract_verification_idea(query, chosen_path)
            actions.append(Action(
                tool_name="idea_verification",
                tool_input={"idea_text": idea_to_verify}
            ))
            logger.debug(f"🔬 识别为验证路径: {idea_to_verify}")
        
        # 📊 分析类路径识别
        analysis_keywords = ['分析', 'analysis', '评估', '比较', '总结', '归纳']
        if any(keyword in path_type or keyword in path_description for keyword in analysis_keywords):
            # 对于分析类任务，可能需要先搜索信息再分析
            if not actions:  # 如果还没有其他行动
                search_query = f"关于 {query} 的详细信息和分析"
                actions.append(Action(
                    tool_name="web_search",
                    tool_input={"query": search_query}
                ))
                logger.debug(f"📊 识别为分析路径，先搜索信息: {search_query}")
        
        # 🤔 创意类路径识别
        creative_keywords = ['创意', 'creative', '创新', '头脑风暴', '想象', '设计']
        if any(keyword in path_type or keyword in path_description for keyword in creative_keywords):
            # 创意类任务通常不需要工具，直接由LLM处理
            logger.debug(f"🤔 识别为创意路径，无需工具支持")
        
        # 🔧 如果没有识别出特定类型，根据查询内容进行通用判断
        if not actions:
            actions.extend(self._generate_fallback_actions(query, chosen_path))
        
        return actions
    
    def _extract_search_query(self, original_query: str, path: ReasoningPath) -> str:
        """从原始查询和路径信息中提取搜索查询"""
        # 简化版实现，根据路径描述优化搜索查询
        if "具体" in path.description or "详细" in path.description:
            return f"{original_query} 详细信息"
        elif "最新" in path.description or "recent" in path.description.lower():
            return f"{original_query} 最新发展"
        elif "对比" in path.description or "比较" in path.description:
            return f"{original_query} 对比分析"
        else:
            return original_query
    
    def _extract_verification_idea(self, original_query: str, path: ReasoningPath) -> str:
        """从查询和路径信息中提取需要验证的想法"""
        # 简化版实现
        return f"基于查询'{original_query}'的想法: {path.description}"
    
    def _generate_fallback_actions(self, query: str, path: ReasoningPath) -> List[Action]:
        """生成回退行动（当无法识别特定路径类型时）"""
        actions = []
        
        # 检查查询中是否包含明显的搜索意图
        search_indicators = ['什么是', '如何', '为什么', '哪里', '谁', '何时', '最新', '信息', '资料']
        if any(indicator in query for indicator in search_indicators):
            actions.append(Action(
                tool_name="web_search",
                tool_input={"query": query}
            ))
            logger.debug(f"🔧 回退策略: 识别为搜索查询")
        
        return actions
    
    def _generate_direct_answer(self, path: ReasoningPath, query: str, thinking_seed: str) -> str:
        """生成直接回答（当不需要工具时）"""
        return (
            f"基于'{path.path_type}'思维路径的分析，"
            f"我认为对于您的查询'{query}'，{path.description}。"
            f"这是基于思维种子的初步回应: {thinking_seed[:200]}..."
        )
    
    def _verify_idea_feasibility(self, idea_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证想法可行性（简化版实现）
        
        这里调用工具系统中的idea_verification工具
        """
        try:
            if self.tool_registry and self.tool_registry.has_tool("idea_verification"):
                result = execute_tool("idea_verification", {"idea_text": idea_text})
                if result.success:
                    return result.data
            
            # 回退实现
            return {
                'feasibility_analysis': {'feasibility_score': 0.7},
                'reward_score': 0.1,
                'fallback': True
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 想法验证失败: {e}")
            return {
                'feasibility_analysis': {'feasibility_score': 0.5},
                'reward_score': 0.0,
                'fallback': True
            }
    
    def _execute_intelligent_detour_thinking(self, user_query: str, thinking_seed: str, 
                                           all_paths: List[ReasoningPath]) -> ReasoningPath:
        """
        执行智能绕道思考（简化版实现）
        
        当所有路径都不可行时，创建一个备选路径
        """
        logger.info("🚀 执行智能绕道思考")
        
        # 创建一个创新路径作为绕道方案
        detour_path = ReasoningPath(
            path_id=f"detour_{int(time.time())}",
            path_type="创新绕道思考",
            description=f"针对'{user_query}'的创新解决方案，突破常规思维限制",
            prompt_template="采用创新思维，寻找独特的解决角度",
            strategy_id="creative_detour",
            instance_id=f"creative_detour_{int(time.time())}"
        )
        
        return detour_path
    
    def _update_component_performance(self, component_name: str, execution_time: float):
        """更新组件性能统计"""
        if component_name in self.performance_stats['component_performance']:
            component_stats = self.performance_stats['component_performance'][component_name]
            component_stats['calls'] += 1
            
            # 计算移动平均
            current_avg = component_stats['avg_time']
            call_count = component_stats['calls']
            component_stats['avg_time'] = (current_avg * (call_count - 1) + execution_time) / call_count
    
    def _update_planner_stats(self, success: bool, execution_time: float):
        """更新规划器统计"""
        self.performance_stats['total_decisions'] += 1
        
        # 更新平均决策时间
        current_avg = self.performance_stats['avg_decision_time']
        total_decisions = self.performance_stats['total_decisions']
        
        if total_decisions == 1:
            self.performance_stats['avg_decision_time'] = execution_time
        else:
            self.performance_stats['avg_decision_time'] = (
                current_avg * (total_decisions - 1) + execution_time
            ) / total_decisions
    
    def _create_error_decision_result(self, user_query: str, error_msg: str, execution_time: float) -> Dict[str, Any]:
        """创建错误决策结果"""
        return {
            'timestamp': time.time(),
            'round_number': self.total_rounds,
            'user_query': user_query,
            'chosen_path': None,
            'available_paths': [],
            'verified_paths': [],
            'reasoning': f"决策失败: {error_msg}",
            'fallback_used': True,
            'error': error_msg,
            'performance_metrics': {
                'total_time': execution_time,
                'error': True
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取规划器统计信息"""
        return {
            'name': self.name,
            'total_rounds': self.total_rounds,
            'performance_stats': self.performance_stats.copy(),
            'decision_history_length': len(self.decision_history),
            'components': {
                'prior_reasoner': type(self.prior_reasoner).__name__,
                'path_generator': type(self.path_generator).__name__,
                'mab_converger': type(self.mab_converger).__name__
            }
        }
