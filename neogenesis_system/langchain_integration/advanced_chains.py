#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - Advanced Chains
高级决策链：智能协调的五阶段决策流程
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

try:
    from langchain.chains.base import Chain
    from langchain.callbacks.manager import CallbackManagerForChainRun
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    
    class BaseModel:
        pass
    
    class Chain:
        input_keys: List[str] = []
        output_keys: List[str] = []
        
        def _call(self, inputs: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
            raise NotImplementedError

from .coordinators import (
    NeogenesisToolCoordinator,
    ExecutionContext,
    ExecutionMode,
    PerformanceOptimizer
)
from .state_management import NeogenesisStateManager, DecisionStage

logger = logging.getLogger(__name__)

# =============================================================================
# 高级输入模型
# =============================================================================

class AdvancedDecisionInput(BaseModel):
    """高级决策链输入模型"""
    user_query: str = Field(description="用户查询")
    execution_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="执行上下文"
    )
    execution_mode: str = Field(
        default="adaptive",
        description="执行模式：sequential, parallel, adaptive, pipeline"
    )
    enable_verification: bool = Field(
        default=True,
        description="是否启用验证"
    )
    enable_caching: bool = Field(
        default=True,
        description="是否启用缓存"
    )
    max_paths: int = Field(
        default=4,
        description="最大思维路径数"
    )
    timeout: float = Field(
        default=120.0,
        description="总超时时间（秒）"
    )
    priority_mode: str = Field(
        default="balanced",
        description="优先级模式：speed, quality, balanced"
    )
    fallback_enabled: bool = Field(
        default=True,
        description="是否启用回退机制"
    )

# =============================================================================
# 智能协调决策链
# =============================================================================

