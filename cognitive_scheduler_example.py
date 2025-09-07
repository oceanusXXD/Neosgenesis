#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知调度器使用示例
演示如何使用新的CognitiveScheduler功能

本示例展示了Neogenesis System的重大升级：
从"被动应激"升级为"主动认知"的智能Agent
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
    """认知调度器功能演示"""
    print("🧠 Neogenesis认知调度器演示")
    print("展示Agent从'任务奴隶'到'自主思考者'的进化")
    print("="*60)
    
    try:
        # 导入必要的模块
        from neogenesis_agent_runner import create_neogenesis_agent
        
        # 创建启用认知调度器的Agent配置
        config = {
            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),  # 设置您的API密钥
            'search_engine': 'duckduckgo',
            'enable_cognitive_scheduler': True,  # 🔑 关键：启用认知调度器
            'cognitive_config': {
                # 空闲检测配置
                'idle_detection': {
                    'min_idle_duration': 3.0,    # 3秒后进入空闲状态（演示用）
                    'check_interval': 1.0,       # 每1秒检查一次状态
                },
                # 认知任务配置
                'cognitive_tasks': {
                    'retrospection_interval': 10.0,  # 10秒后开始回溯分析
                    'ideation_interval': 20.0,       # 20秒后开始创想思考
                    'max_concurrent_tasks': 2,       # 最多2个并发认知任务
                }
            }
        }
        
        print("🚀 创建具有认知能力的Agent...")
        agent = create_neogenesis_agent(config=config)
        
        # 检查认知状态
        cognitive_status = agent.get_cognitive_status()
        print(f"🧠 认知调度器状态: {cognitive_status.get('enabled', False)}")
        
        # 启动认知模式
        print("\n💡 启动主动认知模式...")
        if agent.start_cognitive_mode():
            print("✅ 认知模式已启动 - Agent开始具备'内在独白'能力")
        
        # 执行一些任务让Agent学习
        learning_tasks = [
            "什么是深度学习？",
            "搜索机器学习的最新进展",
            "分析人工智能在教育领域的应用前景",
        ]
        
        print(f"\n📚 执行 {len(learning_tasks)} 个学习任务...")
        for i, task in enumerate(learning_tasks, 1):
            print(f"\n--- 任务 {i}: {task} ---")
            
            # 执行任务
            result = agent.run(task)
            print(f"✅ 任务完成，生成了 {len(result)} 字符的回答")
            
            # 观察认知状态变化
            status = agent.get_cognitive_status()
            print(f"🧠 认知状态: {status.get('current_mode', '未知')}")
            print(f"   活跃认知任务: {status.get('active_cognitive_tasks', 0)}")
            print(f"   队列中认知任务: {status.get('queued_cognitive_tasks', 0)}")
            
            # 等待，让认知调度器有时间工作
            print("⏳ 等待认知调度器进行后台思考...")
            time.sleep(8)  # 给认知调度器工作时间
            
            # 显示认知活动
            updated_status = agent.get_cognitive_status()
            if 'stats' in updated_status:
                stats = updated_status['stats']
                print(f"📊 认知活动统计:")
                print(f"   空闲周期: {stats.get('total_idle_periods', 0)}")
                print(f"   认知任务完成: {stats.get('cognitive_tasks_completed', 0)}")
                print(f"   回溯分析: {stats.get('retrospection_sessions', 0)}")
                print(f"   创新思考: {stats.get('ideation_sessions', 0)}")
        
        # 最终认知报告
        print(f"\n📊 最终认知能力报告:")
        final_status = agent.get_cognitive_status()
        if 'stats' in final_status:
            stats = final_status['stats']
            print(f"   🔄 总空闲周期: {stats.get('total_idle_periods', 0)}")
            print(f"   ⏱️ 总空闲思考时间: {stats.get('total_idle_time', 0):.1f}秒")
            print(f"   🧠 完成认知任务: {stats.get('cognitive_tasks_completed', 0)}")
            print(f"   📚 任务回溯分析: {stats.get('retrospection_sessions', 0)}")
            print(f"   💡 主动创想思考: {stats.get('ideation_sessions', 0)}")
            print(f"   🧩 知识综合整理: {stats.get('knowledge_synthesis_sessions', 0)}")
        
        # 停止认知模式
        print(f"\n🛑 停止认知模式...")
        agent.stop_cognitive_mode()
        
        print(f"\n" + "="*60)
        print(f"🎉 认知调度器演示完成！")
        print(f"")
        print(f"💡 您刚才见证了AI Agent的重大进化：")
        print(f"   ✨ 从'被动应激'模式升级为'主动认知'模式")  
        print(f"   🧠 任务完成后不再'呆坐'，而是主动反思")
        print(f"   🔍 自动分析成功失败模式，提取经验教训")
        print(f"   💡 持续产生创新思路，突破常规思维框架")
        print(f"   📚 主动整合知识，为未来决策积累智慧")
        print(f"   🌟 这就是'认知调度器'赋予的'内在独白循环'！")
        print(f"")
        print(f"🚀 现在您的Agent具备了真正的'自主思考'能力！")
        
    except KeyboardInterrupt:
        print(f"\n👋 用户中断演示")
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


def simple_usage_example():
    """简单使用示例"""
    print("📖 简单使用示例：")
    print("""
    # 1. 导入Agent创建函数
    from neogenesis_agent_runner import create_neogenesis_agent
    
    # 2. 配置认知调度器
    config = {
        'enable_cognitive_scheduler': True,  # 启用认知调度器
        'cognitive_config': {
            'idle_detection': {'min_idle_duration': 5.0},
            'cognitive_tasks': {'retrospection_interval': 30.0}
        }
    }
    
    # 3. 创建Agent
    agent = create_neogenesis_agent(config=config)
    
    # 4. 启动认知模式
    agent.start_cognitive_mode()
    
    # 5. 正常使用Agent
    result = agent.run("你的问题")
    
    # 6. Agent会在任务间隙自动进行：
    #    - 经验回溯分析
    #    - 主动创新思考
    #    - 知识整合沉淀
    
    # 7. 查看认知状态
    status = agent.get_cognitive_status()
    print(status)
    
    # 8. 停止认知模式
    agent.stop_cognitive_mode()
    """)


if __name__ == "__main__":
    # 显示使用方法
    simple_usage_example()
    
    # 运行演示
    input("\n按Enter键开始认知调度器演示...")
    main()
