#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 知识溯源快速入门示例

展示如何在推理路径中使用知识溯源功能。

作者: Neosgenesis Team
日期: 2024
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.data_structures import KnowledgeSource, SourceReference
from cognitive_engine.data_structures import ReasoningPath
from neogenesis_system.shared.logging_setup import setup_logger


def main():
    # 设置日志
    logger = setup_logger("ProvenanceQuickStart", level="INFO")
    
    print("🔍 知识溯源系统 - 快速入门")
    print("=" * 40)
    
    # 1. 创建一个带知识溯源的推理路径
    print("\n1️⃣ 创建学习路径...")
    
    reasoning_path = ReasoningPath(
        path_id="collaborative_problem_solving_v1",
        path_type="协作问题解决型",
        description="基于团队协作的系统化问题解决方法",
        prompt_template="采用团队协作方式解决{task}问题...",
        name="协作问题解决路径",
        steps=[
            "🤝 组建跨领域团队",
            "🎯 明确问题定义和目标",
            "💡 集体头脑风暴解决方案",
            "🔍 评估和筛选最佳方案",
            "🚀 实施并持续优化"
        ],
        keywords=["团队协作", "系统化", "头脑风暴", "方案评估"],
        complexity_level=3,
        success_indicators=["团队参与度", "方案创新性", "实施效果"],
        learning_source="learned_exploration",
        confidence_score=0.8,
        metadata={
            "source": "learned_exploration",
            "learned_from": "团队管理最佳实践研究",
            "confidence": 0.8
        }
    )
    
    print(f"   ✅ 路径创建: {reasoning_path.name}")
    print(f"   🎯 学习来源: {reasoning_path.learning_source}")
    
    # 2. 添加知识来源
    print("\n2️⃣ 添加知识来源...")
    success = reasoning_path.add_provenance_source(
        url="https://example.com/team-collaboration-guide",
        title="现代团队协作方法论",
        author="项目管理专家团队",
        source_type=KnowledgeSource.WEB_SCRAPING,
        content="详细的团队协作方法和案例研究..."
    )
    
    if success:
        print("   ✅ 知识来源添加成功")
    else:
        print("   ⚠️ 知识来源添加失败（可能知识溯源系统不可用）")
    
    # 3. 模拟使用
    print("\n3️⃣ 模拟路径使用...")
    for i in range(5):
        success = i < 4  # 80% 成功率
        reasoning_path.record_usage(success, execution_time=3.2 + i * 0.1)
        result_icon = "✅" if success else "❌"
        print(f"   使用 #{i+1}: {result_icon}")
    
    print(f"   📊 当前成功率: {reasoning_path.success_rate:.2f}")
    print(f"   ⏱️ 平均执行时间: {reasoning_path.avg_execution_time:.1f}秒")
    
    # 4. 添加上下文标签
    print("\n4️⃣ 丰富上下文信息...")
    tags = ["团队合作", "创新方法", "实践验证"]
    for tag in tags:
        reasoning_path.add_context_tag(tag)
    print(f"   🏷️ 标签: {', '.join(tags)}")
    
    # 5. 验证路径
    print("\n5️⃣ 验证路径...")
    reasoning_path.mark_as_verified(
        verification_method="实践验证",
        confidence=0.85,
        notes="通过多次实际项目验证"
    )
    print(f"   ✅ 验证状态: {reasoning_path.validation_status}")
    
    # 6. 查看溯源摘要
    print("\n6️⃣ 知识溯源摘要:")
    summary = reasoning_path.get_provenance_summary()
    
    key_info = [
        ("路径名称", summary['name']),
        ("学习来源", summary['learning_source']),
        ("置信度", f"{summary['confidence_score']:.2f}"),
        ("验证状态", summary['validation_status']),
        ("使用次数", summary['usage_count']),
        ("成功率", f"{summary['success_rate']:.2f}"),
        ("是否学习路径", "是" if summary['is_learned_path'] else "否"),
        ("是否已验证", "是" if summary['is_verified'] else "否")
    ]
    
    for label, value in key_info:
        print(f"   📋 {label}: {value}")
    
    if summary['context_tags']:
        print(f"   🏷️ 上下文标签: {', '.join(summary['context_tags'])}")
    
    # 7. 演示路径进化
    print("\n7️⃣ 创建进化版本...")
    evolved_path = reasoning_path.create_evolved_version(
        changes=["增加远程协作工具支持", "加强异步沟通机制"],
        reason="适应远程工作环境"
    )
    
    print(f"   🧬 进化路径: {evolved_path.path_id}")
    print(f"   📈 进化代数: {evolved_path.evolution_generation}")
    print(f"   📊 新置信度: {evolved_path.confidence_score:.2f}")
    
    print("\n✨ 快速入门完成！")
    print("🎯 知识溯源系统让每个推理路径都有清晰的来源和发展历程。")
    
    # 8. 显示系统优势
    print("\n🌟 知识溯源系统优势:")
    advantages = [
        "🔍 完整的知识来源追踪",
        "📊 自动的性能统计和分析", 
        "✅ 多层次的验证和置信度管理",
        "🧬 支持知识进化和版本控制",
        "🏷️ 灵活的上下文标签系统",
        "🔗 智能的知识关联网络",
        "⚠️ 自动冲突检测和处理",
        "📝 详细的更新历史追踪"
    ]
    
    for advantage in advantages:
        print(f"   {advantage}")
    
    print(f"\n💡 提示: 运行 'python examples/knowledge_provenance_demo.py' 查看完整功能演示！")


if __name__ == "__main__":
    main()