class SmartCoordinatedChain(Chain):
    """
    智能协调决策链
    
    特性：
    - 智能工具协调和执行策略选择
    - 自适应性能优化
    - 高级错误处理和恢复
    - 实时状态监控
    - 灵活的执行模式切换
    """
    
    coordinator: NeogenesisToolCoordinator
    state_manager: Optional[NeogenesisStateManager] = None
    performance_optimizer: PerformanceOptimizer
    enable_async: bool = True
    
    # Chain接口要求
    input_keys: List[str] = ["user_query"]
    output_keys: List[str] = ["smart_decision_result"]
    
    def __init__(self,
                 api_key: str = "",
                 search_engine: str = "duckduckgo",
                 llm_client=None,
                 web_search_client=None,
                 enable_state_management: bool = True,
                 storage_path: str = "./smart_chain_state",
                 max_workers: int = 4,
                 **kwargs):
        """
        初始化智能协调决策链
        
        Args:
            api_key: API密钥
            search_engine: 搜索引擎类型
            llm_client: LLM客户端
            web_search_client: 网络搜索客户端
            enable_state_management: 是否启用状态管理
            storage_path: 状态存储路径
            max_workers: 最大工作线程数
            **kwargs: 其他参数
        """
        # 初始化状态管理器
        state_manager = None
        if enable_state_management:
            try:
                state_manager = NeogenesisStateManager(storage_path=storage_path)
            except Exception as e:
                logger.warning(f"⚠️ 状态管理器初始化失败: {e}")
        
        # 初始化协调器
        coordinator = NeogenesisToolCoordinator(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client,
            state_manager=state_manager,
            max_workers=max_workers
        )
        
        # 初始化性能优化器
        performance_optimizer = PerformanceOptimizer()
        
        super().__init__(
            coordinator=coordinator,
            state_manager=state_manager,
            performance_optimizer=performance_optimizer,
            **kwargs
        )
        
        logger.info("🎯 SmartCoordinatedChain 初始化完成")
    
    def _call(self,
              inputs: Dict[str, Any],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, Any]:
        """
        执行智能协调决策链
        
        Args:
            inputs: 输入字典
            run_manager: LangChain回调管理器
            
        Returns:
            决策结果字典
        """
        # 解析输入
        user_query = inputs["user_query"]
        execution_context_raw = inputs.get("execution_context", {})
        execution_mode = inputs.get("execution_mode", "adaptive")
        enable_verification = inputs.get("enable_verification", True)
        enable_caching = inputs.get("enable_caching", True)
        max_paths = inputs.get("max_paths", 4)
        timeout = inputs.get("timeout", 120.0)
        priority_mode = inputs.get("priority_mode", "balanced")
        fallback_enabled = inputs.get("fallback_enabled", True)
        
        session_id = f"smart_chain_{int(time.time() * 1000)}"
        
        logger.info(f"🚀 开始智能协调决策: {user_query[:50]}...")
        logger.info(f"   模式: {execution_mode}, 验证: {enable_verification}, 缓存: {enable_caching}")
        
        try:
            # 创建执行上下文
            context = ExecutionContext(
                session_id=session_id,
                user_query=user_query,
                execution_mode=ExecutionMode(execution_mode),
                timeout=timeout,
                enable_caching=enable_caching,
                enable_verification=enable_verification,
                fallback_enabled=fallback_enabled,
                custom_config={
                    "max_paths": max_paths,
                    "priority_mode": priority_mode,
                    **execution_context_raw
                }
            )
            
            # 根据优先级模式调整策略
            context = self._apply_priority_mode(context, priority_mode)
            
            # 创建执行计划
            execution_plan = self.coordinator.create_execution_plan(context)
            
            # 执行计划
            if self.enable_async:
                # 异步执行
                results = asyncio.run(
                    self.coordinator.execute_plan_async(execution_plan, context)
                )
            else:
                # 同步执行（简化版）
                results = self._execute_plan_sync(execution_plan, context)
            
            # 分析执行结果
            decision_analysis = self._analyze_execution_results(results, context)
            
            # 生成最终决策
            final_decision = self._generate_final_decision(results, decision_analysis, context)
            
            # 性能分析
            performance_analysis = self.performance_optimizer.analyze_performance(self.coordinator)
            
            # 构建返回结果
            smart_result = {
                "decision_success": decision_analysis["overall_success"],
                "session_id": session_id,
                "user_query": user_query,
                "execution_mode": execution_mode,
                "execution_context": context.custom_config,
                
                # 核心决策结果
                "final_decision": final_decision,
                "thinking_seed": decision_analysis.get("thinking_seed"),
                "reasoning_paths": decision_analysis.get("reasoning_paths", []),
                "verification_results": decision_analysis.get("verification_results", {}),
                
                # 执行详情
                "execution_details": {
                    "total_tools_executed": len(results),
                    "successful_tools": sum(1 for r in results.values() if r.success),
                    "failed_tools": sum(1 for r in results.values() if not r.success),
                    "total_execution_time": sum(r.execution_time for r in results.values()),
                    "cache_hits": sum(1 for r in results.values() if r.cache_hit),
                    "execution_plan_steps": len(execution_plan)
                },
                
                # 性能和优化
                "performance_analysis": performance_analysis,
                "optimization_recommendations": performance_analysis.get("recommendations", []),
                
                # 元数据
                "chain_metadata": {
                    "chain_type": "SmartCoordinatedChain",
                    "execution_timestamp": time.time(),
                    "langchain_integration": True,
                    "async_execution": self.enable_async,
                    "state_management_enabled": self.state_manager is not None
                }
            }
            
            # 完成会话状态
            if self.state_manager:
                self.state_manager.complete_session(session_id, smart_result)
            
            logger.info("✅ 智能协调决策链执行完成")
            return {"smart_decision_result": smart_result}
            
        except Exception as e:
            error_msg = f"智能协调决策链执行失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 错误处理
            error_result = {
                "decision_success": False,
                "error": error_msg,
                "session_id": session_id,
                "user_query": user_query,
                "execution_mode": execution_mode,
                "chain_metadata": {
                    "chain_type": "SmartCoordinatedChain",
                    "error_timestamp": time.time(),
                    "error_details": str(e)
                }
            }
            
            return {"smart_decision_result": error_result}
    
    def _apply_priority_mode(self, context: ExecutionContext, priority_mode: str) -> ExecutionContext:
        """根据优先级模式调整执行策略"""
        if priority_mode == "speed":
            # 速度优先：并行执行，减少验证，shorter timeout
            context.execution_mode = ExecutionMode.PARALLEL
            context.enable_verification = False
            context.timeout = min(context.timeout, 60.0)
            context.max_parallel_tools = 4
            
        elif priority_mode == "quality":
            # 质量优先：完整验证，longer timeout，更多路径
            context.execution_mode = ExecutionMode.SEQUENTIAL
            context.enable_verification = True
            context.timeout = max(context.timeout, 180.0)
            context.custom_config["max_paths"] = max(context.custom_config.get("max_paths", 4), 6)
            
        elif priority_mode == "balanced":
            # 平衡模式：自适应执行
            context.execution_mode = ExecutionMode.ADAPTIVE
            context.enable_verification = True
            
        return context
    
    def _execute_plan_sync(self, 
                          execution_plan: List,
                          context: ExecutionContext) -> Dict[str, Any]:
        """同步执行计划（简化版）"""
        results = {}
        
        for tool_plan in execution_plan:
            try:
                # 检查依赖
                dependencies_met = all(
                    dep in results and results[dep].success
                    for dep in tool_plan.dependencies
                )
                
                if not dependencies_met and tool_plan.dependencies:
                    logger.warning(f"⚠️ 跳过工具 {tool_plan.tool_name}：依赖未满足")
                    continue
                
                # 准备输入
                tool_input = self.coordinator._prepare_tool_input(tool_plan, context, results)
                
                # 执行工具
                start_time = time.time()
                result_data = tool_plan.tool_instance.run(**tool_input)
                execution_time = time.time() - start_time
                
                # 创建结果
                from .coordinators import ExecutionResult
                result = ExecutionResult(
                    tool_name=tool_plan.tool_name,
                    stage=tool_plan.stage,
                    success=True,
                    data=result_data,
                    execution_time=execution_time
                )
                
                results[tool_plan.tool_name] = result
                logger.info(f"✅ 同步执行工具: {tool_plan.tool_name}")
                
            except Exception as e:
                logger.error(f"❌ 同步执行工具失败: {tool_plan.tool_name} - {e}")
                from .coordinators import ExecutionResult
                result = ExecutionResult(
                    tool_name=tool_plan.tool_name,
                    stage=tool_plan.stage,
                    success=False,
                    error_message=str(e),
                    execution_time=0.0
                )
                results[tool_plan.tool_name] = result
        
        return results
    
    def _analyze_execution_results(self, 
                                 results: Dict[str, Any],
                                 context: ExecutionContext) -> Dict[str, Any]:
        """分析执行结果"""
        analysis = {
            "overall_success": True,
            "successful_stages": [],
            "failed_stages": [],
            "thinking_seed": None,
            "reasoning_paths": [],
            "verification_results": {},
            "performance_metrics": {}
        }
        
        # 分析各工具结果
        for tool_name, result in results.items():
            if result.success:
                analysis["successful_stages"].append(tool_name)
                
                # 提取关键数据
                if tool_name in ["thinking_seed", "rag_seed"]:
                    try:
                        data = json.loads(result.data) if isinstance(result.data, str) else result.data
                        analysis["thinking_seed"] = data.get("thinking_seed") or data.get("rag_enhanced_seed")
                    except:
                        analysis["thinking_seed"] = str(result.data)
                        
                elif tool_name == "path_generator":
                    try:
                        data = json.loads(result.data) if isinstance(result.data, str) else result.data
                        analysis["reasoning_paths"] = data.get("reasoning_paths", [])
                    except:
                        pass
                        
                elif tool_name == "idea_verification":
                    try:
                        data = json.loads(result.data) if isinstance(result.data, str) else result.data
                        analysis["verification_results"][result.stage.value] = data
                    except:
                        pass
            else:
                analysis["failed_stages"].append(tool_name)
                analysis["overall_success"] = False
        
        # 计算性能指标
        total_time = sum(r.execution_time for r in results.values())
        cache_hits = sum(1 for r in results.values() if getattr(r, 'cache_hit', False))
        
        analysis["performance_metrics"] = {
            "total_execution_time": total_time,
            "average_tool_time": total_time / len(results) if results else 0,
            "cache_hit_rate": cache_hits / len(results) if results else 0,
            "success_rate": len(analysis["successful_stages"]) / len(results) if results else 0
        }
        
        return analysis
    
    def _generate_final_decision(self,
                               results: Dict[str, Any],
                               analysis: Dict[str, Any],
                               context: ExecutionContext) -> Dict[str, Any]:
        """生成最终决策"""
        # 检查MAB决策结果
        mab_result = results.get("mab_decision")
        if mab_result and mab_result.success:
            try:
                mab_data = json.loads(mab_result.data) if isinstance(mab_result.data, str) else mab_result.data
                selected_path = mab_data.get("selected_path", {})
                mab_statistics = mab_data.get("mab_statistics", {})
                
                return {
                    "decision_type": "mab_optimized",
                    "selected_strategy": selected_path,
                    "confidence_score": mab_statistics.get("confidence_score", 0.8),
                    "decision_reasoning": "基于多臂老虎机算法的智能选择",
                    "alternative_paths": analysis.get("reasoning_paths", []),
                    "verification_support": analysis.get("verification_results", {}),
                    "optimization_level": "high"
                }
            except:
                pass
        
        # 回退到路径选择
        reasoning_paths = analysis.get("reasoning_paths", [])
        if reasoning_paths:
            # 选择第一个路径作为默认决策
            selected_path = reasoning_paths[0]
            
            return {
                "decision_type": "path_based",
                "selected_strategy": selected_path,
                "confidence_score": 0.6,
                "decision_reasoning": "基于路径生成的默认选择",
                "alternative_paths": reasoning_paths[1:],
                "verification_support": analysis.get("verification_results", {}),
                "optimization_level": "medium"
            }
        
        # 最终回退
        return {
            "decision_type": "fallback",
            "selected_strategy": {
                "path_type": "通用分析型",
                "description": f"针对'{context.user_query}'采用系统性分析方法",
                "approach": "基础问题分析和解决方案制定"
            },
            "confidence_score": 0.4,
            "decision_reasoning": "系统回退到基础分析方法",
            "alternative_paths": [],
            "verification_support": {},
            "optimization_level": "basic"
        }

