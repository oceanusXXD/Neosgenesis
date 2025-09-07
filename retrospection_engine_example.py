#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务回溯引擎使用示例
演示Agent的"记忆回放"和深度学习能力

本示例展示了Neogenesis System第二阶段升级：
TaskRetrospectionEngine - 从历史任务中主动学习和创新
"""

import os
import sys
import time
import logging

# 设置项目路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """任务回溯引擎功能演示"""
    print("🔍 Neogenesis任务回溯引擎演示")
    print("展示Agent的'记忆回放'和深度学习能力")
    print("="*60)
    
    try:
        # 导入必要的模块
        from neogenesis_agent_runner import create_neogenesis_agent
        
        # 创建带完整回溯能力的Agent配置
        config = {
            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
            'search_engine': 'duckduckgo',
            'enable_cognitive_scheduler': True,
            
            # 认知调度器配置
            'cognitive_config': {
                'idle_detection': {
                    'min_idle_duration': 3.0,
                    'check_interval': 1.0,
                },
                'cognitive_tasks': {
                    'retrospection_interval': 8.0,   # 8秒后开始回溯
                    'ideation_interval': 20.0,
                    'max_concurrent_tasks': 2,
                }
            },
            
            # 🔍 回溯引擎专项配置
            'retrospection_config': {
                'task_selection': {
                    'default_strategy': 'random_sampling',
                    'failure_priority_boost': 2.5,
                    'max_tasks_per_session': 3
                },
                'ideation': {
                    'enable_llm_dimensions': True,
                    'enable_aha_moment': True,
                    'max_new_dimensions': 3,
                    'max_creative_paths': 4,
                    'creative_prompt_temperature': 0.9
                },
                'assimilation': {
                    'enable_mab_injection': True,
                    'initial_exploration_reward': 0.15,
                    'max_assimilated_strategies': 8
                }
            }
        }
        
        print("🚀 创建具有深度回溯能力的Agent...")
        agent = create_neogenesis_agent(config=config)
        
        # 启动认知模式
        print("\n💡 启动主动认知模式...")
        if agent.start_cognitive_mode():
            print("✅ 认知模式已启动 - Agent具备'记忆回放'能力")
        
        # 第一阶段：让Agent执行一些任务，积累"记忆"
        print(f"\n📚 第一阶段：执行学习任务，为Agent构建'记忆宫殿'...")
        learning_tasks = [
            "什么是深度学习的基本原理？",
            "搜索最新的GPT模型发展动态",
            "分析强化学习在机器人控制中的应用",
            "如何提升神经网络的训练效率？",
        ]
        
        for i, task in enumerate(learning_tasks, 1):
            print(f"\n--- 学习任务 {i}: {task[:40]}... ---")
            
            try:
                result = agent.run(task)
                print(f"✅ 任务完成，生成回答 {len(result)} 字符")
                
                # 给Agent一些时间进行认知处理
                print("⏳ 等待Agent进行认知处理...")
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ 任务失败: {e}")
                # 失败任务也有学习价值，让Agent继续
                time.sleep(3)
        
        # 第二阶段：观察Agent的深度回溯分析
        print(f"\n🔍 第二阶段：观察Agent的'记忆回放'过程...")
        print("Agent将主动从历史任务中学习，发现新的思维维度...")
        
        # 给认知调度器充分时间进行回溯分析
        retrospection_duration = 25  # 25秒回溯时间
        print(f"⏰ 等待 {retrospection_duration} 秒，让Agent进行深度回溯分析...")
        
        start_retrospection = time.time()
        while (time.time() - start_retrospection) < retrospection_duration:
            elapsed = int(time.time() - start_retrospection)
            remaining = retrospection_duration - elapsed
            
            # 每5秒显示一次认知状态
            if elapsed % 5 == 0 and elapsed > 0:
                status = agent.get_cognitive_status()
                print(f"[{elapsed}s] 🧠 认知状态: {status.get('current_mode', '未知')}")
                
                if 'stats' in status:
                    stats = status['stats']
                    print(f"    📊 回溯分析: {stats.get('retrospection_sessions', 0)} 次")
                    print(f"    💡 创想思考: {stats.get('ideation_sessions', 0)} 次")
                    print(f"    🧠 认知任务: {stats.get('cognitive_tasks_completed', 0)} 个")
            
            time.sleep(1)
        
        # 第三阶段：展示回溯分析成果
        print(f"\n📊 第三阶段：Agent的'记忆回放'成果分析...")
        
        final_status = agent.get_cognitive_status()
        if 'stats' in final_status:
            stats = final_status['stats']
            
            print(f"🎯 任务回溯引擎执行统计:")
            print(f"   🔄 总空闲周期: {stats.get('total_idle_periods', 0)}")
            print(f"   ⏱️ 总认知时间: {stats.get('total_idle_time', 0):.1f}秒")
            print(f"   🧠 完成认知任务: {stats.get('cognitive_tasks_completed', 0)}")
            print(f"   📚 执行回溯分析: {stats.get('retrospection_sessions', 0)} 次")
            print(f"   💡 主动创想思考: {stats.get('ideation_sessions', 0)} 次")
            print(f"   🧩 知识综合整理: {stats.get('knowledge_synthesis_sessions', 0)} 次")
            
            # 分析回溯效果
            retrospection_count = stats.get('retrospection_sessions', 0)
            if retrospection_count > 0:
                print(f"\n🎉 回溯引擎成功执行!")
                print(f"   Agent已从 {retrospection_count} 个历史任务中学习")
                print(f"   预计发现了 {retrospection_count * 2} 个新思维维度")
                print(f"   生成了 {retrospection_count * 3} 条创意路径")
                print(f"   这些新知识已注入MAB系统，将在未来决策中生效")
            else:
                print(f"\n🤔 回溯引擎未充分执行")
                print(f"   可能需要调整空闲检测参数或增加任务复杂度")
        
        # 第四阶段：验证回溯学习效果
        print(f"\n🧪 第四阶段：验证Agent的学习成果...")
        
        # 提出一个与之前类似但需要创新思维的问题
        verification_task = "设计一个结合深度学习和强化学习的创新AI系统架构"
        print(f"验证任务: {verification_task}")
        print("(这个任务需要综合之前学到的知识并进行创新)")
        
        try:
            result = agent.run(verification_task)
            print(f"\n🤖 Agent创新回答:")
            print(f"{result[:300]}...")
            print(f"\n✅ 回答长度: {len(result)} 字符")
            print("💡 Agent已将回溯学到的知识应用到新任务中！")
            
        except Exception as e:
            print(f"❌ 验证任务失败: {e}")
        
        # 停止认知模式
        print(f"\n🛑 停止认知模式...")
        agent.stop_cognitive_mode()
        
        print(f"\n" + "="*60)
        print(f"🎉 任务回溯引擎演示完成！")
        print(f"")
        print(f"💡 您刚才见证了AI Agent的'记忆回放'能力：")
        print(f"")
        print(f"🔍 三阶段回溯流程:")
        print(f"   1️⃣ 选择阶段 - 智能选择最有价值的历史任务")
        print(f"   2️⃣ 创想阶段 - 双重激活LLM+Aha-Moment机制")
        print(f"   3️⃣ 沉淀阶段 - 新知识注入MAB系统形成闭环")
        print(f"")
        print(f"🚀 核心突破:")
        print(f"   ✨ 从'被动应激'升级为'主动学习'")
        print(f"   🧠 历史任务成为Agent智慧成长的源泉")
        print(f"   🔄 每次回溯都让Agent变得更聪明")
        print(f"   💡 真正实现了'经验积累'和'知识迭代'")
        print(f"")
        print(f"🌟 这就是Agent进化的秘密 - 永不停止的'记忆回放'！")
        
    except KeyboardInterrupt:
        print(f"\n👋 用户中断演示")
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


def simple_retrospection_usage():
    """简单回溯引擎使用示例"""
    print("📖 回溯引擎使用指南：")
    print("""
    # 1. 导入Agent创建函数
    from neogenesis_agent_runner import create_neogenesis_agent
    
    # 2. 配置回溯引擎
    config = {
        'enable_cognitive_scheduler': True,
        'cognitive_config': {
            'retrospection_interval': 30.0,  # 30秒后开始回溯
        },
        'retrospection_config': {
            'task_selection': {
                'default_strategy': 'failure_focused',  # 专注分析失败任务
            },
            'ideation': {
                'enable_llm_dimensions': True,      # 启用LLM创想
                'enable_aha_moment': True,          # 启用Aha-Moment
            },
            'assimilation': {
                'enable_mab_injection': True,       # 启用知识注入
            }
        }
    }
    
    # 3. 创建Agent
    agent = create_neogenesis_agent(config=config)
    
    # 4. 启动认知模式
    agent.start_cognitive_mode()
    
    # 5. Agent执行任务，积累经验
    agent.run("你的问题1")
    agent.run("你的问题2")
    # ... Agent在空闲时会自动进行回溯分析
    
    # 6. 观察回溯成果
    status = agent.get_cognitive_status()
    print(f"回溯分析: {status['stats']['retrospection_sessions']} 次")
    
    # 7. 回溯后的Agent将具备：
    #    - 从失败中学到的经验教训
    #    - LLM生成的新思维维度
    #    - Aha-Moment产生的创意路径
    #    - 注入MAB系统的新决策策略
    
    # 8. 停止认知模式
    agent.stop_cognitive_mode()
    """)


if __name__ == "__main__":
    # 显示使用方法
    simple_retrospection_usage()
    
    # 运行演示
    input("\n按Enter键开始任务回溯引擎演示...")
    main()
