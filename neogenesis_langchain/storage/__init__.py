'''
Author: answeryt answeryt@qq.com
Date: 2025-09-03 12:46:24
LastEditors: answeryt answeryt@qq.com
LastEditTime: 2025-09-03 13:40:28
FilePath: \Neosgenesis\neogenesis_langchain\storage\__init__.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis LangChain - Storage Module
存储相关组件：持久化存储引擎和配置
"""

from .persistent_storage import (
    # 核心类
    PersistentStorageEngine,
    StorageConfig,
    StorageBackend,
    CompressionType,
    
    # 工厂函数
    create_storage_engine,
)

__all__ = [
    # 核心类
    "PersistentStorageEngine",
    "StorageConfig",
    "StorageBackend", 
    "CompressionType",
    
    # 工厂函数
    "create_storage_engine",
]