# =============================================================================
# 专用高级链
# =============================================================================

class HighPerformanceDecisionChain(SmartCoordinatedChain):
    """
    高性能决策链
    专为性能敏感场景优化
    """
    
    def __init__(self, **kwargs):
        kwargs.setdefault("max_workers", 8)
        super().__init__(**kwargs)
        
        # 性能优化配置
        self.enable_async = True
        self.coordinator.result_cache = {}  # 重置缓存
        
        logger.info("⚡ HighPerformanceDecisionChain 初始化完成")
    
    def _apply_priority_mode(self, context: ExecutionContext, priority_mode: str) -> ExecutionContext:
        """强制性能优化"""
        context = super()._apply_priority_mode(context, priority_mode)
        
        # 强制并行执行
        context.execution_mode = ExecutionMode.PARALLEL
        context.max_parallel_tools = 6
        context.timeout = min(context.timeout, 45.0)
        
        # 启用激进缓存
        context.enable_caching = True
        
        return context

class QualityAssuredDecisionChain(SmartCoordinatedChain):
    """
    质量保证决策链
    专为高质量决策优化
    """
    
    def __init__(self, **kwargs):
        kwargs.setdefault("enable_state_management", True)
        super().__init__(**kwargs)
        
        logger.info("🎯 QualityAssuredDecisionChain 初始化完成")
    
    def _apply_priority_mode(self, context: ExecutionContext, priority_mode: str) -> ExecutionContext:
        """强制质量保证"""
        context = super()._apply_priority_mode(context, priority_mode)
        
        # 强制质量优先设置
        context.execution_mode = ExecutionMode.SEQUENTIAL
        context.enable_verification = True
        context.timeout = max(context.timeout, 200.0)
        context.fallback_enabled = True
        
        # 增加路径数量
        context.custom_config["max_paths"] = max(context.custom_config.get("max_paths", 4), 8)
        
        return context

