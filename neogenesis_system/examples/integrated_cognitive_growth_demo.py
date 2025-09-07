#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知成长完整集成演示 - 知识探索器 + 动态路径生成器
Integrated Cognitive Growth Demo - Knowledge Explorer + Dynamic Path Generator

这个演示展示了知识探索器和动态路径生成器如何协同工作，
实现真正的认知飞轮"学习-进化"闭环：

1. 知识探索器发现新的思维种子
2. 动态路径生成器学习并转化为新路径
3. 新路径参与未来的决策生成
4. 性能反馈优化整个循环

这是认知飞轮"外部智慧→内部进化"的完整演示。
"""

import sys
import os
import time
import logging
from typing import Dict, Any

# 添加项目根路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from neogenesis_system.cognitive_engine.path_generator import PathGenerator
from neogenesis_system.providers.knowledge_explorer import (
    KnowledgeExplorer, ExplorationStrategy, ExplorationTarget,
    KnowledgeItem, ThinkingSeed
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """模拟LLM客户端"""
    
    def call_api(self, prompt: str, temperature: float = 0.8, **kwargs) -> str:
        return f"[LLM分析] 基于提示的智能响应 (温度={temperature})"


class MockWebSearchClient:
    """模拟网络搜索客户端"""
    
    def search(self, query: str, max_results: int = 5):
        """模拟搜索结果"""
        return [
            {
                "title": f"关于'{query}'的最新研究",
                "snippet": f"最新研究表明，{query}在多个领域都有重要应用，特别是在创新思维和系统分析方面显示出巨大潜力...",
                "link": f"https://example.com/research/{query.replace(' ', '-')}",
                "source": "academic_paper"
            },
            {
                "title": f"{query}最佳实践指南", 
                "snippet": f"基于大量实践案例，我们发现{query}的关键在于结合理论分析与实际应用，形成系统性的解决方案...",
                "link": f"https://example.com/guide/{query.replace(' ', '-')}",
                "source": "best_practices"
            },
            {
                "title": f"{query}创新方法探讨",
                "snippet": f"通过跨领域的方法整合，{query}展现了强大的创新潜力，可以通过多维度思考实现突破性进展...",
                "link": f"https://example.com/innovation/{query.replace(' ', '-')}",
                "source": "innovation_study"
            }
        ]


def demonstrate_cognitive_growth_cycle():
    """演示完整的认知成长周期"""
    print("🌟 认知成长完整集成演示")
    print("=" * 60)
    
    # 1. 初始化核心组件
    print("\n1️⃣ 初始化认知系统核心组件...")
    
    llm_client = MockLLMClient()
    search_client = MockWebSearchClient()
    
    # 创建知识探索器
    knowledge_explorer = KnowledgeExplorer(
        llm_client=llm_client,
        web_search_client=search_client,
        config={
            "exploration_strategies": {
                "max_parallel_explorations": 2,
                "exploration_timeout": 30.0
            },
            "seed_generation": {
                "max_seeds_per_exploration": 3,
                "creativity_boost_factor": 1.5
            }
        }
    )
    
    # 创建动态路径生成器
    path_generator = PathGenerator(llm_client=llm_client)
    
    print("✅ 认知系统组件初始化完成")
    print(f"   知识探索器: {'已就绪' if knowledge_explorer else '未就绪'}")
    print(f"   路径生成器: {'已就绪' if path_generator else '未就绪'}")
    
    # 2. 获取系统初始状态
    print("\n2️⃣ 系统初始状态...")
    
    initial_stats = path_generator.get_path_library_stats()
    print(f"📊 初始路径库状态:")
    print(f"   总路径数: {initial_stats['total_paths']}")
    print(f"   学习路径数: {initial_stats['learned_paths']}")
    print(f"   学习比例: {initial_stats['learned_paths']/max(initial_stats['total_paths'],1):.2%}")
    
    # 3. 第一轮：知识探索
    print("\n3️⃣ 第一轮认知循环 - 知识探索...")
    
    exploration_targets = [
        ExplorationTarget(
            target_id="creative_problem_solving",
            target_type="methodology",
            description="创造性问题解决方法论",
            keywords=["创新思维", "问题解决", "设计思维", "系统思考"],
            priority=0.9
        ),
        ExplorationTarget(
            target_id="ai_human_collaboration",
            target_type="trend",
            description="人工智能与人类协作趋势",
            keywords=["人机协作", "AI应用", "协同智能", "未来趋势"],
            priority=0.8
        )
    ]
    
    # 执行知识探索
    print("🔍 执行知识探索...")
    exploration_result = knowledge_explorer.explore_knowledge(
        targets=exploration_targets,
        strategy=ExplorationStrategy.CROSS_DOMAIN_LEARNING
    )
    
    print(f"✅ 知识探索完成:")
    print(f"   探索ID: {exploration_result.exploration_id}")
    print(f"   发现知识: {len(exploration_result.discovered_knowledge)} 项")
    print(f"   生成种子: {len(exploration_result.generated_seeds)} 个")
    print(f"   识别趋势: {len(exploration_result.identified_trends)} 个")
    print(f"   质量评分: {exploration_result.quality_score:.2f}")
    
    # 展示发现的思维种子
    print("\n🌱 发现的思维种子:")
    for i, seed in enumerate(exploration_result.generated_seeds, 1):
        print(f"   {i}. {seed.seed_id}")
        print(f"      创意等级: {seed.creativity_level}")
        print(f"      置信度: {seed.confidence:.2f}")
        print(f"      内容: {seed.seed_content[:80]}...")
    
    # 4. 路径学习和转化
    print("\n4️⃣ 思维路径学习和转化...")
    
    # 转换探索结果为路径生成器格式
    formatted_exploration_result = {
        "exploration_metadata": {
            "exploration_session_id": exploration_result.exploration_id,
            "strategy_used": exploration_result.strategy.value,
            "targets_explored": len(exploration_result.targets),
            "quality_score": exploration_result.quality_score,
            "execution_mode": "professional_explorer"
        },
        "generated_thinking_seeds": [
            {
                "seed_id": seed.seed_id,
                "seed_content": seed.seed_content,
                "creativity_level": seed.creativity_level,
                "confidence": seed.confidence,
                "potential_applications": seed.potential_applications,
                "cross_domain_connections": seed.cross_domain_connections,
                "generated_at": seed.generated_at
            }
            for seed in exploration_result.generated_seeds
        ],
        "identified_trends": [
            {
                "trend_id": trend.get("trend_id", "unknown"),
                "trend_name": trend.get("trend_name", "未命名趋势"),
                "confidence": trend.get("confidence", 0.5)
            }
            for trend in exploration_result.identified_trends
        ],
        "cross_domain_connections": [
            {
                "connection_id": insight.get("insight_id", "unknown"),
                "description": insight.get("description", "跨域连接"),
                "confidence": insight.get("confidence", 0.5)
            }
            for insight in exploration_result.cross_domain_insights
        ]
    }
    
    # 路径生成器从探索结果学习
    print("🧠 路径生成器学习新思维模式...")
    learned_paths_count = path_generator.learn_path_from_exploration(formatted_exploration_result)
    
    print(f"✅ 学习转化完成:")
    print(f"   新增路径数: {learned_paths_count}")
    
    if learned_paths_count > 0:
        # 刷新路径模板
        path_generator.refresh_path_templates()
        print("✅ 路径模板已更新")
        
        # 获取更新后的状态
        updated_stats = path_generator.get_path_library_stats()
        print(f"📊 更新后路径库状态:")
        print(f"   总路径数: {updated_stats['total_paths']} (+{updated_stats['total_paths'] - initial_stats['total_paths']})")
        print(f"   学习路径数: {updated_stats['learned_paths']} (+{updated_stats['learned_paths'] - initial_stats['learned_paths']})")
        print(f"   学习比例: {updated_stats['learned_paths']/max(updated_stats['total_paths'],1):.2%}")
    
    # 5. 新路径的实际应用
    print("\n5️⃣ 新学习路径的实际应用测试...")
    
    test_scenarios = [
        {
            "thinking_seed": "需要跨领域整合的创新解决方案",
            "task": "设计一个融合AI与人文的教育产品",
            "expected_improvement": "应该能使用新学习的跨域思维路径"
        },
        {
            "thinking_seed": "人机协作的未来模式探索",
            "task": "构建下一代智能办公系统",
            "expected_improvement": "应该融合人机协作的新洞察"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 测试场景 {i}: {scenario['task']}")
        print(f"   思维种子: {scenario['thinking_seed']}")
        
        # 生成路径（包含新学习的路径）
        generated_paths = path_generator.generate_paths(
            thinking_seed=scenario['thinking_seed'],
            task=scenario['task'],
            max_paths=4
        )
        
        print(f"   生成路径数: {len(generated_paths)}")
        
        # 检查是否使用了新学习的路径
        learned_path_used = False
        for path in generated_paths:
            if "学习" in path.path_type or "探索" in path.path_type or "跨域" in path.path_type:
                print(f"   ✨ 发现新学习路径: {path.path_type}")
                learned_path_used = True
                break
        
        if not learned_path_used:
            print("   📝 生成的路径:")
            for j, path in enumerate(generated_paths, 1):
                print(f"     {j}. {path.path_type}")
    
    # 6. 性能反馈和优化
    print("\n6️⃣ 性能反馈和系统优化...")
    
    # 模拟一些性能反馈数据
    performance_feedback = [
        ("systematic_analytical", True, 2.3, 0.88),
        ("creative_innovative", True, 3.1, 0.92),
        ("learned_cross_domain", True, 2.8, 0.85),  # 假设这是新学习的路径
        ("practical_pragmatic", False, 1.9, 0.45)
    ]
    
    print("📊 收集性能反馈...")
    for strategy_id, success, exec_time, rating in performance_feedback:
        path_generator.update_path_performance(
            path_id=strategy_id,
            success=success,
            execution_time=exec_time,
            user_rating=rating
        )
        
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {strategy_id}: {status}, {exec_time}s, 评分{rating}")
    
    # 7. 智能推荐验证
    print("\n7️⃣ 基于学习结果的智能推荐...")
    
    recommendation_contexts = [
        {
            "task_type": "innovation",
            "complexity": "high", 
            "domain": "cross_disciplinary",
            "tags": ["creative", "systematic", "collaborative"]
        },
        {
            "task_type": "analysis",
            "complexity": "medium",
            "domain": "technology",
            "tags": ["ai", "human_centered", "future_oriented"]
        }
    ]
    
    for i, context in enumerate(recommendation_contexts, 1):
        print(f"\n💡 推荐场景 {i}: {context}")
        
        recommended_paths = path_generator.get_recommended_paths_by_context(
            task_context=context,
            max_recommendations=3
        )
        
        print(f"   推荐路径:")
        for j, path in enumerate(recommended_paths, 1):
            is_learned = "学习" in path.path_type or "探索" in path.path_type
            marker = "🌟" if is_learned else "📋"
            print(f"     {j}. {marker} {path.path_type}")
    
    # 8. 成长洞察分析
    print("\n8️⃣ 系统成长洞察分析...")
    
    growth_insights = path_generator.get_growth_insights()
    
    print("🌱 成长状况分析:")
    library_growth = growth_insights["library_growth"]
    print(f"   总路径数: {library_growth['total_paths']}")
    print(f"   学习路径数: {library_growth['learned_paths']}")
    print(f"   学习比例: {library_growth['learning_ratio']:.2%}")
    
    usage_patterns = growth_insights["usage_patterns"]
    print(f"🔄 使用模式分析:")
    print(f"   总生成次数: {usage_patterns['total_generations']}")
    print(f"   平均路径数/次: {usage_patterns['avg_paths_per_generation']:.1f}")
    
    if usage_patterns["most_used_paths"]:
        print("📊 最常用路径:")
        for path_type, count in usage_patterns["most_used_paths"]:
            print(f"   - {path_type}: {count} 次")
    
    print("💡 系统成长建议:")
    for recommendation in growth_insights["growth_recommendations"]:
        print(f"   - {recommendation}")
    
    # 9. 第二轮循环预览
    print("\n9️⃣ 第二轮认知循环预览...")
    
    print("🔄 基于第一轮学习成果，系统现在具备了:")
    print("   ✅ 更丰富的思维路径库")
    print("   ✅ 跨域连接的认知能力")
    print("   ✅ 基于实际效果的路径优化")
    print("   ✅ 智能推荐系统的持续改进")
    
    print("\n🔮 下一轮循环将能够:")
    print("   🌟 基于新路径发现更深层的洞察")
    print("   🌟 在更多领域展现创新思维能力")
    print("   🌟 提供更精准的个性化推荐")
    print("   🌟 实现真正的自主认知进化")


def demonstrate_exploration_stats():
    """展示知识探索统计"""
    print("\n🔟 知识探索系统统计...")
    
    llm_client = MockLLMClient()
    search_client = MockWebSearchClient()
    
    knowledge_explorer = KnowledgeExplorer(
        llm_client=llm_client,
        web_search_client=search_client
    )
    
    stats = knowledge_explorer.get_exploration_stats()
    print("📊 知识探索统计:")
    print(f"   总探索次数: {stats['total_explorations']}")
    print(f"   成功探索次数: {stats['successful_explorations']}")
    print(f"   发现知识总数: {stats['total_knowledge_discovered']}")
    print(f"   生成种子总数: {stats['total_seeds_generated']}")
    print(f"   平均质量评分: {stats['average_quality_score']:.2f}")
    print(f"   平均执行时间: {stats['average_execution_time']:.2f}s")
    
    if "strategy_performance" in stats:
        print("🎯 策略性能表现:")
        for strategy, performance in stats["strategy_performance"].items():
            print(f"   {strategy}:")
            print(f"     成功率: {performance['success_rate']:.2%}")
            print(f"     平均质量: {performance['avg_quality']:.2f}")
            print(f"     生成种子数: {performance['total_seeds']}")


if __name__ == "__main__":
    try:
        # 执行完整的认知成长循环演示
        demonstrate_cognitive_growth_cycle()
        
        # 展示探索系统统计
        demonstrate_exploration_stats()
        
        print("\n" + "=" * 60)
        print("🎉 认知成长完整集成演示成功!")
        print("\n📋 演示总结:")
        print("   🌐 知识探索器: 主动发现外部智慧和趋势")
        print("   🧠 动态路径生成器: 学习并转化为内部思维模式")
        print("   🔄 学习闭环: 探索→学习→应用→反馈→优化")
        print("   📊 性能驱动: 基于实际效果的持续改进")
        print("   💡 智能推荐: 上下文感知的路径选择")
        print("   🌱 自主成长: 系统性的认知能力进化")
        
        print("\n🚀 认知飞轮完整闭环已实现!")
        print("   从'被动响应'到'主动认知'")
        print("   从'静态模板'到'动态进化'")
        print("   从'单次决策'到'持续学习'")
        
        print("\n🎯 这标志着AI系统认知架构的重大突破:")
        print("   ✨ 具备真正的自主学习能力")
        print("   ✨ 实现外部智慧的内化转换")
        print("   ✨ 建立持续进化的认知机制")
        print("   ✨ 形成完整的智能成长闭环")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
