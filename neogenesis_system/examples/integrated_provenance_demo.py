#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔗 集成知识溯源演示脚本 - Integrated Knowledge Provenance Demo

这个脚本演示了知识溯源系统与认知飞轮各组件的完整集成：
- KnowledgeExplorer + 知识溯源
- PathGenerator + 动态路径库 + 知识溯源
- MABConverger 试炼场 + 知识溯源
- 端到端的学习-验证-进化循环

作者: Neosgenesis Team  
日期: 2024
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.data_structures import KnowledgeSource, SourceReference
from cognitive_engine.data_structures import ReasoningPath
from cognitive_engine.path_generator import PathGenerator
from cognitive_engine.mab_converger import MABConverger
from neogenesis_system.providers.knowledge_explorer import KnowledgeExplorer
from neogenesis_system.shared.logging_setup import setup_logger


def create_enhanced_knowledge_explorer():
    """创建增强的知识探索器（模拟版本）"""
    
    class MockKnowledgeExplorer:
        """模拟知识探索器"""
        
        def __init__(self):
            # 模拟探索结果数据库
            self.mock_results = {
                "创新思维": {
                    "title": "设计思维与创新方法论",
                    "content": "设计思维是一种以人为中心的创新方法，包括同理心、定义、构思、原型和测试五个阶段...",
                    "source_url": "https://design-thinking.example.com/methodology",
                    "author": "创新研究院",
                    "confidence": 0.85,
                    "source_type": KnowledgeSource.WEB_SCRAPING
                },
                "系统分析": {
                    "title": "复杂系统分析方法",
                    "content": "系统分析是一种结构化的问题解决方法，通过分解复杂系统来理解其组成部分...",
                    "source_url": "https://systems-analysis.example.com/methods",
                    "author": "系统科学研究中心",
                    "confidence": 0.78,
                    "source_type": KnowledgeSource.ACADEMIC_PAPER
                },
                "协作解决": {
                    "title": "团队协作问题解决框架", 
                    "content": "有效的团队协作需要明确的角色分工、开放的沟通渠道和共同的目标...",
                    "source_url": "https://collaboration.example.com/frameworks",
                    "author": "组织行为学专家",
                    "confidence": 0.72,
                    "source_type": KnowledgeSource.EXPERT_SYSTEM
                }
            }
        
        def explore_knowledge(self, query, max_results=3):
            """模拟知识探索"""
            results = []
            
            # 基于查询关键词匹配结果
            for key, data in self.mock_results.items():
                if any(keyword in query for keyword in key.split()):
                    result = {
                        "id": f"knowledge_{key}_{int(time.time())}",
                        "query": query,
                        "title": data["title"],
                        "content": data["content"],
                        "source_url": data["source_url"],
                        "author": data["author"], 
                        "confidence": data["confidence"],
                        "source_type": data["source_type"],
                        "discovered_at": time.time(),
                        "keywords": key.split() + query.split()
                    }
                    results.append(result)
                    
                    if len(results) >= max_results:
                        break
            
            return results
    
    return MockKnowledgeExplorer()


