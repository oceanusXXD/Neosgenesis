#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎭 试炼场演示脚本 - MABConverger 新思想试炼系统

这个脚本演示了 MABConverger 的试炼场功能：
- 新思想的自动适应和探索增强
- 优胜劣汰机制（成功路径提升，失败路径淘汰）
- 试炼场分析和监控系统
- 黄金模板的动态管理

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

from cognitive_engine.mab_converger import MABConverger
from cognitive_engine.path_generator import PathGenerator, ReasoningPath
from utils.logging_setup import setup_logger


def create_mock_learned_paths():
    """创建一些模拟的学习路径用于演示"""
    learned_paths = [
        ReasoningPath(
            name="网络学习路径：创新思维",
            description="从互联网学习到的创新问题解决方法",
            steps=[
                "🌐 分析问题的多维度特征",
                "💡 运用逆向思维寻找突破点", 
                "🔄 建立反馈循环验证假设",
                "🎯 聚焦核心价值输出解决方案"
            ],
            keywords=["创新", "逆向思维", "反馈循环"],
            complexity_level=4,
            estimated_steps=4,
            success_indicators=["方案创新性", "实施可行性", "效果可量化"],
            failure_patterns=["思路过于抽象", "缺乏实证支持"],
            metadata={
                "source": "learned_exploration",
                "learned_from": "知识探索模块",
                "confidence": 0.75
            }
        ),
        ReasoningPath(
            name="网络学习路径：系统分析",
            description="基于网络资源学习的系统化分析方法",
            steps=[
                "📊 建立系统全景图",
                "🔍 识别关键节点和连接",
                "⚖️ 评估各部分权重和影响",
                "🎲 预测系统行为和变化"
            ],
            keywords=["系统思维", "全景分析", "权重评估"],
            complexity_level=5,
            estimated_steps=4,
            success_indicators=["系统理解深度", "预测准确性"],
            failure_patterns=["忽略重要连接", "权重判断失误"],
            metadata={
                "source": "learned_exploration", 
                "learned_from": "知识探索模块",
                "confidence": 0.85
            }
        ),
        ReasoningPath(
            name="网络学习路径：快速原型",
            description="从网络学习的快速原型验证方法",
            steps=[
                "⚡ 提取核心假设",
                "🛠️ 构建最小可验证原型",
                "🧪 设计关键实验",
                "📈 分析结果并迭代"
            ],
            keywords=["快速原型", "MVP", "实验验证"],
            complexity_level=3,
            estimated_steps=4,
            success_indicators=["原型完成速度", "验证有效性"],
            failure_patterns=["原型过于复杂", "实验设计不当"],
            metadata={
                "source": "learned_exploration",
                "learned_from": "知识探索模块", 
                "confidence": 0.65
            }
        )
    ]
    return learned_paths


def demonstrate_trial_ground_basics(mab_converger, logger):
    """演示试炼场的基础功能"""
    logger.info("🎭 === 试炼场基础功能演示 ===")
    
    # 获取初始状态
    initial_analytics = mab_converger.get_trial_ground_analytics()
    logger.info(f"📊 初始状态 - 活跃路径: {initial_analytics['overview']['total_active_paths']}")
    logger.info(f"🌱 学习路径: {initial_analytics['overview']['learned_paths_count']}")
    
    # 创建模拟学习路径
    learned_paths = create_mock_learned_paths()
    
    # 将学习路径注入系统
    logger.info("🌱 注入学习路径到试炼场...")
    for path in learned_paths:
        # 模拟路径选择过程，触发自动适应
        selected_path = mab_converger.select_best_path([path])
        logger.info(f"✅ 学习路径已注入: {path.name}")
        logger.info(f"   探索增强状态: {mab_converger.get_exploration_boost(selected_path.name):.2f}x")
    
    # 显示注入后的状态
    post_injection_analytics = mab_converger.get_trial_ground_analytics()
    logger.info(f"\n📊 注入后状态 - 活跃路径: {post_injection_analytics['overview']['total_active_paths']}")
    logger.info(f"🌱 学习路径: {post_injection_analytics['overview']['learned_paths_count']}")
    logger.info(f"🚀 探索增强中: {post_injection_analytics['overview']['exploration_boost_active']}")


