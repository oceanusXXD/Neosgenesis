#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态路径生成器 - 快速开始示例
Quick Start Example for Dynamic Path Generator

这个脚本展示如何快速开始使用升级后的动态路径生成器：
1. 基本路径生成（与之前完全一样）
2. 学习新路径（新功能）
3. 性能跟踪（新功能）
4. 智能推荐（新功能）

运行这个脚本可以快速验证动态路径生成器的基础功能。
"""

import sys
import os
import logging

# 添加项目根路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from neogenesis_system.cognitive_engine.path_generator import PathGenerator, ReasoningPathTemplates
from neogenesis_system.cognitive_engine.data_structures import ReasoningPath

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleLLMClient:
    """简单的LLM客户端模拟"""
    
    def call_api(self, prompt: str, temperature: float = 0.8, **kwargs) -> str:
        return f"[模拟LLM响应 温度={temperature}]"


def main():
    print("🧠 动态路径生成器 - 快速开始")
    print("=" * 50)
    
    # 1. 创建路径生成器（自动使用动态库）
    print("\n1️⃣ 创建动态路径生成器...")
    llm_client = SimpleLLMClient()
    generator = PathGenerator(llm_client=llm_client)
    print("✅ 路径生成器创建成功")
    
    # 2. 基础路径生成（与之前完全一样）
    print("\n2️⃣ 基础路径生成测试...")
    thinking_seed = "需要创新思维解决复杂问题"
    task = "设计一个智能学习助手"
    
    paths = generator.generate_paths(
        thinking_seed=thinking_seed,
        task=task,
        max_paths=3
    )
    
    print(f"✅ 生成了 {len(paths)} 个思维路径:")
    for i, path in enumerate(paths, 1):
        print(f"   {i}. {path.path_type}")
        print(f"      策略ID: {path.strategy_id}")
    
    # 3. 模拟学习新路径（新功能）
    print("\n3️⃣ 学习功能测试...")
    
    # 添加自定义路径
    custom_path = ReasoningPath(
        path_id="quick_start_custom",
        path_type="快速开始型",
        description="专为快速开始演示的自定义路径",
        prompt_template="快速解决任务：{task}\n基于种子：{thinking_seed}",
        strategy_id="quick_start_custom"
    )
    
    success = generator.add_custom_path(
        path=custom_path,
        learning_source="quick_start_demo"
    )
    
    if success:
        print("✅ 成功添加自定义路径")
        # 刷新模板以使用新路径
        generator.refresh_path_templates()
        print("✅ 路径模板已刷新")
    
    # 4. 性能跟踪测试（新功能）
    print("\n4️⃣ 性能跟踪测试...")
    
    # 模拟一些性能数据
    performance_updates = [
        ("systematic_analytical", True, 2.1, 0.9),
        ("creative_innovative", True, 3.2, 0.8),
        ("practical_pragmatic", False, 1.5, 0.3)
    ]
    
    for strategy_id, success, exec_time, rating in performance_updates:
        updated = generator.update_path_performance(
            path_id=strategy_id,
            success=success,
            execution_time=exec_time,
            user_rating=rating
        )
        
        status = "✅" if success else "❌"
        print(f"   {status} {strategy_id}: {exec_time}s, 评分{rating}")
    
    # 5. 智能推荐测试（新功能）  
    print("\n5️⃣ 智能推荐测试...")
    
    task_context = {
        "task_type": "design",
        "complexity": "high",
        "urgency": "medium",
        "tags": ["creative", "systematic"]
    }
    
    recommended = generator.get_recommended_paths_by_context(
        task_context=task_context,
        max_recommendations=3
    )
    
    print(f"✅ 基于任务上下文推荐了 {len(recommended)} 个路径:")
    for i, path in enumerate(recommended, 1):
        print(f"   {i}. {path.path_type}")
    
    # 6. 系统统计概览
    print("\n6️⃣ 系统统计概览...")
    
    # 路径库统计
    library_stats = generator.get_path_library_stats()
    print(f"📚 路径库统计:")
    print(f"   总路径数: {library_stats['total_paths']}")
    print(f"   激活路径: {library_stats['active_paths']}")
    print(f"   学习路径: {library_stats['learned_paths']}")
    
    # 生成统计
    generation_stats = generator.get_generation_statistics()
    print(f"🛤️ 生成统计:")
    print(f"   缓存生成数: {generation_stats['total_generations']}")
    print(f"   路径生成数: {generation_stats['path_generation_stats']['total_path_generations']}")
    
    # 成长洞察
    insights = generator.get_growth_insights()
    learning_ratio = insights['library_growth']['learning_ratio']
    print(f"🌱 成长洞察:")
    print(f"   学习比例: {learning_ratio:.2%}")
    
    if insights['growth_recommendations']:
        print("💡 成长建议:")
        for rec in insights['growth_recommendations']:
            print(f"   - {rec}")
    
    print("\n🎉 快速开始演示完成!")
    print("\n📋 总结：")
    print("   ✅ 基础路径生成 - 与之前完全兼容")
    print("   ✅ 学习新路径 - 动态扩展能力")
    print("   ✅ 性能跟踪 - 智能优化机制")
    print("   ✅ 智能推荐 - 基于上下文的路径选择")
    print("   ✅ 系统洞察 - 完整的统计和建议")
    print("\n🧠 动态路径生成器已就绪！")


if __name__ == "__main__":
    main()