def create_reasoning_path_from_exploration(exploration_result, logger):
    """从知识探索结果创建推理路径"""
    logger.info(f"🌱 从探索结果创建推理路径: {exploration_result['title']}")
    
    # 基于探索结果生成推理步骤
    base_steps = [
        "🎯 明确问题和目标",
        "🔍 收集和分析相关信息", 
        "💡 生成多个解决方案",
        "⚖️评估和选择最佳方案",
        "🚀 实施并监控效果"
    ]
    
    # 根据内容添加特定步骤
    content = exploration_result['content'].lower()
    specialized_steps = []
    
    if "设计思维" in content or "创新" in content:
        specialized_steps = [
            "🤝 建立用户同理心",
            "🎨 进行头脑风暴",
            "🛠️ 创建快速原型",
            "🧪 进行用户测试"
        ]
    elif "系统" in content or "分析" in content:
        specialized_steps = [
            "📊 系统边界定义",
            "🔗 识别关键要素和关系", 
            "📈 建立系统模型",
            "🔄 分析反馈循环"
        ]
    elif "协作" in content or "团队" in content:
        specialized_steps = [
            "👥 组建跨功能团队",
            "💬 建立沟通机制",
            "🎯 明确角色和职责", 
            "🤝 促进协作和共识"
        ]
    
    # 合并步骤
    all_steps = base_steps[:2] + specialized_steps + base_steps[2:]
    
    # 创建推理路径
    path = ReasoningPath(
        path_id=f"learned_{exploration_result['id']}",
        path_type=f"{exploration_result['title']}型",
        description=f"基于{exploration_result['title']}的推理方法",
        prompt_template=f"运用{exploration_result['title']}的方法来解决{{task}}...",
        name=exploration_result['title'],
        steps=all_steps,
        keywords=exploration_result.get('keywords', []),
        complexity_level=4,
        estimated_steps=len(all_steps),
        success_indicators=["方法适用性", "解决效果", "可复用性"],
        failure_patterns=["方法不匹配", "执行困难", "效果不佳"],
        learning_source="learned_exploration",
        confidence_score=exploration_result['confidence'],
        applicable_domains=["问题解决", "创新设计", "团队协作"],
        metadata={
            "source": "learned_exploration",
            "learned_from": "知识探索模块",
            "confidence": exploration_result['confidence'],
            "discovery_method": "knowledge_exploration",
            "exploration_query": exploration_result['query']
        }
    )
    
    # 添加知识溯源信息
    if hasattr(path, 'add_provenance_source'):
        success = path.add_provenance_source(
            url=exploration_result['source_url'],
            title=exploration_result['title'],
            author=exploration_result.get('author'),
            source_type=exploration_result['source_type'],
            content=exploration_result['content']
        )
        
        if success:
            logger.info(f"   ✅ 知识溯源信息已添加")
            
            # 添加探索相关的上下文标签
            path.add_context_tag("knowledge_exploration")
            path.add_context_tag("learned_method")
            for keyword in exploration_result.get('keywords', [])[:3]:  # 最多3个关键词标签
                path.add_context_tag(keyword)
        else:
            logger.warning(f"   ⚠️ 知识溯源信息添加失败")
    
    logger.info(f"   🎯 路径复杂度: {path.complexity_level}")
    logger.info(f"   📊 初始置信度: {path.confidence_score:.2f}")
    logger.info(f"   📝 步骤数量: {len(path.steps)}")
    
    return path


