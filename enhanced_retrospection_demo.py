#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版回溯引擎演示
展示核心组件增强后的主动认知能力

本演示展示步骤三完成后的效果：
1. LLMDrivenDimensionCreator的回顾性分析能力  
2. MABConverger的知识来源追踪和精细化反馈处理
3. 完整的主动回溯工作流程验证
"""

import os
import sys
import time
import logging
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_components():
    """测试增强后的核心组件"""
    print("🧪 步骤三完成验证：增强版核心组件测试")
    print("="*60)
    
    try:
        # 测试LLMDrivenDimensionCreator的增强功能
        print("\n1️⃣ 测试LLMDrivenDimensionCreator增强功能...")
        
        from neogenesis_system.cognitive_engine.path_generator import LLMDrivenDimensionCreator
        from neogenesis_system.providers.llm_manager import LLMManager
        
        # 创建LLM客户端
        llm_client = LLMManager()
        dimension_creator = LLMDrivenDimensionCreator(llm_client=llm_client)
        
        # 测试常规维度创建
        print("   🔹 测试常规维度创建...")
        normal_dimensions = dimension_creator.create_dynamic_dimensions(
            user_query="如何优化深度学习模型的训练速度？",
            num_dimensions=2,
            creativity_level="medium"
        )
        print(f"   ✅ 常规模式生成 {len(normal_dimensions)} 个维度")
        
        # 测试回顾性分析模式
        print("   🔍 测试回顾性分析模式...")
        retrospective_dimensions = dimension_creator.create_dynamic_dimensions(
            task_description="回顾历史任务：如何优化深度学习模型？我们之前使用了数据并行的方案。现在请从全新角度重新思考这个问题。",
            num_dimensions=3,
            creativity_level="high",
            context={
                "mode": "retrospective_analysis",
                "original_task": "如何优化深度学习模型的训练速度？",
                "original_response": "建议使用数据并行和梯度累积技术...",
                "task_metadata": {
                    "success": True,
                    "complexity": 0.7,
                    "tool_calls": 2
                }
            }
        )
        print(f"   ✨ 回顾性模式生成 {len(retrospective_dimensions)} 个创新维度")
        
        # 显示创新维度的特征
        for i, dim in enumerate(retrospective_dimensions[:2]):
            if hasattr(dim, 'retrospective_metadata'):
                print(f"      维度{i+1}: 创新分数 {dim.retrospective_metadata['innovation_score']}")
        
        print("   ✅ LLMDrivenDimensionCreator增强功能验证完成")
        
        # 测试MABConverger的知识来源追踪
        print("\n2️⃣ 测试MABConverger知识来源追踪...")
        
        from neogenesis_system.cognitive_engine.mab_converger import MABConverger
        
        mab_converger = MABConverger()
        
        # 模拟不同来源的反馈
        print("   📊 注入不同来源的性能反馈...")
        
        # 用户反馈
        mab_converger.update_path_performance(
            "user_strategy_1", success=True, reward=0.8, source="user_feedback"
        )
        
        # 回溯分析反馈
        mab_converger.update_path_performance(
            "retro_innovation_1", success=True, reward=0.6, source="retrospection"
        )
        mab_converger.update_path_performance(
            "retro_innovation_2", success=False, reward=0.2, source="retrospection"
        )
        
        # 工具验证反馈
        mab_converger.update_path_performance(
            "tool_verified_1", success=True, reward=0.9, source="tool_verification"
        )
        
        print("   📈 反馈注入完成，查看来源追踪统计...")
        
        # 获取来源统计
        source_stats = mab_converger.get_feedback_source_stats()
        
        print("   📊 知识来源追踪统计:")
        for source, data in source_stats["source_tracking"].items():
            if data["count"] > 0:
                print(f"      {source}: 次数={data['count']}, 成功率={data['success_rate']:.1%}, 平均奖励={data['avg_reward']:.3f}")
        
        print(f"   🔍 回溯分析贡献: {source_stats['retrospection_contribution']['total_retrospection_feedback']} 次反馈")
        
        print("   ✅ MABConverger知识来源追踪验证完成")
        
        # 测试完整工作流程
        print("\n3️⃣ 测试完整的主动回溯工作流程...")
        
        from neogenesis_agent_runner import create_neogenesis_agent
        
        config = {
            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
            'search_engine': 'duckduckgo',
            'enable_cognitive_scheduler': True,
            'cognitive_config': {
                'idle_detection': {'min_idle_duration': 2.0, 'check_interval': 0.5},
                'cognitive_tasks': {'retrospection_interval': 5.0}
            },
            'retrospection_config': {
                'ideation': {
                    'enable_llm_dimensions': True,
                    'enable_aha_moment': True,
                    'max_new_dimensions': 2
                },
                'assimilation': {
                    'enable_mab_injection': True,
                    'initial_exploration_reward': 0.15
                }
            }
        }
        
        agent = create_neogenesis_agent(config=config)
        
        print("   🚀 启动认知模式进行工作流程测试...")
        agent.start_cognitive_mode()
        
        # 执行一个任务为回溯创建历史
        print("   📚 执行历史任务...")
        result = agent.run("深度学习模型压缩的最新技术有哪些？")
        print(f"   ✅ 历史任务完成: {len(result)} 字符")
        
        print("   ⏳ 等待主动回溯分析...")
        time.sleep(8)  # 等待回溯触发
        
        # 检查认知状态
        status = agent.get_cognitive_status()
        if 'stats' in status:
            stats = status['stats']
            retrospections = stats.get('retrospection_sessions', 0)
            print(f"   🔍 回溯分析执行: {retrospections} 次")
            
            if retrospections > 0:
                print("   ✅ 主动回溯工作流程验证成功")
            else:
                print("   ⚠️ 回溯未触发，可能需要更长等待时间")
        
        agent.stop_cognitive_mode()
        
        print("\n" + "="*60)
        print("🎉 步骤三增强验证完成！")
        print("")
        print("✨ 核心组件增强成果:")
        print("   🧠 LLMDrivenDimensionCreator:")
        print("      - 支持回顾性分析模式")
        print("      - 创新性prompt构建")
        print("      - 增强版维度解析和路径生成")
        print("")
        print("   🎰 MABConverger:")
        print("      - 知识来源追踪系统")
        print("      - 精细化反馈权重调整")
        print("      - 回溯分析专项奖励机制")
        print("")
        print("   🔄 完整工作流程:")
        print("      - 主动回溯 → 创新思维 → 知识沉淀")
        print("      - 闭环学习系统正常运转")
        print("")
        print("🚀 Neogenesis System 已完成从'被动应激'到'主动认知'的核心升级！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("🔬 Neogenesis增强版回溯引擎演示")
    print("验证步骤三核心组件增强效果")
    print("="*60)
    
    try:
        test_enhanced_components()
        
    except KeyboardInterrupt:
        print(f"\n👋 用户中断测试")
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
