#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - LangChain Tools
将Neogenesis System的核心组件封装为LangChain工具
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import asdict
from abc import ABC

try:
    from langchain.tools import BaseTool
    from langchain.callbacks.manager import CallbackManagerForToolRun
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # 如果LangChain不可用，创建兼容的基类
    LANGCHAIN_AVAILABLE = False
    
    class BaseModel:
        pass
    
    class BaseTool(ABC):
        name: str
        description: str
        
        def _run(self, *args, **kwargs):
            raise NotImplementedError
            
        def run(self, *args, **kwargs):
            return self._run(*args, **kwargs)

# 导入Neogenesis核心组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from neogenesis_system.meta_mab.reasoner import PriorReasoner
from neogenesis_system.meta_mab.rag_seed_generator import RAGSeedGenerator
from neogenesis_system.meta_mab.path_generator import PathGenerator
from neogenesis_system.meta_mab.mab_converger import MABConverger
from neogenesis_system.meta_mab.utils.search_tools import IdeaVerificationTool as OriginalIdeaVerificationTool
from neogenesis_system.meta_mab.utils.search_client import WebSearchClient

logger = logging.getLogger(__name__)

# =============================================================================
# 输入模型定义
# =============================================================================

class ThinkingSeedInput(BaseModel):
    """思维种子生成工具的输入模型"""
    user_query: str = Field(description="用户查询文本")
    execution_context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="执行上下文（可选）"
    )

class RAGSeedInput(BaseModel):
    """RAG种子生成工具的输入模型"""
    user_query: str = Field(description="用户查询文本")
    execution_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="执行上下文（可选）"
    )

class PathGeneratorInput(BaseModel):
    """路径生成工具的输入模型"""
    thinking_seed: str = Field(description="思维种子")
    task: str = Field(description="原始任务描述")
    max_paths: int = Field(default=4, description="最大生成路径数")
    mode: str = Field(default='normal', description="生成模式：normal 或 creative_bypass")

class MABDecisionInput(BaseModel):
    """MAB决策工具的输入模型"""
    reasoning_paths: List[Dict[str, Any]] = Field(description="思维路径列表")
    user_query: str = Field(description="用户查询")
    execution_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="执行上下文（可选）"
    )

class IdeaVerificationInput(BaseModel):
    """想法验证工具的输入模型"""
    idea_text: str = Field(description="需要验证的想法文本")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="验证上下文（可选）"
    )

# =============================================================================
# 核心工具类
# =============================================================================

