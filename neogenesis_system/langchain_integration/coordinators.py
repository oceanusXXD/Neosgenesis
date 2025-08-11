#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - Tool Coordinators
智能工具协调器：协调五阶段决策流程中的工具执行
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .tools import (
    NeogenesisThinkingSeedTool,
    NeogenesisRAGSeedTool,
    NeogenesisPathGeneratorTool,
    NeogenesisMABDecisionTool,
    NeogenesisIdeaVerificationTool
)
from .state_management import NeogenesisStateManager, DecisionStage, DecisionState

logger = logging.getLogger(__name__)

# =============================================================================
# 执行策略和模式
# =============================================================================

class ExecutionMode(Enum):
    """执行模式枚举"""
    SEQUENTIAL = "sequential"          # 顺序执行
    PARALLEL = "parallel"             # 并行执行
    ADAPTIVE = "adaptive"             # 自适应执行
    PIPELINE = "pipeline"             # 流水线执行
    FALLBACK_CASCADE = "fallback_cascade"  # 级联回退执行

class ToolPriority(Enum):
    """工具优先级"""
    CRITICAL = "critical"     # 关键工具，必须成功
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中等优先级
    LOW = "low"              # 低优先级，可选
    OPTIONAL = "optional"    # 完全可选

@dataclass
class ExecutionContext:
    """执行上下文"""
    session_id: str
    user_query: str
    execution_mode: ExecutionMode = ExecutionMode.ADAPTIVE
    timeout: float = 60.0
    retry_count: int = 3
    enable_caching: bool = True
    enable_verification: bool = True
    max_parallel_tools: int = 3
    fallback_enabled: bool = True
    custom_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolExecutionPlan:
    """工具执行计划"""
    stage: DecisionStage
    tool_name: str
    tool_instance: Any
    priority: ToolPriority
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_enabled: bool = True
    fallback_tool: Optional[str] = None
    execution_order: int = 0

@dataclass
class ExecutionResult:
    """执行结果"""
    tool_name: str
    stage: DecisionStage
    success: bool
    data: Any = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

# =============================================================================
# 智能工具协调器
# =============================================================================

