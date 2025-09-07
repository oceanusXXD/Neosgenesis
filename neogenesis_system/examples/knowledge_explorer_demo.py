#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识探勘器完整功能演示
Knowledge Explorer Complete Feature Demo

这个演示展示了 knowledge_explorer.py 核心模块的完整功能：
1. 多种探索策略的使用
2. 外部信息源的集成
3. 知识质量评估和过滤机制
4. 思维种子的智能生成
5. 与认知调度器的完整集成
"""

import sys
import os
import time
import logging
from typing import List, Dict

# 添加项目根路径到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from neogenesis_system.providers.knowledge_explorer import (
    KnowledgeExplorer, ExplorationStrategy, ExplorationTarget,
    KnowledgeQuality, KnowledgeItem, ThinkingSeed
)
from core.cognitive_scheduler import CognitiveScheduler
from shared.state_manager import StateManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """模拟LLM客户端"""
    
    def call_api(self, prompt: str, temperature: float = 0.8) -> str:
        """模拟LLM API调用"""
        return f"模拟LLM响应：基于温度{temperature}的智能分析输出"


class MockWebSearchClient:
    """模拟网络搜索客户端"""
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """模拟搜索结果"""
        mock_results = [
            {
                "title": f"关于'{query}'的最新研究",
                "snippet": f"基于{query}的深度分析表明，这个领域正在快速发展，具有重要的应用前景...",
                "link": f"https://example.com/research/{query.replace(' ', '-')}",
                "source": "academic_paper"
            },
            {
                "title": f"{query}技术趋势报告",
                "snippet": f"最新的{query}技术趋势显示，创新应用不断涌现，市场潜力巨大...",
                "link": f"https://example.com/trends/{query.replace(' ', '-')}",
                "source": "industry_report"
            },
            {
                "title": f"{query}实践指南",
                "snippet": f"专家建议在{query}领域采用系统性方法，注重跨领域融合...",
                "link": f"https://example.com/guide/{query.replace(' ', '-')}",
                "source": "expert_guide"
            }
        ]
        return mock_results[:max_results]


def demonstrate_basic_exploration():
    """演示基础知识探索功能"""
    logger.info("🌐 演示基础知识探索功能")
    
    # 1. 创建知识探勘器
    mock_llm = MockLLMClient()
    mock_search = MockWebSearchClient()
    
    explorer_config = {
        "exploration_strategies": {
            "max_parallel_explorations": 2,
            "exploration_timeout": 60.0
        },
        "information_sources": {
            "enable_web_search": True,
            "max_results_per_source": 3
        },
        "seed_generation": {
            "max_seeds_per_exploration": 3,
            "creativity_boost_factor": 1.5
        }
    }
    
    explorer = KnowledgeExplorer(
        llm_client=mock_llm,
        web_search_client=mock_search,
        config=explorer_config
    )
    
    # 2. 创建探索目标
    targets = [
        ExplorationTarget(
            target_id="ai_trends_2024",
            target_type="trend",
            description="人工智能技术发展趋势",
            keywords=["人工智能", "机器学习", "深度学习", "AI应用"],
            priority=0.9,
            exploration_depth=2
        ),
        ExplorationTarget(
            target_id="cross_domain_innovation",
            target_type="methodology",
            description="跨领域创新方法论",
            keywords=["跨领域", "创新方法", "融合思维"],
            priority=0.7,
            exploration_depth=1
        )
    ]
    
    # 3. 执行不同策略的探索
    strategies_to_test = [
        ExplorationStrategy.TREND_MONITORING,
        ExplorationStrategy.CROSS_DOMAIN_LEARNING,
        ExplorationStrategy.DOMAIN_EXPANSION
    ]
    
    for strategy in strategies_to_test:
        logger.info(f"\n📋 测试探索策略: {strategy.value}")
        
        # 执行探索
        result = explorer.explore_knowledge(targets, strategy)
        
        # 展示结果
        logger.info(f"✅ 探索完成:")
        logger.info(f"   探索ID: {result.exploration_id}")
        logger.info(f"   执行时间: {result.execution_time:.2f}s")
        logger.info(f"   成功率: {result.success_rate:.2f}")
        logger.info(f"   质量评分: {result.quality_score:.2f}")
        
        logger.info(f"🔍 发现知识 ({len(result.discovered_knowledge)} 项):")
        for knowledge in result.discovered_knowledge:
            logger.info(f"   - {knowledge.knowledge_id}")
            logger.info(f"     质量: {knowledge.quality.value}")
            logger.info(f"     置信度: {knowledge.confidence_score:.2f}")
            logger.info(f"     内容: {knowledge.content[:80]}...")
        
        logger.info(f"🌱 生成种子 ({len(result.generated_seeds)} 个):")
        for seed in result.generated_seeds:
            logger.info(f"   - {seed.seed_id}")
            logger.info(f"     创意等级: {seed.creativity_level}")
            logger.info(f"     置信度: {seed.confidence:.2f}")
            logger.info(f"     内容: {seed.seed_content[:80]}...")
        
        logger.info(f"📈 识别趋势 ({len(result.identified_trends)} 个):")
        for trend in result.identified_trends:
            logger.info(f"   - {trend.get('trend_name', 'Unknown')}")
        
        time.sleep(1)  # 间隔演示


def demonstrate_quality_assessment():
    """演示知识质量评估机制"""
    logger.info("\n🔬 演示知识质量评估机制")
    
    explorer = KnowledgeExplorer()
    
    # 创建不同质量的测试知识项
    test_knowledge_items = [
        KnowledgeItem(
            knowledge_id="high_quality_1",
            content="最新的人工智能研究表明，大型语言模型在多模态理解方面取得了突破性进展，特别是在视觉-语言融合领域展现出前所未有的能力。这种进展为未来的AI应用开辟了新的可能性...",
            source="https://arxiv.org/example",
            source_type="academic_paper",
            quality=KnowledgeQuality.FAIR  # 初始质量，将被评估更新
        ),
        KnowledgeItem(
            knowledge_id="medium_quality_1",
            content="AI技术正在快速发展，应用广泛。",
            source="https://blog.example.com",
            source_type="web_search",
            quality=KnowledgeQuality.FAIR
        ),
        KnowledgeItem(
            knowledge_id="low_quality_1",
            content="AI好用。",
            source="unknown",
            source_type="unknown",
            quality=KnowledgeQuality.FAIR
        )
    ]
    
    logger.info("📊 知识质量评估结果:")
    
    for knowledge in test_knowledge_items:
        # 执行质量评估
        explorer._evaluate_knowledge_quality(knowledge)
        
        logger.info(f"\n🔍 知识项: {knowledge.knowledge_id}")
        logger.info(f"   最终质量: {knowledge.quality.value}")
        logger.info(f"   置信度: {knowledge.confidence_score:.2f}")
        logger.info(f"   相关性: {knowledge.relevance_score:.2f}")
        logger.info(f"   新颖性: {knowledge.novelty_score:.2f}")
        logger.info(f"   通过过滤: {'是' if explorer._passes_quality_filter(knowledge) else '否'}")
        logger.info(f"   内容长度: {len(knowledge.content)} 字符")


def demonstrate_integrated_workflow():
    """演示与认知调度器的集成工作流程"""
    logger.info("\n🔄 演示与认知调度器的集成工作流程")
    
    # 1. 创建认知调度器（集成知识探勘器）
    state_manager = StateManager()
    mock_llm = MockLLMClient()
    
    scheduler_config = {
        "idle_detection": {
            "min_idle_duration": 1.0,  # 加速演示
            "check_interval": 0.5
        },
        "cognitive_tasks": {
            "exploration_interval": 2.0  # 2秒触发探索
        },
        "knowledge_exploration": {
            "exploration_strategies": ["trend_monitoring", "domain_expansion"],
            "max_exploration_depth": 2,
            "enable_web_search": False,  # 演示中禁用网络搜索
            "knowledge_threshold": 0.5
        }
    }
    
    scheduler = CognitiveScheduler(
        state_manager=state_manager,
        llm_client=mock_llm,
        config=scheduler_config
    )
    
    # 2. 更新知识探勘器依赖（如果需要）
    if hasattr(scheduler, 'knowledge_explorer') and scheduler.knowledge_explorer:
        mock_search = MockWebSearchClient()
        scheduler.update_knowledge_explorer_dependencies(
            web_search_client=mock_search,
            additional_config={"test_mode": True}
        )
    
    # 3. 手动触发知识探索任务
    logger.info("🚀 触发知识探索任务...")
    scheduler._schedule_knowledge_exploration_task()
    
    # 4. 获取并执行任务
    if not scheduler.cognitive_task_queue.empty():
        exploration_task = scheduler.cognitive_task_queue.get()
        
        logger.info(f"📋 执行知识探索任务: {exploration_task.task_id}")
        logger.info(f"   任务类型: {exploration_task.task_type}")
        logger.info(f"   优先级: {exploration_task.priority}")
        
        # 执行任务
        result = scheduler._execute_knowledge_exploration_task(exploration_task)
        
        # 展示完整结果
        logger.info("🎉 集成工作流程结果:")
        logger.info(f"   执行模式: {result['exploration_metadata']['execution_mode']}")
        logger.info(f"   发现知识: {len(result['discovered_knowledge'])} 项")
        logger.info(f"   生成种子: {len(result['generated_thinking_seeds'])} 个")
        
        # 展示几个关键结果
        if result['discovered_knowledge']:
            logger.info("\n📚 发现的知识样例:")
            for knowledge in result['discovered_knowledge'][:2]:
                logger.info(f"   - {knowledge.get('knowledge_id', 'Unknown')}")
                logger.info(f"     质量: {knowledge.get('quality', 'Unknown')}")
                logger.info(f"     内容: {knowledge.get('content', '')[:60]}...")
        
        if result['generated_thinking_seeds']:
            logger.info("\n🌱 生成的思维种子样例:")
            for seed in result['generated_thinking_seeds'][:2]:
                logger.info(f"   - {seed.get('seed_id', 'Unknown')}")
                logger.info(f"     创意等级: {seed.get('creativity_level', 'Unknown')}")
                logger.info(f"     内容: {seed.get('seed_content', '')[:60]}...")
    
    # 5. 展示探索统计
    if hasattr(scheduler, 'knowledge_explorer') and scheduler.knowledge_explorer:
        stats = scheduler.knowledge_explorer.get_exploration_stats()
        logger.info("\n📊 知识探勘器统计:")
        for key, value in stats.items():
            if key not in ['strategy_performance', 'cache_status']:
                logger.info(f"   {key}: {value}")


def demonstrate_exploration_strategies():
    """演示所有探索策略"""
    logger.info("\n🎯 演示所有探索策略")
    
    explorer = KnowledgeExplorer()
    
    # 创建通用探索目标
    target = ExplorationTarget(
        target_id="strategy_demo",
        target_type="general",
        description="策略演示目标",
        keywords=["创新", "技术", "方法论"],
        priority=0.8
    )
    
    strategies = [
        ExplorationStrategy.DOMAIN_EXPANSION,
        ExplorationStrategy.TREND_MONITORING,
        ExplorationStrategy.GAP_ANALYSIS,
        ExplorationStrategy.CROSS_DOMAIN_LEARNING,
        ExplorationStrategy.SERENDIPITY_DISCOVERY
    ]
    
    logger.info("🔄 测试所有探索策略:")
    
    for strategy in strategies:
        logger.info(f"\n📌 策略: {strategy.value}")
        
        # 构建搜索查询（模拟）
        queries = explorer._build_search_queries(target, strategy)
        logger.info(f"   生成查询: {queries[:2]}")  # 显示前2个查询
        
        # 建议推理路径（模拟）
        knowledge_item = KnowledgeItem(
            knowledge_id="demo",
            content="演示内容",
            source="demo",
            source_type="demo",
            quality=KnowledgeQuality.GOOD
        )
        
        paths = explorer._suggest_reasoning_paths(knowledge_item, strategy)
        logger.info(f"   推理路径: {paths}")


if __name__ == "__main__":
    print("🌐 知识探勘器完整功能演示")
    print("=" * 60)
    
    try:
        # 基础探索功能演示
        demonstrate_basic_exploration()
        
        # 质量评估机制演示
        demonstrate_quality_assessment()
        
        # 探索策略演示
        demonstrate_exploration_strategies()
        
        # 集成工作流程演示
        demonstrate_integrated_workflow()
        
        print("\n🎉 演示成功完成!")
        print("📝 总结:")
        print("   ✅ 知识探勘器核心模块功能完整")
        print("   ✅ 多种探索策略运行正常")
        print("   ✅ 知识质量评估机制有效")
        print("   ✅ 思维种子生成能力良好")
        print("   ✅ 与认知调度器集成成功")
        print("   ✅ 认知飞轮外部智慧连接器就绪")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
