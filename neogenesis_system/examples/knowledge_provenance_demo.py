#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 知识溯源系统演示脚本 - Knowledge Provenance System Demo

这个脚本演示了完整的知识溯源 (Knowledge Provenance) 系统：
- 知识来源追踪和管理
- 验证和置信度系统
- 知识网络和关联建立
- 学习路径的生命周期追踪
- 知识进化和版本管理

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

from shared.data_structures import (
    KnowledgeProvenance, SourceReference, KnowledgeValidation, 
    KnowledgeUpdate, KnowledgeNetwork, KnowledgeSource, 
    CredibilityLevel, VerificationStatus
)
from cognitive_engine.data_structures import ReasoningPath
from utils.logging_setup import setup_logger


def create_sample_knowledge_sources():
    """创建示例知识来源"""
    sources = []
    
    # 学术论文来源
    academic_source = SourceReference(
        url="https://arxiv.org/abs/2024.12345",
        title="Advanced Reasoning Patterns in AI Systems",
        author="Dr. Jane Smith, Dr. Bob Wilson",
        published_date=time.time() - 86400 * 30,  # 30天前
        source_type=KnowledgeSource.ACADEMIC_PAPER,
        metadata={
            "journal": "AI Research Quarterly",
            "citations": 45,
            "peer_reviewed": True,
            "impact_factor": 3.2
        }
    )
    sources.append(academic_source)
    
    # 网络爬取来源
    web_source = SourceReference(
        url="https://www.example-ai-blog.com/reasoning-strategies",
        title="实用AI推理策略指南",
        author="AI专家团队",
        published_date=time.time() - 86400 * 7,  # 7天前
        source_type=KnowledgeSource.WEB_SCRAPING,
        metadata={
            "domain_authority": 85,
            "last_updated": "2024-01-15",
            "language": "zh-CN"
        }
    )
    sources.append(web_source)
    
    # API查询来源
    api_source = SourceReference(
        url="https://api.knowledge-base.com/v1/reasoning-methods",
        title="推理方法API数据",
        source_type=KnowledgeSource.API_QUERY,
        metadata={
            "api_version": "v1.2",
            "response_time": 0.15,
            "data_freshness": "real-time"
        }
    )
    sources.append(api_source)
    
    return sources


def demonstrate_basic_provenance(logger):
    """演示基础知识溯源功能"""
    logger.info("🔍 === 基础知识溯源功能演示 ===")
    
    # 1. 创建知识溯源记录
    print("\n1️⃣ 创建知识溯源记录...")
    provenance = KnowledgeProvenance(
        knowledge_id="reasoning_pattern_001",
        confidence_score=0.8
    )
    
    # 2. 添加知识来源
    print("\n2️⃣ 添加知识来源...")
    sources = create_sample_knowledge_sources()
    
    # 添加主要来源
    provenance.add_source(sources[0], is_primary=True)
    print(f"   ✅ 主要来源: {sources[0].title}")
    
    # 添加额外来源
    for source in sources[1:]:
        provenance.add_source(source)
        print(f"   ➕ 额外来源: {source.title}")
    
    # 3. 添加验证记录
    print("\n3️⃣ 添加验证记录...")
    validation = KnowledgeValidation(
        validation_method="expert_review",
        validator="AI Research Team",
        status=VerificationStatus.VERIFIED,
        confidence_score=0.85,
        notes="经专家团队验证，推理模式有效且实用"
    )
    validation.add_evidence("在5个不同场景中测试成功")
    validation.add_evidence("获得3位专家一致认可")
    
    provenance.add_validation(validation)
    print(f"   ✅ 验证状态: {validation.status.value}")
    print(f"   📊 验证置信度: {validation.confidence_score:.2f}")
    
    # 4. 记录使用情况
    print("\n4️⃣ 模拟使用情况...")
    for i in range(10):
        success = i < 8  # 80% 成功率
        provenance.record_usage(success)
        if i % 3 == 0:
            result = "✅ 成功" if success else "❌ 失败"
            print(f"   使用 #{i+1}: {result}")
    
    # 5. 添加上下文标签
    print("\n5️⃣ 添加上下文标签...")
    context_tags = ["AI推理", "系统思维", "问题解决", "学术验证", "实用方法"]
    for tag in context_tags:
        provenance.add_context_tag(tag)
    print(f"   🏷️ 标签: {', '.join(context_tags)}")
    
    # 6. 显示溯源摘要
    print("\n6️⃣ 知识溯源摘要:")
    summary = provenance.get_provenance_summary()
    print(f"   📋 知识ID: {summary['knowledge_id']}")
    print(f"   📊 置信度: {summary['confidence_score']:.3f}")
    print(f"   🎯 可信度级别: {summary['credibility_level']}")
    print(f"   ✅ 已验证: {summary['is_verified']}")
    print(f"   📈 成功率: {summary['success_rate']:.3f}")
    print(f"   ⏰ 年龄: {summary['age_days']:.1f} 天")
    print(f"   🌟 新鲜度: {summary['freshness_score']:.2f}")
    print(f"   🔗 来源数量: {summary['source_count']}")
    
    return provenance


