#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@tool 装饰器演示 - Tool Decorator Demo
展示从"类定义与手动注册"到"函数定义即自动注册"的核心改造

🔥 核心对比演示：
- 旧方式：需要编写完整的类，手动注册
- 新方式：只需要一个@tool装饰器！

运行此文件可以看到新装饰器系统的强大功能
"""

import time
import logging
from typing import Dict, List, Optional

# 导入装饰器系统
from tools.tool_abstraction import (
    tool, ToolCategory, ToolResult,
    list_available_tools, execute_tool, get_tool_info,
    is_tool, get_tool_instance
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 🔥 新方式演示：使用 @tool 装饰器
# ============================================================================

@tool(category=ToolCategory.SEARCH)
def web_search(query: str, limit: int = 10) -> Dict[str, List[str]]:
    """
    网络搜索工具
    根据查询字符串返回搜索结果
    """
    # 模拟搜索逻辑
    time.sleep(0.1)  # 模拟网络延迟
    
    results = [
        f"搜索结果 {i}: {query} 相关内容" for i in range(1, limit + 1)
    ]
    
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@tool(category=ToolCategory.DATA_PROCESSING)
def text_analyzer(text: str, include_stats: bool = True) -> Dict:
    """
    文本分析工具
    分析文本的基本统计信息
    """
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    
    analysis = {
        "text": text,
        "word_count": word_count,
        "char_count": char_count,
    }
    
    if include_stats:
        analysis.update({
            "avg_word_length": char_count / max(word_count, 1),
            "sentences": text.count('.') + text.count('!') + text.count('?'),
        })
    
    return analysis


@tool(category=ToolCategory.SYSTEM, aliases=["calc", "math"])
def calculator(expression: str) -> ToolResult:
    """
    计算器工具
    计算数学表达式并返回结果
    
    注意：这个函数直接返回ToolResult，演示高级用法
    """
    try:
        # 安全的计算（仅支持基本运算）
        allowed_chars = set('0123456789+-*/().= ')
        if not all(c in allowed_chars for c in expression):
            return ToolResult(
                success=False,
                error_message="表达式包含不安全字符"
            )
        
        result = eval(expression)
        
        return ToolResult(
            success=True,
            data={
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            },
            metadata={
                "calculation_engine": "eval",
                "precision": "standard"
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            error_message=f"计算错误: {e}"
        )


@tool(category=ToolCategory.LLM)
async def async_text_generator(prompt: str, max_length: int = 100) -> str:
    """
    异步文本生成工具
    演示异步函数的自动处理
    """
    import asyncio
    
    # 模拟异步生成过程
    await asyncio.sleep(0.2)
    
    # 简单的文本生成逻辑
    generated = f"基于提示 '{prompt}' 生成的文本内容..."
    
    # 限制长度
    if len(generated) > max_length:
        generated = generated[:max_length-3] + "..."
    
    return generated


# ============================================================================
# 🔧 演示新系统的使用
# ============================================================================

def demo_tool_decorator_system():
    """演示新的@tool装饰器系统"""
    
    print("=" * 80)
    print("🔥 @tool 装饰器系统演示")
    print("=" * 80)
    
    # 1. 检查工具自动注册
    print("\n📋 1. 查看自动注册的工具:")
    tools = list_available_tools()
    for tool_name in tools:
        if any(func_name in tool_name for func_name in 
               ['web_search', 'text_analyzer', 'calculator', 'async_text_generator']):
            print(f"  ✅ {tool_name}")
    
    # 2. 检查函数是否为工具
    print("\n🔍 2. 检查函数工具属性:")
    print(f"  web_search 是工具吗? {is_tool(web_search)}")
    print(f"  text_analyzer 是工具吗? {is_tool(text_analyzer)}")
    
    # 3. 获取工具实例信息
    print("\n📊 3. 工具详细信息:")
    tool_instance = get_tool_instance(web_search)
    if tool_instance:
        print(f"  工具名称: {tool_instance.name}")
        print(f"  工具类别: {tool_instance.category.value}")
        print(f"  函数名称: {tool_instance.function_name}")
        print(f"  模块名称: {tool_instance.module_name}")
    
    # 4. 通过工具系统执行
    print("\n🚀 4. 通过工具系统执行:")
    
    # 执行搜索工具
    search_result = execute_tool("web_search", "Python编程", limit=3)
    if search_result and search_result.success:
        print(f"  搜索结果: {search_result.data}")
        print(f"  执行时间: {search_result.execution_time:.3f}秒")
    
    # 执行文本分析工具
    analysis_result = execute_tool("text_analyzer", 
                                   "这是一个测试文本。包含两个句子！", 
                                   include_stats=True)
    if analysis_result and analysis_result.success:
        print(f"  文本分析: {analysis_result.data}")
    
    # 执行计算器工具（使用别名）
    calc_result = execute_tool("calc", "2 + 3 * 4")
    if calc_result and calc_result.success:
        print(f"  计算结果: {calc_result.data}")
    
    # 5. 直接调用函数（保持原有功能）
    print("\n📞 5. 直接调用函数（原有功能保持不变）:")
    direct_result = web_search("直接调用测试", limit=2)
    print(f"  直接调用结果: {direct_result}")
    
    # 6. 查看工具统计信息
    print("\n📈 6. 工具使用统计:")
    info = get_tool_info("web_search")
    if info:
        print(f"  使用次数: {info['usage']['usage_count']}")
        print(f"  工具状态: {info['status']}")
        print(f"  支持的输入: {info['capabilities']['supported_inputs']}")
    
    print("\n" + "=" * 80)
    print("🎉 演示完成！从'类定义与手动注册'到'函数定义即自动注册'的改造成功！")
    print("=" * 80)


# ============================================================================
# 🔍 对比：旧方式 vs 新方式
# ============================================================================

def show_comparison():
    """展示旧方式与新方式的对比"""
    
    print("\n" + "=" * 80)
    print("📊 旧方式 vs 新方式对比")
    print("=" * 80)
    
    print("\n❌ 旧方式（繁琐）:")
    print("""
class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="网络搜索工具，根据查询字符串返回搜索结果",
            category=ToolCategory.SEARCH
        )
    
    @property
    def capabilities(self):
        return ToolCapability(
            supported_inputs=["str", "int"],
            output_types=["dict"],
            async_support=False,
            batch_support=False,
            requires_auth=False,
            rate_limited=False
        )
    
    def execute(self, *args, **kwargs):
        # 参数验证
        # 错误处理
        # 结果包装
        # 统计更新
        # 实际逻辑...
        pass

# 手动注册
tool = WebSearchTool()
register_tool(tool)
    """)
    
    print("\n✅ 新方式（简洁）:")
    print("""
@tool(category=ToolCategory.SEARCH)
def web_search(query: str, limit: int = 10) -> Dict[str, List[str]]:
    '''网络搜索工具，根据查询字符串返回搜索结果'''
    # 只需要写核心逻辑！
    results = [f"搜索结果 {i}: {query} 相关内容" for i in range(1, limit + 1)]
    return {"query": query, "results": results, "total": len(results)}
    """)
    
    print("\n💡 改造收益:")
    print("  📉 代码量减少: ~80%")
    print("  🎯 关注点分离: 只需关注业务逻辑")
    print("  🔄 自动化: 元数据提取、参数验证、错误处理、注册等全自动")
    print("  🛡️ 一致性: 统一的接口和行为")
    print("  🚀 开发效率: 大幅提升工具开发速度")


if __name__ == "__main__":
    # 运行演示
    demo_tool_decorator_system()
    show_comparison()
