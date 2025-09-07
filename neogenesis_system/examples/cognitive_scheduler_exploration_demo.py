#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知调度器知识探索功能演示
Cognitive Scheduler Knowledge Exploration Demo

这个演示展示了扩展后的认知调度器如何：
1. 主动探索外部世界，播下探索的种子
2. 发现新的思维种子并整合到认知飞轮中
3. 支持领域趋势监控、跨域学习等探索策略
"""

import sys
import os
import time
import logging

# 添加项目根路径到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.cognitive_scheduler import CognitiveScheduler, CognitiveMode
from shared.state_manager import StateManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """模拟LLM客户端用于演示"""
    
    def call_api(self, prompt: str, temperature: float = 0.8) -> str:
        """模拟LLM API调用"""
        return f"模拟LLM响应：基于温度{temperature}的创意输出"


def demonstrate_knowledge_exploration():
    """演示知识探索功能"""
    logger.info("🚀 开始认知调度器知识探索功能演示")
    
    # 1. 创建状态管理器
    logger.info("📋 创建状态管理器...")
    state_manager = StateManager()
    
    # 添加一些模拟的对话历史
    state_manager._conversation_history = []  # 简化演示
    
    # 2. 创建模拟LLM客户端
    logger.info("🧠 创建模拟LLM客户端...")
    mock_llm_client = MockLLMClient()
    
    # 3. 创建认知调度器（包含知识探索配置）
    logger.info("🔧 创建扩展的认知调度器...")
    exploration_config = {
        "idle_detection": {
            "min_idle_duration": 2.0,  # 缩短演示时间
            "check_interval": 1.0
        },
        "cognitive_tasks": {
            "exploration_interval": 5.0,  # 5秒后触发探索
        },
        "knowledge_exploration": {
            "exploration_strategies": [
                "domain_expansion",
                "trend_monitoring", 
                "gap_analysis",
                "cross_domain_learning"
            ],
            "max_exploration_depth": 2,
            "exploration_timeout": 30.0,
            "enable_web_search": False,  # 演示中关闭网络搜索
            "enable_trend_analysis": True,
            "knowledge_threshold": 0.6
        }
    }
    
    scheduler = CognitiveScheduler(
        state_manager=state_manager,
        llm_client=mock_llm_client,
        config=exploration_config
    )
    
    # 4. 演示知识探索功能
    logger.info("🌐 演示知识探索任务调度...")
    
    # 手动触发知识探索任务
    scheduler._schedule_knowledge_exploration_task()
    
    # 获取队列中的任务并执行
    if not scheduler.cognitive_task_queue.empty():
        exploration_task = scheduler.cognitive_task_queue.get()
        logger.info(f"📋 执行知识探索任务: {exploration_task.task_id}")
        
        # 执行探索任务
        result = scheduler._execute_knowledge_exploration_task(exploration_task)
        
        # 展示结果
        logger.info("✅ 知识探索结果展示:")
        logger.info(f"   探索会话ID: {result['exploration_metadata']['exploration_session_id']}")
        logger.info(f"   使用策略: {result['exploration_metadata']['strategies_used']}")
        logger.info(f"   探索机会数: {result['exploration_metadata']['opportunities_explored']}")
        
        logger.info(f"🔍 发现的知识 ({len(result['discovered_knowledge'])} 项):")
        for knowledge in result['discovered_knowledge']:
            logger.info(f"   - {knowledge['knowledge_id']}: {knowledge['content']}")
        
        logger.info(f"🌱 生成的思维种子 ({len(result['generated_thinking_seeds'])} 个):")
        for seed in result['generated_thinking_seeds']:
            logger.info(f"   - {seed['seed_id']}: {seed['seed_content']}")
        
        logger.info(f"📈 识别的趋势 ({len(result['identified_trends'])} 个):")
        for trend in result['identified_trends']:
            logger.info(f"   - {trend['trend_id']}: {trend['trend_name']}")
        
        logger.info(f"🔗 跨域连接 ({len(result['cross_domain_connections'])} 个):")
        for connection in result['cross_domain_connections']:
            logger.info(f"   - {connection['connection_id']}: {connection['domain1']} ↔ {connection['domain2']}")
    
    # 5. 展示认知飞轮整合效果
    logger.info("🔄 认知飞轮整合状态:")
    logger.info(f"   探索历史记录: {len(scheduler.exploration_history)} 条")
    logger.info(f"   发现的知识缓存: {len(scheduler.discovered_knowledge)} 项")
    logger.info(f"   探索主题缓存: {len(scheduler.exploration_topics_cache)} 个")
    
    # 6. 演示调度器状态
    status = scheduler.get_status()
    logger.info("📊 调度器当前状态:")
    for key, value in status["stats"].items():
        logger.info(f"   {key}: {value}")
    
    logger.info("✅ 知识探索功能演示完成!")
    logger.info("💡 认知飞轮现在能够主动探索外部世界，发现新的思维种子")


def demonstrate_exploration_opportunities_analysis():
    """演示探索机会分析"""
    logger.info("\n🔍 演示探索机会分析功能...")
    
    state_manager = StateManager()
    scheduler = CognitiveScheduler(state_manager=state_manager)
    
    # 分析探索机会
    opportunities = scheduler._analyze_exploration_opportunities()
    
    logger.info("发现的探索机会:")
    for opp in opportunities:
        logger.info(f"   🎯 {opp['opportunity_id']}")
        logger.info(f"      类型: {opp['type']}")
        logger.info(f"      描述: {opp['description']}")
        logger.info(f"      优先级: {opp['priority']}")
        logger.info(f"      关键词: {opp['exploration_keywords']}")
        logger.info("")
    
    # 识别知识缺口
    gaps = scheduler._identify_knowledge_gaps()
    
    logger.info("识别的知识缺口:")
    for gap in gaps:
        logger.info(f"   📊 {gap['gap_id']}")
        logger.info(f"      领域: {gap['area']}")
        logger.info(f"      描述: {gap['description']}")
        logger.info(f"      影响: {gap['impact']}")
        logger.info(f"      探索优先级: {gap['exploration_priority']}")
        logger.info("")


if __name__ == "__main__":
    print("🌐 认知调度器知识探索功能演示")
    print("=" * 50)
    
    try:
        # 主要演示
        demonstrate_knowledge_exploration()
        
        # 详细功能演示
        demonstrate_exploration_opportunities_analysis()
        
        print("\n🎉 演示成功完成!")
        print("📝 总结:")
        print("   ✅ 知识探索模式已成功集成到认知调度器")
        print("   ✅ 主动探索机制能够发现新的思维种子")
        print("   ✅ 认知飞轮现在支持外部世界探索")
        print("   ✅ 趋势监控和跨域学习功能已就绪")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