class NeogenesisToolCoordinator:
    """
    Neogenesis智能工具协调器
    
    功能：
    - 协调五阶段决策流程中的工具执行
    - 智能执行策略选择
    - 依赖管理和执行顺序优化
    - 错误处理和自动恢复
    - 性能优化和缓存管理
    """
    
    def __init__(self,
                 api_key: str = "",
                 search_engine: str = "duckduckgo",
                 llm_client=None,
                 web_search_client=None,
                 state_manager: Optional[NeogenesisStateManager] = None,
                 max_workers: int = 4):
        """
        初始化协调器
        
        Args:
            api_key: API密钥
            search_engine: 搜索引擎类型
            llm_client: LLM客户端
            web_search_client: 网络搜索客户端
            state_manager: 状态管理器
            max_workers: 最大工作线程数
        """
        self.api_key = api_key
        self.search_engine = search_engine
        self.llm_client = llm_client
        self.web_search_client = web_search_client
        self.state_manager = state_manager
        self.max_workers = max_workers
        
        # 初始化工具实例
        self._initialize_tools()
        
        # 执行统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cache_hits": 0,
            "total_execution_time": 0.0,
            "tool_performance": {},
            "error_patterns": {}
        }
        
        # 缓存和优化
        self.result_cache = {}
        self.execution_history = []
        self.performance_optimizer = PerformanceOptimizer()
        
        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info("🎯 NeogenesisToolCoordinator 初始化完成")
    
    def _initialize_tools(self):
        """初始化所有工具实例"""
        self.tools = {
            "thinking_seed": NeogenesisThinkingSeedTool(api_key=self.api_key),
            "rag_seed": NeogenesisRAGSeedTool(
                api_key=self.api_key,
                search_engine=self.search_engine,
                llm_client=self.llm_client,
                web_search_client=self.web_search_client
            ),
            "path_generator": NeogenesisPathGeneratorTool(
                api_key=self.api_key,
                llm_client=self.llm_client
            ),
            "mab_decision": NeogenesisMABDecisionTool(
                api_key=self.api_key,
                llm_client=self.llm_client
            ),
            "idea_verification": NeogenesisIdeaVerificationTool(
                search_engine=self.search_engine
            )
        }
        
        logger.info(f"🔧 初始化了 {len(self.tools)} 个工具")
    
    def create_execution_plan(self, 
                            context: ExecutionContext,
                            stages: List[DecisionStage] = None) -> List[ToolExecutionPlan]:
        """
        创建智能执行计划
        
        Args:
            context: 执行上下文
            stages: 要执行的阶段列表
            
        Returns:
            执行计划列表
        """
        if stages is None:
            stages = [
                DecisionStage.THINKING_SEED,
                DecisionStage.SEED_VERIFICATION,
                DecisionStage.PATH_GENERATION,
                DecisionStage.PATH_VERIFICATION,
                DecisionStage.MAB_DECISION
            ]
        
        execution_plan = []
        
        for i, stage in enumerate(stages):
            if stage == DecisionStage.THINKING_SEED:
                # 阶段一：思维种子生成
                plan = ToolExecutionPlan(
                    stage=stage,
                    tool_name="thinking_seed",
                    tool_instance=self.tools["thinking_seed"],
                    priority=ToolPriority.CRITICAL,
                    timeout=20.0,
                    execution_order=i * 10
                )
                execution_plan.append(plan)
                
            elif stage == DecisionStage.SEED_VERIFICATION:
                # 阶段二：种子验证（可选）
                if context.enable_verification:
                    plan = ToolExecutionPlan(
                        stage=stage,
                        tool_name="idea_verification",
                        tool_instance=self.tools["idea_verification"],
                        priority=ToolPriority.MEDIUM,
                        dependencies=["thinking_seed"],
                        timeout=15.0,
                        execution_order=i * 10
                    )
                    execution_plan.append(plan)
                    
            elif stage == DecisionStage.PATH_GENERATION:
                # 阶段三：路径生成
                plan = ToolExecutionPlan(
                    stage=stage,
                    tool_name="path_generator",
                    tool_instance=self.tools["path_generator"],
                    priority=ToolPriority.CRITICAL,
                    dependencies=["thinking_seed"],
                    timeout=25.0,
                    execution_order=i * 10
                )
                execution_plan.append(plan)
                
            elif stage == DecisionStage.PATH_VERIFICATION:
                # 阶段四：路径验证（可选）
                if context.enable_verification:
                    plan = ToolExecutionPlan(
                        stage=stage,
                        tool_name="idea_verification",
                        tool_instance=self.tools["idea_verification"],
                        priority=ToolPriority.HIGH,
                        dependencies=["path_generator"],
                        timeout=20.0,
                        execution_order=i * 10
                    )
                    execution_plan.append(plan)
                    
            elif stage == DecisionStage.MAB_DECISION:
                # 阶段五：MAB决策
                plan = ToolExecutionPlan(
                    stage=stage,
                    tool_name="mab_decision",
                    tool_instance=self.tools["mab_decision"],
                    priority=ToolPriority.CRITICAL,
                    dependencies=["path_generator"],
                    timeout=15.0,
                    execution_order=i * 10
                )
                execution_plan.append(plan)
        
        # 根据执行模式优化计划
        execution_plan = self._optimize_execution_plan(execution_plan, context)
        
        logger.info(f"📋 创建执行计划: {len(execution_plan)} 个工具，模式={context.execution_mode.value}")
        return execution_plan
    
    def _optimize_execution_plan(self, 
                                plan: List[ToolExecutionPlan],
                                context: ExecutionContext) -> List[ToolExecutionPlan]:
        """
        优化执行计划
        
        Args:
            plan: 原始执行计划
            context: 执行上下文
            
        Returns:
            优化后的执行计划
        """
        if context.execution_mode == ExecutionMode.PARALLEL:
            # 并行模式：标识可并行执行的工具
            for tool_plan in plan:
                if not tool_plan.dependencies:
                    tool_plan.execution_order = 0  # 可立即执行
                else:
                    tool_plan.execution_order = len(tool_plan.dependencies) * 10
                    
        elif context.execution_mode == ExecutionMode.ADAPTIVE:
            # 自适应模式：根据历史性能调整
            for tool_plan in plan:
                historical_performance = self.execution_stats.get("tool_performance", {}).get(
                    tool_plan.tool_name, {"avg_time": 10.0, "success_rate": 0.9}
                )
                
                # 根据历史性能调整超时时间
                tool_plan.timeout = max(
                    tool_plan.timeout,
                    historical_performance["avg_time"] * 1.5
                )
                
                # 根据成功率调整重试策略
                if historical_performance["success_rate"] < 0.8:
                    tool_plan.retry_enabled = True
                    tool_plan.fallback_tool = self._get_fallback_tool(tool_plan.tool_name)
        
        elif context.execution_mode == ExecutionMode.PIPELINE:
            # 流水线模式：优化执行顺序
            plan.sort(key=lambda x: (len(x.dependencies), x.execution_order))
        
        return plan
    
    def _get_fallback_tool(self, tool_name: str) -> Optional[str]:
        """获取工具的回退选项"""
        fallback_mapping = {
            "rag_seed": "thinking_seed",
            "idea_verification": None,  # 验证工具无回退，可跳过
            "mab_decision": None       # 决策工具关键，无回退
        }
        return fallback_mapping.get(tool_name)
    
    async def execute_plan_async(self, 
                                plan: List[ToolExecutionPlan],
                                context: ExecutionContext) -> Dict[str, ExecutionResult]:
        """
        异步执行计划
        
        Args:
            plan: 执行计划
            context: 执行上下文
            
        Returns:
            执行结果字典
        """
        results = {}
        execution_order_groups = {}
        
        # 按执行顺序分组
        for tool_plan in plan:
            order = tool_plan.execution_order
            if order not in execution_order_groups:
                execution_order_groups[order] = []
            execution_order_groups[order].append(tool_plan)
        
        # 按顺序执行每组
        for order in sorted(execution_order_groups.keys()):
            group = execution_order_groups[order]
            
            if context.execution_mode == ExecutionMode.PARALLEL and len(group) > 1:
                # 并行执行组内工具
                group_results = await self._execute_group_parallel(group, context, results)
            else:
                # 顺序执行组内工具
                group_results = await self._execute_group_sequential(group, context, results)
            
            results.update(group_results)
            
            # 检查关键工具是否成功
            critical_failed = any(
                not result.success for tool_plan in group
                for result in [results.get(tool_plan.tool_name)]
                if tool_plan.priority == ToolPriority.CRITICAL and result
            )
            
            if critical_failed and not context.fallback_enabled:
                logger.error("❌ 关键工具执行失败，终止执行")
                break
        
        return results
    
    async def _execute_group_parallel(self,
                                     group: List[ToolExecutionPlan],
                                     context: ExecutionContext,
                                     previous_results: Dict[str, ExecutionResult]) -> Dict[str, ExecutionResult]:
        """并行执行工具组"""
        tasks = []
        
        for tool_plan in group:
            if self._check_dependencies(tool_plan, previous_results):
                task = asyncio.create_task(
                    self._execute_single_tool_async(tool_plan, context, previous_results)
                )
                tasks.append((tool_plan.tool_name, task))
        
        results = {}
        for tool_name, task in tasks:
            try:
                result = await task
                results[tool_name] = result
            except Exception as e:
                logger.error(f"❌ 并行执行工具 {tool_name} 失败: {e}")
                results[tool_name] = ExecutionResult(
                    tool_name=tool_name,
                    stage=DecisionStage.ERROR,
                    success=False,
                    error_message=str(e)
                )
        
        return results
    
    async def _execute_group_sequential(self,
                                       group: List[ToolExecutionPlan],
                                       context: ExecutionContext,
                                       previous_results: Dict[str, ExecutionResult]) -> Dict[str, ExecutionResult]:
        """顺序执行工具组"""
        results = {}
        
        for tool_plan in group:
            if self._check_dependencies(tool_plan, previous_results):
                result = await self._execute_single_tool_async(tool_plan, context, previous_results)
                results[tool_plan.tool_name] = result
                
                # 如果关键工具失败，考虑回退
                if not result.success and tool_plan.priority == ToolPriority.CRITICAL:
                    fallback_result = await self._try_fallback(tool_plan, context, previous_results)
                    if fallback_result:
                        results[tool_plan.tool_name] = fallback_result
        
        return results
    
    async def _execute_single_tool_async(self,
                                        tool_plan: ToolExecutionPlan,
                                        context: ExecutionContext,
                                        previous_results: Dict[str, ExecutionResult]) -> ExecutionResult:
        """异步执行单个工具"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(tool_plan, context, previous_results)
            if context.enable_caching and cache_key in self.result_cache:
                cached_result = self.result_cache[cache_key]
                cached_result.cache_hit = True
                logger.debug(f"💾 缓存命中: {tool_plan.tool_name}")
                return cached_result
            
            # 准备工具输入
            tool_input = self._prepare_tool_input(tool_plan, context, previous_results)
            
            # 执行工具
            loop = asyncio.get_event_loop()
            result_data = await loop.run_in_executor(
                self.thread_pool,
                self._execute_tool_sync,
                tool_plan.tool_instance,
                tool_input
            )
            
            execution_time = time.time() - start_time
            
            # 创建执行结果
            result = ExecutionResult(
                tool_name=tool_plan.tool_name,
                stage=tool_plan.stage,
                success=True,
                data=result_data,
                execution_time=execution_time,
                metadata={
                    "input": tool_input,
                    "timeout": tool_plan.timeout,
                    "priority": tool_plan.priority.value
                }
            )
            
            # 缓存结果
            if context.enable_caching:
                self.result_cache[cache_key] = result
            
            # 更新状态管理器
            if self.state_manager:
                self.state_manager.update_session_stage(
                    session_id=context.session_id,
                    stage=tool_plan.stage,
                    success=True,
                    data={"tool_result": result_data},
                    execution_time=execution_time
                )
            
            self._update_performance_stats(tool_plan.tool_name, execution_time, True)
            
            logger.info(f"✅ 工具执行成功: {tool_plan.tool_name} ({execution_time:.2f}s)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ 工具执行失败: {tool_plan.tool_name} - {error_msg}")
            
            result = ExecutionResult(
                tool_name=tool_plan.tool_name,
                stage=tool_plan.stage,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
            
            # 更新状态管理器
            if self.state_manager:
                self.state_manager.update_session_stage(
                    session_id=context.session_id,
                    stage=tool_plan.stage,
                    success=False,
                    data={"error": error_msg},
                    execution_time=execution_time,
                    error_message=error_msg
                )
            
            self._update_performance_stats(tool_plan.tool_name, execution_time, False)
            
            return result
    
    def _execute_tool_sync(self, tool_instance, tool_input: Dict[str, Any]) -> Any:
        """同步执行工具（在线程池中运行）"""
        return tool_instance.run(**tool_input)
    
    def _check_dependencies(self, 
                          tool_plan: ToolExecutionPlan,
                          previous_results: Dict[str, ExecutionResult]) -> bool:
        """检查工具依赖是否满足"""
        for dependency in tool_plan.dependencies:
            if dependency not in previous_results:
                logger.warning(f"⚠️ 依赖未满足: {tool_plan.tool_name} 需要 {dependency}")
                return False
            
            if not previous_results[dependency].success:
                logger.warning(f"⚠️ 依赖失败: {dependency} 执行失败，影响 {tool_plan.tool_name}")
                if tool_plan.priority == ToolPriority.CRITICAL:
                    return False
        
        return True
    
    def _prepare_tool_input(self,
                          tool_plan: ToolExecutionPlan,
                          context: ExecutionContext,
                          previous_results: Dict[str, ExecutionResult]) -> Dict[str, Any]:
        """准备工具输入参数"""
        tool_input = {
            "execution_context": context.custom_config
        }
        
        if tool_plan.tool_name == "thinking_seed":
            tool_input.update({
                "user_query": context.user_query,
                "execution_context": context.custom_config
            })
            
        elif tool_plan.tool_name == "rag_seed":
            tool_input.update({
                "user_query": context.user_query,
                "execution_context": context.custom_config
            })
            
        elif tool_plan.tool_name == "path_generator":
            # 需要思维种子
            seed_result = previous_results.get("thinking_seed") or previous_results.get("rag_seed")
            if seed_result and seed_result.success:
                try:
                    seed_data = json.loads(seed_result.data) if isinstance(seed_result.data, str) else seed_result.data
                    thinking_seed = seed_data.get("thinking_seed") or seed_data.get("rag_enhanced_seed", "")
                except:
                    thinking_seed = str(seed_result.data)
                
                tool_input.update({
                    "thinking_seed": thinking_seed,
                    "task": context.user_query,
                    "max_paths": context.custom_config.get("max_paths", 4)
                })
            
        elif tool_plan.tool_name == "mab_decision":
            # 需要思维路径
            path_result = previous_results.get("path_generator")
            if path_result and path_result.success:
                try:
                    path_data = json.loads(path_result.data) if isinstance(path_result.data, str) else path_result.data
                    reasoning_paths = path_data.get("reasoning_paths", [])
                except:
                    reasoning_paths = []
                
                tool_input.update({
                    "reasoning_paths": reasoning_paths,
                    "user_query": context.user_query,
                    "execution_context": context.custom_config
                })
                
        elif tool_plan.tool_name == "idea_verification":
            # 根据阶段确定验证内容
            if tool_plan.stage == DecisionStage.SEED_VERIFICATION:
                seed_result = previous_results.get("thinking_seed") or previous_results.get("rag_seed")
                if seed_result and seed_result.success:
                    try:
                        seed_data = json.loads(seed_result.data) if isinstance(seed_result.data, str) else seed_result.data
                        idea_text = seed_data.get("thinking_seed") or seed_data.get("rag_enhanced_seed", "")
                    except:
                        idea_text = str(seed_result.data)
                    
                    tool_input.update({
                        "idea_text": idea_text,
                        "context": {"stage": "thinking_seed", "query": context.user_query}
                    })
                    
            elif tool_plan.stage == DecisionStage.PATH_VERIFICATION:
                path_result = previous_results.get("path_generator")
                if path_result and path_result.success:
                    try:
                        path_data = json.loads(path_result.data) if isinstance(path_result.data, str) else path_result.data
                        reasoning_paths = path_data.get("reasoning_paths", [])
                        if reasoning_paths:
                            # 验证第一个路径作为示例
                            first_path = reasoning_paths[0]
                            idea_text = f"{first_path.get('path_type', '')}: {first_path.get('description', '')}"
                            
                            tool_input.update({
                                "idea_text": idea_text,
                                "context": {"stage": "reasoning_path", "query": context.user_query}
                            })
                    except:
                        pass
        
        return tool_input
    
    async def _try_fallback(self,
                          failed_plan: ToolExecutionPlan,
                          context: ExecutionContext,
                          previous_results: Dict[str, ExecutionResult]) -> Optional[ExecutionResult]:
        """尝试回退策略"""
        if not failed_plan.fallback_tool or not context.fallback_enabled:
            return None
        
        fallback_tool = self.tools.get(failed_plan.fallback_tool)
        if not fallback_tool:
            return None
        
        logger.info(f"🔄 尝试回退: {failed_plan.tool_name} -> {failed_plan.fallback_tool}")
        
        try:
            # 创建回退执行计划
            fallback_plan = ToolExecutionPlan(
                stage=failed_plan.stage,
                tool_name=failed_plan.fallback_tool,
                tool_instance=fallback_tool,
                priority=ToolPriority.HIGH,
                timeout=failed_plan.timeout * 0.8  # 缩短超时时间
            )
            
            result = await self._execute_single_tool_async(fallback_plan, context, previous_results)
            
            if result.success:
                logger.info(f"✅ 回退成功: {failed_plan.fallback_tool}")
                result.metadata["fallback_from"] = failed_plan.tool_name
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 回退失败: {e}")
            return None
    
    def _generate_cache_key(self,
                          tool_plan: ToolExecutionPlan,
                          context: ExecutionContext,
                          previous_results: Dict[str, ExecutionResult]) -> str:
        """生成缓存键"""
        key_components = [
            tool_plan.tool_name,
            context.user_query,
            str(context.custom_config),
            str([r.data for r in previous_results.values() if r.success])
        ]
        return f"cache_{hash('_'.join(key_components))}"
    
    def _update_performance_stats(self, tool_name: str, execution_time: float, success: bool):
        """更新性能统计"""
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        self.execution_stats["total_execution_time"] += execution_time
        
        # 工具级统计
        if tool_name not in self.execution_stats["tool_performance"]:
            self.execution_stats["tool_performance"][tool_name] = {
                "executions": 0,
                "successes": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "success_rate": 0.0
            }
        
        tool_stats = self.execution_stats["tool_performance"][tool_name]
        tool_stats["executions"] += 1
        tool_stats["total_time"] += execution_time
        
        if success:
            tool_stats["successes"] += 1
        
        tool_stats["avg_time"] = tool_stats["total_time"] / tool_stats["executions"]
        tool_stats["success_rate"] = tool_stats["successes"] / tool_stats["executions"]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "summary": self.execution_stats,
            "cache_efficiency": {
                "cache_size": len(self.result_cache),
                "cache_hit_rate": self.execution_stats.get("cache_hits", 0) / max(self.execution_stats["total_executions"], 1)
            },
            "tool_rankings": sorted(
                self.execution_stats["tool_performance"].items(),
                key=lambda x: x[1]["success_rate"],
                reverse=True
            )
        }

# =============================================================================
# 性能优化器
# =============================================================================

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.optimization_history = []
        self.performance_thresholds = {
            "max_execution_time": 60.0,
            "min_success_rate": 0.8,
            "max_cache_size": 1000
        }
    
    def analyze_performance(self, coordinator: NeogenesisToolCoordinator) -> Dict[str, Any]:
        """分析性能并提供优化建议"""
        report = coordinator.get_performance_report()
        
        recommendations = []
        
        # 分析执行时间
        avg_time = coordinator.execution_stats["total_execution_time"] / max(
            coordinator.execution_stats["total_executions"], 1
        )
        
        if avg_time > self.performance_thresholds["max_execution_time"]:
            recommendations.append({
                "type": "execution_time",
                "message": f"平均执行时间过长: {avg_time:.2f}s",
                "suggestion": "考虑启用并行执行或增加缓存"
            })
        
        # 分析成功率
        success_rate = coordinator.execution_stats["successful_executions"] / max(
            coordinator.execution_stats["total_executions"], 1
        )
        
        if success_rate < self.performance_thresholds["min_success_rate"]:
            recommendations.append({
                "type": "success_rate",
                "message": f"成功率偏低: {success_rate:.1%}",
                "suggestion": "检查工具配置或启用回退机制"
            })
        
        # 分析缓存效率
        if len(coordinator.result_cache) > self.performance_thresholds["max_cache_size"]:
            recommendations.append({
                "type": "cache_size",
                "message": "缓存大小超限",
                "suggestion": "清理旧缓存或调整缓存策略"
            })
        
        return {
            "performance_metrics": report,
            "recommendations": recommendations,
            "optimization_score": self._calculate_optimization_score(report)
        }
    
    def _calculate_optimization_score(self, report: Dict[str, Any]) -> float:
        """计算优化分数（0-100）"""
        stats = report["summary"]
        
        # 成功率权重40%
        success_rate = stats["successful_executions"] / max(stats["total_executions"], 1)
        success_score = success_rate * 40
        
        # 平均执行时间权重30%
        avg_time = stats["total_execution_time"] / max(stats["total_executions"], 1)
        time_score = max(0, (60 - avg_time) / 60) * 30
        
        # 缓存命中率权重30%
        cache_hit_rate = report["cache_efficiency"]["cache_hit_rate"]
        cache_score = cache_hit_rate * 30
        
        return success_score + time_score + cache_score

if __name__ == "__main__":
    # 测试协调器
    print("🧪 测试Neogenesis工具协调器...")
    
    # 创建协调器
    coordinator = NeogenesisToolCoordinator(api_key="test_key")
    
    # 创建执行上下文
    context = ExecutionContext(
        session_id="test_session",
        user_query="设计一个Web应用架构",
        execution_mode=ExecutionMode.ADAPTIVE
    )
    
    # 创建执行计划
    plan = coordinator.create_execution_plan(context)
    print(f"✅ 创建执行计划: {len(plan)} 个工具")
    
    # 模拟异步执行
    async def test_execution():
        results = await coordinator.execute_plan_async(plan, context)
        print(f"✅ 执行完成: {len(results)} 个结果")
        
        # 获取性能报告
        report = coordinator.get_performance_report()
        print(f"📊 性能报告: {report}")
    
    # 运行测试
    try:
        asyncio.run(test_execution())
        print("✅ 协调器测试完成")
    except Exception as e:
        print(f"❌ 协调器测试失败: {e}")
