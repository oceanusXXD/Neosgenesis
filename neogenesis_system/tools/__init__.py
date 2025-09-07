#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tools Package - 工具包

提供统一的工具抽象接口和工具管理功能。
所有工具都遵循相同的接口规范，便于系统统一调用和管理。
"""

# 导出主要的工具相关类和函数
from .tool_abstraction import (
    Tool, 
    BaseTool,
    tool,
    ToolExecutionError,
    ToolManager,
    get_registered_tools,
    register_tool,
    call_tool
)

# 导入默认工具
from .default_tools import DefaultTools

__all__ = [
    # 核心工具抽象
    "Tool",
    "BaseTool", 
    "tool",
    "ToolExecutionError",
    
    # 工具管理
    "ToolManager",
    "get_registered_tools",
    "register_tool", 
    "call_tool",
    
    # 默认工具
    "DefaultTools"
]
