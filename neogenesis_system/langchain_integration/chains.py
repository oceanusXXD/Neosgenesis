#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - LangChain Chains
将Neogenesis System的五阶段决策流程封装为LangChain链
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .coordinators import NeogenesisToolCoordinator, ExecutionContext, ExecutionMode
    from .state_management import NeogenesisStateManager, DecisionStage

try:
    from langchain.chains.base import Chain
    from langchain.callbacks.manager import CallbackManagerForChainRun
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # 如果LangChain不可用，创建兼容的基类
    LANGCHAIN_AVAILABLE = False
    
    class BaseModel:
        pass
    
    class Chain:
        input_keys: List[str] = []
        output_keys: List[str] = []
        
        def _call(self, inputs: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
            raise NotImplementedError

from .tools import (
    NeogenesisThinkingSeedTool,
    NeogenesisRAGSeedTool,
    NeogenesisPathGeneratorTool,
    NeogenesisMABDecisionTool,
    NeogenesisIdeaVerificationTool,
    NeogenesisFiveStageDecisionTool
)

try:
    from .coordinators import NeogenesisToolCoordinator, ExecutionContext, ExecutionMode
    from .state_management import NeogenesisStateManager, DecisionStage
    COORDINATORS_AVAILABLE = True
except ImportError:
    COORDINATORS_AVAILABLE = False
    NeogenesisToolCoordinator = None
    ExecutionContext = None
    ExecutionMode = None
    NeogenesisStateManager = None
    DecisionStage = None

logger = logging.getLogger(__name__)

# =============================================================================
# 输入输出模型
# =============================================================================

class NeogenesisDecisionInput(BaseModel):
    """Neogenesis决策链的输入模型"""
    user_query: str = Field(description="用户查询")
    execution_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="执行上下文"
    )
    deepseek_confidence: float = Field(
        default=0.5,
        description="DeepSeek置信度"
    )
    use_rag_enhancement: bool = Field(
        default=True,
        description="是否使用RAG增强"
    )
    max_paths: int = Field(
        default=4,
        description="最大思维路径数"
    )
    enable_verification: bool = Field(
        default=True,
        description="是否启用想法验证"
    )

# =============================================================================
# 核心决策链
# =============================================================================

