#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System Test Suite
测试套件包
"""

__version__ = "1.0.0"
__author__ = "Neogenesis Team"

# 测试工具导入
import os
import sys

# 添加项目根目录到Python路径
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)