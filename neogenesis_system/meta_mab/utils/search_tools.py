#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索工具 - Search Tools
将现有的搜索客户端封装成符合统一Tool接口的工具
"""

import time
import logging
from typing import Any, Dict, List, Optional, Union

# 导入统一工具接口
from .tool_abstraction import (
    BaseTool, 
    AsyncBaseTool, 
    BatchProcessingTool,
    ToolCategory, 
    ToolResult, 
    ToolCapability,
    ToolStatus,
    register_tool
)

# 导入现有搜索客户端
from .search_client import (
    WebSearchClient, 
    IdeaVerificationSearchClient,
    SearchResult, 
    SearchResponse,
    IdeaVerificationResult
)

logger = logging.getLogger(__name__)


class WebSearchTool(BatchProcessingTool):
    """
    网络搜索工具 - 将WebSearchClient封装为统一Tool接口
    
    功能：执行网络搜索，获取相关信息
    适用场景：信息检索、事实验证、实时信息获取
    """
    
    def __init__(self, search_engine: str = "duckduckgo", max_results: int = 5):
        """
        初始化网络搜索工具
        
        Args:
            search_engine: 搜索引擎类型
            max_results: 最大结果数量
        """
        super().__init__(
            name="web_search",
            description=(
                "执行网络搜索并返回相关结果。"
                "输入：搜索查询字符串；"
                "输出：包含标题、摘要、URL的搜索结果列表。"
                "适用于信息检索、事实验证、获取最新资讯等场景。"
            ),
            category=ToolCategory.SEARCH
        )
        
        # 初始化底层搜索客户端
        self._search_client = WebSearchClient(
            search_engine=search_engine,
            max_results=max_results
        )
        
        logger.info(f"🔍 网络搜索工具初始化完成 - 引擎: {search_engine}, 最大结果: {max_results}")
    
    @property
    def capabilities(self) -> ToolCapability:
        """返回工具能力描述"""
        return ToolCapability(
            supported_inputs=["string", "search_query"],
            output_types=["search_results", "json"],
            async_support=False,
            batch_support=True,
            requires_auth=False,
            rate_limited=True
        )
    
    def validate_input(self, query: str, **kwargs) -> bool:
        """
        验证搜索输入
        
        Args:
            query: 搜索查询
            **kwargs: 其他参数
            
        Returns:
            bool: 输入是否有效
        """
        if not isinstance(query, str):
            logger.error(f"❌ 搜索输入无效: 期望字符串，得到 {type(query)}")
            return False
        
        if not query.strip():
            logger.error("❌ 搜索输入无效: 查询字符串为空")
            return False
        
        if len(query.strip()) < 2:
            logger.error("❌ 搜索输入无效: 查询字符串过短")
            return False
        
        return True
    
    def execute(self, query: str, max_results: Optional[int] = None, **kwargs) -> ToolResult:
        """
        执行网络搜索
        
        Args:
            query: 搜索查询字符串
            max_results: 最大结果数量（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 包含搜索结果的工具结果
        """
        start_time = time.time()
        
        # 更新工具状态
        self._set_status(ToolStatus.BUSY)
        
        try:
            # 验证输入
            if not self.validate_input(query, **kwargs):
                return ToolResult(
                    success=False,
                    error_message="输入验证失败",
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"🔍 执行网络搜索: {query[:50]}...")
            
            # 执行搜索
            search_response = self._search_client.search(query, max_results)
            
            execution_time = time.time() - start_time
            
            # 更新使用统计
            self._update_usage_stats()
            
            if search_response.success:
                # 转换为标准格式
                results_data = {
                    "query": search_response.query,
                    "results": [
                        {
                            "title": result.title,
                            "snippet": result.snippet,
                            "url": result.url,
                            "relevance_score": result.relevance_score
                        }
                        for result in search_response.results
                    ],
                    "total_results": search_response.total_results,
                    "search_time": search_response.search_time
                }
                
                logger.info(f"✅ 搜索完成: 找到 {len(search_response.results)} 个结果")
                
                return ToolResult(
                    success=True,
                    data=results_data,
                    execution_time=execution_time,
                    metadata={
                        "search_engine": self._search_client.search_engine,
                        "original_response": search_response
                    }
                )
            else:
                logger.error(f"❌ 搜索失败: {search_response.error_message}")
                
                return ToolResult(
                    success=False,
                    error_message=search_response.error_message,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"搜索工具执行异常: {e}"
            logger.error(f"❌ {error_msg}")
            
            return ToolResult(
                success=False,
                error_message=error_msg,
                execution_time=execution_time
            )
        
        finally:
            # 恢复工具状态
            self._set_status(ToolStatus.READY)
    
    def execute_batch(self, input_list: List[str], **kwargs) -> List[ToolResult]:
        """
        批量执行搜索
        
        Args:
            input_list: 搜索查询列表
            **kwargs: 其他参数
            
        Returns:
            List[ToolResult]: 搜索结果列表
        """
        logger.info(f"🔍 批量搜索开始: {len(input_list)} 个查询")
        
        results = []
        for i, query in enumerate(input_list):
            logger.debug(f"🔍 批量搜索 {i+1}/{len(input_list)}: {query[:30]}...")
            result = self.execute(query, **kwargs)
            results.append(result)
            
            # 批量处理时增加间隔，避免速率限制
            if i < len(input_list) - 1:
                time.sleep(0.5)
        
        successful_count = sum(1 for r in results if r.success)
        logger.info(f"✅ 批量搜索完成: {successful_count}/{len(input_list)} 成功")
        
        return results


class IdeaVerificationTool(BaseTool):
    """
    想法验证工具 - 将IdeaVerificationSearchClient封装为统一Tool接口
    
    功能：验证想法的可行性，提供分析和建议
    适用场景：创意评估、可行性分析、决策支持
    """
    
    def __init__(self, search_engine: str = "duckduckgo", max_results: int = 5):
        """
        初始化想法验证工具
        
        Args:
            search_engine: 搜索引擎类型
            max_results: 最大结果数量
        """
        super().__init__(
            name="idea_verification",
            description=(
                "验证想法或概念的可行性，提供详细分析和建议。"
                "输入：想法描述文本；"
                "输出：可行性评分、分析摘要、相关搜索结果。"
                "适用于创意评估、投资决策、产品规划等场景。"
            ),
            category=ToolCategory.SEARCH
        )
        
        # 初始化底层验证客户端
        # IdeaVerificationSearchClient需要WebSearchClient实例，不是search_engine参数
        web_search_client = WebSearchClient(search_engine=search_engine, max_results=max_results)
        self._verification_client = IdeaVerificationSearchClient(web_search_client)
        
        logger.info(f"💡 想法验证工具初始化完成")
    
    @property
    def capabilities(self) -> ToolCapability:
        """返回工具能力描述"""
        return ToolCapability(
            supported_inputs=["string", "idea_text"],
            output_types=["verification_result", "json"],
            async_support=False,
            batch_support=False,
            requires_auth=False,
            rate_limited=True
        )
    
    def validate_input(self, idea_text: str, **kwargs) -> bool:
        """
        验证想法输入
        
        Args:
            idea_text: 想法描述文本
            **kwargs: 其他参数
            
        Returns:
            bool: 输入是否有效
        """
        if not isinstance(idea_text, str):
            logger.error(f"❌ 想法验证输入无效: 期望字符串，得到 {type(idea_text)}")
            return False
        
        if not idea_text.strip():
            logger.error("❌ 想法验证输入无效: 想法文本为空")
            return False
        
        if len(idea_text.strip()) < 10:
            logger.error("❌ 想法验证输入无效: 想法描述过短")
            return False
        
        return True
    
    def execute(self, idea_text: str, **kwargs) -> ToolResult:
        """
        执行想法验证
        
        Args:
            idea_text: 想法描述文本
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 包含验证结果的工具结果
        """
        start_time = time.time()
        
        # 更新工具状态
        self._set_status(ToolStatus.BUSY)
        
        try:
            # 验证输入
            if not self.validate_input(idea_text, **kwargs):
                return ToolResult(
                    success=False,
                    error_message="输入验证失败",
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"💡 执行想法验证: {idea_text[:50]}...")
            
            # 执行验证
            verification_result = self._verification_client.verify_idea(idea_text)
            
            execution_time = time.time() - start_time
            
            # 更新使用统计
            self._update_usage_stats()
            
            if verification_result.success:
                # 转换为标准格式
                results_data = {
                    "idea_text": verification_result.idea_text,
                    "feasibility_score": verification_result.feasibility_score,
                    "analysis_summary": verification_result.analysis_summary,
                    "search_results": [
                        {
                            "title": result.title,
                            "snippet": result.snippet,
                            "url": result.url,
                            "relevance_score": result.relevance_score
                        }
                        for result in verification_result.search_results
                    ]
                }
                
                logger.info(f"✅ 想法验证完成: 可行性评分 {verification_result.feasibility_score:.2f}")
                
                return ToolResult(
                    success=True,
                    data=results_data,
                    execution_time=execution_time,
                    metadata={
                        "verification_engine": self._verification_client.search_engine,
                        "original_result": verification_result
                    }
                )
            else:
                logger.error(f"❌ 想法验证失败: {verification_result.error_message}")
                
                return ToolResult(
                    success=False,
                    error_message=verification_result.error_message,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"想法验证工具执行异常: {e}"
            logger.error(f"❌ {error_msg}")
            
            return ToolResult(
                success=False,
                error_message=error_msg,
                execution_time=execution_time
            )
        
        finally:
            # 恢复工具状态
            self._set_status(ToolStatus.READY)


# 便捷函数：创建和注册搜索工具
def create_and_register_search_tools():
    """创建并注册所有搜索工具到全局注册表"""
    
    # 创建网络搜索工具
    web_search_tool = WebSearchTool()
    register_tool(web_search_tool)
    
    # 创建想法验证工具
    idea_verification_tool = IdeaVerificationTool()
    register_tool(idea_verification_tool)
    
    logger.info("🔧 所有搜索工具已创建并注册")
    
    return {
        "web_search": web_search_tool,
        "idea_verification": idea_verification_tool
    }


# 便捷函数：快速搜索
def quick_web_search(query: str, max_results: int = 5) -> ToolResult:
    """
    便捷函数：快速执行网络搜索
    
    Args:
        query: 搜索查询
        max_results: 最大结果数量
        
    Returns:
        ToolResult: 搜索结果
    """
    tool = WebSearchTool(max_results=max_results)
    return tool.execute(query)


# 便捷函数：快速想法验证
def quick_idea_verification(idea_text: str) -> ToolResult:
    """
    便捷函数：快速执行想法验证
    
    Args:
        idea_text: 想法描述
        
    Returns:
        ToolResult: 验证结果
    """
    tool = IdeaVerificationTool()
    return tool.execute(idea_text)