class NeogenesisDecisionChain(Chain):
    """
    Neogenesis核心决策链
    
    实现简化的三阶段决策流程：
    1. 思维种子生成（可选RAG增强）
    2. 思维路径生成
    3. MAB决策选择
    """
    
    thinking_seed_tool: NeogenesisThinkingSeedTool
    rag_seed_tool: Optional[NeogenesisRAGSeedTool] = None
    path_generator_tool: NeogenesisPathGeneratorTool
    mab_decision_tool: NeogenesisMABDecisionTool
    verification_tool: Optional[NeogenesisIdeaVerificationTool] = None
    
    # Chain接口要求
    input_keys: List[str] = ["user_query"]
    output_keys: List[str] = ["decision_result"]
    
    def __init__(
        self,
        api_key: str = "",
        search_engine: str = "duckduckgo",
        llm_client=None,
        web_search_client=None,
        **kwargs
    ):
        # 初始化工具
        thinking_seed_tool = NeogenesisThinkingSeedTool(api_key=api_key)
        rag_seed_tool = NeogenesisRAGSeedTool(
            api_key=api_key,
            search_engine=search_engine,
            web_search_client=web_search_client,
            llm_client=llm_client
        ) if llm_client else None
        path_generator_tool = NeogenesisPathGeneratorTool(
            api_key=api_key,
            llm_client=llm_client
        )
        mab_decision_tool = NeogenesisMABDecisionTool(
            api_key=api_key,
            llm_client=llm_client
        )
        verification_tool = NeogenesisIdeaVerificationTool(
            search_engine=search_engine
        )
        
        super().__init__(
            thinking_seed_tool=thinking_seed_tool,
            rag_seed_tool=rag_seed_tool,
            path_generator_tool=path_generator_tool,
            mab_decision_tool=mab_decision_tool,
            verification_tool=verification_tool,
            **kwargs
        )
        
        logger.info("🔗 NeogenesisDecisionChain 初始化完成")
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """
        执行Neogenesis决策链
        
        Args:
            inputs: 输入字典，必须包含user_query
            run_manager: LangChain回调管理器
            
        Returns:
            决策结果字典
        """
        user_query = inputs["user_query"]
        execution_context = inputs.get("execution_context")
        use_rag_enhancement = inputs.get("use_rag_enhancement", True)
        max_paths = inputs.get("max_paths", 4)
        enable_verification = inputs.get("enable_verification", True)
        
        logger.info(f"🚀 开始Neogenesis决策链: {user_query[:50]}...")
        
        try:
            # 阶段一：思维种子生成
            if use_rag_enhancement and self.rag_seed_tool:
                logger.info("🔍 使用RAG增强种子生成")
                seed_result = self.rag_seed_tool.run(
                    user_query=user_query,
                    execution_context=execution_context
                )
                seed_data = json.loads(seed_result)
                thinking_seed = seed_data.get("rag_enhanced_seed", "")
            else:
                logger.info("🧠 使用基础思维种子生成")
                seed_result = self.thinking_seed_tool.run(
                    user_query=user_query,
                    execution_context=execution_context
                )
                seed_data = json.loads(seed_result)
                thinking_seed = seed_data.get("thinking_seed", "")
            
            if not thinking_seed:
                raise ValueError("思维种子生成失败")
            
            # 可选：种子验证
            verification_result = None
            if enable_verification and self.verification_tool:
                logger.info("🔍 执行思维种子验证")
                verification_result = self.verification_tool.run(
                    idea_text=thinking_seed,
                    context={"stage": "thinking_seed"}
                )
            
            # 阶段二：思维路径生成
            logger.info("🛤️ 生成思维路径")
            paths_result = self.path_generator_tool.run(
                thinking_seed=thinking_seed,
                task=user_query,
                max_paths=max_paths
            )
            paths_data = json.loads(paths_result)
            reasoning_paths = paths_data.get("reasoning_paths", [])
            
            if not reasoning_paths:
                raise ValueError("思维路径生成失败")
            
            # 阶段三：MAB决策
            logger.info("🎰 执行MAB决策")
            decision_result = self.mab_decision_tool.run(
                reasoning_paths=reasoning_paths,
                user_query=user_query,
                execution_context=execution_context
            )
            decision_data = json.loads(decision_result)
            
            # 构建最终结果
            final_result = {
                "decision_success": True,
                "user_query": user_query,
                "thinking_seed": thinking_seed,
                "reasoning_paths": reasoning_paths,
                "selected_path": decision_data.get("selected_path"),
                "mab_statistics": decision_data.get("mab_statistics"),
                "verification_result": verification_result,
                "chain_metadata": {
                    "chain_name": "NeogenesisDecisionChain",
                    "execution_time": time.time(),
                    "stages_completed": ["seed_generation", "path_generation", "mab_decision"],
                    "rag_enhanced": use_rag_enhancement,
                    "verification_enabled": enable_verification
                }
            }
            
            logger.info("✅ Neogenesis决策链执行完成")
            return {"decision_result": final_result}
            
        except Exception as e:
            error_msg = f"决策链执行失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 返回错误结果
            error_result = {
                "decision_success": False,
                "error": error_msg,
                "user_query": user_query,
                "chain_metadata": {
                    "chain_name": "NeogenesisDecisionChain",
                    "error_time": time.time()
                }
            }
            
            return {"decision_result": error_result}

