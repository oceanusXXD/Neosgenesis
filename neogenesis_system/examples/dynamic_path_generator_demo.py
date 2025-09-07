#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态路径生成器完整功能演示
Dynamic Path Generator Complete Feature Demo

这个演示展示了改造后的 path_generator.py 的全部新功能：
1. 动态思维路径库的持久化存储
2. 从静态模板到动态管理的升级
3. 学习和成长接口的使用
4. 与知识探索器的完整集成
5. 性能跟踪和智能推荐系统
"""

import sys
import os
import time
import logging
from typing import Dict, Any

# 添加项目根路径到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from neogenesis_system.cognitive_engine.path_generator import PathGenerator, ReasoningPathTemplates
from neogenesis_system.cognitive_engine.path_library import (
    DynamicPathLibrary, StorageBackend, ExplorationTarget, KnowledgeItem,
    ThinkingSeed, EnhancedReasoningPath, PathMetadata, PathCategory, PathStatus
)
from neogenesis_system.cognitive_engine.data_structures import ReasoningPath

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """模拟LLM客户端"""
    
    def call_api(self, prompt: str, temperature: float = 0.8, system_message: str = "") -> str:
        """模拟LLM API调用"""
        return f"模拟LLM响应：基于温度{temperature}的智能分析输出 (系统消息: {system_message[:20]}...)"


def demonstrate_dynamic_library_initialization():
    """演示动态路径库的初始化"""
    logger.info("🧠 演示动态路径库初始化")
    
    # 测试不同的存储后端
    backends_to_test = [
        (StorageBackend.MEMORY, "内存存储（测试模式）"),
        (StorageBackend.JSON, "JSON文件存储"),
        # (StorageBackend.SQLITE, "SQLite数据库存储")  # 可选
    ]
    
    for backend, description in backends_to_test:
        logger.info(f"\n📁 测试存储后端: {description}")
        
        try:
            # 创建动态路径库
            library = DynamicPathLibrary(
                storage_backend=backend,
                storage_path=f"demo_data/test_paths_{backend.value}",
                auto_backup=True
            )
            
            # 显示初始状态
            stats = library.get_library_stats()
            logger.info(f"   初始路径数量: {stats['total_paths']}")
            logger.info(f"   存储后端: {stats['storage_backend']}")
            
            # 添加一个测试路径
            test_path = EnhancedReasoningPath(
                path_id=f"test_path_{int(time.time())}",
                path_type="测试路径型",
                description="用于演示的测试路径",
                prompt_template="这是一个测试路径：{task}",
                strategy_id="test_strategy",
                metadata=PathMetadata(
                    author="demo_system",
                    category=PathCategory.EXPERIMENTAL,
                    tags=["demo", "test"]
                )
            )
            
            success = library.add_path(test_path)
            if success:
                logger.info(f"   ✅ 成功添加测试路径")
            
            # 显示更新后状态
            updated_stats = library.get_library_stats()
            logger.info(f"   更新后路径数量: {updated_stats['total_paths']}")
            
        except Exception as e:
            logger.error(f"   ❌ {description} 测试失败: {e}")


def demonstrate_template_migration():
    """演示静态模板迁移"""
    logger.info("\n🚚 演示静态模板迁移到动态库")
    
    # 创建动态路径模板管理器
    template_manager = ReasoningPathTemplates.get_instance(
        storage_backend="memory",  # 使用内存存储以便演示
        storage_path="demo_data/migrated_paths"
    )
    
    # 获取迁移后的模板
    all_templates = template_manager.get_all_templates()
    
    logger.info(f"📚 迁移完成，共有 {len(all_templates)} 个路径模板:")
    for template_id, template in list(all_templates.items())[:5]:  # 显示前5个
        logger.info(f"   - {template_id}: {template.path_type}")
        logger.debug(f"     描述: {template.description}")
    
    # 显示库统计信息
    stats = template_manager.get_library_stats()
    logger.info(f"📊 路径库统计:")
    logger.info(f"   总路径数: {stats['total_paths']}")
    logger.info(f"   激活路径: {stats['active_paths']}")
    logger.info(f"   学习路径: {stats['learned_paths']}")


def demonstrate_path_generator_integration():
    """演示路径生成器与动态库的集成"""
    logger.info("\n🛤️ 演示动态路径生成器")
    
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 创建路径生成器（自动集成动态路径库）
    path_generator = PathGenerator(llm_client=mock_llm)
    
    # 测试思维种子到路径的生成
    test_seeds_and_tasks = [
        ("需要创新突破的产品设计思路", "设计一个智能家居产品"),
        ("系统性分析复杂问题的方法", "分析企业数字化转型策略"),
        ("快速实用的解决方案", "解决团队沟通效率问题")
    ]
    
    for thinking_seed, task in test_seeds_and_tasks:
        logger.info(f"\n🌱 测试思维种子: {thinking_seed}")
        logger.info(f"🎯 关联任务: {task}")
        
        try:
            # 生成路径（普通模式）
            normal_paths = path_generator.generate_paths(
                thinking_seed=thinking_seed,
                task=task,
                max_paths=3,
                mode='normal'
            )
            
            logger.info(f"📋 普通模式生成 {len(normal_paths)} 个路径:")
            for i, path in enumerate(normal_paths, 1):
                logger.info(f"   {i}. {path.path_type}")
                logger.debug(f"      策略ID: {path.strategy_id}")
                logger.debug(f"      描述: {path.description[:60]}...")
            
            # 生成路径（创造性绕道模式）
            creative_paths = path_generator.generate_paths(
                thinking_seed=thinking_seed,
                task=task,
                max_paths=2,
                mode='creative_bypass'
            )
            
            logger.info(f"💡 创造性模式生成 {len(creative_paths)} 个路径:")
            for i, path in enumerate(creative_paths, 1):
                logger.info(f"   {i}. {path.path_type}")
        
        except Exception as e:
            logger.error(f"❌ 路径生成失败: {e}")


def demonstrate_learning_capabilities():
    """演示学习能力"""
    logger.info("\n🌱 演示学习和成长能力")
    
    # 创建路径生成器
    mock_llm = MockLLMClient()
    path_generator = PathGenerator(llm_client=mock_llm)
    
    # 模拟知识探索结果
    mock_exploration_result = {
        "exploration_metadata": {
            "exploration_session_id": "demo_exploration_001",
            "strategy_used": "trend_monitoring",
            "execution_mode": "professional_explorer"
        },
        "generated_thinking_seeds": [
            {
                "seed_id": "seed_trend_001",
                "seed_content": "基于AI技术发展趋势，提出多模态融合的创新解决方案",
                "creativity_level": "high",
                "confidence": 0.8,
                "potential_applications": ["技术创新", "产品设计", "市场策略"],
                "cross_domain_connections": ["人工智能", "用户体验", "商业模式"],
                "generated_at": time.time()
            },
            {
                "seed_id": "seed_analysis_002", 
                "seed_content": "通过系统性分析用户需求，发现潜在的服务优化机会",
                "creativity_level": "medium",
                "confidence": 0.7,
                "potential_applications": ["需求分析", "服务优化", "用户体验"],
                "cross_domain_connections": ["数据分析", "用户研究"],
                "generated_at": time.time()
            }
        ],
        "identified_trends": [
            {
                "trend_id": "trend_multimodal_ai",
                "trend_name": "多模态AI技术趋势",
                "confidence": 0.9
            }
        ],
        "cross_domain_connections": [
            {
                "connection_id": "ai_ux_fusion",
                "description": "AI技术与用户体验设计的深度融合",
                "confidence": 0.8
            }
        ]
    }
    
    # 从探索结果中学习
    logger.info("🔍 从知识探索结果中学习新路径...")
    learned_count = path_generator.learn_path_from_exploration(mock_exploration_result)
    logger.info(f"🌟 成功学习到 {learned_count} 个新路径")
    
    # 手动添加自定义路径
    logger.info("\n➕ 演示手动添加自定义路径...")
    custom_path = ReasoningPath(
        path_id="custom_demo_path_001",
        path_type="演示自定义型",
        description="专为演示创建的自定义思维路径",
        prompt_template="""请使用自定义演示方法解决任务：{task}