def demonstrate_knowledge_network(logger):
    """演示知识网络功能"""
    logger.info("\n🕸️ === 知识网络功能演示 ===")
    
    # 创建主知识节点
    main_provenance = KnowledgeProvenance(
        knowledge_id="systematic_reasoning",
        confidence_score=0.9
    )
    
    # 创建相关知识节点
    related_knowledge_ids = [
        "analytical_thinking",
        "logical_deduction", 
        "creative_problem_solving",
        "critical_evaluation"
    ]
    
    print("1️⃣ 建立知识关联网络...")
    
    # 添加相关关系
    main_provenance.knowledge_network.add_relationship(
        "analytical_thinking", "related", similarity_score=0.85,
        metadata={"relationship_strength": "strong", "domain": "logic"}
    )
    
    main_provenance.knowledge_network.add_relationship(
        "logical_deduction", "supporting", similarity_score=0.92,
        metadata={"support_type": "foundational", "evidence": "共同的逻辑基础"}
    )
    
    main_provenance.knowledge_network.add_relationship(
        "creative_problem_solving", "related", similarity_score=0.65,
        metadata={"relationship_strength": "moderate", "complementary": True}
    )
    
    main_provenance.knowledge_network.add_relationship(
        "critical_evaluation", "influences", similarity_score=0.78,
        metadata={"influence_type": "quality_control", "direction": "bidirectional"}
    )
    
    # 显示网络统计
    network = main_provenance.knowledge_network
    print(f"   🔗 总连接数: {network.total_connections}")
    print(f"   💪 连接强度: {network.connection_strength:.2f}")
    print(f"   📊 相关知识: {len(network.related_knowledge)}")
    print(f"   🤝 支持性知识: {len(network.supporting_knowledge)}")
    print(f"   ⭐ 影响关系: {len(network.influences)}")
    
    # 显示具体关联
    print("\n2️⃣ 知识关联详情:")
    for knowledge_id, score in network.similarity_scores.items():
        relationship_type = "未知"
        if knowledge_id in network.related_knowledge:
            relationship_type = "相关"
        elif knowledge_id in network.supporting_knowledge:
            relationship_type = "支持"
        elif knowledge_id in network.influences:
            relationship_type = "影响"
        
        metadata = network.relationship_metadata.get(knowledge_id, {})
        print(f"   🔗 {knowledge_id} ({relationship_type}) - 相似度: {score:.2f}")
        if metadata:
            print(f"      💬 元信息: {metadata}")
    
    return main_provenance


