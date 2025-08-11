#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - Execution Engines
智能执行引擎：高级工具执行策略和优化
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import threading
from collections import defaultdict, deque
import heapq

from .coordinators import (
    ExecutionContext,
    ExecutionMode,
    ToolExecutionPlan,
    ExecutionResult,
    ToolPriority
)

logger = logging.getLogger(__name__)

# =============================================================================
# 执行策略和算法
# =============================================================================

class ExecutionStrategy(Enum):
    """执行策略枚举"""
    ROUND_ROBIN = "round_robin"           # 轮询执行
    PRIORITY_QUEUE = "priority_queue"     # 优先级队列
    DEPENDENCY_GRAPH = "dependency_graph" # 依赖图拓扑排序
    LOAD_BALANCED = "load_balanced"       # 负载均衡
    CRITICAL_PATH = "critical_path"       # 关键路径优先
    ADAPTIVE_BATCH = "adaptive_batch"     # 自适应批处理

class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    API_QUOTA = "api_quota"
    CACHE = "cache"

@dataclass
class ResourceConstraint:
    """资源约束"""
    resource_type: ResourceType
    max_usage: float
    current_usage: float = 0.0
    allocation_strategy: str = "fair"  # fair, priority, greedy

@dataclass
class ExecutionNode:
    """执行节点"""
    plan: ToolExecutionPlan
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    estimated_duration: float = 10.0
    resource_requirements: Dict[ResourceType, float] = field(default_factory=dict)
    scheduling_priority: float = 0.0

@dataclass
class ExecutionBatch:
    """执行批次"""
    batch_id: str
    nodes: List[ExecutionNode]
    estimated_total_time: float
    resource_usage: Dict[ResourceType, float] = field(default_factory=dict)
    can_parallel: bool = True

# =============================================================================
# 智能执行引擎
# =============================================================================