def demonstrate_end_to_end_learning_cycle(logger):
    """演示端到端学习循环"""
    logger.info("🔄 === 端到端学习循环演示 ===")
    
    # 1. 初始化各个组件
    print("\n1️⃣ 初始化认知飞轮组件...")
    
    knowledge_explorer = create_enhanced_knowledge_explorer()
    path_generator = PathGenerator()
    mab_converger = MABConverger()
    
    print("   ✅ 知识探索器已就绪")
    print("   ✅ 路径生成器已就绪") 
    print("   ✅ MAB试炼场已就绪")
    
    # 2. 知识探索阶段
    print("\n2️⃣ 知识探索阶段...")
    
    exploration_queries = [
        "创新思维方法",
        "系统分析技术", 
        "团队协作解决"
    ]
    
    learned_paths = []
    for query in exploration_queries:
        print(f"\n   🔍 探索查询: {query}")
        
        # 执行知识探索
        results = knowledge_explorer.explore_knowledge(query, max_results=1)
        
        for result in results:
            print(f"   📚 发现: {result['title']}")
            print(f"   🎯 置信度: {result['confidence']:.2f}")
            print(f"   📝 来源: {result['source_url']}")
            
            # 从探索结果创建推理路径
            learned_path = create_reasoning_path_from_exploration(result, logger)
            learned_paths.append(learned_path)
            
            # 将新路径添加到路径生成器
            if hasattr(path_generator, 'add_custom_path'):
                path_generator.add_custom_path(learned_path)
                print(f"   ➕ 路径已添加到动态库")
    
    print(f"\n   📊 总共学习到 {len(learned_paths)} 个新的推理路径")
    
    # 3. 试炼场验证阶段
    print("\n3️⃣ 试炼场验证阶段...")
    
    print("   🎭 将学习路径注入试炼场进行验证...")
    
    # 获取所有可用路径（包括新学习的）
    all_paths = []
    try:
        # 获取动态路径
        if hasattr(path_generator, 'get_recommended_paths_by_context'):
            recommended_paths = path_generator.get_recommended_paths_by_context("综合问题解决")
            all_paths.extend(recommended_paths)
    except Exception as e:
        logger.warning(f"   ⚠️ 无法获取动态路径: {e}")
    
    # 添加学习到的路径
    all_paths.extend(learned_paths)
    
    print(f"   📋 可用路径总数: {len(all_paths)}")
    
    # 模拟多轮试炼
    trial_rounds = 20
    print(f"\n   🎯 开始 {trial_rounds} 轮试炼...")
    
    for round_num in range(1, trial_rounds + 1):
        if round_num % 5 == 1:
            print(f"\n   🔄 第 {round_num}-{min(round_num+4, trial_rounds)} 轮试炼")
        
        # 选择最佳路径
        if all_paths:
            selected_path = mab_converger.select_best_path(all_paths)
            
            # 模拟执行结果
            # 学习路径初期成功率较低，但会逐渐提高
            if hasattr(selected_path, 'is_learned_path') and selected_path.is_learned_path:
                # 学习路径：随时间改善的成功率
                base_success_rate = selected_path.confidence_score * 0.6  # 初始较低
                improvement = min(round_num / trial_rounds, 1.0) * 0.3    # 最多提升30%
                success_probability = base_success_rate + improvement
            else:
                # 静态路径：相对稳定的成功率
                success_probability = 0.75
            
            import random
            success = random.random() < success_probability
            reward = random.uniform(0.7, 1.0) if success else random.uniform(0.1, 0.4)
            
            # 更新性能
            mab_converger.update_path_performance(
                path_id=selected_path.path_id,
                success=success,
                reward=reward,
                source="trial_validation"
            )
            
            # 同时更新路径本身的统计（如果支持）
            if hasattr(selected_path, 'record_usage'):
                execution_time = 2.0 + random.uniform(-0.5, 1.0)
                selected_path.record_usage(success, execution_time)
            
            if round_num % 5 == 0:
                result_icon = "✅" if success else "❌"
                boost = ""
                if hasattr(mab_converger, 'get_exploration_boost'):
                    boost_value = mab_converger.get_exploration_boost(selected_path.path_id)
                    if boost_value > 1.0:
                        boost = f" (探索增强: {boost_value:.1f}x)"
                
                print(f"      {result_icon} 第{round_num}轮: {selected_path.name[:20]}... 奖励: {reward:.2f}{boost}")
    
    # 4. 试炼结果分析
    print("\n4️⃣ 试炼结果分析...")
    
    # 获取试炼场分析
    if hasattr(mab_converger, 'get_trial_ground_analytics'):
        analytics = mab_converger.get_trial_ground_analytics()
        
        print(f"   📊 试炼场状态:")
        print(f"      总活跃路径: {analytics['overview']['total_active_paths']}")
        print(f"      学习路径: {analytics['overview']['learned_paths_count']}")
        print(f"      探索增强中: {analytics['overview']['exploration_boost_active']}")
        print(f"      淘汰候选: {analytics['overview']['culling_candidates']}")
        print(f"      黄金模板: {analytics['overview']['golden_templates']}")
        
        print(f"   🎯 系统健康: {analytics['performance_trends']['overall_system_health']}")
        print(f"   📈 平均成功率: {analytics['performance_trends']['avg_success_rate']:.3f}")
        
        # 分析学习路径表现
        if analytics['learned_paths']['active_learned_paths']:
            print(f"\n   🌱 学习路径详细表现:")
            for path_info in analytics['learned_paths']['active_learned_paths']:
                print(f"      📋 {path_info['strategy_id'][:30]}...")
                print(f"         成功率: {path_info['success_rate']:.3f}")
                print(f"         激活次数: {path_info['activations']}")
                print(f"         试炼时长: {path_info['trial_duration_hours']:.2f} 小时")
                print(f"         探索增强: {'✅' if path_info['has_exploration_boost'] else '❌'}")
                print(f"         提升候选: {'🏆' if path_info['is_promotion_candidate'] else '⭐'}")
    
    # 5. 知识溯源追踪
    print("\n5️⃣ 知识溯源追踪...")
    
    print("   🔍 学习路径的完整溯源信息:")
    for i, path in enumerate(learned_paths, 1):
        print(f"\n   路径 #{i}: {path.name}")
        
        summary = path.get_provenance_summary()
        
        key_metrics = [
            ("学习来源", summary['learning_source']),
            ("置信度", f"{summary['confidence_score']:.3f}"),
            ("验证状态", summary['validation_status']),
            ("使用次数", summary['usage_count']),
            ("成功率", f"{summary['success_rate']:.3f}"),
            ("是否已验证", "✅" if summary['is_verified'] else "❌")
        ]
        
        for label, value in key_metrics:
            print(f"      {label}: {value}")
        
        if summary.get('context_tags'):
            print(f"      上下文标签: {', '.join(list(summary['context_tags'])[:3])}...")
        
        # 显示详细溯源信息（如果可用）
        if 'detailed_provenance' in summary:
            detailed = summary['detailed_provenance']
            print(f"      年龄: {detailed['age_days']:.1f} 天")
            print(f"      新鲜度: {detailed['freshness_score']:.2f}")
            print(f"      来源数量: {detailed['source_count']}")
    
    # 6. 进化和优化
    print("\n6️⃣ 知识进化和优化...")
    
    # 选择表现最好的学习路径进行进化
    best_learned_path = None
    best_success_rate = 0.0
    
    for path in learned_paths:
        if hasattr(path, 'success_rate') and path.success_rate > best_success_rate:
            best_success_rate = path.success_rate
            best_learned_path = path
    
    if best_learned_path and best_success_rate > 0.6:
        print(f"   🌟 最佳学习路径: {best_learned_path.name}")
        print(f"   📊 成功率: {best_success_rate:.3f}")
        
        # 创建进化版本
        if hasattr(best_learned_path, 'create_evolved_version'):
            evolved_changes = [
                "基于试炼反馈优化步骤流程",
                "增强错误处理和边界情况",
                "提升执行效率和用户体验"
            ]
            
            evolved_path = best_learned_path.create_evolved_version(
                changes=evolved_changes,
                reason="基于试炼场验证结果进行优化升级"
            )
            
            print(f"   🧬 进化路径: {evolved_path.path_id}")
            print(f"   📈 进化代数: {evolved_path.evolution_generation}")
            print(f"   📊 进化后置信度: {evolved_path.confidence_score:.3f}")
            
            # 将进化路径添加回系统
            if hasattr(path_generator, 'add_custom_path'):
                path_generator.add_custom_path(evolved_path)
                print(f"   ➕ 进化路径已添加到动态库")
    
    # 7. 系统维护
    print("\n7️⃣ 系统维护...")
    
    if hasattr(mab_converger, 'trigger_trial_ground_maintenance'):
        maintenance_result = mab_converger.trigger_trial_ground_maintenance()
        print(f"   🔧 执行维护任务: {len(maintenance_result['tasks_executed'])} 个")
        
        if maintenance_result['cleanup_results'].get('culling'):
            culling = maintenance_result['cleanup_results']['culling']
            if culling.get('paths_culled'):
                print(f"   🗡️ 淘汰路径: {len(culling['paths_culled'])} 个")
            
        if maintenance_result['cleanup_results'].get('expired_boosts'):
            boosts = maintenance_result['cleanup_results']['expired_boosts']
            print(f"   🧹 清理过期探索增强: {boosts['cleaned_count']} 个")
    
    return {
        'learned_paths': learned_paths,
        'trial_rounds': trial_rounds,
        'system_health': analytics.get('performance_trends', {}).get('overall_system_health', 'unknown') if 'analytics' in locals() else 'unknown'
    }