def demonstrate_reasoning_path_provenance(logger):
    """演示推理路径的知识溯源功能"""
    logger.info("\n🧠 === 推理路径知识溯源演示 ===")
    
    print("1️⃣ 创建带有知识溯源的推理路径...")
    
    # 创建学习型推理路径
    learned_path = ReasoningPath(
        path_id="ai_enhanced_reasoning_v1",
        path_type="AI增强推理型",
        description="结合人工智能辅助的高效推理方法",
        prompt_template="使用AI协作进行{task}的系统性分析...",
        name="AI增强推理路径",
        steps=[
            "🤖 启动AI协作模式",
            "🧠 人机协同问题分析",
            "💡 AI生成创新解决方案",
            "🔍 人类专家验证和优化",
            "🎯 输出优化的最终方案"
        ],
        keywords=["AI协作", "人机协同", "创新解决", "专家验证"],
        complexity_level=4,
        estimated_steps=5,
        success_indicators=["方案创新性", "实施可行性", "专家认可度"],
        failure_patterns=["过度依赖AI", "缺乏人类洞察", "方案不切实际"],
        learning_source="learned_exploration",
        confidence_score=0.75,
        metadata={
            "source": "learned_exploration",
            "learned_from": "知识探索模块",
            "confidence": 0.75,
            "discovery_method": "web_scraping_analysis"
        }
    )
    
    print(f"   ✅ 路径创建: {learned_path.name}")
    print(f"   🎯 学习来源: {learned_path.learning_source}")
    print(f"   📊 初始置信度: {learned_path.confidence_score:.2f}")
    
    # 2. 添加详细的知识来源
    print("\n2️⃣ 添加知识来源...")
    success = learned_path.add_provenance_source(
        url="https://ai-research.example.com/human-ai-collaboration",
        title="人机协作推理方法研究",
        author="AI研究院",
        content="人机协作推理的详细方法和案例研究..."
    )
    print(f"   📚 来源添加: {'✅ 成功' if success else '❌ 失败'}")
    
    # 3. 模拟使用和验证
    print("\n3️⃣ 模拟路径使用和反馈...")
    for i in range(15):
        success = i < 12  # 80% 成功率
        execution_time = 2.5 + (i * 0.1)  # 逐渐优化的执行时间
        learned_path.record_usage(success, execution_time)
        
        if i % 5 == 4:
            print(f"   📊 第 {i+1} 次使用后 - 成功率: {learned_path.success_rate:.2f}, 平均时间: {learned_path.avg_execution_time:.1f}s")
    
    # 4. 添加上下文标签
    print("\n4️⃣ 丰富上下文信息...")
    context_tags = ["AI辅助", "创新方法", "协作推理", "专家验证", "高效解决"]
    for tag in context_tags:
        learned_path.add_context_tag(tag)
    print(f"   🏷️ 上下文标签: {', '.join(context_tags)}")
    
    # 5. 验证路径
    print("\n5️⃣ 验证路径有效性...")
    learned_path.mark_as_verified(
        verification_method="实际使用验证",
        confidence=0.88,
        notes="通过15次实际使用验证，表现良好"
    )
    print(f"   ✅ 验证状态: {learned_path.validation_status}")
    print(f"   🎯 已验证: {learned_path.is_verified}")
    
    # 6. 创建进化版本
    print("\n6️⃣ 创建路径进化版本...")
    changes = [
        "优化AI-人类交互流程",
        "增加实时反馈机制", 
        "加强专家验证环节"
    ]
    evolved_path = learned_path.create_evolved_version(
        changes=changes,
        reason="基于使用反馈进行优化升级"
    )
    
    print(f"   🧬 进化路径: {evolved_path.path_id}")
    print(f"   📈 进化代数: {evolved_path.evolution_generation}")
    print(f"   👨‍💻 父路径: {evolved_path.parent_path_id}")
    print(f"   📊 进化后置信度: {evolved_path.confidence_score:.2f}")
    
    # 7. 显示完整溯源摘要
    print("\n7️⃣ 完整知识溯源摘要:")
    summary = learned_path.get_provenance_summary()
    
    print(f"   📋 路径ID: {summary['path_id']}")
    print(f"   📝 友好名称: {summary['name']}")
    print(f"   🌱 学习来源: {summary['learning_source']}")
    print(f"   📊 置信度: {summary['confidence_score']:.3f}")
    print(f"   ✅ 验证状态: {summary['validation_status']}")
    print(f"   🎯 使用次数: {summary['usage_count']}")
    print(f"   📈 成功率: {summary['success_rate']:.3f}")
    print(f"   🔍 是否学习路径: {summary['is_learned_path']}")
    print(f"   ✅ 是否已验证: {summary['is_verified']}")
    print(f"   ⚠️ 是否有冲突: {summary['has_conflicts']}")
    print(f"   🧬 进化代数: {summary['evolution_generation']}")
    
    if 'detailed_provenance' in summary:
        detailed = summary['detailed_provenance']
        print(f"   📅 年龄: {detailed['age_days']:.1f} 天")
        print(f"   🌟 新鲜度: {detailed['freshness_score']:.2f}")
        print(f"   🔗 网络连接: {detailed['network_connections']}")
        print(f"   📚 来源数量: {detailed['source_count']}")
    
    print(f"   🏷️ 上下文标签: {', '.join(summary['context_tags'])}")
    
    return learned_path, evolved_path


