#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工作流生成代理 - 专注于"决定怎么做"的战术规划器
重构后的架构将战术规划职责从NeogenesisPlanner中分离出来，形成专门的WorkflowGenerationAgent

核心职责:
1. 接收战略决策结果（StrategyDecision）
2. 将抽象的ReasoningPath转化为具体的Action序列
3. 智能工具选择和参数生成
4. 输出可执行的Plan对象

设计原则:
- 严格遵循abstractions.py中的BaseAgent和BasePlanner接口规范
- 职责单一：专注于战术层面的"如何执行"
- 与战略规划器解耦：通过StrategyDecision进行通信
- 可插拔设计：支持不同的工具执行器和记忆模块
"""

import time
import logging
from typing import Dict, List, Optional, Any, Union

# 导入框架核心接口
try:
    from ..abstractions import BaseAgent, BasePlanner, BaseToolExecutor, BaseAsyncToolExecutor, BaseMemory
    from ..shared.data_structures import Plan, Action, Observation, ExecutionContext, AgentState
except ImportError:
    from neogenesis_system.abstractions import BaseAgent, BasePlanner, BaseToolExecutor, BaseAsyncToolExecutor, BaseMemory
    from neogenesis_system.shared.data_structures import Plan, Action, Observation, ExecutionContext, AgentState

# 导入战略决策数据结构（需要在data_structures.py中定义）
try:
    from ..shared.data_structures import StrategyDecision
    from ..cognitive_engine.data_structures import ReasoningPath
except ImportError:
    # 如果还未定义StrategyDecision，使用临时定义
    from dataclasses import dataclass
    from neogenesis_system.cognitive_engine.data_structures import ReasoningPath
    
    @dataclass
    class StrategyDecision:
        """临时的战略决策数据结构"""
        chosen_path: ReasoningPath
        thinking_seed: str
        reasoning: str
        user_query: str
        available_paths: List[ReasoningPath]
        verified_paths: List[Dict[str, Any]]
        timestamp: float
        round_number: int
        selection_algorithm: str
        verification_stats: Dict[str, Any]
        performance_metrics: Dict[str, Any]
        execution_context: Optional[Dict[str, Any]] = None
        confidence_score: float = 0.5

# 导入工具系统
from ..tools.tool_abstraction import ToolRegistry, global_tool_registry

logger = logging.getLogger(__name__)


class WorkflowPlanner(BasePlanner):
    """
    工作流规划器 - 专门的战术规划器
    
    专注于将抽象的战略决策转换为具体的执行计划。
    这是连接抽象思维和具体行动的关键组件。
    
    核心能力:
    1. StrategyDecision到Plan的智能转换
    2. 基于路径类型的工具选择策略
    3. 智能参数生成和上下文感知
    4. LLM辅助的决策优化
    """
    
    def __init__(self, 
                 tool_registry: Optional[ToolRegistry] = None,
                 config: Optional[Dict] = None,
                 name: str = "WorkflowPlanner",
                 description: str = "将战略决策转化为具体执行计划的战术规划器"):
        """
        初始化工作流规划器
        
        Args:
            tool_registry: 工具注册表，默认使用全局注册表
            config: 配置字典
            name: 规划器名称
            description: 规划器描述
        """
        super().__init__(name=name, description=description)
        
        self.tool_registry = tool_registry or global_tool_registry
        self.config = config or {}
        
        # 战略路径到行动的映射规则
        self.strategy_to_action_rules = {
            'exploratory_investigative': self._handle_exploratory_strategy,
            'critical_questioning': self._handle_critical_strategy,
            'systematic_analytical': self._handle_analytical_strategy,
            'practical_pragmatic': self._handle_practical_strategy,
            'creative_innovative': self._handle_creative_strategy,
            '创新绕道思考': self._handle_detour_strategy,
            'default': self._handle_default_strategy
        }
        
        # 统计信息
        self.conversion_stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'direct_answer_rate': 0.0,
            'avg_action_count': 0.0,
            'strategy_type_distribution': {}
        }
        
        logger.info(f"🔧 WorkflowPlanner 初始化完成")
        logger.info(f"   支持策略类型: {len(self.strategy_to_action_rules)} 种")
        
    def create_plan(self, query: str, memory: Any, context: Optional[Dict[str, Any]] = None) -> Plan:
        """
        基于战略决策创建具体执行计划 - 实现BasePlanner接口
        
        Args:
            query: 用户查询（主要用于兼容接口）
            memory: Agent记忆模块
            context: 执行上下文，必须包含'strategy_decision'字段
            
        Returns:
            Plan: 具体的执行计划
            
        Raises:
            ValueError: 当缺少必要的战略决策上下文时
        """
        start_time = time.time()
        self.conversion_stats['total_conversions'] += 1
        
        logger.info(f"🔧 开始战术规划: 查询='{query[:50]}...'")
        
        # 验证输入
        if not context or 'strategy_decision' not in context:
            error_msg = "WorkflowPlanner需要战略决策上下文才能生成执行计划"
            logger.error(f"❌ {error_msg}")
            return self._create_error_plan(query, error_msg)
        
        strategy_decision: StrategyDecision = context['strategy_decision']
        
        try:
            # 🎯 核心转换：从StrategyDecision到Plan
            plan = self._convert_strategy_to_workflow_plan(strategy_decision, query, memory)
            
            # 📊 更新统计信息
            execution_time = time.time() - start_time
            self._update_conversion_stats(plan, strategy_decision, execution_time, success=True)
            
            logger.info(f"✅ 战术规划完成: {plan.action_count} 个行动, 耗时 {execution_time:.3f}s")
            return plan
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_conversion_stats(None, strategy_decision, execution_time, success=False)
            
            logger.error(f"❌ 战术规划失败: {e}")
            return self._create_error_plan(query, f"战术规划过程中出现错误: {str(e)}")
    
    def validate_plan(self, plan: Plan) -> bool:
        """
        验证计划的有效性 - 实现BasePlanner接口
        
        Args:
            plan: 要验证的计划
            
        Returns:
            bool: 计划是否有效
        """
        try:
            # 检查基本结构
            if not plan.thought:
                logger.warning("⚠️ 计划缺少思考过程")
                return False
            
            # 直接回答模式验证
            if plan.is_direct_answer:
                is_valid = plan.final_answer is not None and len(plan.final_answer.strip()) > 0
                if not is_valid:
                    logger.warning("⚠️ 直接回答模式下缺少有效答案")
                return is_valid
            
            # 工具执行模式验证
            if not plan.actions:
                logger.warning("⚠️ 工具执行模式下缺少行动列表")
                return False
            
            # 验证所有行动
            for i, action in enumerate(plan.actions):
                if not action.tool_name or not isinstance(action.tool_input, dict):
                    logger.warning(f"⚠️ 行动 {i} 缺少有效的工具名称或输入参数")
                    return False
                
                # 检查工具是否存在（如果有工具注册表）
                if (self.tool_registry and 
                    hasattr(self.tool_registry, 'has_tool') and 
                    not self.tool_registry.has_tool(action.tool_name)):
                    logger.warning(f"⚠️ 行动 {i} 使用的工具 '{action.tool_name}' 未在注册表中找到")
                    return False
            
            logger.debug(f"✅ 计划验证通过: {plan.action_count} 个行动")
            return True
            
        except Exception as e:
            logger.error(f"❌ 计划验证失败: {e}")
            return False
    
    def estimate_complexity(self, query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """
        估算任务复杂度 - 重写BasePlanner方法
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            float: 复杂度分数 (0.0-1.0)
        """
        if not context or 'strategy_decision' not in context:
            return 0.5  # 默认中等复杂度
        
        strategy_decision: StrategyDecision = context['strategy_decision']
        
        # 基于战略决策信息估算复杂度
        complexity_factors = []
        
        # 因子1：路径验证统计
        verification_stats = strategy_decision.verification_stats
        feasible_ratio = verification_stats.get('feasible_paths', 0) / max(verification_stats.get('paths_verified', 1), 1)
        complexity_factors.append(1.0 - feasible_ratio)  # 可行路径越少，复杂度越高
        
        # 因子2：查询长度
        query_complexity = min(len(query) / 200.0, 1.0)  # 查询越长，复杂度可能越高
        complexity_factors.append(query_complexity)
        
        # 因子3：策略类型
        strategy_type_complexity = {
            'exploratory_investigative': 0.7,
            'critical_questioning': 0.8,
            'systematic_analytical': 0.9,
            'creative_innovative': 0.6,
            'practical_pragmatic': 0.3,
            '创新绕道思考': 0.5
        }
        path_type = strategy_decision.chosen_path.path_type
        strategy_complexity = strategy_type_complexity.get(path_type, 0.5)
        complexity_factors.append(strategy_complexity)
        
        # 计算平均复杂度
        estimated_complexity = sum(complexity_factors) / len(complexity_factors)
        
        logger.debug(f"🔍 复杂度估算: {estimated_complexity:.2f} (基于 {len(complexity_factors)} 个因子)")
        return estimated_complexity
    
    def can_handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        判断是否能处理该查询 - 重写BasePlanner方法
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            bool: 是否能处理
        """
        # WorkflowPlanner需要战略决策上下文才能工作
        if not context or 'strategy_decision' not in context:
            return False
        
        try:
            strategy_decision: StrategyDecision = context['strategy_decision']
            # 检查战略决策是否有有效的选中路径
            return (strategy_decision.chosen_path is not None and 
                   hasattr(strategy_decision.chosen_path, 'path_type'))
        except Exception as e:
            logger.warning(f"⚠️ 检查处理能力时出错: {e}")
            return False
    
    def _convert_strategy_to_workflow_plan(self, strategy_decision: StrategyDecision, 
                                         query: str, memory: Any) -> Plan:
        """
        核心转换方法：将StrategyDecision转换为Plan
        
        🔥 集成了从NeogenesisPlanner迁移的LLM驱动决策逻辑
        
        Args:
            strategy_decision: 战略决策结果
            query: 用户查询
            memory: Agent记忆
            
        Returns:
            Plan: 工作流执行计划
        """
        chosen_path = strategy_decision.chosen_path
        thinking_seed = strategy_decision.thinking_seed
        
        logger.info(f"🔄 开始策略转换: {chosen_path.path_type}")
        
        # 构建战术思考过程
        tactical_thought_parts = [
            f"基于战略决策，我将采用'{chosen_path.path_type}'策略",
            f"战略推理: {strategy_decision.reasoning}",
            f"现在转化为具体执行计划..."
        ]
        tactical_thought = "\n".join(tactical_thought_parts)
        
        try:
            # 🧠 使用LLM作为最终战术决策官（从NeogenesisPlanner迁移的核心逻辑）
            llm_decision = self._llm_tactical_decision_maker(chosen_path, query, thinking_seed, strategy_decision)
            
            if llm_decision.get('needs_tools', False):
                # LLM判断需要工具，使用LLM推荐的行动
                actions = llm_decision.get('actions', [])
                if not actions:
                    # 如果LLM没有提供具体行动，回退到规则分析
                    actions = self._analyze_path_actions(chosen_path, query, strategy_decision)
                
                if actions:
                    plan = Plan(
                        thought=llm_decision.get('explanation', tactical_thought),
                        actions=actions
                    )
                else:
                    # 即使LLM说需要工具，但没有找到合适工具，返回直接回答
                    plan = Plan(
                        thought=llm_decision.get('explanation', tactical_thought),
                        final_answer=llm_decision.get('direct_answer', "抱歉，我无法找到合适的工具来处理您的请求。")
                    )
            else:
                # LLM判断不需要工具，直接返回智能生成的回答
                plan = Plan(
                    thought=llm_decision.get('explanation', tactical_thought),
                    final_answer=llm_decision.get('direct_answer')
                )
            
            # 添加元数据
            plan.metadata.update({
                'workflow_generation': {
                    'strategy_decision_id': f"{strategy_decision.round_number}_{strategy_decision.timestamp}",
                    'chosen_strategy': chosen_path.path_type,
                    'conversion_method': 'llm_tactical_decision_maker',
                    'tactical_reasoning': llm_decision.get('explanation', ''),
                    'generation_timestamp': time.time(),
                    'llm_decision': llm_decision
                },
                'strategic_context': {
                    'thinking_seed': thinking_seed,
                    'verification_stats': strategy_decision.verification_stats,
                    'selection_algorithm': strategy_decision.selection_algorithm
                }
            })
            
            action_count = len(plan.actions) if plan.actions else 0
            answer_mode = "工具执行" if plan.actions else "直接回答"
            logger.info(f"🔄 LLM驱动战术决策完成: {answer_mode}, {action_count} 个行动，策略 '{chosen_path.path_type}'")
            return plan
            
        except Exception as e:
            logger.error(f"❌ LLM战术决策失败，回退到规则引擎: {e}")
            
            # 回退到原有的规则引擎
            path_type = chosen_path.path_type.lower()
            handler = self.strategy_to_action_rules.get(path_type, self.strategy_to_action_rules['default'])
            
            # 调用策略处理器
            workflow_result = handler(chosen_path, query, strategy_decision, memory)
            
            # 构建最终计划
            plan = Plan(
                thought=tactical_thought,
                actions=workflow_result.get('actions', []),
                final_answer=workflow_result.get('final_answer')
            )
            
            # 添加元数据
            plan.metadata.update({
                'workflow_generation': {
                    'strategy_decision_id': f"{strategy_decision.round_number}_{strategy_decision.timestamp}",
                    'chosen_strategy': chosen_path.path_type,
                    'conversion_method': handler.__name__ + '_fallback',
                    'tactical_reasoning': workflow_result.get('reasoning', ''),
                    'generation_timestamp': time.time(),
                    'fallback_reason': str(e)
                },
                'strategic_context': {
                    'thinking_seed': thinking_seed,
                    'verification_stats': strategy_decision.verification_stats,
                    'selection_algorithm': strategy_decision.selection_algorithm
                }
            })
            
            return plan
    
    # 策略处理方法组
    def _handle_exploratory_strategy(self, path: ReasoningPath, query: str, 
                                   decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理探索调研型策略"""
        logger.debug("🔍 处理探索调研型策略")
        
        # 探索型策略通常需要搜索工具
        actions = []
        
        # 生成搜索查询
        search_query = self._optimize_search_query(query, "探索", path.description)
        
        if self._tool_available("web_search"):
            actions.append(Action(
                tool_name="web_search",
                tool_input={"query": search_query}
            ))
        
        # 如果有知识查询工具，也可以使用
        if self._tool_available("knowledge_query"):
            actions.append(Action(
                tool_name="knowledge_query", 
                tool_input={"query": query}
            ))
        
        return {
            'actions': actions,
            'reasoning': f"探索调研策略: 使用搜索工具获取相关信息",
            'final_answer': None if actions else f"基于探索调研的角度，我来为您分析「{query}」这个问题..."
        }
    
    def _handle_critical_strategy(self, path: ReasoningPath, query: str, 
                                decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理批判质疑型策略"""
        logger.debug("🔬 处理批判质疑型策略")
        
        actions = []
        
        # 批判型策略可能需要验证工具
        if self._tool_available("idea_verification"):
            verification_idea = f"对于'{query}'这个问题的批判性思考和质疑分析"
            actions.append(Action(
                tool_name="idea_verification",
                tool_input={"idea_text": verification_idea}
            ))
        
        # 也可能需要搜索相关的反对观点或争议
        if self._tool_available("web_search"):
            critical_search = f"{query} 争议 问题 缺点 风险"
            actions.append(Action(
                tool_name="web_search",
                tool_input={"query": critical_search}
            ))
        
        return {
            'actions': actions,
            'reasoning': f"批判质疑策略: 验证想法并搜索潜在问题",
            'final_answer': None if actions else f"从批判性角度来看「{query}」，我需要考虑以下几个方面..."
        }
    
    def _handle_analytical_strategy(self, path: ReasoningPath, query: str, 
                                  decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理系统分析型策略"""
        logger.debug("📊 处理系统分析型策略")
        
        actions = []
        
        # 系统分析可能需要多种信息源
        if self._tool_available("web_search"):
            analytical_search = self._optimize_search_query(query, "分析", "系统性 方法 步骤")
            actions.append(Action(
                tool_name="web_search",
                tool_input={"query": analytical_search}
            ))
        
        return {
            'actions': actions,
            'reasoning': f"系统分析策略: 收集全面信息进行结构化分析",
            'final_answer': None if actions else f"对「{query}」进行系统分析，我将从以下维度进行..."
        }
    
    def _handle_practical_strategy(self, path: ReasoningPath, query: str, 
                                 decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理实用直接型策略"""
        logger.debug("🎯 处理实用直接型策略")
        
        # 实用型策略通常直接回答，但可能需要快速验证
        query_lower = query.lower()
        
        # 简单问候和常见问题直接回答
        if any(greeting in query_lower for greeting in ['你好', 'hello', 'hi', '您好']):
            return {
                'actions': [],
                'reasoning': "识别为问候语，直接友好回应",
                'final_answer': "你好！我是Neogenesis智能助手，很高兴为您服务。有什么我可以帮助您的吗？"
            }
        
        if '介绍' in query_lower and ('自己' in query_lower or '你' in query_lower):
            return {
                'actions': [],
                'reasoning': "识别为自我介绍请求，提供助手信息",
                'final_answer': "我是Neogenesis智能助手，基于先进的认知架构设计。我具备战略决策和战术规划的双重能力，可以帮助您进行信息搜索、问题分析、创意思考等多种任务。我的特点是能够根据不同问题智能选择最合适的处理策略。"
            }
        
        # 其他情况提供实用性回答
        return {
            'actions': [],
            'reasoning': f"实用直接策略: 基于现有知识直接回答",
            'final_answer': f"基于实用的角度，对于「{query}」这个问题，我认为..."
        }
    
    def _handle_creative_strategy(self, path: ReasoningPath, query: str, 
                                decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理创新创意型策略"""
        logger.debug("💡 处理创新创意型策略")
        
        # 创意型策略通常不需要工具，直接发挥创造力
        return {
            'actions': [],
            'reasoning': f"创新创意策略: 发挥创造性思维",
            'final_answer': f"让我们从创新的角度来思考「{query}」这个问题..."
        }
    
    def _handle_detour_strategy(self, path: ReasoningPath, query: str, 
                              decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理绕道思考型策略"""
        logger.debug("🚀 处理绕道思考型策略")
        
        # 绕道策略需要突破常规，可能需要搜索不同角度的信息
        actions = []
        
        if self._tool_available("web_search"):
            detour_search = f"{query} 另类角度 不同观点 新颖方法"
            actions.append(Action(
                tool_name="web_search", 
                tool_input={"query": detour_search}
            ))
        
        return {
            'actions': actions,
            'reasoning': f"绕道思考策略: 寻找非常规解决方案",
            'final_answer': None if actions else f"让我用不同寻常的角度来思考「{query}」..."
        }
    
    def _handle_default_strategy(self, path: ReasoningPath, query: str, 
                               decision: StrategyDecision, memory: Any) -> Dict[str, Any]:
        """处理默认/未知策略"""
        logger.debug("🔧 处理默认策略")
        
        # 默认策略：尝试搜索，如果不可用就直接回答
        actions = []
        
        if self._tool_available("web_search"):
            actions.append(Action(
                tool_name="web_search",
                tool_input={"query": query}
            ))
        
        return {
            'actions': actions,
            'reasoning': f"默认策略处理: {path.path_type}",
            'final_answer': None if actions else f"我来为您解答「{query}」这个问题..."
        }
    
    # 工具方法组
    def _tool_available(self, tool_name: str) -> bool:
        """检查工具是否可用"""
        try:
            if not self.tool_registry:
                return False
            
            if hasattr(self.tool_registry, 'has_tool'):
                return self.tool_registry.has_tool(tool_name)
            elif hasattr(self.tool_registry, 'tools'):
                return tool_name in self.tool_registry.tools
            elif hasattr(self.tool_registry, '_tools'):
                return tool_name in self.tool_registry._tools
            else:
                return False
        except Exception as e:
            logger.debug(f"检查工具可用性时出错: {e}")
            return False
    
    def _optimize_search_query(self, original_query: str, strategy_type: str, 
                             additional_keywords: str = "") -> str:
        """优化搜索查询"""
        optimized_query = original_query
        
        if strategy_type == "探索":
            optimized_query += f" {additional_keywords} 详细信息"
        elif strategy_type == "分析":
            optimized_query += f" {additional_keywords} 分析 研究"
        elif additional_keywords:
            optimized_query += f" {additional_keywords}"
        
        return optimized_query.strip()
    
    def _update_conversion_stats(self, plan: Optional[Plan], strategy_decision: StrategyDecision, 
                               execution_time: float, success: bool):
        """更新转换统计信息"""
        if success:
            self.conversion_stats['successful_conversions'] += 1
            
            if plan:
                # 更新直接回答率
                total = self.conversion_stats['total_conversions']
                current_direct_rate = self.conversion_stats['direct_answer_rate']
                is_direct = plan.is_direct_answer
                self.conversion_stats['direct_answer_rate'] = (current_direct_rate * (total - 1) + (1 if is_direct else 0)) / total
                
                # 更新平均行动数量
                current_avg_actions = self.conversion_stats['avg_action_count']
                action_count = plan.action_count
                self.conversion_stats['avg_action_count'] = (current_avg_actions * (total - 1) + action_count) / total
        
        # 更新策略类型分布
        strategy_type = strategy_decision.chosen_path.path_type
        if strategy_type not in self.conversion_stats['strategy_type_distribution']:
            self.conversion_stats['strategy_type_distribution'][strategy_type] = 0
        self.conversion_stats['strategy_type_distribution'][strategy_type] += 1
    
    def _create_error_plan(self, query: str, error_message: str) -> Plan:
        """创建错误处理计划"""
        return Plan(
            thought=f"战术规划过程中出现错误: {error_message}",
            final_answer=f"抱歉，我在制定执行计划时遇到了问题: {error_message}"
        )
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """获取转换统计信息"""
        return {
            'planner_name': self.name,
            'conversion_stats': self.conversion_stats.copy(),
            'success_rate': (self.conversion_stats['successful_conversions'] / 
                           max(self.conversion_stats['total_conversions'], 1))
        }
    
    # ==================== 从NeogenesisPlanner迁移的战术规划方法 ====================
    
    def _llm_tactical_decision_maker(self, chosen_path: ReasoningPath, query: str, 
                                   thinking_seed: str, strategy_decision: StrategyDecision) -> Dict[str, Any]:
        """
        🧠 LLM作为战术决策制定者（从NeogenesisPlanner迁移）
        
        让LLM扮演"战术决策官"的角色，智能判断是否需要工具以及生成自然回答。
        这是从NeogenesisPlanner迁移的核心战术逻辑。
        
        Args:
            chosen_path: 选中的思维路径
            query: 用户原始查询
            thinking_seed: 思维种子
            strategy_decision: 完整战略决策结果
            
        Returns:
            Dict[str, Any]: LLM的战术决策结果，包含：
            - needs_tools: bool - 是否需要工具
            - actions: List[Action] - 推荐的行动（如果需要工具）
            - direct_answer: str - 直接回答（如果不需要工具）
            - explanation: str - 决策解释
        """
        try:
            logger.info(f"🧠 LLM战术决策官开始工作: 查询='{query[:50]}...', 路径='{chosen_path.path_type}'")
            
            # 🔍 收集可用工具信息
            available_tools = self._get_available_tools_info()
            
            # 🧠 构建LLM决策提示
            decision_prompt = self._build_llm_decision_prompt(
                user_query=query,
                chosen_path=chosen_path,
                thinking_seed=thinking_seed,
                available_tools=available_tools,
                strategy_context=strategy_decision
            )
            
            # 🚀 调用LLM进行智能决策
            llm_response = self._call_llm_for_decision(decision_prompt)
            
            if llm_response:
                # 🔍 解析LLM响应
                parsed_decision = self._parse_llm_decision_response(llm_response, chosen_path, query)
                logger.info(f"✅ LLM战术决策成功: 需要工具={parsed_decision.get('needs_tools')}")
                return parsed_decision
            else:
                logger.warning("⚠️ LLM调用失败，使用智能回退策略")
                
            # 🔧 智能回退策略
            return self._intelligent_fallback_decision(chosen_path, query, thinking_seed, available_tools)
            
        except Exception as e:
            logger.error(f"❌ LLM战术决策失败: {e}")
            return self._emergency_fallback_decision(chosen_path, query, thinking_seed)
    
    def _call_llm_for_decision(self, decision_prompt: str) -> Optional[str]:
        """调用LLM进行决策（统一的LLM调用接口）"""
        # 尝试多种LLM调用方式
        
        # 方式1：通过prior_reasoner调用
        try:
            if hasattr(self, 'prior_reasoner') and self.prior_reasoner and hasattr(self.prior_reasoner, 'llm_manager'):
                logger.info(f"🔍 尝试通过prior_reasoner调用LLM...")
                llm_response = self.prior_reasoner.llm_manager.generate_response(
                    query=decision_prompt,
                    provider="deepseek",
                    temperature=0.3,
                    max_tokens=1000
                )
                
                if llm_response and llm_response.strip():
                    return llm_response.strip()
        except Exception as e:
            logger.debug(f"prior_reasoner LLM调用失败: {e}")
        
        # 方式2：直接调用DeepSeek客户端
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
                    return llm_response.strip()
        except Exception as e:
            logger.debug(f"直接LLM调用失败: {e}")
        
        return None
    
    def _analyze_path_actions(self, chosen_path: ReasoningPath, query: str, 
                            strategy_decision: StrategyDecision) -> List[Action]:
        """
        智能路径分析 - 根据选中的思维路径生成具体行动（从NeogenesisPlanner迁移）
        
        这个方法分析chosen_path的特征，判断应该使用什么工具。
        """
        actions = []
        path_description = chosen_path.description
        
        # 尝试使用语义分析器（如果可用）
        if hasattr(self, 'semantic_analyzer') and self.semantic_analyzer and path_description:
            try:
                # 分析路径描述和查询内容
                combined_text = f"{path_description} {query}"
                analysis_result = self.semantic_analyzer.analyze(
                    combined_text, 
                    ['intent_detection', 'domain_classification']
                )
                
                # 基于意图分析生成行动
                if 'intent_detection' in analysis_result.analysis_results:
                    intent_result = analysis_result.analysis_results['intent_detection'].result
                    primary_intent = intent_result.get('primary_intent', '').lower()
                    
                    # 🔍 智能工具选择
                    if any(word in primary_intent for word in ['information', 'search', 'research', 'explore', 'find']):
                        # 信息搜索需求
                        search_query = self._extract_search_query(query, chosen_path)
                        if self._tool_available("web_search"):
                            actions.append(Action(
                                tool_name="web_search",
                                tool_input={"query": search_query}
                            ))
                        logger.debug(f"🔍 语义识别为搜索路径: {search_query}")
                        
                    elif any(word in primary_intent for word in ['verification', 'validate', 'check', 'confirm', 'verify']):
                        # 验证需求
                        idea_to_verify = self._extract_verification_idea(query, chosen_path)
                        if self._tool_available("idea_verification"):
                            actions.append(Action(
                                tool_name="idea_verification",
                                tool_input={"idea_text": idea_to_verify}
                            ))
                        logger.debug(f"🔬 语义识别为验证路径: {idea_to_verify}")
                        
                    elif any(word in primary_intent for word in ['analysis', 'analyze', 'evaluate', 'compare', 'assess']):
                        # 分析需求
                        if not actions:  # 如果还没有其他行动
                            search_query = f"关于 {query} 的详细信息和分析"
                            if self._tool_available("web_search"):
                                actions.append(Action(
                                    tool_name="web_search",
                                    tool_input={"query": search_query}
                                ))
                            logger.debug(f"📊 语义识别为分析路径，先搜索信息: {search_query}")
                
                logger.debug("🔍 路径行动语义分析成功")
                
            except Exception as e:
                logger.warning(f"⚠️ 路径行动语义分析失败: {e}")
        else:
            logger.debug("📝 语义分析器不可用，跳过智能路径分析")
        
        # 🔧 如果没有识别出任何行动，使用回退方法
        if not actions:
            actions.extend(self._generate_fallback_actions(query, chosen_path))
        
        return actions
    
    def _extract_search_query(self, original_query: str, path: ReasoningPath) -> str:
        """从原始查询和路径信息中提取搜索查询（从NeogenesisPlanner迁移）"""
        # 根据路径描述优化搜索查询
        if "具体" in path.description or "详细" in path.description:
            return f"{original_query} 详细信息"
        elif "最新" in path.description or "recent" in path.description.lower():
            return f"{original_query} 最新发展"
        elif "对比" in path.description or "比较" in path.description:
            return f"{original_query} 对比分析"
        else:
            return original_query
    
    def _extract_verification_idea(self, original_query: str, path: ReasoningPath) -> str:
        """从查询和路径信息中提取需要验证的想法（从NeogenesisPlanner迁移）"""
        return f"基于查询'{original_query}'的想法: {path.description}"
    
    def _generate_fallback_actions(self, query: str, path: ReasoningPath) -> List[Action]:
        """生成简化的默认行动（从NeogenesisPlanner迁移）"""
        # 返回空的行动列表，让系统使用直接回答模式
        return []
    
    def _get_available_tools_info(self) -> Dict[str, str]:
        """获取可用工具信息（从NeogenesisPlanner迁移）"""
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
                                  strategy_context: StrategyDecision) -> str:
        """构建LLM决策提示（从NeogenesisPlanner迁移）"""
        
        tools_description = "\n".join([f"- {name}: {desc}" for name, desc in available_tools.items()])
        
        prompt = f"""你是Neogenesis智能助手的战术决策官，负责做出智能、合理的执行决策。

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
        """解析LLM的决策响应（从NeogenesisPlanner迁移）"""
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
        """根据工具名称生成合适的输入参数（从NeogenesisPlanner迁移）"""
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
        """从响应文本中提取回退决策（从NeogenesisPlanner迁移）"""
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
        """智能回退决策（从NeogenesisPlanner迁移）"""
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
        
        # 🔧 智能识别自我介绍类查询
        self_intro_patterns = ['介绍一下你自己', '你是谁', '自我介绍', '介绍自己', 'introduce yourself', 'who are you']
        if any(pattern in query_lower for pattern in self_intro_patterns):
            return {
                'needs_tools': False,
                'direct_answer': "你好！我是Neogenesis智能助手，一个基于先进认知架构的AI系统。我具备战略决策和战术规划的双重能力，包括思维种子生成、路径规划、策略选择、验证学习和智能执行。我可以帮助您进行信息查询、问题分析、创意思考等多种任务。我的特点是能够根据不同问题选择最合适的思维路径，并通过持续学习不断优化决策质量。有什么我可以帮助您的吗？",
                'explanation': "识别为自我介绍查询，提供Neogenesis智能助手的详细介绍",
                'tool_reasoning': "自我介绍无需工具支持，直接提供助手信息",
                'actions': []
            }
        
        # 🔧 智能识别能力相关查询  
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
        """紧急回退决策（从NeogenesisPlanner迁移）"""
        logger.warning("🚨 使用紧急回退决策")
        return {
            'needs_tools': False,
            'direct_answer': "抱歉，我在处理您的请求时遇到了一些技术问题。请稍后再试或重新表述您的问题。",
            'explanation': "系统遇到错误，返回安全回退回答",
            'tool_reasoning': "系统错误，无法正常判断",
            'actions': []
        }


class WorkflowGenerationAgent(BaseAgent):
    """
    工作流生成代理 - 专注于"决定怎么做"的Agent
    
    这是一个完整的Agent实现，专门负责接收战略决策并转化为具体的执行计划。
    它将WorkflowPlanner与工具执行器和记忆模块整合在一起。
    
    设计特点:
    1. 专业化：专注于战术层面的工作流生成
    2. 协同性：与战略规划器协同工作
    3. 标准化：严格遵循BaseAgent接口规范
    4. 可扩展：支持不同的工具执行器和记忆模块
    """
    
    def __init__(self, 
                 tool_executor: Union[BaseToolExecutor, BaseAsyncToolExecutor],
                 memory: BaseMemory,
                 workflow_planner: Optional[WorkflowPlanner] = None,
                 tool_registry: Optional[ToolRegistry] = None,
                 config: Optional[Dict] = None,
                 name: str = "WorkflowGenerationAgent",
                 description: str = "专注于将战略决策转化为具体执行计划的战术Agent"):
        """
        初始化工作流生成代理
        
        Args:
            tool_executor: 工具执行器实例
            memory: 记忆模块实例
            workflow_planner: 工作流规划器实例（可选，会自动创建）
            tool_registry: 工具注册表
            config: 配置字典
            name: Agent名称
            description: Agent描述
        """
        # 创建或使用提供的WorkflowPlanner
        if workflow_planner is None:
            workflow_planner = WorkflowPlanner(
                tool_registry=tool_registry,
                config=config
            )
        
        # 初始化BaseAgent
        super().__init__(
            planner=workflow_planner,
            tool_executor=tool_executor,
            memory=memory,
            name=name,
            description=description
        )
        
        self.config = config or {}
        
        # 工作流生成专用统计
        self.workflow_stats = {
            'strategic_decisions_processed': 0,
            'successful_workflows_generated': 0,
            'average_workflow_generation_time': 0.0,
            'tool_usage_distribution': {},
            'strategy_type_preferences': {}
        }
        
        logger.info(f"🤖 {name} 初始化完成")
        logger.info(f"   工作流规划器: {workflow_planner.name}")
        logger.info(f"   工具执行器: {tool_executor.name}")
        logger.info(f"   记忆模块: {memory.name}")
    
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        运行工作流生成代理 - 实现BaseAgent接口
        
        Args:
            query: 用户查询
            context: 执行上下文，必须包含'strategy_decision'
            
        Returns:
            str: 执行结果
        """
        start_time = time.time()
        self.is_running = True
        
        try:
            logger.info(f"🚀 WorkflowGenerationAgent 开始处理: {query[:50]}...")
            
            # 验证战略决策上下文
            if not context or 'strategy_decision' not in context:
                error_msg = "WorkflowGenerationAgent需要战略决策上下文"
                logger.error(f"❌ {error_msg}")
                return f"错误: {error_msg}"
            
            strategy_decision: StrategyDecision = context['strategy_decision']
            self.workflow_stats['strategic_decisions_processed'] += 1
            
            # 第一步：使用WorkflowPlanner生成执行计划
            logger.info("📋 第一阶段: 战术规划")
            plan = self.plan_task(query, context)
            
            if not self.planner.validate_plan(plan):
                logger.error("❌ 生成的计划未通过验证")
                return "抱歉，生成的执行计划存在问题，无法继续执行。"
            
            # 第二步：执行计划
            execution_result = ""
            
            if plan.is_direct_answer:
                # 直接回答模式
                logger.info("💬 第二阶段: 直接回答")
                execution_result = plan.final_answer
                
                # 存储到记忆
                self._store_workflow_memory(query, plan, strategy_decision, execution_result)
                
            else:
                # 工具执行模式
                logger.info(f"🔧 第二阶段: 执行 {plan.action_count} 个工具行动")
                
                try:
                    observations = self.execute_plan(plan)
                    
                    # 🎨 增强的结果整合逻辑：支持图文并茂输出
                    if observations:
                        execution_result = self._integrate_multimedia_results(observations, query, plan)
                    else:
                        execution_result = "工具执行完成。"
                    
                    # 存储到记忆
                    self._store_workflow_memory(query, plan, strategy_decision, execution_result, observations)
                    
                except Exception as e:
                    logger.error(f"❌ 工具执行失败: {e}")
                    execution_result = f"抱歉，执行过程中遇到问题: {str(e)}"
            
            # 更新统计信息
            execution_time = time.time() - start_time
            self._update_workflow_stats(strategy_decision, plan, execution_time, success=True)
            
            logger.info(f"✅ WorkflowGenerationAgent 处理完成, 耗时 {execution_time:.3f}s")
            return execution_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_workflow_stats(None, None, execution_time, success=False)
            
            logger.error(f"❌ WorkflowGenerationAgent 处理失败: {e}")
            return f"抱歉，处理您的请求时遇到了问题: {str(e)}"
            
        finally:
            self.is_running = False
    
    def _store_workflow_memory(self, query: str, plan: Plan, strategy_decision: StrategyDecision, 
                             result: str, observations: Optional[List[Observation]] = None):
        """存储工作流执行记忆"""
        try:
            memory_key = f"workflow_{int(time.time())}_{hash(query) % 10000}"
            memory_value = {
                'query': query,
                'strategy_decision': {
                    'chosen_strategy': strategy_decision.chosen_path.path_type,
                    'reasoning': strategy_decision.reasoning,
                    'round_number': strategy_decision.round_number
                },
                'generated_plan': {
                    'is_direct_answer': plan.is_direct_answer,
                    'action_count': plan.action_count,
                    'thought': plan.thought
                },
                'execution_result': result,
                'timestamp': time.time()
            }
            
            if observations:
                memory_value['observations'] = [
                    {'tool_name': obs.action.tool_name, 'success': obs.success, 'output_length': len(str(obs.output))}
                    for obs in observations
                ]
            
            self.store_memory(memory_key, memory_value, {
                'type': 'workflow_execution',
                'strategy_type': strategy_decision.chosen_path.path_type
            })
            
            logger.debug(f"💾 工作流记忆已存储: {memory_key}")
            
        except Exception as e:
            logger.warning(f"⚠️ 存储工作流记忆失败: {e}")
    
    def _update_workflow_stats(self, strategy_decision: Optional[StrategyDecision], 
                             plan: Optional[Plan], execution_time: float, success: bool):
        """更新工作流统计信息"""
        if success:
            self.workflow_stats['successful_workflows_generated'] += 1
            
            # 更新平均生成时间
            total_processed = self.workflow_stats['strategic_decisions_processed']
            current_avg = self.workflow_stats['average_workflow_generation_time']
            self.workflow_stats['average_workflow_generation_time'] = (
                current_avg * (total_processed - 1) + execution_time
            ) / total_processed
            
            if strategy_decision and plan:
                # 更新策略类型偏好
                strategy_type = strategy_decision.chosen_path.path_type
                if strategy_type not in self.workflow_stats['strategy_type_preferences']:
                    self.workflow_stats['strategy_type_preferences'][strategy_type] = 0
                self.workflow_stats['strategy_type_preferences'][strategy_type] += 1
                
                # 更新工具使用分布
                if not plan.is_direct_answer:
                    for action in plan.actions:
                        tool_name = action.tool_name
                        if tool_name not in self.workflow_stats['tool_usage_distribution']:
                            self.workflow_stats['tool_usage_distribution'][tool_name] = 0
                        self.workflow_stats['tool_usage_distribution'][tool_name] += 1
        
        # 更新基础Agent统计
        plan_size = plan.action_count if plan else 0
        self.update_stats(success, execution_time, plan_size)
    
    def _integrate_multimedia_results(self, observations: List[Observation], query: str, plan: Plan) -> str:
        """🎨 整合多媒体结果，支持图文并茂输出"""
        text_results = []
        image_results = []
        other_results = []
        
        logger.info(f"🖼️ 开始整合 {len(observations)} 个观察结果")
        
        # 分类处理不同类型的结果
        for obs in observations:
            if not obs.output:
                continue
                
            # 🎨 检测是否为图像生成工具的输出
            if self._is_image_generation_result(obs):
                image_info = self._extract_image_information(obs)
                if image_info:
                    image_results.append(image_info)
                    logger.info(f"🎨 检测到图像生成结果: {image_info.get('filename', 'unknown')}")
            else:
                # 其他类型的结果
                result_text = self._format_observation_output(obs)
                if result_text:
                    if self._is_textual_result(obs):
                        text_results.append(result_text)
                    else:
                        other_results.append(result_text)
        
        # 生成最终的图文整合响应
        return self._create_multimedia_response(text_results, image_results, other_results, query, plan)
    
    def _is_image_generation_result(self, obs: Observation) -> bool:
        """🖼️ 检测观察结果是否来自图像生成工具"""
        # 检查工具名称
        if hasattr(obs.action, 'tool_name'):
            image_tool_names = ['stable_diffusion_xl_generator', 'image_generation', 'generate_image']
            if obs.action.tool_name in image_tool_names:
                return True
        
        # 检查输出内容是否包含图像信息
        if isinstance(obs.output, dict):
            image_indicators = ['saved_path', 'image_object', 'filename', 'image_size']
            if any(indicator in obs.output for indicator in image_indicators):
                return True
        elif isinstance(obs.output, str):
            # 检查字符串中是否包含图像路径
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
            if any(ext in obs.output.lower() for ext in image_extensions):
                return True
        
        return False
    
    def _extract_image_information(self, obs: Observation) -> Optional[Dict[str, Any]]:
        """🖼️ 提取图像信息"""
        image_info = {
            'type': 'image',
            'tool_name': getattr(obs.action, 'tool_name', 'unknown'),
            'success': obs.success
        }
        
        if isinstance(obs.output, dict):
            # 结构化的图像结果
            image_info.update({
                'filename': obs.output.get('filename', ''),
                'saved_path': obs.output.get('saved_path', ''),
                'prompt': obs.output.get('prompt', ''),
                'image_size': obs.output.get('image_size', ''),
                'model': obs.output.get('model', ''),
                'generated_at': obs.output.get('generated_at', '')
            })
        elif isinstance(obs.output, str):
            # 简单的字符串结果，尝试提取有用信息
            image_info['raw_output'] = obs.output
            # 尝试从字符串中提取文件路径
            import re
            path_match = re.search(r'([^\s]+\.(png|jpg|jpeg|gif|bmp|webp))', obs.output, re.IGNORECASE)
            if path_match:
                image_info['saved_path'] = path_match.group(1)
                image_info['filename'] = path_match.group(1).split('/')[-1].split('\\')[-1]
        
        return image_info if image_info.get('saved_path') or image_info.get('filename') else None
    
    def _is_textual_result(self, obs: Observation) -> bool:
        """检查是否为文本类结果"""
        if hasattr(obs.action, 'tool_name'):
            text_tool_names = ['web_search', 'knowledge_query', 'idea_verification', 'text_analysis']
            return obs.action.tool_name in text_tool_names
        return True  # 默认为文本结果
    
    def _format_observation_output(self, obs: Observation) -> str:
        """格式化观察结果为字符串"""
        if isinstance(obs.output, str):
            return obs.output
        elif isinstance(obs.output, dict):
            # 尝试提取有意义的文本内容
            if 'content' in obs.output:
                return obs.output['content']
            elif 'result' in obs.output:
                return str(obs.output['result'])
            elif 'message' in obs.output:
                return obs.output['message']
            else:
                return str(obs.output)
        else:
            return str(obs.output)
    
    def _create_multimedia_response(self, text_results: List[str], image_results: List[Dict], 
                                  other_results: List[str], query: str, plan: Plan) -> str:
        """🎨 创建图文并茂的响应"""
        response_parts = []
        
        # 🎨 如果有图像结果，优先展示
        if image_results:
            logger.info(f"🎨 正在生成图文并茂响应，包含 {len(image_results)} 张图片")
            
            # 生成图像部分的介绍
            response_parts.append(self._generate_image_introduction(query, len(image_results)))
            
            # 添加每张图片的信息
            for i, img_info in enumerate(image_results, 1):
                image_section = self._format_image_section(img_info, i, len(image_results))
                response_parts.append(image_section)
        
        # 📝 添加文本结果
        if text_results:
            if image_results:
                response_parts.append("\n" + "─" * 50)
                response_parts.append("📝 **相关信息和分析**\n")
            
            for result in text_results:
                response_parts.append(result)
        
        # 🔧 添加其他结果
        if other_results:
            if image_results or text_results:
                response_parts.append("\n" + "─" * 30)
                response_parts.append("🔧 **其他信息**\n")
            
            for result in other_results:
                response_parts.append(result)
        
        # 📊 添加执行统计
        if image_results or text_results or other_results:
            stats_info = self._generate_execution_stats(plan, len(image_results), len(text_results))
            response_parts.append(stats_info)
        
        # 如果没有任何结果
        if not response_parts:
            return "执行完成，但未获得具体结果。"
        
        return "\n\n".join(response_parts)
    
    def _generate_image_introduction(self, query: str, image_count: int) -> str:
        """🎨 生成图像介绍文本"""
        if image_count == 1:
            intro = f"🎨 **根据您的请求“{query}”，我为您生成了以下图像：**"
        else:
            intro = f"🎨 **根据您的请求“{query}”，我为您生成了 {image_count} 张相关图像：**"
        return intro
    
    def _format_image_section(self, img_info: Dict, index: int, total: int) -> str:
        """🖼️ 格式化单个图像信息部分"""
        lines = []
        
        # 图像标题
        if total > 1:
            lines.append(f"### 🖼️ 图像 {index}/{total}")
        else:
            lines.append(f"### 🖼️ 生成的图像")
        
        # 文件信息
        if img_info.get('filename'):
            lines.append(f"📁 **文件名**: {img_info['filename']}")
        
        if img_info.get('saved_path'):
            lines.append(f"💾 **保存路径**: `{img_info['saved_path']}`")
        
        # 图像详情
        if img_info.get('prompt'):
            lines.append(f"🎨 **生成提示词**: {img_info['prompt']}")
        
        if img_info.get('image_size'):
            size = img_info['image_size']
            if isinstance(size, (list, tuple)) and len(size) >= 2:
                lines.append(f"📏 **图像尺寸**: {size[0]} x {size[1]} 像素")
            else:
                lines.append(f"📏 **图像尺寸**: {size}")
        
        if img_info.get('model'):
            lines.append(f"🤖 **生成模型**: {img_info['model']}")
        
        if img_info.get('generated_at'):
            lines.append(f"⏰ **生成时间**: {img_info['generated_at']}")
        
        # 状态信息
        status = "✅ 生成成功" if img_info.get('success', True) else "❌ 生成失败"
        lines.append(f"📊 **生成状态**: {status}")
        
        return "\n".join(lines)
    
    def _generate_execution_stats(self, plan: Plan, image_count: int, text_count: int) -> str:
        """📊 生成执行统计信息"""
        stats_lines = [
            "\n" + "─" * 40,
            "📊 **执行统计**",
            f"🚀 执行了 {plan.action_count} 个工具行动",
        ]
        
        if image_count > 0:
            stats_lines.append(f"🎨 生成了 {image_count} 张图片")
        
        if text_count > 0:
            stats_lines.append(f"📝 获得了 {text_count} 条文本结果")
        
        stats_lines.append("✨ **此响应由 Neogenesis 智能系统生成**")
        
        return "\n".join(stats_lines)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流Agent的详细状态"""
        base_status = self.get_status()
        
        # 添加工作流专用统计
        base_status['workflow_stats'] = self.workflow_stats.copy()
        
        # 添加规划器统计（如果可用）
        if hasattr(self.planner, 'get_conversion_stats'):
            base_status['planner_stats'] = self.planner.get_conversion_stats()
        
        # 计算成功率
        total_processed = self.workflow_stats['strategic_decisions_processed']
        if total_processed > 0:
            base_status['workflow_success_rate'] = (
                self.workflow_stats['successful_workflows_generated'] / total_processed
            )
        else:
            base_status['workflow_success_rate'] = 0.0
        
        return base_status


# 工厂函数：简化WorkflowGenerationAgent的创建
def create_workflow_agent(tool_executor: Union[BaseToolExecutor, BaseAsyncToolExecutor],
                         memory: BaseMemory,
                         tool_registry: Optional[ToolRegistry] = None,
                         config: Optional[Dict] = None) -> WorkflowGenerationAgent:
    """
    工作流代理工厂函数
    
    Args:
        tool_executor: 工具执行器
        memory: 记忆模块
        tool_registry: 工具注册表
        config: 配置
        
    Returns:
        WorkflowGenerationAgent: 配置完成的工作流生成代理
    """
    return WorkflowGenerationAgent(
        tool_executor=tool_executor,
        memory=memory,
        tool_registry=tool_registry,
        config=config
    )