class NeogenesisFiveStageChain(Chain):
    """
    Neogenesis完整五阶段决策链
    
    实现完整的五阶段决策流程：
    1. 思维种子生成
    2. 种子验证检查
    3. 思维路径生成
    4. 路径验证学习
    5. 智能最终决策
    """
    
    # 工具组件
    thinking_seed_tool: NeogenesisThinkingSeedTool
    rag_seed_tool: Optional[NeogenesisRAGSeedTool] = None
    verification_tool: NeogenesisIdeaVerificationTool
    path_generator_tool: NeogenesisPathGeneratorTool
    mab_decision_tool: NeogenesisMABDecisionTool
    
    # Chain接口要求
    input_keys: List[str] = ["user_query"]
    output_keys: List[str] = ["five_stage_result"]
    
    def __init__(
        self,
        api_key: str = "",
        search_engine: str = "duckduckgo",
        llm_client=None,
        web_search_client=None,
        **kwargs
    ):
        # 初始化所有必需的工具
        thinking_seed_tool = NeogenesisThinkingSeedTool(api_key=api_key)
        rag_seed_tool = NeogenesisRAGSeedTool(
            api_key=api_key,
            search_engine=search_engine,
            web_search_client=web_search_client,
            llm_client=llm_client
        ) if llm_client else None
        verification_tool = NeogenesisIdeaVerificationTool(search_engine=search_engine)
        path_generator_tool = NeogenesisPathGeneratorTool(
            api_key=api_key,
            llm_client=llm_client
        )
        mab_decision_tool = NeogenesisMABDecisionTool(
            api_key=api_key,
            llm_client=llm_client
        )
        
        super().__init__(
            thinking_seed_tool=thinking_seed_tool,
            rag_seed_tool=rag_seed_tool,
            verification_tool=verification_tool,
            path_generator_tool=path_generator_tool,
            mab_decision_tool=mab_decision_tool,
            **kwargs
        )
        
        logger.info("🔗 NeogenesisFiveStageChain 初始化完成")
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """
        执行完整的五阶段决策流程
        
        Args:
            inputs: 输入字典
            run_manager: LangChain回调管理器
            
        Returns:
            五阶段决策结果
        """
        user_query = inputs["user_query"]
        execution_context = inputs.get("execution_context")
        deepseek_confidence = inputs.get("deepseek_confidence", 0.5)
        use_rag = inputs.get("use_rag_enhancement", True)
        max_paths = inputs.get("max_paths", 4)
        
        logger.info(f"🚀 开始五阶段Neogenesis决策: {user_query[:50]}...")
        
        stage_results = {}
        
        try:
            # 🧠 阶段一：思维种子生成
            logger.info("🧠 阶段一：思维种子生成")
            if use_rag and self.rag_seed_tool:
                seed_result = self.rag_seed_tool.run(
                    user_query=user_query,
                    execution_context=execution_context
                )
                seed_data = json.loads(seed_result)
                thinking_seed = seed_data.get("rag_enhanced_seed", "")
                stage_results["stage_1"] = {"type": "rag_enhanced", "data": seed_data}
            else:
                seed_result = self.thinking_seed_tool.run(
                    user_query=user_query,
                    execution_context=execution_context
                )
                seed_data = json.loads(seed_result)
                thinking_seed = seed_data.get("thinking_seed", "")
                stage_results["stage_1"] = {"type": "basic_seed", "data": seed_data}
            
            # 🔍 阶段二：种子验证检查
            logger.info("🔍 阶段二：种子验证检查")
            seed_verification = self.verification_tool.run(
                idea_text=thinking_seed,
                context={
                    "stage": "thinking_seed",
                    "domain": "strategic_planning",
                    "query": user_query
                }
            )
            verification_data = json.loads(seed_verification)
            stage_results["stage_2"] = {"type": "seed_verification", "data": verification_data}
            
            # 分析验证结果
            verification_success = verification_data.get("verification_success", False)
            if not verification_success:
                logger.warning("⚠️ 思维种子验证存在问题，但继续执行")
            
            # 🛤️ 阶段三：思维路径生成
            logger.info("🛤️ 阶段三：思维路径生成")
            paths_result = self.path_generator_tool.run(
                thinking_seed=thinking_seed,
                task=user_query,
                max_paths=max_paths
            )
            paths_data = json.loads(paths_result)
            reasoning_paths = paths_data.get("reasoning_paths", [])
            stage_results["stage_3"] = {"type": "path_generation", "data": paths_data}
            
            # 🔬 阶段四：路径验证学习
            logger.info("🔬 阶段四：路径验证学习")
            verified_paths = []
            for i, path in enumerate(reasoning_paths):
                path_verification = self.verification_tool.run(
                    idea_text=f"{path['path_type']}: {path['description']}",
                    context={
                        "stage": "reasoning_path",
                        "path_id": path["path_id"],
                        "path_type": path["path_type"],
                        "query": user_query
                    }
                )
                path_verification_data = json.loads(path_verification)
                
                # 为路径添加验证结果
                verified_path = path.copy()
                verified_path["verification_result"] = path_verification_data
                verified_paths.append(verified_path)
                
                logger.debug(f"  路径{i+1}验证完成: {path['path_type']}")
            
            stage_results["stage_4"] = {
                "type": "path_verification",
                "data": {
                    "verified_paths": verified_paths,
                    "total_paths": len(verified_paths)
                }
            }
            
            # 🏆 阶段五：智能最终决策
            logger.info("🏆 阶段五：智能最终决策")
            final_decision = self.mab_decision_tool.run(
                reasoning_paths=verified_paths,
                user_query=user_query,
                execution_context=execution_context
            )
            decision_data = json.loads(final_decision)
            stage_results["stage_5"] = {"type": "mab_decision", "data": decision_data}
            
            # 构建最终结果
            final_result = {
                "five_stage_success": True,
                "user_query": user_query,
                "deepseek_confidence": deepseek_confidence,
                "thinking_seed": thinking_seed,
                "stage_results": stage_results,
                "final_decision": decision_data.get("selected_path"),
                "mab_statistics": decision_data.get("mab_statistics"),
                "chain_metadata": {
                    "chain_name": "NeogenesisFiveStageChain",
                    "execution_time": time.time(),
                    "total_stages": 5,
                    "rag_enhanced": use_rag,
                    "total_paths_generated": len(reasoning_paths),
                    "total_paths_verified": len(verified_paths)
                }
            }
            
            logger.info("✅ 五阶段Neogenesis决策链执行完成")
            return {"five_stage_result": final_result}
            
        except Exception as e:
            error_msg = f"五阶段决策链执行失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 返回错误结果，包含已完成的阶段
            error_result = {
                "five_stage_success": False,
                "error": error_msg,
                "user_query": user_query,
                "partial_results": stage_results,
                "chain_metadata": {
                    "chain_name": "NeogenesisFiveStageChain",
                    "error_time": time.time(),
                    "completed_stages": list(stage_results.keys())
                }
            }
            
            return {"five_stage_result": error_result}