def demonstrate_update_tracking(logger):
    """演示知识更新追踪"""
    logger.info("\n📝 === 知识更新追踪演示 ===")
    
    # 创建初始知识
    provenance = KnowledgeProvenance(
        knowledge_id="dynamic_reasoning_method",
        confidence_score=0.7
    )
    
    print("1️⃣ 初始知识创建...")
    print(f"   📊 初始置信度: {provenance.confidence_score:.2f}")
    
    # 模拟多次更新
    updates = [
        {
            "type": "content_update",
            "reason": "发现新的应用场景",
            "changes": ["增加金融分析应用", "扩展到医疗诊断领域"],
            "confidence_change": 0.1
        },
        {
            "type": "verification_update", 
            "reason": "专家团队验证通过",
            "changes": ["通过同行评议", "获得权威认证"],
            "confidence_change": 0.15
        },
        {
            "type": "confidence_update",
            "reason": "实际使用反馈良好",
            "changes": ["成功率提升到92%", "用户满意度高"],
            "confidence_change": 0.05
        }
    ]
    
    print("\n2️⃣ 记录知识更新历史...")
    for i, update_info in enumerate(updates, 1):
        update = KnowledgeUpdate(
            update_type=update_info["type"],
            reason=update_info["reason"],
            changes=update_info["changes"],
            confidence_change=update_info["confidence_change"]
        )
        
        provenance.add_update(update)
        provenance.confidence_score += update_info["confidence_change"]
        
        print(f"   📝 更新 #{i}: {update_info['reason']}")
        print(f"      类型: {update_info['type']}")
        print(f"      置信度变化: +{update_info['confidence_change']:.2f}")
        print(f"      当前置信度: {provenance.confidence_score:.2f}")
    
    # 显示更新历史
    print(f"\n3️⃣ 更新历史摘要 (共 {len(provenance.update_history)} 次更新):")
    for i, update in enumerate(provenance.update_history, 1):
        print(f"   #{i} - {update.reason} ({update.update_type})")
        for change in update.changes:
            print(f"        • {change}")
    
    return provenance


def demonstrate_conflict_detection(logger):
    """演示冲突检测功能"""
    logger.info("\n⚠️ === 冲突检测功能演示 ===")
    
    # 创建存在冲突的知识
    provenance = KnowledgeProvenance(
        knowledge_id="controversial_method",
        confidence_score=0.6
    )
    
    print("1️⃣ 创建具有冲突的验证记录...")
    
    # 添加正面验证
    positive_validation = KnowledgeValidation(
        validation_method="academic_study",
        validator="University A Research Team",
        status=VerificationStatus.VERIFIED,
        confidence_score=0.8,
        notes="在控制实验中表现良好"
    )
    positive_validation.add_evidence("实验组比对照组提升25%")
    positive_validation.add_evidence("通过统计显著性检验")
    
    provenance.add_validation(positive_validation)
    
    # 添加负面验证
    negative_validation = KnowledgeValidation(
        validation_method="independent_replication",
        validator="University B Research Team",
        status=VerificationStatus.CONFLICTING,
        confidence_score=0.3,
        notes="无法复现原始研究结果"
    )
    negative_validation.add_conflict("实验结果无法复现")
    negative_validation.add_conflict("样本大小可能不足")
    negative_validation.add_evidence("重复实验3次均无显著效果")
    
    provenance.add_validation(negative_validation)
    
    print(f"   ✅ 正面验证: {positive_validation.confidence_score:.2f} 置信度")
    print(f"   ⚠️ 冲突验证: {negative_validation.confidence_score:.2f} 置信度")
    print(f"   🎯 最终状态: {'有冲突' if provenance.has_conflicts else '无冲突'}")
    
    # 显示冲突详情
    print("\n2️⃣ 冲突详情分析:")
    for i, validation in enumerate(provenance.validation_history, 1):
        print(f"   验证 #{i} - {validation.validator}")
        print(f"      状态: {validation.status.value}")
        print(f"      置信度: {validation.confidence_score:.2f}")
        
        if validation.evidence:
            print("      证据:")
            for evidence in validation.evidence:
                print(f"        ✓ {evidence}")
        
        if validation.conflicts:
            print("      冲突:")
            for conflict in validation.conflicts:
                print(f"        ⚠ {conflict}")
    
    print(f"\n3️⃣ 系统建议:")
    print(f"   📊 整体置信度: {provenance.confidence_score:.2f}")
    print(f"   🎯 可信度级别: {provenance.credibility_level.value}")
    print(f"   💡 建议: 需要更多独立验证来解决冲突")
    
    return provenance


