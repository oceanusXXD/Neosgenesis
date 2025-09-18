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

# 导入语义分析器
try:
    from ..cognitive_engine.semantic_analyzer import create_semantic_analyzer
    SEMANTIC_ANALYZER_AVAILABLE = True
except ImportError:
    SEMANTIC_ANALYZER_AVAILABLE = False
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
                 workflow_agent=None,
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
            workflow_agent: WorkflowGenerationAgent实例（可选，用于委托战术规划）
            tool_registry: 工具注册表（可选，默认使用全局注册表）
            state_manager: 状态管理器（可选）
            config: 配置字典（可选）
            cognitive_scheduler: 认知调度器（可选）
        """
        super().__init__(
            name="NeogenesisPlanner",
            description="基于Meta MAB的五阶段智能规划器"
        )
        
        # 依赖注入的核心组件
        self.prior_reasoner = prior_reasoner
        self.path_generator = path_generator
        self.mab_converger = mab_converger
        
        # 🚀 委托代理 - 用于战术规划
        self.workflow_agent = workflow_agent
        
        # 可选组件
        self.tool_registry = tool_registry or global_tool_registry
        self.state_manager = state_manager
        self.config = config or {}
        
        # 🧠 认知调度器集成
        self.cognitive_scheduler = cognitive_scheduler
        
        # 🚀 初始化语义分析器
        self.semantic_analyzer = None
        if SEMANTIC_ANALYZER_AVAILABLE:
            try:
                self.semantic_analyzer = create_semantic_analyzer()
                logger.info("🔍 NeogenesisPlanner 已集成语义分析器")
            except Exception as e:
                logger.warning(f"⚠️ 语义分析器初始化失败，将使用降级方法: {e}")
                self.semantic_analyzer = None
        else:
            logger.info("📝 未发现语义分析器，使用传统关键词方法")
        
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
        logger.info(f"   战略组件: PriorReasoner, PathGenerator, MABConverger")
        logger.info(f"   战术代理: {'已配置WorkflowAgent' if self.workflow_agent else '未配置(兼容模式)'}")
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
        
        新的委托模式：
        1. 执行战略决策 (make_strategic_decision) 
        2. 委托战术规划 (_delegate_to_workflow_agent)
        3. 返回完整的执行计划
        
        Args:
            query: 用户查询
            memory: Agent的记忆对象
            context: 可选的执行上下文
            
        Returns:
            Plan: 标准格式的执行计划
        """
        logger.info(f"🎯 NeogenesisPlanner开始战略+委托模式: {query[:50]}...")
        start_time = time.time()
        
        # 🧠 通知认知调度器Agent正在活跃工作
        if self.cognitive_scheduler:
            self.cognitive_scheduler.notify_activity("task_planning", {
                "query": query[:100],
                "timestamp": start_time,
                "source": "create_plan"
            })
        
        try:
            # 🎯 阶段1: 执行战略决策
            logger.info("🧠 阶段1: 战略规划")
            strategy_decision = self.make_strategic_decision(
                user_query=query,
                confidence=context.get('confidence', 0.5) if context else 0.5,
                execution_context=context
            )
            
            # 🚀 阶段2: 委托战术规划
            logger.info("📋 阶段2: 委托战术规划")
            plan = self._delegate_to_workflow_agent(query, memory, strategy_decision)
            
            # 📊 更新性能统计
            execution_time = time.time() - start_time
            self._update_planner_stats(True, execution_time)
            
            logger.info(f"✅ 战略+委托规划完成: {plan.action_count if plan.actions else 0} 个行动, 耗时 {execution_time:.3f}s")
            return plan
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_planner_stats(False, execution_time)
            
            logger.error(f"❌ 战略+委托规划失败: {e}")
            
            # 返回错误回退计划
            return Plan(
                thought=f"战略+委托规划过程中出现错误: {str(e)}",
                final_answer=f"抱歉，我在处理您的请求时遇到了问题: {str(e)}",
                metadata={'delegation_error': str(e)}
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
    
    def make_strategic_decision(self, user_query: str, confidence: float = 0.5, 
                              execution_context: Optional[Dict] = None) -> 'StrategyDecision':
        """
        执行战略决策 - NeogenesisPlanner的核心职责
        
        专注于"决定做什么"，输出StrategyDecision供战术规划器使用
        
        Args:
            user_query: 用户查询
            confidence: 置信度
            execution_context: 执行上下文
            
        Returns:
            StrategyDecision: 战略决策结果
        """
        from ..shared.data_structures import StrategyDecision
        
        # 调用原有的决策逻辑
        decision_result = self._make_decision_logic(user_query, confidence, execution_context)
        
        # 转换为StrategyDecision格式
        strategy_decision = StrategyDecision(
            chosen_path=decision_result.get('chosen_path'),
            thinking_seed=decision_result.get('thinking_seed', ''),
            reasoning=decision_result.get('reasoning', ''),
            user_query=user_query,
            available_paths=decision_result.get('available_paths', []),
            verified_paths=decision_result.get('verified_paths', []),
            timestamp=decision_result.get('timestamp', time.time()),
            round_number=decision_result.get('round_number', self.total_rounds),
            selection_algorithm=decision_result.get('selection_algorithm', 'mab'),
            verification_stats=decision_result.get('verification_stats', {}),
            performance_metrics=decision_result.get('performance_metrics', {}),
            execution_context=execution_context,
            confidence_score=confidence
        )
        
        logger.info(f"🎯 战略决策完成: {strategy_decision.chosen_path.path_type}")
        return strategy_decision
    
    
    # ==================== 委托管理方法 ====================
    
    def _delegate_to_workflow_agent(self, query: str, memory: Any, 
                                   strategy_decision: 'StrategyDecision') -> Plan:
        """
        委托给WorkflowGenerationAgent进行战术规划
        
        Args:
            query: 用户查询
            memory: Agent记忆
            strategy_decision: 战略决策结果
            
        Returns:
            Plan: 完整的执行计划
        """
        if not self.workflow_agent:
            logger.warning("⚠️ 未配置WorkflowAgent，使用简化的回退计划")
            return self._create_fallback_plan(query, strategy_decision)
        
        try:
            logger.info(f"📋 委托战术规划: {strategy_decision.chosen_path.path_type}")
            
            # 构建上下文，包含战略决策
            context = {
                'strategy_decision': strategy_decision,
                'source': 'strategic_planner',
                'delegation_timestamp': time.time()
            }
            
            # 委托给WorkflowAgent执行
            result = self.workflow_agent.run(query, context)
            
            if isinstance(result, str):
                # 如果返回字符串，转换为Plan
                return Plan(
                    thought=f"通过委托完成战术规划：{strategy_decision.chosen_path.path_type}",
                    final_answer=result,
                    metadata={
                        'strategy_decision': strategy_decision,
                        'is_delegated': True,
                        'delegation_successful': True
                    }
                )
            elif hasattr(result, 'actions') or hasattr(result, 'final_answer'):
                # 如果返回Plan对象，添加委托元数据
                if hasattr(result, 'metadata'):
                    result.metadata.update({
                        'strategy_decision': strategy_decision,
                        'is_delegated': True,
                        'delegation_successful': True
                    })
                return result
            else:
                logger.warning(f"⚠️ WorkflowAgent返回了未预期的结果类型: {type(result)}")
                return self._create_fallback_plan(query, strategy_decision)
                
        except Exception as e:
            logger.error(f"❌ WorkflowAgent委托失败: {e}")
            return self._create_fallback_plan(query, strategy_decision, error=str(e))
    
    def _create_fallback_plan(self, query: str, strategy_decision: 'StrategyDecision', 
                             error: Optional[str] = None) -> Plan:
        """
        创建回退计划（当委托失败时使用）
        
        Args:
            query: 用户查询
            strategy_decision: 战略决策
            error: 错误信息（可选）
            
        Returns:
            Plan: 回退执行计划
        """
        chosen_path = strategy_decision.chosen_path
        
        if error:
            thought = f"委托失败({error})，基于战略决策'{chosen_path.path_type}'生成简化计划"
            answer = f"我已经分析了您的查询「{query}」，选择了'{chosen_path.path_type}'处理策略。由于战术规划组件暂不可用，我提供简化的处理建议："
        else:
            thought = f"未配置WorkflowAgent，基于战略决策'{chosen_path.path_type}'生成简化计划"
            answer = f"我已经分析了您的查询「{query}」，选择了'{chosen_path.path_type}'处理策略："
        
        # 根据路径类型提供不同的建议
        if chosen_path.path_type == "exploratory_investigative":
            answer += "\n\n📚 建议采用探索调研策略：\n1. 收集相关信息和资料\n2. 分析不同观点和方案\n3. 验证关键假设和数据\n4. 形成综合性结论"
        elif chosen_path.path_type == "practical_pragmatic":
            answer += "\n\n🎯 建议采用实用直接策略：\n1. 明确具体目标和要求\n2. 选择最直接有效的方法\n3. 快速执行和验证结果\n4. 根据反馈调整优化"
        elif chosen_path.path_type == "systematic_analytical":
            answer += "\n\n🔍 建议采用系统分析策略：\n1. 分解问题为多个子问题\n2. 逐一分析各个组成部分\n3. 研究部分间的关联关系\n4. 综合形成整体解决方案"
        else:
            answer += f"\n\n💡 基于'{chosen_path.path_type}'策略，建议您：\n1. {chosen_path.description}\n2. 根据具体情况制定详细计划\n3. 分步骤执行并监控进度\n4. 持续优化和改进"
        
        return Plan(
            thought=thought,
            final_answer=answer,
            metadata={
                'strategy_decision': strategy_decision,
                'is_fallback': True,
                'fallback_reason': error or 'no_workflow_agent'
            }
        )

    # ==================== 战略规划专用方法 ====================
    
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