def simulate_path_trials(mab_converger, logger, num_rounds=20):
    """模拟路径试炼过程"""
    logger.info(f"\n🎯 === 开始模拟 {num_rounds} 轮路径试炼 ===")
    
    # 获取所有可用路径
    path_generator = PathGenerator()
    all_paths = path_generator.get_recommended_paths_by_context("测试场景")
    
    # 添加学习路径
    learned_paths = create_mock_learned_paths()
    all_paths.extend(learned_paths)
    
    logger.info(f"📋 可用路径总数: {len(all_paths)}")
    
    # 模拟多轮选择和反馈
    for round_num in range(1, num_rounds + 1):
        logger.info(f"\n🔄 第 {round_num} 轮试炼")
        
        # 选择最佳路径
        selected_path = mab_converger.select_best_path(all_paths)
        logger.info(f"🎯 选中路径: {selected_path.name}")
        
        # 模拟执行结果（为学习路径设置不同的成功概率）
        if hasattr(selected_path, 'metadata') and selected_path.metadata.get('source') == 'learned_exploration':
            # 学习路径：初期较低成功率，后期提高
            base_success_rate = selected_path.metadata.get('confidence', 0.5)
            # 模拟学习路径逐渐改善
            improvement_factor = min(round_num / 15, 1.0)  # 15轮后达到最佳状态
            success_probability = base_success_rate + (0.3 * improvement_factor)
        else:
            # 静态路径：相对稳定的成功率
            success_probability = 0.75
        
        # 生成随机结果
        import random
        success = random.random() < success_probability
        reward = random.uniform(0.7, 1.0) if success else random.uniform(0.1, 0.4)
        
        # 更新性能
        mab_converger.update_path_performance(
            path_id=selected_path.name,
            success=success,
            reward=reward,
            source="simulation"
        )
        
        result_emoji = "✅" if success else "❌"
        logger.info(f"   {result_emoji} 执行结果: {'成功' if success else '失败'} (奖励: {reward:.2f})")
        
        # 每5轮显示一次状态
        if round_num % 5 == 0:
            analytics = mab_converger.get_trial_ground_analytics()
            logger.info(f"📊 第 {round_num} 轮后状态:")
            logger.info(f"   淘汰候选: {len(analytics['culling_analysis']['current_candidates'])}")
            logger.info(f"   提升候选: {len(analytics['golden_template_candidates']['promotion_candidates'])}")
            logger.info(f"   黄金模板: {analytics['golden_template_candidates']['current_golden_count']}")


def demonstrate_culling_mechanism(mab_converger, logger):
    """演示淘汰机制"""
    logger.info("\n🗡️ === 淘汰机制演示 ===")
    
    # 创建一个必然失败的路径
    failing_path = ReasoningPath(
        name="注定失败路径",
        description="用于演示淘汰机制的测试路径",
        steps=["❌ 这个路径总是失败"],
        keywords=["测试", "失败"],
        complexity_level=1,
        estimated_steps=1,
        success_indicators=[],
        failure_patterns=["一切"],
        metadata={"source": "test", "will_fail": True}
    )
    
    # 让这个路径多次失败
    logger.info("🔥 制造连续失败...")
    for i in range(15):
        selected = mab_converger.select_best_path([failing_path])
        mab_converger.update_path_performance(
            path_id=failing_path.name,
            success=False,
            reward=0.0,
            source="test_failure"
        )
    
    # 检查淘汰候选状态
    analytics = mab_converger.get_trial_ground_analytics()
    logger.info(f"⚠️ 当前淘汰候选: {len(analytics['culling_analysis']['current_candidates'])}")
    for candidate in analytics['culling_analysis']['current_candidates']:
        logger.info(f"   - {candidate['strategy_id']}: 成功率 {candidate['success_rate']:.3f}")
    
    # 执行自动淘汰
    culling_result = mab_converger.execute_automatic_culling()
    logger.info(f"🗡️ 淘汰执行结果: 淘汰 {len(culling_result['paths_culled'])} 个路径")
    
    for culled in culling_result['paths_culled']:
        logger.info(f"   💀 已淘汰: {culled['strategy_id']} - {culled['reason']}")


def demonstrate_golden_promotion(mab_converger, logger):
    """演示黄金模板提升"""
    logger.info("\n🏆 === 黄金模板提升演示 ===")
    
    # 创建一个高性能路径
    excellent_path = ReasoningPath(
        name="卓越学习路径",
        description="表现优异的学习路径",
        steps=["🌟 总是成功的步骤"],
        keywords=["卓越", "成功"],
        complexity_level=3,
        estimated_steps=1,
        success_indicators=["一切"],
        failure_patterns=[],
        metadata={"source": "learned_exploration", "confidence": 0.95}
    )
    
    # 让这个路径多次成功
    logger.info("🌟 制造优秀表现...")
    for i in range(25):
        selected = mab_converger.select_best_path([excellent_path])
        mab_converger.update_path_performance(
            path_id=excellent_path.name,
            success=True,
            reward=0.9,
            source="excellence_test"
        )
    
    # 检查提升候选状态
    analytics = mab_converger.get_trial_ground_analytics()
    logger.info(f"🌟 当前提升候选: {len(analytics['golden_template_candidates']['promotion_candidates'])}")
    
    for candidate in analytics['golden_template_candidates']['promotion_candidates']:
        logger.info(f"   - {candidate['strategy_id']}: 成功率 {candidate['success_rate']:.3f}, 资格评分: {candidate['qualification_score']:.3f}")
    
    # 手动提升为黄金模板
    promotion_result = mab_converger.force_promote_to_golden(
        excellent_path.name, 
        "演示优秀学习路径提升"
    )
    
    if promotion_result['success']:
        logger.info(f"🏆 成功提升为黄金模板: {excellent_path.name}")
        logger.info(f"   提升时成功率: {promotion_result['previous_status']['success_rate']:.3f}")
    else:
        logger.info(f"❌ 提升失败: {promotion_result.get('error', '未知错误')}")