# =============================================================================
# 链工厂函数
# =============================================================================

def create_smart_coordinated_chain(
    api_key: str = "",
    search_engine: str = "duckduckgo",
    llm_client=None,
    web_search_client=None,
    chain_type: str = "smart",
    **kwargs
) -> SmartCoordinatedChain:
    """
    创建智能协调决策链
    
    Args:
        api_key: API密钥
        search_engine: 搜索引擎类型
        llm_client: LLM客户端
        web_search_client: 网络搜索客户端
        chain_type: 链类型（"smart", "high_performance", "quality_assured"）
        **kwargs: 其他参数
        
    Returns:
        智能协调决策链实例
    """
    chain_classes = {
        "smart": SmartCoordinatedChain,
        "high_performance": HighPerformanceDecisionChain,
        "quality_assured": QualityAssuredDecisionChain
    }
    
    chain_class = chain_classes.get(chain_type, SmartCoordinatedChain)
    
    return chain_class(
        api_key=api_key,
        search_engine=search_engine,
        llm_client=llm_client,
        web_search_client=web_search_client,
        **kwargs
    )

def create_adaptive_chain_pipeline(
    queries: List[str],
    api_key: str = "",
    **kwargs
) -> List[Dict[str, Any]]:
    """
    创建自适应链管道，处理多个查询
    
    Args:
        queries: 查询列表
        api_key: API密钥
        **kwargs: 其他参数
        
    Returns:
        处理结果列表
    """
    chain = create_smart_coordinated_chain(api_key=api_key, **kwargs)
    results = []
    
    for i, query in enumerate(queries):
        logger.info(f"🔄 处理查询 {i+1}/{len(queries)}: {query[:50]}...")
        
        # 根据查询复杂度选择执行模式
        if len(query) > 200 or "复杂" in query or "分析" in query:
            execution_mode = "quality"
        elif "快速" in query or "简单" in query:
            execution_mode = "speed"
        else:
            execution_mode = "balanced"
        
        result = chain({
            "user_query": query,
            "priority_mode": execution_mode,
            "execution_context": {"pipeline_index": i}
        })
        
        results.append(result)
    
    return results

