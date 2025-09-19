#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Default Tools - 默认工具定义

这个模块定义了系统的内置工具，如idea_verification等。
提供基础工具的具体实现。

"""

from typing import Dict, Any, List
from .tool_abstraction import BaseTool, ToolCategory, ToolResult

# 导入图像生成工具
try:
    from .image_generation_tools import ImageGenerationTool, generate_image_simple
    IMAGE_TOOLS_AVAILABLE = True
except ImportError:
    IMAGE_TOOLS_AVAILABLE = False


class Tool:
    """简化的工具类，用于快速创建工具实例"""
    
    def __init__(self, name: str, description: str, function: callable, parameters: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters or {}
    
    def execute(self, **kwargs) -> Any:
        """执行工具函数"""
        return self.function(**kwargs)


class DefaultTools:
    """默认工具集合"""
    
    @staticmethod
    def get_all_default_tools() -> List[Tool]:
        """获取所有默认工具"""
        tools = [
            DefaultTools.idea_verification_tool(),
            DefaultTools.search_tool(),
            DefaultTools.analysis_tool()
        ]
        
        # 添加图像生成工具（如果依赖可用）
        if IMAGE_TOOLS_AVAILABLE:
            tools.extend([
                DefaultTools.image_generation_tool(),
                DefaultTools.batch_image_generation_tool()
            ])
        
        return tools
    
    @staticmethod
    def idea_verification_tool() -> Tool:
        """思想验证工具"""
        def verify_idea(idea: str, criteria: List[str] = None) -> Dict[str, Any]:
            """验证思想的可行性和质量"""
            if criteria is None:
                criteria = ["feasibility", "novelty", "impact", "clarity"]
            
            # 基础验证逻辑（可扩展）
            results = {
                "idea": idea,
                "verification_results": {},
                "overall_score": 0.0,
                "recommendations": []
            }
            
            for criterion in criteria:
                # 简化的评分逻辑（实际实现可以更复杂）
                if criterion == "feasibility":
                    score = 0.8 if len(idea.split()) > 5 else 0.5
                elif criterion == "novelty":
                    score = 0.7 if "创新" in idea or "新" in idea else 0.6
                elif criterion == "impact":
                    score = 0.9 if "影响" in idea or "改进" in idea else 0.7
                elif criterion == "clarity":
                    score = 0.8 if len(idea) > 20 else 0.6
                else:
                    score = 0.7
                
                results["verification_results"][criterion] = score
            
            # 计算总体分数
            results["overall_score"] = sum(results["verification_results"].values()) / len(criteria)
            
            # 生成建议
            if results["overall_score"] < 0.6:
                results["recommendations"].append("需要进一步完善思想")
            if results["verification_results"].get("feasibility", 0) < 0.7:
                results["recommendations"].append("考虑提高可行性")
            
            return results
        
        return Tool(
            name="idea_verification",
            description="验证思想的可行性、新颖性和影响力",
            function=verify_idea,
            parameters={
                "idea": {"type": "str", "description": "要验证的思想"},
                "criteria": {"type": "List[str]", "description": "验证标准", "optional": True}
            }
        )
    
    @staticmethod
    def search_tool() -> Tool:
        """搜索工具"""
        def search_knowledge(query: str, max_results: int = 5) -> Dict[str, Any]:
            """搜索相关知识"""
            # 模拟搜索结果
            return {
                "query": query,
                "results": [
                    {
                        "title": f"关于'{query}'的研究",
                        "content": f"这是关于{query}的详细信息...",
                        "relevance": 0.9,
                        "source": "知识库"
                    }
                    # 可以添加更多模拟结果
                ],
                "total_found": max_results
            }
        
        return Tool(
            name="search_knowledge",
            description="搜索相关知识和信息",
            function=search_knowledge,
            parameters={
                "query": {"type": "str", "description": "搜索查询"},
                "max_results": {"type": "int", "description": "最大结果数", "optional": True}
            }
        )
    
    @staticmethod
    def analysis_tool() -> Tool:
        """分析工具"""
        def analyze_text(text: str, analysis_type: str = "sentiment") -> Dict[str, Any]:
            """分析文本内容"""
            results = {
                "text": text,
                "analysis_type": analysis_type,
                "results": {}
            }
            
            if analysis_type == "sentiment":
                # 简化的情感分析
                positive_words = ["好", "优秀", "成功", "有效", "创新"]
                negative_words = ["差", "失败", "问题", "困难", "错误"]
                
                positive_count = sum(1 for word in positive_words if word in text)
                negative_count = sum(1 for word in negative_words if word in text)
                
                if positive_count > negative_count:
                    sentiment = "positive"
                    score = 0.7 + (positive_count - negative_count) * 0.1
                elif negative_count > positive_count:
                    sentiment = "negative" 
                    score = 0.3 - (negative_count - positive_count) * 0.1
                else:
                    sentiment = "neutral"
                    score = 0.5
                
                results["results"] = {
                    "sentiment": sentiment,
                    "score": max(0.0, min(1.0, score)),
                    "positive_indicators": positive_count,
                    "negative_indicators": negative_count
                }
            
            elif analysis_type == "complexity":
                # 文本复杂度分析
                word_count = len(text.split())
                char_count = len(text)
                avg_word_length = char_count / max(word_count, 1)
                
                results["results"] = {
                    "word_count": word_count,
                    "character_count": char_count,
                    "average_word_length": avg_word_length,
                    "complexity_score": min(1.0, (word_count * 0.01 + avg_word_length * 0.1))
                }
            
            return results
        
        return Tool(
            name="analyze_text",
            description="分析文本内容的情感、复杂度等特征",
            function=analyze_text,
            parameters={
                "text": {"type": "str", "description": "要分析的文本"},
                "analysis_type": {"type": "str", "description": "分析类型", "optional": True}
            }
        )
    
    @staticmethod
    def image_generation_tool() -> Tool:
        """图像生成工具"""
        def generate_image(prompt: str, save_image: bool = True) -> Dict[str, Any]:
            """
            使用Stable Diffusion XL生成图像
            
            Args:
                prompt: 图像生成提示词
                save_image: 是否保存图像到本地
                
            Returns:
                Dict[str, Any]: 生成结果
            """
            if not IMAGE_TOOLS_AVAILABLE:
                return {
                    "success": False,
                    "error": "图像生成功能不可用。请安装依赖: pip install huggingface_hub Pillow",
                    "result": None
                }
            
            try:
                tool_instance = ImageGenerationTool()
                result = tool_instance.execute(prompt=prompt, save_image=save_image)
                
                return {
                    "success": result.success,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "result": result.result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"图像生成失败: {str(e)}",
                    "result": None
                }
        
        return Tool(
            name="generate_image",
            description="使用Stable Diffusion XL 1.0模型生成高质量图像，支持中英文提示词",
            function=generate_image,
            parameters={
                "prompt": {"type": "str", "description": "图像生成提示词，描述要生成的图像内容"},
                "save_image": {"type": "bool", "description": "是否保存图像到本地", "optional": True}
            }
        )
    
    @staticmethod 
    def batch_image_generation_tool() -> Tool:
        """批量图像生成工具"""
        def batch_generate_images(prompts: List[str], save_images: bool = True) -> Dict[str, Any]:
            """
            批量生成多张图像
            
            Args:
                prompts: 提示词列表
                save_images: 是否保存图像到本地
                
            Returns:
                Dict[str, Any]: 批量生成结果
            """
            if not IMAGE_TOOLS_AVAILABLE:
                return {
                    "success": False,
                    "error": "图像生成功能不可用。请安装依赖: pip install huggingface_hub Pillow",
                    "results": []
                }
            
            if not prompts:
                return {
                    "success": False,
                    "error": "提示词列表不能为空",
                    "results": []
                }
            
            try:
                from .image_generation_tools import batch_generate_images as batch_generate
                return batch_generate(prompts, save_images)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"批量图像生成失败: {str(e)}",
                    "results": []
                }
        
        return Tool(
            name="batch_generate_images",
            description="批量生成多张图像，输入多个提示词，返回所有生成结果",
            function=batch_generate_images,
            parameters={
                "prompts": {"type": "List[str]", "description": "提示词列表"},
                "save_images": {"type": "bool", "description": "是否保存图像到本地", "optional": True}
            }
        )