# =============================================================================
# 链工厂函数
# =============================================================================

def create_neogenesis_decision_chain(
    api_key: str = "",
    search_engine: str = "duckduckgo",
    llm_client=None,
    web_search_client=None,
    chain_type: str = "basic"
) -> Chain:
    """
    创建Neogenesis决策链
    
    Args:
        api_key: API密钥
        search_engine: 搜索引擎类型
        llm_client: LLM客户端
        web_search_client: 网络搜索客户端
        chain_type: 链类型（"basic" 或 "five_stage"）
        
    Returns:
        决策链实例
    """
    if chain_type == "five_stage":
        return NeogenesisFiveStageChain(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client
        )
    else:
        return NeogenesisDecisionChain(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client
        )

def create_custom_neogenesis_chain(
    tools: Dict[str, Any],
    stages: List[str] = None
) -> Chain:
    """
    创建自定义Neogenesis决策链
    
    Args:
        tools: 工具字典
        stages: 要执行的阶段列表
        
    Returns:
        自定义决策链
    """
    # 这里可以实现更灵活的链构建逻辑
    # 暂时返回基础链
    return NeogenesisDecisionChain(**tools)

# =============================================================================
# 兼容性和测试
# =============================================================================

def check_chain_dependencies() -> Dict[str, Any]:
    """
    检查链的依赖关系
    
    Returns:
        依赖检查结果
    """
    dependencies = {
        "langchain_available": LANGCHAIN_AVAILABLE,
        "required_tools": [
            "NeogenesisThinkingSeedTool",
            "NeogenesisPathGeneratorTool", 
            "NeogenesisMABDecisionTool"
        ],
        "optional_tools": [
            "NeogenesisRAGSeedTool",
            "NeogenesisIdeaVerificationTool"
        ]
    }
    
    return dependencies

# =============================================================================
# 第二阶段增强：协调器集成链
# =============================================================================