class SmartExecutionEngine:
    """
    智能执行引擎
    
    功能：
    - 依赖关系分析和拓扑排序
    - 资源管理和约束检查
    - 智能批处理和调度
    - 动态负载均衡
    - 执行性能优化
    """
    
    def __init__(self,
                 max_parallel_workers: int = 4,
                 enable_resource_management: bool = True,
                 enable_smart_scheduling: bool = True):
        """
        初始化智能执行引擎
        
        Args:
            max_parallel_workers: 最大并行工作线程数
            enable_resource_management: 是否启用资源管理
            enable_smart_scheduling: 是否启用智能调度
        """
        self.max_parallel_workers = max_parallel_workers
        self.enable_resource_management = enable_resource_management
        self.enable_smart_scheduling = enable_smart_scheduling
        
        # 执行器
        self.thread_pool = ThreadPoolExecutor(max_workers=max_parallel_workers)
        
        # 资源管理
        self.resource_constraints = {
            ResourceType.CPU: ResourceConstraint(ResourceType.CPU, max_usage=1.0),
            ResourceType.MEMORY: ResourceConstraint(ResourceType.MEMORY, max_usage=1024.0),  # MB
            ResourceType.NETWORK: ResourceConstraint(ResourceType.NETWORK, max_usage=10.0),  # requests/sec
            ResourceType.API_QUOTA: ResourceConstraint(ResourceType.API_QUOTA, max_usage=100.0),  # calls/min
        }
        
        # 调度器
        self.scheduler = IntelligentScheduler()
        self.dependency_analyzer = DependencyAnalyzer()
        self.performance_tracker = PerformanceTracker()
        
        # 执行状态
        self.active_executions = {}
        self.execution_history = deque(maxlen=1000)
        self.resource_allocations = defaultdict(float)
        
        logger.info("🚀 SmartExecutionEngine 初始化完成")
    
    async def execute_optimized_plan(self,
                                   execution_plans: List[ToolExecutionPlan],
                                   context: ExecutionContext) -> Dict[str, ExecutionResult]:
        """
        执行优化的执行计划
        
        Args:
            execution_plans: 执行计划列表
            context: 执行上下文
            
        Returns:
            执行结果字典
        """
        logger.info(f"🎯 开始优化执行: {len(execution_plans)} 个工具")
        
        try:
            # 1. 构建执行图
            execution_graph = self._build_execution_graph(execution_plans, context)
            
            # 2. 依赖分析
            dependency_order = self.dependency_analyzer.analyze_dependencies(execution_graph)
            
            # 3. 智能调度
            execution_batches = self.scheduler.create_execution_batches(
                execution_graph, dependency_order, context
            )
            
            # 4. 资源分配
            if self.enable_resource_management:
                execution_batches = self._allocate_resources(execution_batches)
            
            # 5. 执行批次
            results = await self._execute_batches(execution_batches, context)
            
            # 6. 性能跟踪
            self.performance_tracker.record_execution(execution_plans, results, context)
            
            logger.info(f"✅ 优化执行完成: {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 优化执行失败: {e}")
            # 回退到简单执行
            return await self._fallback_execution(execution_plans, context)
    
    def _build_execution_graph(self,
                             execution_plans: List[ToolExecutionPlan],
                             context: ExecutionContext) -> Dict[str, ExecutionNode]:
        """构建执行图"""
        graph = {}
        
        for plan in execution_plans:
            # 估算执行时间
            estimated_duration = self._estimate_execution_time(plan, context)
            
            # 估算资源需求
            resource_requirements = self._estimate_resource_requirements(plan, context)
            
            # 计算调度优先级
            scheduling_priority = self._calculate_scheduling_priority(plan, context)
            
            # 创建执行节点
            node = ExecutionNode(
                plan=plan,
                dependencies=set(plan.dependencies),
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements,
                scheduling_priority=scheduling_priority
            )
            
            graph[plan.tool_name] = node
        
        # 建立依赖关系
        for tool_name, node in graph.items():
            for dep_name in node.dependencies:
                if dep_name in graph:
                    graph[dep_name].dependents.add(tool_name)
        
        logger.info(f"📊 构建执行图: {len(graph)} 个节点")
        return graph
    
    def _estimate_execution_time(self, plan: ToolExecutionPlan, context: ExecutionContext) -> float:
        """估算执行时间"""
        # 基础时间估算
        base_times = {
            "thinking_seed": 8.0,
            "rag_seed": 15.0,
            "path_generator": 12.0,
            "mab_decision": 6.0,
            "idea_verification": 10.0
        }
        
        base_time = base_times.get(plan.tool_name, 10.0)
        
        # 根据历史性能调整
        historical_avg = self.performance_tracker.get_average_execution_time(plan.tool_name)
        if historical_avg > 0:
            base_time = (base_time + historical_avg) / 2
        
        # 根据查询复杂度调整
        query_complexity = len(context.user_query) / 100.0
        complexity_factor = min(2.0, 1.0 + query_complexity * 0.5)
        
        return base_time * complexity_factor
    
    def _estimate_resource_requirements(self,
                                      plan: ToolExecutionPlan,
                                      context: ExecutionContext) -> Dict[ResourceType, float]:
        """估算资源需求"""
        requirements = {}
        
        # CPU需求
        cpu_intensive_tools = {"path_generator", "mab_decision"}
        if plan.tool_name in cpu_intensive_tools:
            requirements[ResourceType.CPU] = 0.3
        else:
            requirements[ResourceType.CPU] = 0.1
        
        # 内存需求
        memory_intensive_tools = {"rag_seed", "path_generator"}
        if plan.tool_name in memory_intensive_tools:
            requirements[ResourceType.MEMORY] = 50.0  # MB
        else:
            requirements[ResourceType.MEMORY] = 20.0
        
        # 网络需求
        network_intensive_tools = {"rag_seed", "idea_verification"}
        if plan.tool_name in network_intensive_tools:
            requirements[ResourceType.NETWORK] = 2.0  # requests/sec
        else:
            requirements[ResourceType.NETWORK] = 0.5
        
        # API配额需求
        api_intensive_tools = {"thinking_seed", "rag_seed", "path_generator", "mab_decision"}
        if plan.tool_name in api_intensive_tools:
            requirements[ResourceType.API_QUOTA] = 5.0  # calls/min
        else:
            requirements[ResourceType.API_QUOTA] = 1.0
        
        return requirements
    
    def _calculate_scheduling_priority(self,
                                     plan: ToolExecutionPlan,
                                     context: ExecutionContext) -> float:
        """计算调度优先级"""
        priority_score = 0.0
        
        # 工具优先级权重
        priority_weights = {
            ToolPriority.CRITICAL: 100.0,
            ToolPriority.HIGH: 75.0,
            ToolPriority.MEDIUM: 50.0,
            ToolPriority.LOW: 25.0,
            ToolPriority.OPTIONAL: 10.0
        }
        
        priority_score += priority_weights.get(plan.priority, 50.0)
        
        # 依赖数量权重（依赖少的优先）
        dependency_penalty = len(plan.dependencies) * 10.0
        priority_score -= dependency_penalty
        
        # 执行时间权重（时间短的优先）
        estimated_time = self._estimate_execution_time(plan, context)
        time_bonus = max(0, 20.0 - estimated_time)
        priority_score += time_bonus
        
        # 历史成功率权重
        success_rate = self.performance_tracker.get_success_rate(plan.tool_name)
        success_bonus = success_rate * 20.0
        priority_score += success_bonus
        
        return priority_score
    
    def _allocate_resources(self, execution_batches: List[ExecutionBatch]) -> List[ExecutionBatch]:
        """分配资源"""
        allocated_batches = []
        
        for batch in execution_batches:
            # 检查资源约束
            if self._check_resource_availability(batch):
                # 分配资源
                self._allocate_batch_resources(batch)
                allocated_batches.append(batch)
            else:
                # 资源不足，拆分批次
                split_batches = self._split_batch(batch)
                allocated_batches.extend(split_batches)
        
        return allocated_batches
    
    def _check_resource_availability(self, batch: ExecutionBatch) -> bool:
        """检查资源可用性"""
        for resource_type, required in batch.resource_usage.items():
            constraint = self.resource_constraints[resource_type]
            if constraint.current_usage + required > constraint.max_usage:
                logger.debug(f"⚠️ 资源不足: {resource_type.value} 需要 {required}, 可用 {constraint.max_usage - constraint.current_usage}")
                return False
        return True
    
    def _allocate_batch_resources(self, batch: ExecutionBatch):
        """分配批次资源"""
        for resource_type, required in batch.resource_usage.items():
            self.resource_constraints[resource_type].current_usage += required
            self.resource_allocations[f"{batch.batch_id}_{resource_type.value}"] = required
    
    def _split_batch(self, batch: ExecutionBatch) -> List[ExecutionBatch]:
        """拆分批次"""
        # 简单策略：按优先级分组
        high_priority_nodes = [node for node in batch.nodes if node.plan.priority in [ToolPriority.CRITICAL, ToolPriority.HIGH]]
        low_priority_nodes = [node for node in batch.nodes if node.plan.priority not in [ToolPriority.CRITICAL, ToolPriority.HIGH]]
        
        split_batches = []
        
        if high_priority_nodes:
            high_batch = ExecutionBatch(
                batch_id=f"{batch.batch_id}_high",
                nodes=high_priority_nodes,
                estimated_total_time=sum(node.estimated_duration for node in high_priority_nodes)
            )
            split_batches.append(high_batch)
        
        if low_priority_nodes:
            low_batch = ExecutionBatch(
                batch_id=f"{batch.batch_id}_low",
                nodes=low_priority_nodes,
                estimated_total_time=sum(node.estimated_duration for node in low_priority_nodes)
            )
            split_batches.append(low_batch)
        
        return split_batches
    
    async def _execute_batches(self,
                             execution_batches: List[ExecutionBatch],
                             context: ExecutionContext) -> Dict[str, ExecutionResult]:
        """执行批次"""
        results = {}
        
        for batch in execution_batches:
            logger.info(f"🔄 执行批次: {batch.batch_id} ({len(batch.nodes)} 个工具)")
            
            if batch.can_parallel and len(batch.nodes) > 1:
                # 并行执行
                batch_results = await self._execute_batch_parallel(batch, context, results)
            else:
                # 顺序执行
                batch_results = await self._execute_batch_sequential(batch, context, results)
            
            results.update(batch_results)
            
            # 释放资源
            self._release_batch_resources(batch)
        
        return results
    
    async def _execute_batch_parallel(self,
                                    batch: ExecutionBatch,
                                    context: ExecutionContext,
                                    previous_results: Dict[str, ExecutionResult]) -> Dict[str, ExecutionResult]:
        """并行执行批次"""
        tasks = []
        
        for node in batch.nodes:
            task = asyncio.create_task(
                self._execute_single_node(node, context, previous_results)
            )
            tasks.append((node.plan.tool_name, task))
        
        results = {}
        for tool_name, task in tasks:
            try:
                result = await task
                results[tool_name] = result
            except Exception as e:
                logger.error(f"❌ 并行执行节点失败: {tool_name} - {e}")
                results[tool_name] = ExecutionResult(
                    tool_name=tool_name,
                    stage=batch.nodes[0].plan.stage,  # 使用第一个节点的阶段
                    success=False,
                    error_message=str(e)
                )
        
        return results
    
    async def _execute_batch_sequential(self,
                                      batch: ExecutionBatch,
                                      context: ExecutionContext,
                                      previous_results: Dict[str, ExecutionResult]) -> Dict[str, ExecutionResult]:
        """顺序执行批次"""
        results = {}
        
        for node in batch.nodes:
            result = await self._execute_single_node(node, context, previous_results)
            results[node.plan.tool_name] = result
            
            # 更新之前的结果，供后续节点使用
            previous_results[node.plan.tool_name] = result
        
        return results
    
    async def _execute_single_node(self,
                                 node: ExecutionNode,
                                 context: ExecutionContext,
                                 previous_results: Dict[str, ExecutionResult]) -> ExecutionResult:
        """执行单个节点"""
        start_time = time.time()
        
        try:
            # 准备工具输入（需要协调器的方法）
            tool_input = self._prepare_node_input(node, context, previous_results)
            
            # 执行工具
            loop = asyncio.get_event_loop()
            result_data = await loop.run_in_executor(
                self.thread_pool,
                node.plan.tool_instance.run,
                **tool_input
            )
            
            execution_time = time.time() - start_time
            
            result = ExecutionResult(
                tool_name=node.plan.tool_name,
                stage=node.plan.stage,
                success=True,
                data=result_data,
                execution_time=execution_time,
                metadata={
                    "node_priority": node.scheduling_priority,
                    "estimated_duration": node.estimated_duration,
                    "actual_duration": execution_time
                }
            )
            
            logger.info(f"✅ 节点执行成功: {node.plan.tool_name} ({execution_time:.2f}s)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ 节点执行失败: {node.plan.tool_name} - {error_msg}")
            
            return ExecutionResult(
                tool_name=node.plan.tool_name,
                stage=node.plan.stage,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def _prepare_node_input(self,
                          node: ExecutionNode,
                          context: ExecutionContext,
                          previous_results: Dict[str, ExecutionResult]) -> Dict[str, Any]:
        """准备节点输入（简化版本）"""
        # 这里应该与协调器的_prepare_tool_input方法保持一致
        # 为了简化，这里提供基础实现
        
        tool_input = {
            "execution_context": context.custom_config
        }
        
        if node.plan.tool_name == "thinking_seed":
            tool_input.update({
                "user_query": context.user_query,
                "execution_context": context.custom_config
            })
        elif node.plan.tool_name == "rag_seed":
            tool_input.update({
                "user_query": context.user_query,
                "execution_context": context.custom_config
            })
        # 其他工具的输入准备逻辑...
        
        return tool_input
    
    def _release_batch_resources(self, batch: ExecutionBatch):
        """释放批次资源"""
        for resource_type, allocated in batch.resource_usage.items():
            self.resource_constraints[resource_type].current_usage -= allocated
            allocation_key = f"{batch.batch_id}_{resource_type.value}"
            if allocation_key in self.resource_allocations:
                del self.resource_allocations[allocation_key]
    
    async def _fallback_execution(self,
                                execution_plans: List[ToolExecutionPlan],
                                context: ExecutionContext) -> Dict[str, ExecutionResult]:
        """回退执行方案"""
        logger.warning("🔄 使用回退执行方案")
        
        results = {}
        
        for plan in execution_plans:
            try:
                # 检查依赖
                dependencies_met = all(
                    dep in results and results[dep].success
                    for dep in plan.dependencies
                )
                
                if not dependencies_met and plan.dependencies:
                    logger.warning(f"⚠️ 跳过工具 {plan.tool_name}：依赖未满足")
                    continue
                
                # 简单执行
                start_time = time.time()
                result_data = plan.tool_instance.run()  # 简化调用
                execution_time = time.time() - start_time
                
                result = ExecutionResult(
                    tool_name=plan.tool_name,
                    stage=plan.stage,
                    success=True,
                    data=result_data,
                    execution_time=execution_time
                )
                
                results[plan.tool_name] = result
                
            except Exception as e:
                logger.error(f"❌ 回退执行失败: {plan.tool_name} - {e}")
                result = ExecutionResult(
                    tool_name=plan.tool_name,
                    stage=plan.stage,
                    success=False,
                    error_message=str(e),
                    execution_time=0.0
                )
                results[plan.tool_name] = result
        
        return results

# =============================================================================
# 依赖分析器
# =============================================================================

class DependencyAnalyzer:
    """依赖关系分析器"""
    
    def analyze_dependencies(self, execution_graph: Dict[str, ExecutionNode]) -> List[List[str]]:
        """
        分析依赖关系，返回拓扑排序结果
        
        Args:
            execution_graph: 执行图
            
        Returns:
            按依赖顺序分组的工具名称列表
        """
        # 拓扑排序
        in_degree = {}
        for tool_name, node in execution_graph.items():
            in_degree[tool_name] = len(node.dependencies)
        
        # 找到没有依赖的节点
        queue = [tool_name for tool_name, degree in in_degree.items() if degree == 0]
        ordered_groups = []
        
        while queue:
            # 当前层的所有无依赖节点
            current_level = queue[:]
            queue.clear()
            ordered_groups.append(current_level)
            
            # 处理当前层的节点
            for tool_name in current_level:
                node = execution_graph[tool_name]
                # 减少依赖此节点的其他节点的入度
                for dependent in node.dependents:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        logger.info(f"📊 依赖分析完成: {len(ordered_groups)} 层，{sum(len(group) for group in ordered_groups)} 个节点")
        return ordered_groups

# =============================================================================
# 智能调度器
# =============================================================================

class IntelligentScheduler:
    """智能调度器"""
    
    def create_execution_batches(self,
                                execution_graph: Dict[str, ExecutionNode],
                                dependency_order: List[List[str]],
                                context: ExecutionContext) -> List[ExecutionBatch]:
        """
        创建执行批次
        
        Args:
            execution_graph: 执行图
            dependency_order: 依赖顺序
            context: 执行上下文
            
        Returns:
            执行批次列表
        """
        batches = []
        
        for level_idx, tool_names in enumerate(dependency_order):
            if not tool_names:
                continue
            
            nodes = [execution_graph[tool_name] for tool_name in tool_names]
            
            # 根据执行模式决定批次策略
            if context.execution_mode == ExecutionMode.PARALLEL:
                # 并行模式：同层节点放在一个批次
                batch = ExecutionBatch(
                    batch_id=f"parallel_batch_level_{level_idx}",
                    nodes=nodes,
                    estimated_total_time=max(node.estimated_duration for node in nodes),
                    can_parallel=True
                )
                batches.append(batch)
                
            elif context.execution_mode == ExecutionMode.SEQUENTIAL:
                # 顺序模式：每个节点一个批次
                for node_idx, node in enumerate(nodes):
                    batch = ExecutionBatch(
                        batch_id=f"sequential_batch_level_{level_idx}_node_{node_idx}",
                        nodes=[node],
                        estimated_total_time=node.estimated_duration,
                        can_parallel=False
                    )
                    batches.append(batch)
                    
            else:  # ADAPTIVE
                # 自适应模式：根据节点特征智能分组
                adaptive_batches = self._create_adaptive_batches(nodes, level_idx)
                batches.extend(adaptive_batches)
        
        # 计算批次资源使用
        for batch in batches:
            batch.resource_usage = self._calculate_batch_resource_usage(batch)
        
        logger.info(f"📋 创建执行批次: {len(batches)} 个批次")
        return batches
    
    def _create_adaptive_batches(self,
                               nodes: List[ExecutionNode],
                               level_idx: int) -> List[ExecutionBatch]:
        """创建自适应批次"""
        # 按优先级和估算时间分组
        high_priority_fast = []
        high_priority_slow = []
        low_priority = []
        
        for node in nodes:
            if node.plan.priority in [ToolPriority.CRITICAL, ToolPriority.HIGH]:
                if node.estimated_duration <= 10.0:
                    high_priority_fast.append(node)
                else:
                    high_priority_slow.append(node)
            else:
                low_priority.append(node)
        
        batches = []
        
        # 高优先级快速任务 - 并行执行
        if high_priority_fast:
            batch = ExecutionBatch(
                batch_id=f"adaptive_high_fast_level_{level_idx}",
                nodes=high_priority_fast,
                estimated_total_time=max(node.estimated_duration for node in high_priority_fast),
                can_parallel=True
            )
            batches.append(batch)
        
        # 高优先级慢速任务 - 顺序执行
        for idx, node in enumerate(high_priority_slow):
            batch = ExecutionBatch(
                batch_id=f"adaptive_high_slow_level_{level_idx}_node_{idx}",
                nodes=[node],
                estimated_total_time=node.estimated_duration,
                can_parallel=False
            )
            batches.append(batch)
        
        # 低优先级任务 - 并行执行
        if low_priority:
            batch = ExecutionBatch(
                batch_id=f"adaptive_low_level_{level_idx}",
                nodes=low_priority,
                estimated_total_time=max(node.estimated_duration for node in low_priority),
                can_parallel=True
            )
            batches.append(batch)
        
        return batches
    
    def _calculate_batch_resource_usage(self, batch: ExecutionBatch) -> Dict[ResourceType, float]:
        """计算批次资源使用"""
        resource_usage = defaultdict(float)
        
        if batch.can_parallel:
            # 并行执行：取最大值
            for node in batch.nodes:
                for resource_type, requirement in node.resource_requirements.items():
                    resource_usage[resource_type] = max(resource_usage[resource_type], requirement)
        else:
            # 顺序执行：取平均值
            node_count = len(batch.nodes)
            for node in batch.nodes:
                for resource_type, requirement in node.resource_requirements.items():
                    resource_usage[resource_type] += requirement / node_count
        
        return dict(resource_usage)

# =============================================================================
# 性能跟踪器
# =============================================================================

class PerformanceTracker:
    """性能跟踪器"""
    
    def __init__(self):
        self.execution_history = []
        self.tool_stats = defaultdict(lambda: {
            "executions": 0,
            "successes": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "success_rate": 0.0
        })
    
    def record_execution(self,
                        execution_plans: List[ToolExecutionPlan],
                        results: Dict[str, ExecutionResult],
                        context: ExecutionContext):
        """记录执行性能"""
        execution_record = {
            "timestamp": time.time(),
            "context": context,
            "plans": execution_plans,
            "results": results,
            "total_time": sum(r.execution_time for r in results.values()),
            "success_count": sum(1 for r in results.values() if r.success)
        }
        
        self.execution_history.append(execution_record)
        
        # 更新工具统计
        for tool_name, result in results.items():
            stats = self.tool_stats[tool_name]
            stats["executions"] += 1
            stats["total_time"] += result.execution_time
            
            if result.success:
                stats["successes"] += 1
            
            stats["avg_time"] = stats["total_time"] / stats["executions"]
            stats["success_rate"] = stats["successes"] / stats["executions"]
    
    def get_average_execution_time(self, tool_name: str) -> float:
        """获取工具平均执行时间"""
        return self.tool_stats[tool_name]["avg_time"]
    
    def get_success_rate(self, tool_name: str) -> float:
        """获取工具成功率"""
        return self.tool_stats[tool_name]["success_rate"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        return {
            "total_executions": len(self.execution_history),
            "tool_stats": dict(self.tool_stats),
            "recent_performance": self.execution_history[-10:] if self.execution_history else []
        }

# =============================================================================
# 测试和演示
# =============================================================================

if __name__ == "__main__":
    # 测试智能执行引擎
    print("🧪 测试智能执行引擎...")
    
    # 创建执行引擎
    engine = SmartExecutionEngine(
        max_parallel_workers=4,
        enable_resource_management=True,
        enable_smart_scheduling=True
    )
    
    print("✅ 智能执行引擎创建成功")
    
    # 创建模拟执行计划
    from .coordinators import ToolExecutionPlan, DecisionStage, ToolPriority
    
    mock_plans = [
        ToolExecutionPlan(
            stage=DecisionStage.THINKING_SEED,
            tool_name="thinking_seed",
            tool_instance=None,  # 模拟
            priority=ToolPriority.CRITICAL
        ),
        ToolExecutionPlan(
            stage=DecisionStage.PATH_GENERATION,
            tool_name="path_generator",
            tool_instance=None,
            priority=ToolPriority.HIGH,
            dependencies=["thinking_seed"]
        )
    ]
    
    # 创建执行上下文
    mock_context = ExecutionContext(
        session_id="test_session",
        user_query="测试查询",
        execution_mode=ExecutionMode.ADAPTIVE
    )
    
    # 构建执行图
    execution_graph = engine._build_execution_graph(mock_plans, mock_context)
    print(f"✅ 构建执行图: {len(execution_graph)} 个节点")
    
    # 依赖分析
    dependency_order = engine.dependency_analyzer.analyze_dependencies(execution_graph)
    print(f"✅ 依赖分析: {len(dependency_order)} 层")
    
    # 创建执行批次
    execution_batches = engine.scheduler.create_execution_batches(
        execution_graph, dependency_order, mock_context
    )
    print(f"✅ 创建批次: {len(execution_batches)} 个批次")
    
    print("✅ 智能执行引擎测试完成")