def demonstrate_analytics_and_maintenance(mab_converger, logger):
    """演示分析和维护功能"""
    logger.info("\n📊 === 试炼场分析和维护演示 ===")
    
    # 获取完整分析报告
    analytics = mab_converger.get_trial_ground_analytics()
    
    logger.info("📊 试炼场全面分析报告:")
    
    # 总体概况
    overview = analytics['overview']
    logger.info(f"   总活跃路径: {overview['total_active_paths']}")
    logger.info(f"   学习路径: {overview['learned_paths_count']}")
    logger.info(f"   黄金模板: {overview['golden_templates']}")
    logger.info(f"   探索增强中: {overview['exploration_boost_active']}")
    logger.info(f"   淘汰候选: {overview['culling_candidates']}")
    
    # 性能趋势
    trends = analytics['performance_trends']
    logger.info(f"\n📈 系统健康状况: {trends['overall_system_health']}")
    logger.info(f"   平均成功率: {trends['avg_success_rate']:.3f}")
    logger.info(f"   优秀路径: {trends['performance_distribution']['excellent']}")
    logger.info(f"   良好路径: {trends['performance_distribution']['good']}")
    logger.info(f"   一般路径: {trends['performance_distribution']['average']}")
    logger.info(f"   较差路径: {trends['performance_distribution']['poor']}")
    
    # 学习路径分析
    learned_analysis = analytics['learned_paths']
    if learned_analysis['active_learned_paths']:
        logger.info(f"\n🌱 学习路径分析:")
        logger.info(f"   平均成功率: {learned_analysis['avg_success_rate']:.3f}")
        logger.info(f"   总激活次数: {learned_analysis['total_activations']}")
        logger.info("   性能分布:")
        for level, count in learned_analysis['performance_summary'].items():
            logger.info(f"     {level}: {count} 个")
    
    # 执行维护任务
    logger.info("\n🔧 执行试炼场维护...")
    maintenance_result = mab_converger.trigger_trial_ground_maintenance()
    
    logger.info("🔧 维护任务执行结果:")
    for task in maintenance_result['tasks_executed']:
        logger.info(f"   ✅ {task}")
    
    # 显示清理结果
    if 'expired_boosts' in maintenance_result['cleanup_results']:
        expired = maintenance_result['cleanup_results']['expired_boosts']
        logger.info(f"   🧹 清理过期探索增强: {expired['cleaned_count']} 个")
    
    if 'history' in maintenance_result['cleanup_results']:
        history = maintenance_result['cleanup_results']['history']
        if history.get('trimmed', 0) > 0:
            logger.info(f"   📚 修剪淘汰历史: {history['trimmed']} 条")


def main():
    """主演示函数"""
    # 设置日志
    logger = setup_logger("TrialGroundDemo")
    
    logger.info("🎭 ========================================")
    logger.info("🎭      MABConverger 试炼场系统演示")
    logger.info("🎭 ========================================")
    logger.info("🎭 这个演示将展示新思想在试炼场中的完整生命周期:")
    logger.info("🎭 1. 新思想的自动适应和探索增强")
    logger.info("🎭 2. 多轮试炼和性能反馈")
    logger.info("🎭 3. 优胜劣汰机制（提升和淘汰）")
    logger.info("🎭 4. 试炼场分析和维护")
    logger.info("🎭 ========================================\n")
    
    try:
        # 初始化 MABConverger
        logger.info("🎰 初始化 MABConverger...")
        mab_converger = MABConverger()
        logger.info("✅ MABConverger 初始化完成\n")
        
        # 1. 基础功能演示
        demonstrate_trial_ground_basics(mab_converger, logger)
        
        # 等待用户确认
        input("\n🔄 按 Enter 键继续模拟试炼过程...")
        
        # 2. 路径试炼模拟
        simulate_path_trials(mab_converger, logger, num_rounds=25)
        
        # 等待用户确认
        input("\n🗡️ 按 Enter 键继续演示淘汰机制...")
        
        # 3. 淘汰机制演示
        demonstrate_culling_mechanism(mab_converger, logger)
        
        # 等待用户确认
        input("\n🏆 按 Enter 键继续演示黄金模板提升...")
        
        # 4. 黄金模板提升演示
        demonstrate_golden_promotion(mab_converger, logger)
        
        # 等待用户确认
        input("\n📊 按 Enter 键继续演示分析和维护功能...")
        
        # 5. 分析和维护演示
        demonstrate_analytics_and_maintenance(mab_converger, logger)
        
        logger.info("\n🎭 ========================================")
        logger.info("🎭      试炼场演示完成！")
        logger.info("🎭 ========================================")
        logger.info("🎯 关键特性展示:")
        logger.info("   ✅ 新思想自动适应和探索增强")
        logger.info("   ✅ 智能的优胜劣汰机制")
        logger.info("   ✅ 全面的性能分析和监控")
        logger.info("   ✅ 自动化的维护和优化")
        logger.info("\n🌟 试炼场系统已经准备好迎接真正的认知进化！")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 演示被用户中断")
    except Exception as e:
        logger.error(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("👋 演示结束")


if __name__ == "__main__":
    main()