class NeogenesisThinkingSeedTool(BaseTool):
    """
    Neogenesis思维种子生成工具
    
    功能：基于用户查询快速生成高质量的思维种子
    优势：提供专家级的任务分析和思维起点
    """
    
    name: str = "neogenesis_thinking_seed"
    description: str = """
    生成高质量的思维种子，用于复杂决策任务的起点。
    
    输入：
    - user_query: 用户查询文本
    - execution_context: 可选的执行上下文
    
    输出：结构化的思维种子文本，包含问题分析、复杂度评估和推荐策略
    
    适用场景：需要系统性思考和分析的复杂任务
    """
    args_schema: Type[BaseModel] = ThinkingSeedInput
    
    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(**kwargs)
        # 使用object.__setattr__绕过Pydantic的字段验证
        object.__setattr__(self, 'reasoner', PriorReasoner(api_key=api_key))
        logger.info("🧠 NeogenesisThinkingSeedTool 初始化完成")
    
    def _run(
        self, 
        user_query: str,
        execution_context: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行思维种子生成
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            run_manager: LangChain回调管理器
            
        Returns:
            思维种子文本
        """
        try:
            logger.info(f"🌱 开始生成思维种子: {user_query[:50]}...")
            
            # 调用原始的reasoner逻辑
            thinking_seed = self.reasoner.get_thinking_seed(
                user_query=user_query,
                execution_context=execution_context
            )
            
            # 获取置信度评估
            confidence = self.reasoner.assess_task_confidence(
                user_query=user_query,
                execution_context=execution_context
            )
            
            # 获取复杂度分析
            complexity_info = self.reasoner.analyze_task_complexity(user_query)
            
            # 构建增强的输出
            enhanced_output = {
                "thinking_seed": thinking_seed,
                "confidence_score": confidence,
                "complexity_analysis": complexity_info,
                "tool_metadata": {
                    "tool_name": self.name,
                    "generation_time": time.time(),
                    "query_length": len(user_query)
                }
            }
            
            logger.info(f"✅ 思维种子生成完成 (置信度: {confidence:.3f})")
            return json.dumps(enhanced_output, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"思维种子生成失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "error": error_msg,
                "fallback_seed": f"针对'{user_query}'这个任务，需要进行系统性的分析和解决。",
                "tool_metadata": {"tool_name": self.name, "error_time": time.time()}
            }, ensure_ascii=False)

class NeogenesisRAGSeedTool(BaseTool):
    """
    Neogenesis RAG增强种子生成工具
    
    功能：结合实时信息搜索生成增强的思维种子
    优势：整合最新信息，提供信息丰富的分析起点
    """
    
    name: str = "neogenesis_rag_seed"
    description: str = """
    使用RAG（检索增强生成）技术生成信息丰富的思维种子。
    
    输入：
    - user_query: 用户查询文本
    - execution_context: 可选的执行上下文
    
    输出：包含实时信息的增强思维种子，整合了网络搜索结果
    
    适用场景：需要最新信息支持的决策任务、研究分析等
    """
    args_schema: Type[BaseModel] = RAGSeedInput
    
    def __init__(self, api_key: str = "", search_engine: str = "duckduckgo", 
                 web_search_client=None, llm_client=None, **kwargs):
        super().__init__(**kwargs)
        # 使用object.__setattr__绕过Pydantic的字段验证
        object.__setattr__(self, 'rag_generator', RAGSeedGenerator(
            api_key=api_key,
            search_engine=search_engine,
            web_search_client=web_search_client,
            llm_client=llm_client
        ))
        logger.info("🔍 NeogenesisRAGSeedTool 初始化完成")
    
    def _run(
        self, 
        user_query: str,
        execution_context: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行RAG增强种子生成
        
        Args:
            user_query: 用户查询
            execution_context: 执行上下文
            run_manager: LangChain回调管理器
            
        Returns:
            RAG增强的思维种子
        """
        try:
            logger.info(f"🔍 开始RAG增强种子生成: {user_query[:50]}...")
            
            # 调用原始的RAG生成逻辑
            rag_seed = self.rag_generator.generate_rag_seed(
                user_query=user_query,
                execution_context=execution_context
            )
            
            # 获取性能统计
            performance_stats = self.rag_generator.get_rag_performance_stats()
            
            # 构建输出
            output = {
                "rag_enhanced_seed": rag_seed,
                "performance_stats": performance_stats,
                "tool_metadata": {
                    "tool_name": self.name,
                    "generation_time": time.time(),
                    "search_enabled": True
                }
            }
            
            logger.info("✅ RAG增强种子生成完成")
            return json.dumps(output, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"RAG种子生成失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 回退到基础种子生成
            fallback_output = {
                "error": error_msg,
                "fallback_seed": f"基于'{user_query}'的基础分析，建议采用系统性方法进行处理。",
                "tool_metadata": {"tool_name": self.name, "error_time": time.time()}
            }
            return json.dumps(fallback_output, ensure_ascii=False)

class NeogenesisPathGeneratorTool(BaseTool):
    """
    Neogenesis思维路径生成工具
    
    功能：基于思维种子生成多样化的思维路径
    优势：提供多角度思考方案，支持创造性绕道模式
    """
    
    name: str = "neogenesis_path_generator"
    description: str = """
    基于思维种子生成多样化的思维路径。
    
    输入：
    - thinking_seed: 思维种子文本
    - task: 原始任务描述
    - max_paths: 最大生成路径数（默认4）
    - mode: 生成模式（normal 或 creative_bypass）
    
    输出：包含多个思维路径的结构化列表，每个路径有不同的思考角度
    
    适用场景：需要多角度分析、创新思维、复杂决策的任务
    """
    args_schema: Type[BaseModel] = PathGeneratorInput
    
    def __init__(self, api_key: str = "", llm_client=None, **kwargs):
        super().__init__(**kwargs)
        # 使用object.__setattr__绕过Pydantic的字段验证
        object.__setattr__(self, 'path_generator', PathGenerator(
            api_key=api_key,
            llm_client=llm_client
        ))
        logger.info("🛤️ NeogenesisPathGeneratorTool 初始化完成")
    
    def _run(
        self, 
        thinking_seed: str,
        task: str,
        max_paths: int = 4,
        mode: str = 'normal',
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行思维路径生成
        
        Args:
            thinking_seed: 思维种子
            task: 任务描述
            max_paths: 最大路径数
            mode: 生成模式
            run_manager: LangChain回调管理器
            
        Returns:
            思维路径列表的JSON字符串
        """
        try:
            logger.info(f"🛤️ 开始生成思维路径: 模式={mode}, 最大路径数={max_paths}")
            
            # 调用原始的路径生成逻辑
            reasoning_paths = self.path_generator.generate_paths(
                thinking_seed=thinking_seed,
                task=task,
                max_paths=max_paths,
                mode=mode
            )
            
            # 转换为可序列化的格式
            paths_data = []
            for path in reasoning_paths:
                path_dict = {
                    "path_id": path.path_id,
                    "path_type": path.path_type,
                    "description": path.description,
                    "prompt_template": path.prompt_template,
                    "strategy_id": getattr(path, 'strategy_id', path.path_type),
                    "instance_id": getattr(path, 'instance_id', path.path_id)
                }
                paths_data.append(path_dict)
            
            # 获取生成统计
            generation_stats = self.path_generator.get_generation_statistics()
            
            # 构建输出
            output = {
                "reasoning_paths": paths_data,
                "generation_stats": generation_stats,
                "generation_mode": mode,
                "tool_metadata": {
                    "tool_name": self.name,
                    "generation_time": time.time(),
                    "total_paths": len(paths_data)
                }
            }
            
            logger.info(f"✅ 思维路径生成完成: {len(paths_data)}条路径")
            return json.dumps(output, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"思维路径生成失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 回退路径
            fallback_paths = [
                {
                    "path_id": "fallback_systematic",
                    "path_type": "系统分析型",
                    "description": "基础的系统性分析方法",
                    "prompt_template": f"请系统性分析: {task}。基于种子: {thinking_seed[:100]}..."
                }
            ]
            
            fallback_output = {
                "error": error_msg,
                "reasoning_paths": fallback_paths,
                "tool_metadata": {"tool_name": self.name, "error_time": time.time()}
            }
            return json.dumps(fallback_output, ensure_ascii=False)

class NeogenesisMABDecisionTool(BaseTool):
    """
    Neogenesis多臂老虎机决策工具
    
    功能：使用MAB算法从多个思维路径中选择最优方案
    优势：具备学习能力，在使用中不断优化决策质量
    """
    
    name: str = "neogenesis_mab_decision"
    description: str = """
    使用多臂老虎机（MAB）算法进行智能决策。
    
    输入：
    - reasoning_paths: 思维路径列表
    - user_query: 用户查询
    - execution_context: 可选的执行上下文
    
    输出：经过MAB算法选择的最优路径和决策结果
    
    适用场景：需要在多个方案中进行智能选择，要求决策质量和学习能力
    """
    args_schema: Type[BaseModel] = MABDecisionInput
    
    def __init__(self, api_key: str = "", llm_client=None, **kwargs):
        super().__init__(**kwargs)
        # 初始化真正的MABConverger，使用object.__setattr__绕过Pydantic验证
        try:
            object.__setattr__(self, 'mab_converger', MABConverger())
            object.__setattr__(self, '_initialized', True)
            logger.info("🎰 MABConverger初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ MABConverger初始化失败，使用回退逻辑: {e}")
            object.__setattr__(self, 'mab_converger', None)
            object.__setattr__(self, '_initialized', False)
        
        object.__setattr__(self, '_api_key', api_key)
        object.__setattr__(self, '_llm_client', llm_client)
        logger.info("🎰 NeogenesisMABDecisionTool 初始化完成")
    
    def _run(
        self, 
        reasoning_paths: List[Dict[str, Any]],
        user_query: str,
        execution_context: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行MAB决策
        
        Args:
            reasoning_paths: 思维路径列表
            user_query: 用户查询
            execution_context: 执行上下文
            run_manager: LangChain回调管理器
            
        Returns:
            MAB决策结果的JSON字符串
        """
        try:
            logger.info(f"🎰 开始MAB决策: {len(reasoning_paths)}条路径")
            
            if not reasoning_paths:
                raise ValueError("思维路径列表为空")
            
            if self._initialized and self.mab_converger:
                # 使用真正的MABConverger进行决策
                selected_path, mab_stats = self._use_mab_converger(reasoning_paths, user_query)
            else:
                # 回退到简化逻辑
                logger.info("🔄 使用回退决策逻辑")
                selected_path, mab_stats = self._fallback_decision(reasoning_paths)
            
            # 构建输出
            output = {
                "selected_path": selected_path,
                "mab_statistics": mab_stats,
                "decision_reasoning": "基于MAB算法选择的最优路径",
                "tool_metadata": {
                    "tool_name": self.name,
                    "decision_time": time.time(),
                    "total_candidates": len(reasoning_paths)
                }
            }
            
            logger.info(f"✅ MAB决策完成: 选择路径 {selected_path.get('path_type', 'unknown')}")
            return json.dumps(output, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"MAB决策失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 回退决策
            fallback_output = {
                "error": error_msg,
                "fallback_decision": "选择第一个可用路径" if reasoning_paths else "无可用路径",
                "tool_metadata": {"tool_name": self.name, "error_time": time.time()}
            }
            return json.dumps(fallback_output, ensure_ascii=False)
    
    def _use_mab_converger(self, reasoning_paths: List[Dict[str, Any]], user_query: str) -> tuple:
        """使用真正的MABConverger进行决策"""
        try:
            # 将Dict格式的路径转换为ReasoningPath对象
            from neogenesis_system.meta_mab.data_structures import ReasoningPath
            
            path_objects = []
            for i, path_dict in enumerate(reasoning_paths):
                # 创建ReasoningPath对象
                reasoning_path = ReasoningPath(
                    path_id=path_dict.get("path_id", f"path_{i}"),
                    strategy_id=path_dict.get("strategy_id", path_dict.get("path_type", f"strategy_{i}")),
                    path_type=path_dict.get("path_type", "未知类型"),
                    description=path_dict.get("description", ""),
                    expected_outcome=path_dict.get("expected_outcome", ""),
                    confidence_score=path_dict.get("confidence_score", 0.5),
                    keywords=path_dict.get("keywords", []),
                    reasoning_steps=path_dict.get("reasoning_steps", [])
                )
                path_objects.append(reasoning_path)
            
            # 使用MABConverger选择最佳路径
            selected_path_obj = self.mab_converger.select_best_path(
                paths=path_objects,
                algorithm='auto'
            )
            
            # 转换回Dict格式
            selected_path_dict = {
                "path_id": selected_path_obj.path_id,
                "strategy_id": selected_path_obj.strategy_id,
                "path_type": selected_path_obj.path_type,
                "description": selected_path_obj.description,
                "expected_outcome": selected_path_obj.expected_outcome,
                "confidence_score": selected_path_obj.confidence_score,
                "keywords": selected_path_obj.keywords,
                "reasoning_steps": selected_path_obj.reasoning_steps
            }
            
            # 获取MAB统计信息
            mab_stats = {
                "total_arms": len(reasoning_paths),
                "selected_arm": selected_path_obj.strategy_id,
                "confidence_score": selected_path_obj.confidence_score,
                "total_selections": self.mab_converger.total_path_selections,
                "algorithm_used": "mab_converger",
                "golden_template_used": hasattr(selected_path_obj, 'from_golden_template')
            }
            
            logger.info(f"🎯 MABConverger选择路径: {selected_path_obj.path_type}")
            return selected_path_dict, mab_stats
            
        except Exception as e:
            logger.error(f"❌ MABConverger执行失败: {e}")
            # 回退到简化逻辑
            return self._fallback_decision(reasoning_paths)
    
    def _fallback_decision(self, reasoning_paths: List[Dict[str, Any]]) -> tuple:
        """回退决策逻辑"""
        logger.info("🔄 使用简化决策逻辑")
        
        if not reasoning_paths:
            return {}, {"error": "无可用路径"}
        
        # 简单选择：优先选择置信度最高的路径
        selected_path = max(reasoning_paths, 
                          key=lambda x: x.get("confidence_score", 0))
        
        # 模拟MAB统计信息
        mab_stats = {
            "total_arms": len(reasoning_paths),
            "selected_arm": selected_path.get("strategy_id", selected_path.get("path_id")),
            "confidence_score": selected_path.get("confidence_score", 0.8),
            "algorithm_used": "fallback_highest_confidence",
            "exploration_rate": 0.0
        }
        
        return selected_path, mab_stats

class NeogenesisIdeaVerificationTool(BaseTool):
    """
    Neogenesis想法验证工具
    
    功能：验证想法的可行性，提供详细分析和建议
    优势：基于网络搜索的实时验证，提供可行性评分
    """
    
    name: str = "neogenesis_idea_verification"
    description: str = """
    验证想法或概念的可行性，提供详细分析和建议。
    
    输入：
    - idea_text: 需要验证的想法文本
    - context: 可选的验证上下文
    
    输出：包含可行性评分、分析摘要和相关搜索结果的验证报告
    
    适用场景：创意评估、投资决策、产品规划、技术可行性分析
    """
    args_schema: Type[BaseModel] = IdeaVerificationInput
    
    def __init__(self, search_engine: str = "duckduckgo", max_results: int = 5, **kwargs):
        super().__init__(**kwargs)
        # 使用object.__setattr__绕过Pydantic的字段验证
        object.__setattr__(self, 'verification_tool', OriginalIdeaVerificationTool(
            search_engine=search_engine,
            max_results=max_results
        ))
        logger.info("💡 NeogenesisIdeaVerificationTool 初始化完成")
    
    def _run(
        self, 
        idea_text: str,
        context: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行想法验证
        
        Args:
            idea_text: 想法文本
            context: 验证上下文
            run_manager: LangChain回调管理器
            
        Returns:
            验证结果的JSON字符串
        """
        try:
            logger.info(f"💡 开始验证想法: {idea_text[:50]}...")
            
            # 调用原始的验证工具
            verification_result = self.verification_tool.execute(
                idea_text=idea_text,
                context=context
            )
            
            # 转换为可序列化的格式
            if verification_result.success:
                output = {
                    "verification_success": True,
                    "verification_data": verification_result.data,
                    "execution_time": verification_result.execution_time,
                    "tool_metadata": {
                        "tool_name": self.name,
                        "verification_time": time.time()
                    }
                }
            else:
                output = {
                    "verification_success": False,
                    "error_message": verification_result.error_message,
                    "execution_time": verification_result.execution_time,
                    "tool_metadata": {
                        "tool_name": self.name,
                        "verification_time": time.time()
                    }
                }
            
            logger.info("✅ 想法验证完成")
            return json.dumps(output, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"想法验证失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            fallback_output = {
                "verification_success": False,
                "error": error_msg,
                "fallback_analysis": "无法进行自动验证，建议人工评估",
                "tool_metadata": {"tool_name": self.name, "error_time": time.time()}
            }
            return json.dumps(fallback_output, ensure_ascii=False)

# =============================================================================
# 完整五阶段决策工具
# =============================================================================

class NeogenesisFiveStageDecisionInput(BaseModel):
    """五阶段决策工具的输入模型"""
    user_query: str = Field(description="用户查询或决策问题")
    execution_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="执行上下文（可选）"
    )
    use_rag_enhancement: bool = Field(
        default=True,
        description="是否使用RAG增强（阶段一）"
    )
    enable_seed_verification: bool = Field(
        default=True,
        description="是否启用种子验证（阶段二）"
    )
    max_paths: int = Field(
        default=4,
        description="最大生成路径数（阶段三）"
    )
    enable_path_verification: bool = Field(
        default=True,
        description="是否启用路径验证（阶段四）"
    )
    use_mab_algorithm: bool = Field(
        default=True,
        description="是否使用MAB算法（阶段五）"
    )

class NeogenesisFiveStageDecisionTool(BaseTool):
    """
    Neogenesis完整五阶段决策工具
    
    功能：执行完整的五阶段AI决策流程，为LangChain用户提供端到端的智能决策
    优势：一次调用完成所有阶段，输出详细的决策报告
    """
    
    name: str = "neogenesis_five_stage_decision"
    description: str = """
    执行完整的Neogenesis五阶段AI决策流程，提供端到端的智能决策支持。
    
    五个阶段：
    1. 思维种子生成 - 理解问题，生成分析基础
    2. 种子验证检查 - 验证思维方向的正确性  
    3. 思维路径生成 - 生成多种解决方案路径
    4. 路径验证学习 - 验证和评估各个路径
    5. 智能最终决策 - 使用MAB算法选择最优方案
    
    输入：user_query（必需）和各阶段配置参数
    输出：完整的五阶段决策报告，包含每个阶段的详细结果和最终建议
    
    适用场景：复杂决策问题、战略规划、方案选择、产品设计
    """
    args_schema: Type[BaseModel] = NeogenesisFiveStageDecisionInput
    
    def __init__(self, 
                 api_key: str = "",
                 search_engine: str = "duckduckgo",
                 llm_client=None,
                 web_search_client=None,
                 **kwargs):
        super().__init__(**kwargs)
        
        # 初始化各阶段工具，使用object.__setattr__绕过Pydantic验证
        object.__setattr__(self, 'thinking_seed_tool', NeogenesisThinkingSeedTool(api_key=api_key))
        object.__setattr__(self, 'rag_seed_tool', NeogenesisRAGSeedTool(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client
        ) if llm_client or web_search_client else None)
        object.__setattr__(self, 'verification_tool', NeogenesisIdeaVerificationTool(search_engine=search_engine))
        object.__setattr__(self, 'path_generator_tool', NeogenesisPathGeneratorTool(
            api_key=api_key,
            llm_client=llm_client
        ))
        object.__setattr__(self, 'mab_decision_tool', NeogenesisMABDecisionTool(
            api_key=api_key,
            llm_client=llm_client
        ))
        
        logger.info("🔗 NeogenesisFiveStageDecisionTool 初始化完成")
    
    def _run(
        self,
        user_query: str,
        execution_context: Optional[Dict[str, Any]] = None,
        use_rag_enhancement: bool = True,
        enable_seed_verification: bool = True,
        max_paths: int = 4,
        enable_path_verification: bool = True,
        use_mab_algorithm: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        执行完整的五阶段决策流程
        """
        try:
            logger.info(f"🚀 开始五阶段决策流程: {user_query[:50]}...")
            start_time = time.time()
            
            stage_results = {}
            
            # 🧠 阶段一：思维种子生成
            logger.info("🧠 阶段一：思维种子生成")
            try:
                if use_rag_enhancement and self.rag_seed_tool:
                    seed_result = self.rag_seed_tool._run(
                        user_query=user_query,
                        execution_context=execution_context
                    )
                    seed_data = json.loads(seed_result)
                    thinking_seed = seed_data.get("rag_enhanced_seed", "")
                    stage_results["stage_1"] = {"type": "rag_enhanced", "data": seed_data, "success": True}
                else:
                    seed_result = self.thinking_seed_tool._run(
                        user_query=user_query,
                        execution_context=execution_context
                    )
                    seed_data = json.loads(seed_result)
                    thinking_seed = seed_data.get("thinking_seed", "")
                    stage_results["stage_1"] = {"type": "basic_thinking", "data": seed_data, "success": True}
                
                logger.info("✅ 阶段一完成")
                
            except Exception as e:
                logger.error(f"❌ 阶段一失败: {e}")
                thinking_seed = f"基于问题的基础分析：{user_query}"
                stage_results["stage_1"] = {"success": False, "error": str(e)}
            
            # 🔍 阶段二：种子验证检查
            if enable_seed_verification:
                logger.info("🔍 阶段二：种子验证检查")
                try:
                    verification_result = self.verification_tool._run(
                        idea_text=thinking_seed,
                        context={"stage": "seed_verification", "query": user_query}
                    )
                    verification_data = json.loads(verification_result)
                    stage_results["stage_2"] = {"type": "verification", "data": verification_data, "success": True}
                    logger.info("✅ 阶段二完成")
                except Exception as e:
                    logger.error(f"❌ 阶段二失败: {e}")
                    stage_results["stage_2"] = {"success": False, "error": str(e)}
            else:
                stage_results["stage_2"] = {"type": "skipped", "message": "验证已禁用"}
            
            # 🛤️ 阶段三：思维路径生成
            logger.info("🛤️ 阶段三：思维路径生成")
            try:
                paths_result = self.path_generator_tool._run(
                    thinking_seed=thinking_seed,
                    task=user_query,
                    max_paths=max_paths
                )
                paths_data = json.loads(paths_result)
                reasoning_paths = paths_data.get("reasoning_paths", [])
                stage_results["stage_3"] = {"type": "path_generation", "data": paths_data, "success": True}
                logger.info(f"✅ 阶段三完成：生成{len(reasoning_paths)}条路径")
            except Exception as e:
                logger.error(f"❌ 阶段三失败: {e}")
                reasoning_paths = [{"path_type": "直接分析", "description": thinking_seed, "confidence_score": 0.6}]
                stage_results["stage_3"] = {"success": False, "error": str(e)}
            
            # 🔬 阶段四：路径验证学习
            if enable_path_verification and reasoning_paths:
                logger.info("🔬 阶段四：路径验证学习")
                try:
                    verified_paths = []
                    for i, path in enumerate(reasoning_paths):
                        try:
                            path_text = f"{path.get('path_type', '')}: {path.get('description', '')}"
                            path_verification = self.verification_tool._run(
                                idea_text=path_text,
                                context={"stage": "path_verification", "path_index": i}
                            )
                            verification_data = json.loads(path_verification)
                            path["verification_result"] = verification_data
                            verified_paths.append(path)
                        except:
                            verified_paths.append(path)  # 保留原路径
                    
                    reasoning_paths = verified_paths
                    stage_results["stage_4"] = {"type": "path_verification", "verified_count": len(verified_paths), "success": True}
                    logger.info(f"✅ 阶段四完成：验证{len(verified_paths)}条路径")
                except Exception as e:
                    logger.error(f"❌ 阶段四失败: {e}")
                    stage_results["stage_4"] = {"success": False, "error": str(e)}
            else:
                stage_results["stage_4"] = {"type": "skipped", "message": "路径验证已禁用"}
            
            # 🏆 阶段五：智能最终决策
            logger.info("🏆 阶段五：智能最终决策")
            try:
                if use_mab_algorithm and reasoning_paths:
                    decision_result = self.mab_decision_tool._run(
                        reasoning_paths=reasoning_paths,
                        user_query=user_query,
                        execution_context=execution_context
                    )
                    decision_data = json.loads(decision_result)
                    final_decision = decision_data.get("selected_path", {})
                    stage_results["stage_5"] = {"type": "mab_decision", "data": decision_data, "success": True}
                else:
                    final_decision = reasoning_paths[0] if reasoning_paths else {}
                    stage_results["stage_5"] = {"type": "simple_selection", "selected": final_decision, "success": True}
                
                logger.info("✅ 阶段五完成")
            except Exception as e:
                logger.error(f"❌ 阶段五失败: {e}")
                final_decision = reasoning_paths[0] if reasoning_paths else {"description": "无法完成决策"}
                stage_results["stage_5"] = {"success": False, "error": str(e)}
            
            # 构建完整报告
            end_time = time.time()
            complete_report = {
                "success": True,
                "user_query": user_query,
                "execution_time": end_time - start_time,
                "thinking_seed": thinking_seed,
                "stage_results": stage_results,
                "final_recommendation": final_decision,
                "summary": {
                    "stages_completed": len([s for s in stage_results.values() if s.get("success", False)]),
                    "success_rate": len([s for s in stage_results.values() if s.get("success", False)]) / 5 * 100,
                    "paths_generated": len(reasoning_paths) if reasoning_paths else 0
                }
            }
            
            logger.info("🎉 五阶段决策流程完成")
            return json.dumps(complete_report, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"❌ 五阶段流程失败: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "user_query": user_query
            }, ensure_ascii=False)

# =============================================================================
# 工具注册和管理
# =============================================================================

def get_all_neogenesis_tools(
    api_key: str = "",
    search_engine: str = "duckduckgo",
    llm_client=None,
    web_search_client=None
) -> List[BaseTool]:
    """
    获取所有Neogenesis工具的列表
    
    Args:
        api_key: API密钥
        search_engine: 搜索引擎类型
        llm_client: LLM客户端
        web_search_client: 网络搜索客户端
        
    Returns:
        工具列表
    """
    tools = [
        NeogenesisThinkingSeedTool(api_key=api_key),
        NeogenesisRAGSeedTool(
            api_key=api_key,
            search_engine=search_engine,
            web_search_client=web_search_client,
            llm_client=llm_client
        ),
        NeogenesisPathGeneratorTool(
            api_key=api_key,
            llm_client=llm_client
        ),
        NeogenesisMABDecisionTool(
            api_key=api_key,
            llm_client=llm_client
        ),
        NeogenesisIdeaVerificationTool(
            search_engine=search_engine
        ),
        NeogenesisFiveStageDecisionTool(
            api_key=api_key,
            search_engine=search_engine,
            llm_client=llm_client,
            web_search_client=web_search_client
        )
    ]
    
    logger.info(f"🔧 创建了 {len(tools)} 个Neogenesis工具")
    return tools

def create_neogenesis_toolset(config: Dict[str, Any] = None) -> Dict[str, BaseTool]:
    """
    创建Neogenesis工具集合
    
    Args:
        config: 配置字典
        
    Returns:
        工具名称到工具对象的映射
    """
    if config is None:
        config = {}
    
    tools_list = get_all_neogenesis_tools(**config)
    tools_dict = {tool.name: tool for tool in tools_list}
    
    logger.info(f"🛠️ Neogenesis工具集合创建完成: {list(tools_dict.keys())}")
    return tools_dict

# =============================================================================
# 兼容性检查
# =============================================================================

def check_langchain_compatibility() -> Dict[str, Any]:
    """
    检查LangChain兼容性
    
    Returns:
        兼容性信息
    """
    compatibility_info = {
        "langchain_available": LANGCHAIN_AVAILABLE,
        "required_packages": ["langchain", "langchain-core"],
        "optional_packages": ["langchain-openai", "langchain-anthropic"],
        "recommendation": "Install LangChain for full functionality"
    }
    
    if LANGCHAIN_AVAILABLE:
        try:
            from langchain import __version__ as langchain_version
            compatibility_info["langchain_version"] = langchain_version
        except:
            compatibility_info["langchain_version"] = "unknown"
    
    return compatibility_info

if __name__ == "__main__":
    # 测试工具创建
    print("🧪 测试Neogenesis工具创建...")
    
    # 检查兼容性
    compat_info = check_langchain_compatibility()
    print(f"兼容性信息: {compat_info}")
    
    # 创建工具
    try:
        tools = get_all_neogenesis_tools()
        print(f"✅ 成功创建 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")
    except Exception as e:
        print(f"❌ 工具创建失败: {e}")