🎯 **自定义策略**:
1. **需求理解**: 深入理解具体需求和约束
2. **创意激发**: 激发多元化的解决思路
3. **方案整合**: 整合最佳元素形成完整方案
4. **实施规划**: 制定可行的实施计划

基于思维种子：{thinking_seed}
请提供创新且实用的解决方案。""",
        strategy_id="custom_demo"
    )
    
    success = path_generator.add_custom_path(
        path=custom_path,
        learning_source="manual_demo",
        effectiveness_score=0.7
    )
    
    if success:
        logger.info("✅ 自定义路径添加成功")
        
        # 测试新路径的使用
        logger.info("🧪 测试新路径的生成能力...")
        
        # 刷新路径模板以确保新路径可用
        path_generator.refresh_path_templates()
        
        # 生成包含新路径的结果
        test_paths = path_generator.generate_paths(
            thinking_seed="测试新学习的自定义路径",
            task="验证路径学习功能",
            max_paths=4
        )
        
        logger.info(f"🔄 生成的路径中包含 {len(test_paths)} 个，检查是否有新学习的路径:")
        for path in test_paths:
            if "自定义" in path.path_type or "演示" in path.path_type:
                logger.info(f"   ✨ 发现新学习的路径: {path.path_type}")
                break


def demonstrate_performance_tracking():
    """演示性能跟踪和推荐系统"""
    logger.info("\n📊 演示性能跟踪和智能推荐")
    
    mock_llm = MockLLMClient()
    path_generator = PathGenerator(llm_client=mock_llm)
    
    # 模拟路径使用和性能更新
    logger.info("📈 模拟路径性能数据...")
    
    performance_data = [
        ("systematic_analytical", True, 2.5, 0.9),    # 成功，耗时2.5秒，评分0.9
        ("creative_innovative", True, 3.1, 0.8),      # 成功，耗时3.1秒，评分0.8
        ("practical_pragmatic", False, 1.2, 0.4),     # 失败，耗时1.2秒，评分0.4
        ("systematic_analytical", True, 2.8, 0.85),   # 再次成功
        ("critical_questioning", True, 3.5, 0.75),    # 成功，但耗时较长
    ]
    
    for strategy_id, success, exec_time, rating in performance_data:
        updated = path_generator.update_path_performance(
            path_id=strategy_id,
            success=success,
            execution_time=exec_time,
            user_rating=rating
        )
        
        if updated:
            status = "✅ 成功" if success else "❌ 失败"
            logger.debug(f"   {strategy_id}: {status}, {exec_time}s, 评分{rating}")
    
    # 获取智能推荐
    logger.info("\n💡 基于性能数据的智能推荐:")
    
    test_contexts = [
        {
            "task_type": "analysis", 
            "complexity": "high",
            "urgency": "normal",
            "tags": ["systematic", "thorough"]
        },
        {
            "task_type": "innovation",
            "complexity": "medium", 
            "urgency": "high",
            "tags": ["creative", "breakthrough"]
        }
    ]
    
    for i, context in enumerate(test_contexts, 1):
        logger.info(f"📋 测试场景 {i}: {context}")
        
        recommended_paths = path_generator.get_recommended_paths_by_context(
            task_context=context,
            max_recommendations=3
        )
        
        logger.info(f"   推荐路径:")
        for j, path in enumerate(recommended_paths, 1):
            logger.info(f"     {j}. {path.path_type}")


def demonstrate_growth_insights():
    """演示成长洞察分析"""
    logger.info("\n🔮 演示成长洞察和发展建议")
    
    mock_llm = MockLLMClient()
    path_generator = PathGenerator(llm_client=mock_llm)
    
    # 获取成长洞察
    insights = path_generator.get_growth_insights()
    
    logger.info("📊 路径库成长情况:")
    library_growth = insights["library_growth"]
    logger.info(f"   总路径数: {library_growth['total_paths']}")
    logger.info(f"   学习路径数: {library_growth['learned_paths']}")
    logger.info(f"   学习比例: {library_growth['learning_ratio']:.2%}")
    
    logger.info("📈 使用模式分析:")
    usage_patterns = insights["usage_patterns"]
    logger.info(f"   总生成次数: {usage_patterns['total_generations']}")
    logger.info(f"   平均路径数/次: {usage_patterns['avg_paths_per_generation']:.1f}")
    
    if usage_patterns["most_used_paths"]:
        logger.info("   最常用路径:")
        for path_type, usage_count in usage_patterns["most_used_paths"]:
            logger.info(f"     - {path_type}: {usage_count} 次")
    
    logger.info("💡 成长建议:")
    for recommendation in insights["growth_recommendations"]:
        logger.info(f"   - {recommendation}")
    
    # 获取路径库详细统计
    library_stats = path_generator.get_path_library_stats()
    logger.info(f"\n📚 路径库详细统计:")
    logger.info(f"   存储后端: {library_stats['storage_backend']}")
    logger.info(f"   缓存效率: {library_stats.get('cache_efficiency', 0):.2%}")
    
    if "top_performers" in library_stats:
        logger.info("🏆 表现最佳路径:")
        for performer in library_stats["top_performers"]:
            logger.info(f"   - {performer['path_type']}: 效果{performer['effectiveness_score']:.2f}")


def demonstrate_backup_and_management():
    """演示备份和管理功能"""
    logger.info("\n💾 演示备份和管理功能")
    
    mock_llm = MockLLMClient()
    path_generator = PathGenerator(llm_client=mock_llm)
    
    # 创建备份
    backup_path = f"demo_data/backup_paths_{int(time.time())}"
    success = path_generator.backup_path_library(backup_path)
    
    if success:
        logger.info(f"✅ 路径库备份成功: {backup_path}")
    else:
        logger.warning("⚠️ 路径库备份失败")
    
    # 显示生成统计
    generation_stats = path_generator.get_generation_statistics()
    logger.info(f"📊 生成统计:")
    logger.info(f"   缓存生成数: {generation_stats['total_generations']}")
    logger.info(f"   平均路径数: {generation_stats['avg_paths_per_generation']:.1f}")
    logger.info(f"   回退使用率: {generation_stats['fallback_usage_rate']:.2%}")
    
    # 显示创造性绕道统计
    creative_stats = path_generator.get_creative_bypass_stats()
    logger.info(f"💡 创造性模式统计:")
    logger.info(f"   创造性使用比例: {creative_stats['creative_ratio']:.2%}")
    if creative_stats['most_used_creative_path']:
        logger.info(f"   最常用创造性路径: {creative_stats['most_used_creative_path']}")


if __name__ == "__main__":
    print("🧠 动态路径生成器完整功能演示")
    print("=" * 60)
    
    try:
        # 创建演示数据目录
        demo_data_dir = "demo_data"
        if not os.path.exists(demo_data_dir):
            os.makedirs(demo_data_dir)
        
        # 1. 动态库初始化演示
        demonstrate_dynamic_library_initialization()
        
        # 2. 静态模板迁移演示
        demonstrate_template_migration()
        
        # 3. 路径生成器集成演示
        demonstrate_path_generator_integration()
        
        # 4. 学习能力演示
        demonstrate_learning_capabilities()
        
        # 5. 性能跟踪演示
        demonstrate_performance_tracking()
        
        # 6. 成长洞察演示
        demonstrate_growth_insights()
        
        # 7. 备份管理演示
        demonstrate_backup_and_management()
        
        print("\n🎉 演示成功完成!")
        print("📝 总结:")
        print("   ✅ 动态路径库创建和管理")
        print("   ✅ 静态模板无缝迁移")
        print("   ✅ 智能路径生成和推荐")
        print("   ✅ 学习和自我成长能力")
        print("   ✅ 性能跟踪和优化建议")
        print("   ✅ 完整的备份和管理系统")
        print("   🧠 路径生成器已完全升级为可成长的'大脑皮层'")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理演示数据（可选）
        import shutil
        demo_data_dir = "demo_data"
        if os.path.exists(demo_data_dir):
            try:
                shutil.rmtree(demo_data_dir)
                logger.info("🧹 演示数据已清理")
            except Exception as e:
                logger.debug(f"清理演示数据时出现警告: {e}")