def main():
    """主演示函数"""
    # 设置日志
    logger = setup_logger("IntegratedProvenanceDemo", level="INFO")
    
    print("🔗 ========================================")
    print("🔗    集成知识溯源系统完整演示")
    print("🔗 ========================================")
    print("🔗 这个演示展示知识溯源系统与认知飞轮的完整集成:")
    print("🔗 1. 知识探索 → 创建带溯源的推理路径")
    print("🔗 2. 动态路径库 → 持久化学习成果")
    print("🔗 3. MAB试炼场 → 验证和优选路径")
    print("🔗 4. 知识溯源 → 全程追踪和管理")
    print("🔗 5. 路径进化 → 持续优化改进")
    print("🔗 ========================================\n")
    
    try:
        # 执行端到端演示
        results = demonstrate_end_to_end_learning_cycle(logger)
        
        print("\n🔗 ========================================")
        print("🔗      集成演示完成！")
        print("🔗 ========================================")
        print("🎯 演示成果总结:")
        print(f"   🌱 学习到新路径: {len(results['learned_paths'])} 个")
        print(f"   🎭 完成试炼轮次: {results['trial_rounds']} 轮")
        print(f"   💊 系统健康状况: {results['system_health']}")
        
        print("\n🌟 集成效果:")
        integration_benefits = [
            "🔍 完整的知识来源追踪和验证",
            "🧠 从探索到应用的自动化流程",
            "🎭 基于实际表现的路径优选",
            "📊 全方位的性能分析和监控",
            "🧬 支持知识进化和持续改进",
            "🔗 各组件间的无缝数据流转",
            "⚡ 高效的学习-验证-优化循环",
            "🛡️ 可靠的质量控制和风险管理"
        ]
        
        for benefit in integration_benefits:
            print(f"   {benefit}")
        
        print(f"\n💡 这个集成系统实现了真正的自主学习和持续进化！")
        print(f"🔄 认知飞轮现在具备了完整的知识生命周期管理能力。")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 演示被用户中断")
    except Exception as e:
        logger.error(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("👋 集成演示结束")


if __name__ == "__main__":
    main()
