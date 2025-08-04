#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
强化版 DeepSeek 客户端使用示例
Enhanced DeepSeek Client Usage Examples

演示各种使用方式和高级功能
"""

import os
import time
import json
from typing import Dict, Any

from .deepseek_client import (
    DeepSeekClient, 
    ClientConfig, 
    create_client, 
    quick_chat,
    APIErrorType
)
from .client_adapter import DeepSeekClientAdapter


def example_basic_usage():
    """基本使用示例"""
    print("📝 基本使用示例")
    print("-" * 40)
    
    api_key = os.getenv('DEEPSEEK_API_KEY', 'your_api_key_here')
    
    # 方式1: 使用工厂函数创建客户端
    with create_client(api_key) as client:
        response = client.simple_chat(
            prompt="如何提升团队创新能力？",
            system_message="你是一个专业的管理顾问"
        )
        
        if response.success:
            print(f"✅ 成功: {response.content[:100]}...")
            print(f"📊 响应时间: {response.response_time:.2f}s")
            print(f"🎯 Token使用: {response.tokens_used}")
        else:
            print(f"❌ 失败: {response.error_message}")


def example_advanced_usage():
    """高级使用示例"""
    print("\n📝 高级使用示例")
    print("-" * 40)
    
    api_key = os.getenv('DEEPSEEK_API_KEY', 'your_api_key_here')
    
    # 自定义配置
    config = ClientConfig(
        api_key=api_key,
        temperature=0.8,
        max_tokens=1500,
        enable_cache=True,
        cache_ttl=600,  # 10分钟缓存
        enable_metrics=True
    )
    
    with DeepSeekClient(config) as client:
        # 多轮对话
        messages = [
            {"role": "user", "content": "什么是人工智能？"},
            {"role": "assistant", "content": "人工智能（AI）是计算机科学的一个分支..."},
            {"role": "user", "content": "AI的发展历程是怎样的？"}
        ]
        
        response = client.chat_completion(
            messages=messages,
            temperature=0.7
        )
        
        if response.success:
            print(f"✅ 多轮对话成功")
            print(f"📝 响应: {response.content[:100]}...")
            
            # 获取性能指标
            metrics = client.get_metrics()
            print(f"📊 成功率: {metrics.success_rate:.1%}")
            print(f"⏱️ 平均响应时间: {metrics.average_response_time:.2f}s")
            print(f"🎯 总Token使用: {metrics.total_tokens_used}")


def example_batch_processing():
    """批量处理示例"""
    print("\n📝 批量处理示例")
    print("-" * 40)
    
    api_key = os.getenv('DEEPSEEK_API_KEY', 'your_api_key_here')
    
    queries = [
        "如何提升团队协作效率？",
        "什么是敏捷开发方法？",
        "如何进行有效的项目管理？"
    ]
    
    with create_client(api_key, enable_cache=True) as client:
        with client.batch_mode():
            results = []
            
            for i, query in enumerate(queries, 1):
                print(f"处理查询 {i}/{len(queries)}: {query[:30]}...")
                
                response = client.simple_chat(
                    prompt=query,
                    system_message="你是一个专业的业务顾问"
                )
                
                results.append({
                    'query': query,
                    'success': response.success,
                    'content': response.content if response.success else response.error_message,
                    'response_time': response.response_time
                })
                
                time.sleep(0.5)  # 避免过快请求
            
            # 显示结果
            total_time = sum(r['response_time'] for r in results)
            success_count = sum(1 for r in results if r['success'])
            
            print(f"📊 批量处理完成:")
            print(f"   总查询: {len(results)}")
            print(f"   成功: {success_count}")
            print(f"   总时间: {total_time:.2f}s")
            print(f"   平均时间: {total_time/len(results):.2f}s")


def example_error_handling():
    """错误处理示例"""
    print("\n📝 错误处理示例")
    print("-" * 40)
    
    # 使用无效的API密钥演示错误处理
    invalid_key = "invalid_key_for_demo"
    
    with create_client(invalid_key, max_retries=1) as client:
        response = client.simple_chat("测试查询")
        
        if not response.success:
            print(f"❌ API调用失败:")
            print(f"   错误类型: {response.error_type}")
            print(f"   错误信息: {response.error_message}")
            print(f"   状态码: {response.status_code}")
            
            # 根据错误类型采取不同行动
            if response.error_type == APIErrorType.AUTHENTICATION:
                print("💡 建议: 检查API密钥是否正确")
            elif response.error_type == APIErrorType.RATE_LIMIT:
                print("💡 建议: 减少请求频率或升级API套餐")
            elif response.error_type == APIErrorType.NETWORK_ERROR:
                print("💡 建议: 检查网络连接")


def example_compatibility_adapter():
    """兼容性适配器示例"""
    print("\n📝 兼容性适配器示例")
    print("-" * 40)
    
    api_key = os.getenv('DEEPSEEK_API_KEY', 'your_api_key_here')
    
    # 使用适配器，提供与旧API完全相同的接口
    adapter = DeepSeekClientAdapter(api_key)
    
    try:
        # 这个接口与原来的 DeepSeekAPICaller.call_api 完全相同
        result = adapter.call_api(
            prompt="分析市场趋势",
            temperature=0.7,
            system_message="你是一个市场分析师"
        )
        
        print(f"✅ 兼容性调用成功: {result[:100]}...")
        
        # 但底层使用的是强化版客户端，可以获取额外的性能指标
        metrics = adapter.get_metrics()
        print(f"📊 强化功能 - 成功率: {metrics.success_rate:.1%}")
        
    except ConnectionError as e:
        print(f"❌ 兼容性调用失败: {e}")
    
    finally:
        # 清理资源
        adapter.session.close()


def example_quick_chat():
    """快速聊天示例"""
    print("\n📝 快速聊天示例")
    print("-" * 40)
    
    api_key = os.getenv('DEEPSEEK_API_KEY', 'your_api_key_here')
    
    try:
        # 最简单的使用方式
        result = quick_chat(
            api_key=api_key,
            prompt="什么是机器学习？",
            system_message="你是一个AI教育专家"
        )
        
        print(f"✅ 快速聊天成功: {result[:100]}...")
        
    except Exception as e:
        print(f"❌ 快速聊天失败: {e}")


def main():
    """运行所有示例"""
    print("🚀 强化版 DeepSeek 客户端示例")
    print("=" * 50)
    
    examples = [
        example_basic_usage,
        example_advanced_usage, 
        example_batch_processing,
        example_error_handling,
        example_compatibility_adapter,
        example_quick_chat
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ 示例 {example_func.__name__} 执行失败: {e}")
        
        print()  # 空行分隔
    
    print("🎉 所有示例执行完成！")


if __name__ == "__main__":
    main()