class CoordinatedNeogenesisChain(Chain):
    """
    协调器增强的Neogenesis决策链
    
    特性：
    - 集成智能工具协调器
    - 支持多种执行模式
    - 高级错误处理和恢复
    - 智能资源管理
    """
    
    coordinator: Optional[Any] = None
    execution_mode: str = "adaptive"
    enable_smart_coordination: bool = True
    
    # Chain接口要求
    input_keys: List[str] = ["user_query"]
    output_keys: List[str] = ["coordinated_result"]
    
    def __init__(self,
                 api_key: str = "",
                 search_engine: str = "duckduckgo",
                 llm_client=None,
                 web_search_client=None,
                 enable_coordination: bool = True,
                 **kwargs):
        """
        初始化协调器增强链
        
        Args:
            api_key: API密钥
            search_engine: 搜索引擎类型
            llm_client: LLM客户端
            web_search_client: 网络搜索客户端
            enable_coordination: 是否启用智能协调
            **kwargs: 其他参数
        """
        # 初始化协调器
        coordinator = None
        if enable_coordination and COORDINATORS_AVAILABLE:
            try:
                coordinator = NeogenesisToolCoordinator(
                    api_key=api_key,
                    search_engine=search_engine,
                    llm_client=llm_client,
                    web_search_client=web_search_client
                )
                logger.info("🎯 协调器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 协调器初始化失败，回退到基础模式: {e}")
        
        super().__init__(
            coordinator=coordinator,
            enable_smart_coordination=enable_coordination and coordinator is not None,
            **kwargs
        )
        
        logger.info("🔗 CoordinatedNeogenesisChain 初始化完成")
    
    def _call(self,
              inputs: Dict[str, Any],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, Any]:
        """
        执行协调器增强的决策链
        
        Args:
            inputs: 输入字典
            run_manager: LangChain回调管理器
            
        Returns:
            协调决策结果
        """
        user_query = inputs["user_query"]
        execution_context = inputs.get("execution_context", {})
        execution_mode = inputs.get("execution_mode", self.execution_mode)
        enable_verification = inputs.get("enable_verification", True)
        max_paths = inputs.get("max_paths", 4)
        
        session_id = f"coordinated_{int(time.time() * 1000)}"
        
        logger.info(f"🚀 开始协调器增强决策: {user_query[:50]}...")
        
        try:
            if self.enable_smart_coordination and self.coordinator:
                # 使用智能协调器
                result = self._execute_with_coordinator(
                    user_query, execution_context, execution_mode,
                    enable_verification, max_paths, session_id
                )
            else:
                # 回退到基础链模式
                result = self._execute_fallback_chain(
                    user_query, execution_context, 
                    enable_verification, max_paths, session_id
                )
            
            return {"coordinated_result": result}
            
        except Exception as e:
            error_msg = f"协调器增强决策失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            error_result = {
                "decision_success": False,
                "error": error_msg,
                "user_query": user_query,
                "session_id": session_id,
                "coordination_enabled": self.enable_smart_coordination
            }
            
            return {"coordinated_result": error_result}
    
    def _execute_with_coordinator(self,
                                user_query: str,
                                execution_context: Dict[str, Any],
                                execution_mode: str,
                                enable_verification: bool,
                                max_paths: int,
                                session_id: str) -> Dict[str, Any]:
        """使用协调器执行"""
        # 创建执行上下文
        if not ExecutionContext or not ExecutionMode:
            raise RuntimeError("协调器功能不可用：ExecutionContext 或 ExecutionMode 未定义")
        
        coord_context = ExecutionContext(
            session_id=session_id,
            user_query=user_query,
            execution_mode=ExecutionMode(execution_mode),
            enable_verification=enable_verification,
            custom_config={
                "max_paths": max_paths,
                **execution_context
            }
        )
        
        # 创建执行计划
        execution_plan = self.coordinator.create_execution_plan(coord_context)
        
        # 执行计划
        import asyncio
        results = asyncio.run(
            self.coordinator.execute_plan_async(execution_plan, coord_context)
        )
        
        # 分析结果
        final_decision = self._analyze_coordinated_results(results, coord_context)
        
        # 获取性能报告
        performance_report = self.coordinator.get_performance_report()
        
        return {
            "decision_success": True,
            "coordination_mode": "smart_coordinator",
            "session_id": session_id,
            "user_query": user_query,
            "execution_mode": execution_mode,
            "final_decision": final_decision,
            "tool_results": {name: result.data for name, result in results.items() if result.success},
            "execution_stats": {
                "total_tools": len(results),
                "successful_tools": sum(1 for r in results.values() if r.success),
                "total_time": sum(r.execution_time for r in results.values()),
                "cache_hits": sum(1 for r in results.values() if getattr(r, 'cache_hit', False))
            },
            "performance_report": performance_report,
            "chain_metadata": {
                "chain_type": "CoordinatedNeogenesisChain",
                "coordinator_enabled": True,
                "execution_timestamp": time.time()
            }
        }
    
    def _execute_fallback_chain(self,
                              user_query: str,
                              execution_context: Dict[str, Any],
                              enable_verification: bool,
                              max_paths: int,
                              session_id: str) -> Dict[str, Any]:
        """回退到基础链执行"""
        logger.info("🔄 使用基础链回退模式")
        
        # 创建基础五阶段链
        basic_chain = NeogenesisFiveStageChain(
            api_key=getattr(self.coordinator, 'api_key', '') if self.coordinator else '',
            search_engine="duckduckgo"
        )
        
        # 执行基础链
        chain_input = {
            "user_query": user_query,
            "execution_context": execution_context,
            "enable_verification": enable_verification,
            "max_paths": max_paths
        }
        
        chain_result = basic_chain(chain_input)
        five_stage_result = chain_result.get("five_stage_result", {})
        
        return {
            "decision_success": five_stage_result.get("five_stage_success", False),
            "coordination_mode": "fallback_chain",
            "session_id": session_id,
            "user_query": user_query,
            "fallback_result": five_stage_result,
            "chain_metadata": {
                "chain_type": "CoordinatedNeogenesisChain",
                "coordinator_enabled": False,
                "fallback_mode": True,
                "execution_timestamp": time.time()
            }
        }
    
    def _analyze_coordinated_results(self,
                                   results: Dict[str, Any],
                                   context: Any) -> Dict[str, Any]:
        """分析协调执行结果"""
        # 提取决策结果
        mab_result = results.get("mab_decision")
        if mab_result and mab_result.success:
            try:
                mab_data = json.loads(mab_result.data) if isinstance(mab_result.data, str) else mab_result.data
                return {
                    "decision_type": "coordinated_mab",
                    "selected_path": mab_data.get("selected_path", {}),
                    "confidence": mab_data.get("mab_statistics", {}).get("confidence_score", 0.8),
                    "coordination_quality": "high"
                }
            except:
                pass
        
        # 回退分析
        path_result = results.get("path_generator")
        if path_result and path_result.success:
            try:
                path_data = json.loads(path_result.data) if isinstance(path_result.data, str) else path_result.data
                paths = path_data.get("reasoning_paths", [])
                if paths:
                    return {
                        "decision_type": "coordinated_path",
                        "selected_path": paths[0],
                        "confidence": 0.6,
                        "coordination_quality": "medium"
                    }
            except:
                pass
        
        # 最终回退
        return {
            "decision_type": "coordinated_fallback",
            "selected_path": {
                "path_type": "协调分析型",
                "description": f"基于协调器的系统性分析: {context.user_query}"
            },
            "confidence": 0.4,
            "coordination_quality": "basic"
        }