# =============================================================================
# 兼容性和测试
# =============================================================================

def test_smart_coordinated_chain():
    """测试智能协调决策链"""
    print("🧪 测试智能协调决策链...")
    
    try:
        # 创建链
        chain = create_smart_coordinated_chain(
            api_key="test_key",
            chain_type="smart"
        )
        print("✅ 智能协调链创建成功")
        
        # 测试执行
        test_input = {
            "user_query": "设计一个高性能的分布式缓存系统",
            "execution_mode": "adaptive",
            "priority_mode": "balanced",
            "max_paths": 3
        }
        
        result = chain(test_input)
        
        if result.get("smart_decision_result", {}).get("decision_success", False):
            print("✅ 测试执行成功")
            
            decision_result = result["smart_decision_result"]
            print(f"   执行模式: {decision_result.get('execution_mode')}")
            print(f"   工具执行数: {decision_result.get('execution_details', {}).get('total_tools_executed', 0)}")
            print(f"   总执行时间: {decision_result.get('execution_details', {}).get('total_execution_time', 0):.2f}s")
            
        else:
            print(f"❌ 测试执行失败: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    success = test_smart_coordinated_chain()
    
    if success:
        print("✅ 智能协调决策链测试完成")
    else:
        print("❌ 测试未通过，需要检查配置")
