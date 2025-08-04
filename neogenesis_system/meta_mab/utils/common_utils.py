#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用工具函数模块 - Common Utility Functions
从 api_caller.py 迁移的工具函数，独立于任何特定的API客户端实现
"""

import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """
    解析DeepSeek的JSON响应
    
    Args:
        response: API响应字符串
        
    Returns:
        解析后的字典，如果解析失败返回None
    """
    # 首先验证输入类型
    if not isinstance(response, (str, bytes, bytearray)):
        logger.error(f"❌ 解析DeepSeek响应失败: 输入类型错误，期望字符串，实际得到 {type(response)}")
        logger.error(f"原始响应: {str(response)[:200]}...")
        return None  # 返回None表示无效输入
    
    # 如果是bytes或bytearray，转换为字符串
    if isinstance(response, (bytes, bytearray)):
        try:
            response = response.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"❌ 解析DeepSeek响应失败: 编码错误 {e}")
            return None
    
    # 检查空字符串
    if not response or not response.strip():
        logger.error("❌ 解析DeepSeek响应失败: 响应为空")
        return None
    
    try:
        # 尝试直接解析JSON
        response_stripped = response.strip()
        if response_stripped.startswith('{') and response_stripped.endswith('}'):
            return json.loads(response_stripped)
        
        # 尝试从markdown代码块中提取JSON
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 尝试从response中提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ 解析DeepSeek响应失败: JSON格式错误 {e}")
        logger.error(f"原始响应: {response[:200]}...")
    except Exception as e:
        logger.error(f"❌ 解析DeepSeek响应失败: {e}")
        logger.error(f"原始响应: {response[:200]}...")
    
    # 解析失败时返回None，让调用方决定如何处理
    return None


def extract_context_factors(user_query: str) -> List[str]:
    """
    从用户查询中提取上下文因子
    
    Args:
        user_query: 用户查询
        
    Returns:
        上下文因子列表
    """
    query_lower = user_query.lower()
    factors = []
    
    # 技术关键词
    tech_keywords = {
        'api': 'api_related',
        '数据库': 'database_related',
        '网络': 'network_related',
        '文件': 'file_related',
        '爬虫': 'scraping_related',
        '分析': 'analysis_related',
        '机器学习': 'ml_related',
        '实时': 'real_time',
        '高性能': 'high_performance',
        '安全': 'security_related'
    }
    
    for keyword, factor in tech_keywords.items():
        if keyword in query_lower:
            factors.append(factor)
    
    # 复杂度关键词
    complexity_keywords = {
        '复杂': 'high_complexity',
        '简单': 'low_complexity',
        '快速': 'speed_critical',
        '稳定': 'stability_critical',
        '优化': 'optimization_needed'
    }
    
    for keyword, factor in complexity_keywords.items():
        if keyword in query_lower:
            factors.append(factor)
    
    return factors


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        
    Returns:
        相似度分数 (0.0-1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥的有效性
    
    Args:
        api_key: API密钥
        
    Returns:
        是否有效
    """
    if not api_key or len(api_key) < 10:
        return False
    
    # 可以添加更多验证逻辑
    # 例如：格式检查、长度检查等
    
    return True


def format_prompt_with_context(template: str, **kwargs) -> str:
    """
    使用上下文信息格式化提示模板
    
    Args:
        template: 提示模板
        **kwargs: 上下文变量
        
    Returns:
        格式化后的提示
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"⚠️ 提示模板缺少变量: {e}")
        # 用空字符串替换缺失的变量
        for key in e.args:
            kwargs[key] = ""
        return template.format(**kwargs)
    except Exception as e:
        logger.error(f"❌ 提示模板格式化失败: {e}")
        return template