# =============================================================================
# 增强工厂函数
# =============================================================================

def create_enhanced_neogenesis_chain(
    api_key: str = "",
    search_engine: str = "duckduckgo",
    llm_client=None,
    web_search_client=None,
    chain_type: str = "coordinated",
    **kwargs
) -> Chain:
    """
    创建增强的Neogenesis决策链
    
    Args:
        api_key: API密钥
        search_engine: 搜索引擎类型
        llm_client: LLM客户端
        web_search_client: 网络搜索客户端
        chain_type: 链类型（"coordinated", "basic", "five_stage"）
        **kwargs: 其他参数
        
    Returns:
        增强决策链实例
    """
    if chain_type == "coordinated" and COORDINATORS_AVAILABLE:
        return CoordinatedNeogenesisChain(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client,
            **kwargs
        )
    elif chain_type == "five_stage":
        return NeogenesisFiveStageChain(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client,
            **kwargs
        )
    else:
        return NeogenesisDecisionChain(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client,
            **kwargs
        )

if __name__ == "__main__":
    # 测试链创建
    print("🧪 测试Neogenesis决策链创建...")
    
    # 检查依赖
    deps_info = check_chain_dependencies()
    print(f"依赖信息: {deps_info}")
    
    # 创建基础链
    try:
        basic_chain = create_neogenesis_decision_chain(chain_type="basic")
        print(f"✅ 基础决策链创建成功: {basic_chain.__class__.__name__}")
        
        five_stage_chain = create_neogenesis_decision_chain(chain_type="five_stage")
        print(f"✅ 五阶段决策链创建成功: {five_stage_chain.__class__.__name__}")
        
        # 测试协调器增强链
        if COORDINATORS_AVAILABLE:
            coordinated_chain = create_enhanced_neogenesis_chain(chain_type="coordinated")
            print(f"✅ 协调器增强链创建成功: {coordinated_chain.__class__.__name__}")
        else:
            print("⚠️ 协调器功能不可用，跳过协调器增强链测试")
        
    except Exception as e:
        print(f"❌ 链创建失败: {e}")
