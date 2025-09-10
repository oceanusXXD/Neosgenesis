"""
Neogenesis System Web API Module

这个模块提供了 Neogenesis System 的 FastAPI Web API 接口。
它将核心认知引擎、规划器和其他组件的功能暴露为 RESTful API 服务。

主要功能：
- 认知引擎 API 接口
- 规划和决策 API
- 知识管理和检索 API  
- 系统状态监控 API
"""

from .main import app
from .models import *

__version__ = "1.0.0"
__author__ = "Neogenesis System Team"

__all__ = [
    "app",
]