def main():
    """主演示函数"""
    # 设置日志
    logger = setup_logger("KnowledgeProvenanceDemo", level="INFO")
    
    print("🔍 ========================================")
    print("🔍      知识溯源系统完整功能演示")
    print("🔍 ========================================")
    print("🔍 这个演示将展示知识溯源系统的各项核心功能:")
    print("🔍 1. 基础知识溯源和来源管理")
    print("🔍 2. 知识网络和关联建立")
    print("🔍 3. 推理路径的完整生命周期追踪")
    print("🔍 4. 知识更新和版本管理")
    print("🔍 5. 冲突检测和处理")
    print("🔍 ========================================\n")
    
    try:
        # 1. 基础溯源演示
        basic_provenance = demonstrate_basic_provenance(logger)
        
        input("\n🔄 按 Enter 键继续知识网络演示...")
        
        # 2. 知识网络演示
        network_provenance = demonstrate_knowledge_network(logger)
        
        input("\n🧠 按 Enter 键继续推理路径溯源演示...")
        
        # 3. 推理路径溯源演示
        learned_path, evolved_path = demonstrate_reasoning_path_provenance(logger)
        
        input("\n📝 按 Enter 键继续更新追踪演示...")
        
        # 4. 更新追踪演示
        update_provenance = demonstrate_update_tracking(logger)
        
        input("\n⚠️ 按 Enter 键继续冲突检测演示...")
        
        # 5. 冲突检测演示
        conflict_provenance = demonstrate_conflict_detection(logger)
        
        print("\n🔍 ========================================")
        print("🔍      知识溯源系统演示完成！")
        print("🔍 ========================================")
        print("🎯 演示的核心功能:")
        print("   ✅ 完整的知识来源追踪和管理")
        print("   ✅ 多层次的验证和置信度系统")
        print("   ✅ 智能的知识网络关联")
        print("   ✅ 学习路径的生命周期追踪")
        print("   ✅ 知识进化和版本管理")
        print("   ✅ 自动的冲突检测和处理")
        print("   ✅ 全面的使用统计和分析")
        print("   ✅ 灵活的上下文标签系统")
        
        print("\n📊 演示总结:")
        print(f"   🔍 基础溯源记录: 置信度 {basic_provenance.confidence_score:.2f}")
        print(f"   🕸️ 知识网络连接: {network_provenance.knowledge_network.total_connections} 个")
        print(f"   🧠 学习路径使用: {learned_path.usage_count} 次")
        print(f"   🧬 路径进化代数: {evolved_path.evolution_generation}")
        print(f"   📝 知识更新次数: {len(update_provenance.update_history)}")
        print(f"   ⚠️ 冲突检测: {'发现冲突' if conflict_provenance.has_conflicts else '无冲突'}")
        
        print("\n🌟 知识溯源系统为认知飞轮提供了透明、可追溯、可验证的知识基础！")
        
        # 可选：保存演示数据
        print(f"\n📋 想要查看完整的知识溯源数据吗？(y/N): ", end="")
        if input().lower().startswith('y'):
            print("\n🔍 完整知识溯源数据:")
            
            print("\n1. 基础溯源摘要:")
            print(json.dumps(basic_provenance.get_provenance_summary(), 
                           indent=2, ensure_ascii=False, default=str))
            
            print("\n2. 推理路径溯源摘要:")
            print(json.dumps(learned_path.get_provenance_summary(), 
                           indent=2, ensure_ascii=False, default=str))
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 演示被用户中断")
    except Exception as e:
        logger.error(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("👋 知识溯源演示结束")


if __name__ == "__main__":
    main()
