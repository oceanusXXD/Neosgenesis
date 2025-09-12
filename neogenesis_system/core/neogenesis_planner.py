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
    from ..shared.data_structures import Plan, Action
except ImportError:
    from neogenesis_system.abstractions import BasePlanner
    from neogenesis_system.shared.data_structures import Plan, Action

# 导入Meta MAB组件
from ..cognitive_engine.reasoner import PriorReasoner
from ..cognitive_engine.path_generator import PathGenerator
from ..cognitive_engine.mab_converger import MABConverger
from ..cognitive_engine.data_structures import DecisionResult, ReasoningPath
from ..shared.state_manager import StateManager

# 导入工具系统
from ..tools.tool_abstraction import (
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
                 config: Optional[Dict] = None,
                 cognitive_scheduler=None):
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
        
        # 🧠 认知调度器集成
        self.cognitive_scheduler = cognitive_scheduler
        
        # 🔧 如果认知调度器存在，尝试注入回溯引擎依赖
        if self.cognitive_scheduler:
            self._inject_cognitive_dependencies()
        
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
        try:
            tool_count = len(self.tool_registry.tools) if hasattr(self.tool_registry, 'tools') else len(getattr(self.tool_registry, '_tools', {}))
            logger.info(f"   工具注册表: {tool_count} 个工具")
        except:
            logger.info(f"   工具注册表: 已初始化")
    
    def _inject_cognitive_dependencies(self):
        """向认知调度器注入核心依赖组件"""
        try:
            if (self.cognitive_scheduler and 
                hasattr(self.cognitive_scheduler, 'update_retrospection_dependencies')):
                
                success = self.cognitive_scheduler.update_retrospection_dependencies(
                    path_generator=self.path_generator,
                    mab_converger=self.mab_converger
                )
                
                if success:
                    logger.info("✅ 回溯引擎依赖组件已成功注入")
                else:
                    logger.warning("⚠️ 回溯引擎依赖组件注入失败")
            
        except Exception as e:
            logger.warning(f"⚠️ 认知调度器依赖注入异常: {e}")
    
    def set_cognitive_scheduler(self, cognitive_scheduler):
        """设置认知调度器并自动注入依赖组件"""
        self.cognitive_scheduler = cognitive_scheduler
        if cognitive_scheduler:
            self._inject_cognitive_dependencies()
            logger.info("🧠 认知调度器已设置并完成依赖注入")
    
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
        
        # 🧠 通知认知调度器Agent正在活跃工作
        if self.cognitive_scheduler:
            self.cognitive_scheduler.notify_activity("task_planning", {
                "query": query[:100],
                "timestamp": start_time,
                "source": "create_plan"
            })
        
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
        
        🔥 核心改进：引入LLM作为最终解释和生成器
        - 智能判断是否需要工具
        - 自然语言生成，避免生硬回答
        - 上下文感知的决策制定
        
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
            
            # 🧠 核心改进：使用LLM作为最终决策官
            llm_decision = self._llm_final_decision_maker(chosen_path, query, thinking_seed, decision_result)
            
            if llm_decision.get('needs_tools', False):
                # LLM判断需要工具，使用LLM推荐的行动
                actions = llm_decision.get('actions', [])
                if not actions:
                    # 如果LLM没有提供具体行动，回退到规则分析
                    actions = self._analyze_path_actions(chosen_path, query, decision_result)
                
                if actions:
                    plan = Plan(
                        thought=llm_decision.get('explanation', thought),
                        actions=actions
                    )
                else:
                    # 即使LLM说需要工具，但没有找到合适工具，返回直接回答
                    plan = Plan(
                        thought=llm_decision.get('explanation', thought),
                        final_answer=llm_decision.get('direct_answer', "抱歉，我无法找到合适的工具来处理您的请求。")
                    )
            else:
                # LLM判断不需要工具，直接返回智能生成的回答
                plan = Plan(
                    thought=llm_decision.get('explanation', thought),
                    final_answer=llm_decision.get('direct_answer')
                )
            
            # 添加元数据
            plan.metadata.update({
                'neogenesis_decision': decision_result,
                'chosen_path_type': chosen_path.path_type,
                'path_id': chosen_path.path_id,
                'verification_stats': decision_result.get('verification_stats', {}),
                'performance_metrics': decision_result.get('performance_metrics', {}),
                'llm_decision': llm_decision,
                'decision_method': 'llm_final_decision_maker'
            })
            
            action_count = len(plan.actions) if plan.actions else 0
            answer_mode = "工具执行" if plan.actions else "直接回答"
            logger.info(f"🔄 LLM驱动决策完成: {answer_mode}, {action_count} 个行动，策略 '{chosen_path.path_type}'")
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
    
    def _llm_final_decision_maker(self, chosen_path: ReasoningPath, query: str, 
                                 thinking_seed: str, decision_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        🧠 LLM作为最终解释和生成器
        
        让LLM扮演"最终决策官"的角色，智能判断是否需要工具以及生成自然回答。
        这是解决路径解释错误和回答生硬问题的核心方法。
        
        Args:
            chosen_path: 选中的思维路径
            query: 用户原始查询
            thinking_seed: 思维种子
            decision_result: 完整决策结果
            
        Returns:
            Dict[str, Any]: LLM的决策结果，包含：
            - needs_tools: bool - 是否需要工具
            - actions: List[Action] - 推荐的行动（如果需要工具）
            - direct_answer: str - 直接回答（如果不需要工具）
            - explanation: str - 决策解释
        """
        try:
            logger.info(f"🧠 LLM最终决策官开始工作: 查询='{query[:50]}...', 路径='{chosen_path.path_type}'")
            
            # 🔍 收集可用工具信息
            available_tools = self._get_available_tools_info()
            
            # 🧠 构建LLM决策提示
            decision_prompt = self._build_llm_decision_prompt(
                user_query=query,
                chosen_path=chosen_path,
                thinking_seed=thinking_seed,
                available_tools=available_tools,
                decision_context=decision_result
            )
            
            # 🚀 调用LLM进行智能决策
            llm_success = False
            
            # 多种方式尝试LLM调用
            if hasattr(self, 'prior_reasoner') and self.prior_reasoner and hasattr(self.prior_reasoner, 'llm_manager'):
                try:
                    logger.info(f"🔍 尝试通过prior_reasoner调用LLM...")
                    llm_response = self.prior_reasoner.llm_manager.generate_response(
                        query=decision_prompt,
                        provider="deepseek",
                        temperature=0.3,  # 较低温度确保一致性
                        max_tokens=1000
                    )
                    
                    if llm_response and llm_response.strip():
                        # 🔍 解析LLM响应
                        parsed_decision = self._parse_llm_decision_response(llm_response, chosen_path, query)
                        logger.info(f"✅ LLM决策成功: 需要工具={parsed_decision.get('needs_tools')}")
                        return parsed_decision
                    else:
                        logger.warning("⚠️ LLM返回空响应")
                        
                except Exception as e:
                    logger.error(f"❌ prior_reasoner LLM调用失败: {e}")
            else:
                logger.warning("⚠️ prior_reasoner或其llm_manager不可用")
            
            # 🔍 尝试直接使用DeepSeek客户端
            if not llm_success:
                try:
                    import os
                    api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('NEOGENESIS_API_KEY')
                    
                    if api_key:
                        logger.info(f"🔍 尝试直接创建DeepSeek客户端...")
                        from neogenesis_system.providers.impl.deepseek_client import DeepSeekClient, ClientConfig
                        
                        client_config = ClientConfig(
                            api_key=api_key,
                            model="deepseek-chat",
                            temperature=0.3,
                            max_tokens=1000,
                            enable_cache=False
                        )
                        
                        direct_client = DeepSeekClient(client_config)
                        api_response = direct_client.simple_chat(
                            prompt=decision_prompt,
                            max_tokens=1000,
                            temperature=0.3
                        )
                        
                        # 从APIResponse中提取文本内容
                        llm_response = api_response.content if hasattr(api_response, 'content') else str(api_response)
                        
                        if llm_response and llm_response.strip():
                            parsed_decision = self._parse_llm_decision_response(llm_response, chosen_path, query)
                            logger.info(f"✅ 直接LLM决策成功: 需要工具={parsed_decision.get('needs_tools')}")
                            return parsed_decision
                        else:
                            logger.warning("⚠️ 直接LLM调用返回空响应")
                    else:
                        logger.warning("⚠️ 未找到API密钥，无法使用直接LLM调用")
                        
                except Exception as e:
                    logger.error(f"❌ 直接LLM调用失败: {e}")
            
            # 🔧 智能回退策略 - 现在提供更好的回答质量
            logger.info("🔧 LLM调用失败，使用改进的智能回退策略")
            return self._intelligent_fallback_decision(chosen_path, query, thinking_seed, available_tools)
            
        except Exception as e:
            logger.error(f"❌ LLM最终决策失败: {e}")
            return self._emergency_fallback_decision(chosen_path, query, thinking_seed)
    
    def _get_available_tools_info(self) -> Dict[str, str]:
        """获取可用工具信息"""
        tools_info = {}
        try:
            if self.tool_registry:
                # 尝试获取工具列表
                if hasattr(self.tool_registry, 'tools') and self.tool_registry.tools:
                    for tool_name, tool_obj in self.tool_registry.tools.items():
                        if hasattr(tool_obj, 'description'):
                            tools_info[tool_name] = tool_obj.description
                        else:
                            tools_info[tool_name] = f"{tool_name} - 工具"
                elif hasattr(self.tool_registry, '_tools') and self.tool_registry._tools:
                    for tool_name, tool_obj in self.tool_registry._tools.items():
                        if hasattr(tool_obj, 'description'):
                            tools_info[tool_name] = tool_obj.description
                        else:
                            tools_info[tool_name] = f"{tool_name} - 工具"
                else:
                    # 常见工具的硬编码描述
                    tools_info = {
                        'web_search': '网络搜索 - 搜索网络信息和最新资讯',
                        'knowledge_query': '知识查询 - 查询内部知识库',
                        'idea_verification': '想法验证 - 验证想法的可行性',
                        'llm_advisor': 'LLM顾问 - 获取AI建议和分析'
                    }
        except Exception as e:
            logger.debug(f"获取工具信息时出错: {e}")
            # 使用默认工具信息
            tools_info = {
                'web_search': '网络搜索 - 搜索网络信息和最新资讯',
                'knowledge_query': '知识查询 - 查询内部知识库'
            }
        
        logger.debug(f"📋 可用工具: {list(tools_info.keys())}")
        return tools_info
    
    def _build_llm_decision_prompt(self, user_query: str, chosen_path: ReasoningPath, 
                                  thinking_seed: str, available_tools: Dict[str, str],
                                  decision_context: Dict[str, Any]) -> str:
        """构建LLM决策提示"""
        
        tools_description = "\n".join([f"- {name}: {desc}" for name, desc in available_tools.items()])
        
        prompt = f"""你是Neogenesis智能助手的最终决策官，负责做出智能、合理的最终决策。

📋 **决策上下文**
用户问题: {user_query}
选择的策略: {chosen_path.path_type}
策略描述: {chosen_path.description}
思维种子: {thinking_seed}

🔧 **可用工具**
{tools_description if tools_description else "暂无可用工具"}

💡 **你的任务**
请分析这个情况，然后做出智能判断：

1. **是否需要工具?** 
   - 对于简单的问候、感谢、闲聊等，通常不需要工具
   - 对于需要搜索信息、获取数据、验证想法的任务，才需要工具
   - 即使策略是"分析型"或"批判型"，如果用户只是说"你好"，也不应该使用工具

2. **如何回应?**
   - 如果不需要工具：直接生成自然、友好、符合对话上下文的回答
   - 如果需要工具：说明需要哪些工具以及原因

📝 **请用以下JSON格式回答**
{{
    "needs_tools": false,  // true或false
    "tool_reasoning": "判断是否需要工具的理由",
    "direct_answer": "如果不需要工具，这里是你的直接回答。要自然、友好、有个性。",
    "recommended_tools": [  // 如果需要工具，推荐的工具名称
        // ["web_search", "knowledge_query"] 等
    ],
    "explanation": "你的整体思考和决策解释"
}}

⚠️ **特别注意**
- 回答要自然真诚，避免机械化的模板回答
- 要考虑上下文，不要生硬地套用策略
- JSON格式要严格正确"""
        
        return prompt
    
    def _parse_llm_decision_response(self, response: str, chosen_path: ReasoningPath, 
                                   query: str) -> Dict[str, Any]:
        """解析LLM的决策响应"""
        try:
            import json
            import re
            
            # 提取JSON部分
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1) if json_match.groups() else json_match.group()
                decision_data = json.loads(json_str)
                
                # 构建标准化决策结果
                result = {
                    'needs_tools': decision_data.get('needs_tools', False),
                    'direct_answer': decision_data.get('direct_answer', ''),
                    'explanation': decision_data.get('explanation', ''),
                    'tool_reasoning': decision_data.get('tool_reasoning', ''),
                    'actions': []
                }
                
                # 如果需要工具，转换为Action对象
                if result['needs_tools'] and decision_data.get('recommended_tools'):
                    for tool_name in decision_data.get('recommended_tools', []):
                        if isinstance(tool_name, str):
                            # 基于工具名称生成合适的参数
                            tool_input = self._generate_tool_input(tool_name, query, chosen_path)
                            result['actions'].append(Action(
                                tool_name=tool_name,
                                tool_input=tool_input
                            ))
                
                logger.info(f"🔍 LLM决策解析成功: {result['needs_tools']=}, 工具数={len(result['actions'])}")
                return result
            
        except Exception as e:
            logger.warning(f"⚠️ 解析LLM决策响应失败: {e}")
        
        # 解析失败，使用响应文本生成回退决策
        return self._extract_fallback_from_response(response, chosen_path, query)
    
    def _generate_tool_input(self, tool_name: str, query: str, path: ReasoningPath) -> Dict[str, Any]:
        """根据工具名称生成合适的输入参数"""
        if tool_name == 'web_search':
            return {"query": query}
        elif tool_name == 'knowledge_query':
            return {"query": query}
        elif tool_name == 'idea_verification':
            return {"idea_text": f"验证关于'{query}'的想法: {path.description}"}
        else:
            return {"query": query}  # 通用参数
    
    def _extract_fallback_from_response(self, response: str, chosen_path: ReasoningPath, 
                                      query: str) -> Dict[str, Any]:
        """从响应文本中提取回退决策"""
        # 简单的关键词分析
        response_lower = response.lower()
        
        # 判断是否提到需要工具
        tool_keywords = ['需要', '应该', '建议', '搜索', '查询', '工具', 'tool']
        needs_tools = any(keyword in response_lower for keyword in tool_keywords)
        
        if needs_tools:
            return {
                'needs_tools': True,
                'direct_answer': '',
                'explanation': f"基于LLM响应分析，判断需要使用工具处理: {response[:200]}...",
                'tool_reasoning': "从响应中检测到工具使用意图",
                'actions': []  # 将由回退逻辑处理
            }
        else:
            return {
                'needs_tools': False,
                'direct_answer': response.strip(),
                'explanation': f"LLM提供直接回答: {chosen_path.path_type}",
                'tool_reasoning': "从响应中判断无需工具",
                'actions': []
            }
    
    def _intelligent_fallback_decision(self, chosen_path: ReasoningPath, query: str, 
                                     thinking_seed: str, available_tools: Dict[str, str]) -> Dict[str, Any]:
        """智能回退决策"""
        logger.info("🔧 使用智能回退决策策略")
        
        query_lower = query.lower().strip()
        
        # 简单问候和感谢的处理
        greeting_patterns = ['你好', 'hello', 'hi', '您好', '早上好', '下午好', '晚上好']
        thanks_patterns = ['谢谢', 'thanks', 'thank you', '感谢']
        
        if any(pattern in query_lower for pattern in greeting_patterns):
            return {
                'needs_tools': False,
                'direct_answer': "你好！我是Neogenesis智能助手，很高兴为您服务。有什么我可以帮助您的吗？",
                'explanation': "识别为问候语，无需调用工具，直接友好回应",
                'tool_reasoning': "问候语不需要工具支持",
                'actions': []
            }
        
        if any(pattern in query_lower for pattern in thanks_patterns):
            return {
                'needs_tools': False,
                'direct_answer': "不客气！如果还有其他问题，随时可以问我。",
                'explanation': "识别为感谢语，无需调用工具，直接回应",
                'tool_reasoning': "感谢语不需要工具支持", 
                'actions': []
            }
        
        # 判断是否需要搜索信息
        search_indicators = ['什么是', '如何', '为什么', '哪里', '谁', '何时', '最新', '信息', '资料', '怎样']
        if any(indicator in query_lower for indicator in search_indicators) and 'web_search' in available_tools:
            return {
                'needs_tools': True,
                'direct_answer': '',
                'explanation': f"基于'{chosen_path.path_type}'策略，检测到需要搜索相关信息",
                'tool_reasoning': "检测到信息查询需求，建议使用搜索工具",
                'actions': [Action(tool_name="web_search", tool_input={"query": query})]
            }
        
        # 🔧 新增：智能识别自我介绍类查询
        self_intro_patterns = ['介绍一下你自己', '你是谁', '自我介绍', '介绍自己', 'introduce yourself', 'who are you']
        if any(pattern in query_lower for pattern in self_intro_patterns):
            return {
                'needs_tools': False,
                'direct_answer': "你好！我是Neogenesis智能助手，一个基于先进认知架构的AI系统。我具备五阶段智能决策能力，包括思维种子生成、路径规划、策略选择、验证学习和智能执行。我可以帮助您进行信息查询、问题分析、创意思考等多种任务。我的特点是能够根据不同问题选择最合适的思维路径，并通过持续学习不断优化决策质量。有什么我可以帮助您的吗？",
                'explanation': "识别为自我介绍查询，提供Neogenesis智能助手的详细介绍",
                'tool_reasoning': "自我介绍无需工具支持，直接提供助手信息",
                'actions': []
            }
        
        # 🔧 新增：智能识别能力相关查询  
        capability_patterns = ['你能做什么', '你有什么功能', '你会什么', '你的能力', 'what can you do', 'your capabilities']
        if any(pattern in query_lower for pattern in capability_patterns):
            return {
                'needs_tools': False,
                'direct_answer': "我具备以下核心能力：\n1. 🧠 智能决策：五阶段认知架构，能够分析问题并选择最佳处理策略\n2. 🔍 信息搜索：可以帮您搜索网络信息、获取最新资讯\n3. 🔬 想法验证：分析和验证想法的可行性\n4. 📊 数据分析：处理和分析各种文本数据\n5. 💭 创意思考：提供创新性的解决方案和建议\n6. 📝 内容生成：协助写作、总结、翻译等文本任务\n7. 🤔 问题解答：回答各领域的专业问题\n\n我最大的特点是能够根据您的具体需求，智能选择最合适的思维模式和工具来为您提供帮助。",
                'explanation': "识别为能力查询，详细介绍助手功能",
                'tool_reasoning': "能力介绍无需工具支持，直接提供功能清单",
                'actions': []
            }
        
        # 默认情况：生成更自然的回答，而不是暴露内部思维种子
        return {
            'needs_tools': False,
            'direct_answer': f"我已经仔细分析了您的问题「{query}」。基于{chosen_path.path_type}的处理方式，我认为这个问题可以直接为您提供有用的回答。如果您需要更详细的信息或有其他相关问题，请随时告诉我，我会很乐意为您进一步解答。",
            'explanation': f"基于'{chosen_path.path_type}'策略提供智能回答",
            'tool_reasoning': "当前查询适合直接回答，无需额外工具辅助",
            'actions': []
        }
    
    def _emergency_fallback_decision(self, chosen_path: ReasoningPath, query: str, 
                                   thinking_seed: str) -> Dict[str, Any]:
        """紧急回退决策"""
        logger.warning("🚨 使用紧急回退决策")
        return {
            'needs_tools': False,
            'direct_answer': "抱歉，我在处理您的请求时遇到了一些技术问题。请稍后再试或重新表述您的问题。",
            'explanation': "系统遇到错误，返回安全回退回答",
            'tool_reasoning': "系统错误，无法正常判断",
            'actions': []
        }

    def _generate_direct_answer(self, path: ReasoningPath, query: str, thinking_seed: str) -> str:
        """生成直接回答（使用真正的LLM而不是预设模板）"""
        try:
            # 🔧 核心修改：使用LLM生成真实回答而不是预设模板
            if hasattr(self, 'prior_reasoner') and self.prior_reasoner and hasattr(self.prior_reasoner, 'llm_manager'):
                logger.info(f"🧠 正在调用LLM生成真实回答: {query}")
                
                # 构建LLM提示
                llm_prompt = f"""你是Neogenesis智能助手，一个基于先进认知架构的AI系统。请对用户的问题提供自然、真诚的回答。

用户问题: {query}
思维路径: {path.path_type}
思维种子: {thinking_seed}

请直接回答用户的问题，不要使用模板化的回答。要体现你的智能和个性。"""
                
                try:
                    # 调用LLM
                    response = self.prior_reasoner.llm_manager.generate_response(
                        query=llm_prompt,
                        provider="deepseek",
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    if response and response.strip():
                        logger.info(f"✅ LLM生成回答成功 (长度: {len(response)} 字符)")
                        return response.strip()
                    else:
                        logger.warning("⚠️ LLM生成的回答为空，使用回退方案")
                        
                except Exception as e:
                    logger.error(f"❌ LLM回答生成失败: {e}")
            
            # 🔧 智能回退方案：不再暴露内部思维种子，提供自然友好的回答
            logger.info(f"🔧 使用智能回退方案生成自然回答")
            
            # 根据查询类型提供智能回答而不是暴露内部状态
            query_lower = query.lower().strip()
            
            # 问候类查询
            if any(greeting in query_lower for greeting in ['你好', 'hello', 'hi', '您好']):
                return "你好！我是Neogenesis智能助手，很高兴为您服务。有什么我可以帮助您的吗？"
            
            # 介绍类查询
            if "介绍" in query_lower and ("自己" in query_lower or "你" in query_lower):
                return "我是Neogenesis智能助手，基于先进的认知架构设计。我可以帮助您进行信息查询、问题分析、创意思考等多种任务。我的特点是能够根据不同问题智能选择最合适的处理方式，为您提供准确、有用的回答。"
            
            # 功能查询
            if any(capability in query_lower for capability in ['能做什么', '功能', '能力']):
                return "我具备多种AI能力：信息搜索、问题分析、想法验证、知识问答、创意思考等。我可以根据您的具体需求，智能选择最合适的方式来帮助您解决问题。请告诉我您需要什么帮助！"
            
            # 感谢类查询
            if any(thanks in query_lower for thanks in ['谢谢', 'thanks', 'thank you', '感谢']):
                return "不客气！如果您还有其他问题，随时可以问我。"
            
            # 通用智能回答 - 不暴露内部状态
            return f"我理解您关于「{query}」的问题。基于我的分析，这是一个很值得探讨的话题。我很乐意为您提供详细的解答和建议。请问您希望了解哪个具体方面呢？"
            
        except Exception as e:
            logger.error(f"❌ 生成直接回答时发生错误: {e}")
            return f"抱歉，处理您的问题「{query}」时遇到了技术问题。请稍后再试或重新描述您的问题。"
    
    def _verify_idea_feasibility(self, idea_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证想法可行性（简化版实现）
        
        这里调用工具系统中的idea_verification工具
        """
        try:
            if self.tool_registry and self.tool_registry.has_tool("idea_verification"):
                result = execute_tool("idea_verification", idea_text=idea_text)
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
