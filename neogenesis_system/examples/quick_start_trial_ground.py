#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 试炼场快速入门示例

演示如何使用 MABConverger 的试炼场功能来管理和进化思维路径。

作者: Neosgenesis Team
日期: 2024
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cognitive_engine.mab_converger import MABConverger
from cognitive_engine.path_generator import PathGenerator, ReasoningPath
from utils.logging_setup import setup_logger


def main():
    # 设置日志
    logger = setup_logger("TrialGroundQuickStart", level="INFO")
    
    print("🎭 MABConverger 试炼场 - 快速入门")
    print("=" * 50)
    
    # 1. 初始化系统
    print("\n1️⃣ 初始化试炼场系统...")
    mab_converger = MABConverger()
    path_generator = PathGenerator()
    
    # 2. 创建一个新学习路径
    print("\n2️⃣ 创建新学习路径...")
    new_path = ReasoningPath(
        name="AI增强思维路径",
        description="结合AI辅助的创新思维方法",
        steps=[
            "🤖 启用AI协作模式",
            "🧠 人机协同分析问题",
            "💡 AI启发创新方案",
            "🎯 人类验证和优化"
        ],
        keywords=["AI协作", "人机协同", "创新"],
        complexity_level=4,
        estimated_steps=4,
        success_indicators=["方案质量", "协作效率"],
        failure_patterns=["过度依赖AI", "缺乏人类洞察"],
        metadata={
            "source": "learned_exploration",
            "learned_from": "最新AI研究",
            "confidence": 0.8
        }
    )
    
    # 3. 将路径注入试炼场
    print(f"   ✅ 创建路径: {new_path.name}")
    selected = mab_converger.select_best_path([new_path])
    print(f"   🚀 探索增强倍数: {mab_converger.get_exploration_boost(new_path.name):.2f}x")
    
    # 4. 模拟几次使用和反馈
    print("\n3️⃣ 模拟路径使用和反馈...")
    for i in range(5):
        # 模拟成功使用
        mab_converger.update_path_performance(
            path_id=new_path.name,
            success=True,
            reward=0.85,
            source="user_feedback"
        )
        print(f"   第{i+1}次使用: ✅ 成功")
    
    # 5. 查看试炼场状态
    print("\n4️⃣ 查看试炼场分析...")
    analytics = mab_converger.get_trial_ground_analytics()
    
    print(f"   📊 总活跃路径: {analytics['overview']['total_active_paths']}")
    print(f"   🌱 学习路径: {analytics['overview']['learned_paths_count']}")
    print(f"   🚀 探索增强中: {analytics['overview']['exploration_boost_active']}")
    print(f"   📈 系统健康: {analytics['performance_trends']['overall_system_health']}")
    
    # 6. 展示学习路径详情
    if analytics['learned_paths']['active_learned_paths']:
        learned_path = analytics['learned_paths']['active_learned_paths'][0]
        print(f"\n5️⃣ 学习路径详情:")
        print(f"   路径ID: {learned_path['strategy_id']}")
        print(f"   成功率: {learned_path['success_rate']:.3f}")
        print(f"   激活次数: {learned_path['activations']}")
        print(f"   试炼时长: {learned_path['trial_duration_hours']:.2f} 小时")
        print(f"   探索增强: {'✅' if learned_path['has_exploration_boost'] else '❌'}")
    
    # 7. 手动维护
    print("\n6️⃣ 执行试炼场维护...")
    maintenance = mab_converger.trigger_trial_ground_maintenance()
    print(f"   🔧 执行了 {len(maintenance['tasks_executed'])} 个维护任务")
    
    # 8. 演示手动提升
    print("\n7️⃣ 演示路径管理功能...")
    
    # 如果路径表现好，可以手动提升为黄金模板
    if analytics['learned_paths']['active_learned_paths']:
        path_id = analytics['learned_paths']['active_learned_paths'][0]['strategy_id']
        success_rate = analytics['learned_paths']['active_learned_paths'][0]['success_rate']
        
        if success_rate > 0.7:
            promotion_result = mab_converger.force_promote_to_golden(
                path_id, "快速入门演示提升"
            )
            if promotion_result['success']:
                print(f"   🏆 成功提升为黄金模板: {path_id}")
            else:
                print(f"   ⚠️ 提升失败: {promotion_result.get('error')}")
    
    print("\n✨ 快速入门完成！")
    print("试炼场系统已经为新思想的到来做好准备。")
    
    # 9. 显示JSON格式的完整分析（可选）
    print("\n📋 想要查看完整分析报告吗？(y/N): ", end="")
    if input().lower().startswith('y'):
        final_analytics = mab_converger.get_trial_ground_analytics()
        print("\n📊 完整试炼场分析报告:")
        print(json.dumps(final_analytics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
