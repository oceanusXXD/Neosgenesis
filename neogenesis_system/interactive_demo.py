#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# 元认知智能决策系统 - 交互式可视化演示
Interactive Visualization Demo for Meta-Cognitive Decision System

目标：让用户"观察"AI的思考过程，见证智能决策的每个环节
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from neogenesis_system.core.neogenesis_planner import NeogenesisPlanner
from neogenesis_system.cognitive_engine.reasoner import PriorReasoner
from neogenesis_system.cognitive_engine.path_generator import PathGenerator
from neogenesis_system.cognitive_engine.mab_converger import MABConverger
from neogenesis_system.cognitive_engine.data_structures import ReasoningPath
from neogenesis_system.shared.data_structures import Plan, Action

# 配置日志以捕获详细的思考过程
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

class AIThinkingVisualizer:
    """AI思考过程可视化器"""
    
    def __init__(self):
        self.step_count = 0
        self.thinking_log = []
        
    def print_header(self, title: str, icon: str = "🎯"):
        """打印标题头"""
        print(f"\n{'='*60}")
        print(f"{icon} {title}")
        print(f"{'='*60}")
        
    def print_step(self, step_name: str, content: str, icon: str = "🔍"):
        """打印思考步骤"""
        self.step_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{icon} 步骤 {self.step_count}: {step_name} [{timestamp}]")
        print(f"{'─'*50}")
        print(content)
        
        # 记录到思考日志
        self.thinking_log.append({
            'step': self.step_count,
            'name': step_name,
            'content': content,
            'timestamp': timestamp
        })
    
    def print_thinking_process(self, stage: str, details: Dict[str, Any]):
        """可视化思考过程"""
        if stage == "thinking_seed":
            self.visualize_thinking_seed(details)
        elif stage == "path_generation":
            self.visualize_path_generation(details)
        elif stage == "path_selection":
            self.visualize_path_selection(details)
        elif stage == "verification":
            self.visualize_verification(details)
        elif stage == "final_decision":
            self.visualize_final_decision(details)
    
    def visualize_thinking_seed(self, details: Dict[str, Any]):
        """可视化思维种子生成"""
        seed = details.get('thinking_seed', '')
        confidence = details.get('task_confidence', 0.5)
        complexity = details.get('complexity_analysis', {}).get('complexity_score', 0.5)
        
        content = f"""
🧠 **内心独白**: "让我仔细思考这个问题..."
📊 **复杂度评估**: {complexity:.2f} ({'简单' if complexity < 0.3 else '中等' if complexity < 0.7 else '复杂'})
🎯 **置信度评估**: {confidence:.2f} ({'低' if confidence < 0.4 else '中' if confidence < 0.7 else '高'})

💭 **思维种子**:
{seed[:200]}{'...' if len(seed) > 200 else ''}

🔍 **AI分析**: 基于问题的复杂度和我的经验，我需要生成多条思维路径来确保找到最优解决方案。
"""
        self.print_step("思维种子萌发", content, "🌱")
    
    def visualize_path_generation(self, details: Dict[str, Any]):
        """可视化路径生成"""
        paths = details.get('available_paths', [])
        
        content = f"""
🧠 **内心独白**: "现在我要从不同角度思考这个问题..."

📋 **生成的思维路径** ({len(paths)}条):
"""
        for i, path in enumerate(paths, 1):
            path_type = getattr(path, 'path_type', '未知类型')
            description = getattr(path, 'description', '无描述')
            content += f"""
  {i}. 🛤️ **{path_type}**
     思路: {description[:100]}{'...' if len(description) > 100 else ''}
"""
        
        content += f"""
🔍 **AI分析**: 我生成了{len(paths)}种不同的思考方式，涵盖系统分析、创新突破、实用导向等多个维度，确保不遗漏任何可能的解决方案。
"""
        self.print_step("多路径思维展开", content, "🛤️")
    
    def visualize_path_selection(self, details: Dict[str, Any]):
        """可视化路径选择"""
        chosen_path = details.get('chosen_path') or details.get('selected_path')
        mab_decision = details.get('mab_decision', {})
        algorithm = mab_decision.get('selection_algorithm', 'unknown')
        
        path_type = getattr(chosen_path, 'path_type', '未知') if chosen_path else '未知'
        
        # 检查是否使用了黄金模板
        golden_used = any(key in mab_decision for key in ['template_match', 'golden_template_used'])
        aha_triggered = mab_decision.get('detour_triggered', False) or mab_decision.get('traditional_aha_triggered', False)
        
        content = f"""
🧠 **内心独白**: "让我选择最适合的思考方式..."

🎰 **决策算法**: {algorithm}
{'🏆 **黄金模板匹配**: 发现了之前成功的模式！' if golden_used else ''}
{'💡 **Aha-Moment触发**: 常规路径遇阻，启动创新思考！' if aha_triggered else ''}

🎯 **选中路径**: {path_type}

🔍 **AI分析**: {'基于历史成功经验，我直接选择了经过验证的黄金模板。' if golden_used else '我使用多臂老虎机算法，平衡探索与利用，选择了当前最优的思考路径。'}
"""
        self.print_step("最优路径选择", content, "🎯")
    
    def visualize_verification(self, details: Dict[str, Any]):
        """可视化验证过程"""
        verification_stats = details.get('verification_stats', {})
        verified_paths = details.get('verified_paths', [])
        feasible_count = verification_stats.get('feasible_paths', 0)
        total_verified = verification_stats.get('paths_verified', 0)
        
        content = f"""
🧠 **内心独白**: "我需要验证这些想法的可行性..."

🔬 **验证结果**:
  📊 验证路径: {total_verified} 条
  ✅ 可行路径: {feasible_count} 条  
  ❌ 不可行路径: {total_verified - feasible_count} 条
  📈 可行率: {(feasible_count/max(total_verified,1)*100):.1f}%

💡 **实时学习**: 每个验证结果都在更新我的知识库，让我变得更智能！
"""
        
        if verified_paths:
            content += "\n📋 **详细验证**:\n"
            for i, vp in enumerate(verified_paths[:3], 1):
                feasibility = vp.get('feasibility_score', 0)
                is_feasible = vp.get('is_feasible', False)
                path = vp.get('path', {})
                path_type = getattr(path, 'path_type', '未知') if hasattr(path, 'path_type') else '未知'
                
                status = "✅ 可行" if is_feasible else "❌ 不可行"
                content += f"  {i}. {path_type}: {status} (置信度: {feasibility:.2f})\n"
        
        content += f"""
🔍 **AI分析**: 通过实时验证，我不仅选择了最优路径，还积累了宝贵的经验数据，这将帮助我在未来做出更好的决策。
"""
        self.print_step("智能验证与学习", content, "🔬")
    
    def visualize_final_decision(self, details: Dict[str, Any]):
        """可视化最终决策"""
        chosen_path = details.get('chosen_path') or details.get('selected_path')
        architecture_version = details.get('architecture_version', '未知')
        total_time = details.get('performance_metrics', {}).get('total_time', 0)
        
        path_type = getattr(chosen_path, 'path_type', '未知') if chosen_path else '未知'
        description = getattr(chosen_path, 'description', '无描述') if chosen_path else '无描述'
        
        content = f"""
🧠 **内心独白**: "经过深思熟虑，我已经找到了最佳方案！"

🎯 **最终决策**: {path_type}
📝 **解决方案**: {description}
🏗️ **架构版本**: {architecture_version}
⏱️ **思考耗时**: {total_time:.2f}秒

🎓 **经验积累**: 这次决策的结果将被记录下来，如果成功，可能会成为未来的"黄金模板"。

✨ **AI反思**: "通过多阶段验证和实时学习，我不仅解决了当前问题，还提升了自己的智能水平。这就是元认知的力量！"
"""
        self.print_step("智慧决策诞生", content, "✨")
    
    def pause_for_observation(self, message: str = "按 Enter 继续观察..."):
        """暂停以供观察"""
        print(f"\n🔍 {message}")
        input()


class AIExpertDemo:
    """AI专家演示系统"""
    
    def __init__(self):
        self.visualizer = AIThinkingVisualizer()
        self.planner = None
        self.demo_scenarios = [
            {
                'name': '标准元认知决策',
                'description': '观察完整的五阶段决策流程',
                'query': '如何构建一个高性能的网络爬虫系统？',
                'icon': '🎯'
            },
            {
                'name': 'Aha-Moment灵感迸发', 
                'description': '观察系统如何创造性地解决问题',
                'query': '设计一个能够自我进化的AI算法框架',
                'icon': '💡'
            },
            {
                'name': '经验成金智慧沉淀',
                'description': '观察黄金模板的形成和复用',
                'query': '优化分布式系统的性能瓶颈',
                'icon': '🏆'
            }
        ]
    
    def welcome(self):
        """欢迎界面"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        元认知智能决策系统 - AI思维可视化演示                    ║
║                                                              ║
║    欢迎来到AI的"内心世界"！                                    ║
║    您将扮演观察者的角色，亲眼见证AI如何像专家一样思考            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🌟 **演示特色**:
• 🧠 观察AI的"内心独白"和思考过程
• 🛤️ 见证多路径探索和智能选择
• 🔬 体验实时验证和经验学习
• 💡 感受"Aha-Moment"的创新突破
• 🏆 发现"黄金模板"的智慧沉淀

🎯 **三大场景**:
""")
        
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"  {i}. {scenario['icon']} {scenario['name']}")
            print(f"     {scenario['description']}")
        
        print("\n🚀 准备开始这场AI思维之旅！")
        self.visualizer.pause_for_observation("按 Enter 开始演示...")
    
    def initialize_system(self):
        """初始化系统"""
        self.visualizer.print_header("🔧 系统初始化", "⚙️")
        
        print("🔧 正在初始化AI专家系统...")
        
        # 模拟API密钥检查
        api_key = os.getenv('DEEPSEEK_API_KEY', '')
        if not api_key:
            print("⚠️ 注意: 未检测到DEEPSEEK_API_KEY，将运行演示模式")
            print("💡 提示: 设置真实API密钥可体验完整的AI分析能力")
        else:
            print("✅ DeepSeek API密钥已配置")
        
        try:
            # 创建NeogenesisPlanner所需的依赖组件
            prior_reasoner = PriorReasoner(api_key)
            
            # 为了向后兼容，创建简单的LLM客户端
            llm_client = None
            if api_key:
                try:
                    from neogenesis_system.providers.client_adapter import DeepSeekClientAdapter
                    llm_client = DeepSeekClientAdapter(api_key)
                except ImportError:
                    pass
            
            path_generator = PathGenerator(api_key, llm_client=llm_client)
            mab_converger = MABConverger()
            
            # 创建NeogenesisPlanner实例
            self.planner = NeogenesisPlanner(
                prior_reasoner=prior_reasoner,
                path_generator=path_generator,
                mab_converger=mab_converger
            )
            print("✅ Neogenesis规划器初始化完成")
            print("✅ 多臂老虎机学习系统已就绪")
            print("✅ 五阶段决策流程已激活")
            print("✅ 新架构规划器已启用")
            
            # 显示系统状态
            planner_stats = self.planner.get_stats()
            print(f"\n📊 **系统状态**:")
            print(f"   🎰 规划器组件: {', '.join(planner_stats.get('components', {}).values())}")
            print(f"   📈 历史决策: {planner_stats.get('total_rounds', 0)} 轮")
            print(f"   ⏱️ 平均耗时: {planner_stats.get('performance_stats', {}).get('avg_decision_time', 0):.2f}s")
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            print("🔄 将使用模拟模式继续演示...")
            self.planner = None
        
        self.visualizer.pause_for_observation()
    
    def run_scenario(self, scenario_index: int):
        """运行指定场景"""
        scenario = self.demo_scenarios[scenario_index]
        
        self.visualizer.print_header(
            f"场景 {scenario_index + 1}: {scenario['name']}", 
            scenario['icon']
        )
        
        print(f"📋 **场景描述**: {scenario['description']}")
        print(f"🎯 **测试问题**: {scenario['query']}")
        print(f"\n🔍 **观察要点**: 请注意AI如何分阶段思考...")
        
        self.visualizer.pause_for_observation("准备好观察AI的思考过程了吗？按 Enter 开始...")
        
        if self.planner:
            self.run_real_scenario(scenario)
        else:
            self.run_simulated_scenario(scenario)
    
    def run_real_scenario(self, scenario: Dict[str, Any]):
        """运行真实场景"""
        query = scenario['query']
        
        # 创建自定义的日志处理器来捕获思考过程
        thinking_handler = ThinkingLogHandler(self.visualizer)
        logger = logging.getLogger('cognitive_engine')
        logger.addHandler(thinking_handler)
        logger.setLevel(logging.INFO)
        
        try:
            # 调用规划系统
            print("\n🚀 AI开始思考...")
            plan_result = self.planner.create_plan(
                query=query,
                memory=None,  # 演示模式不需要memory
                context={'scenario': scenario['name'], 'confidence': 0.6}
            )
            
            # 从Plan对象的metadata中提取原始决策信息
            decision_data = plan_result.metadata.get('neogenesis_decision', {})
            
            # 可视化决策过程
            self.visualizer.visualize_thinking_seed({
                'thinking_seed': decision_data.get('thinking_seed', ''),
                'task_confidence': decision_data.get('task_confidence', 0.5),
                'complexity_analysis': decision_data.get('complexity_analysis', {})
            })
            
            self.visualizer.pause_for_observation()
            
            self.visualizer.visualize_path_generation({
                'available_paths': decision_data.get('available_paths', [])
            })
            
            self.visualizer.pause_for_observation()
            
            self.visualizer.visualize_path_selection({
                'chosen_path': decision_data.get('chosen_path'),
                'mab_decision': decision_data.get('mab_decision', {})
            })
            
            self.visualizer.pause_for_observation()
            
            if 'verification_stats' in decision_data:
                self.visualizer.visualize_verification({
                    'verification_stats': decision_data.get('verification_stats', {}),
                    'verified_paths': decision_data.get('verified_paths', [])
                })
                
                self.visualizer.pause_for_observation()
            
            self.visualizer.visualize_final_decision(decision_data)
            
            # 展示Plan结果
            print("\n🎯 **规划结果**:")
            print(f"💭 思考过程: {plan_result.thought}")
            
            if plan_result.is_direct_answer:
                print(f"💬 直接回答: {plan_result.final_answer}")
            else:
                print(f"🔧 计划行动: {len(plan_result.actions)} 个")
                for i, action in enumerate(plan_result.actions, 1):
                    print(f"   {i}. {action.tool_name}: {action.tool_input}")
            
            print("✅ 规划过程完成！")
            
        except Exception as e:
            print(f"❌ 演示过程中出现错误: {e}")
            self.run_simulated_scenario(scenario)
        finally:
            logger.removeHandler(thinking_handler)
    
    def run_simulated_scenario(self, scenario: Dict[str, Any]):
        """运行模拟场景"""
        print("\n🎭 进入演示模式...")
        
        # 模拟思维种子生成
        self.visualizer.visualize_thinking_seed({
            'thinking_seed': f"这是一个关于{scenario['query']}的复杂技术问题。需要考虑系统架构、性能优化、可扩展性等多个方面...",
            'task_confidence': 0.75,
            'complexity_analysis': {'complexity_score': 0.8}
        })
        
        self.visualizer.pause_for_observation()
        
        # 模拟路径生成
        mock_paths = [
            type('MockPath', (), {
                'path_type': '系统分析型',
                'description': '从系统架构角度分析问题，考虑组件设计、数据流、接口规范等技术细节'
            })(),
            type('MockPath', (), {
                'path_type': '创新突破型', 
                'description': '跳出传统思路，探索新兴技术和创新方法来解决问题'
            })(),
            type('MockPath', (), {
                'path_type': '实用务实型',
                'description': '注重实际可行性，优先选择成熟稳定的技术方案'
            })()
        ]
        
        self.visualizer.visualize_path_generation({
            'available_paths': mock_paths
        })
        
        self.visualizer.pause_for_observation()
        
        # 模拟路径选择
        chosen_path = mock_paths[0]  # 选择系统分析型
        
        self.visualizer.visualize_path_selection({
            'chosen_path': chosen_path,
            'mab_decision': {
                'selection_algorithm': 'thompson_sampling',
                'template_match': scenario['name'] == '经验成金智慧沉淀'
            }
        })
        
        self.visualizer.pause_for_observation()
        
        # 模拟验证过程
        if scenario['name'] == 'Aha-Moment灵感迸发':
            # 模拟验证失败，触发Aha-Moment
            self.visualizer.visualize_verification({
                'verification_stats': {
                    'paths_verified': 3,
                    'feasible_paths': 0
                },
                'verified_paths': [
                    {'path': mock_paths[0], 'feasibility_score': 0.2, 'is_feasible': False},
                    {'path': mock_paths[1], 'feasibility_score': 0.25, 'is_feasible': False},
                    {'path': mock_paths[2], 'feasibility_score': 0.15, 'is_feasible': False}
                ]
            })
            
            self.visualizer.pause_for_observation()
            
            # 触发Aha-Moment
            print("\n💡 **Aha-Moment触发！**")
            print("🧠 AI内心独白: '常规方法都行不通，我需要突破性思考...'")
            print("🌟 启动创造性绕道思考模式...")
            
            # 选择创新路径
            chosen_path = mock_paths[1]  # 切换到创新突破型
            
        else:
            self.visualizer.visualize_verification({
                'verification_stats': {
                    'paths_verified': 3, 
                    'feasible_paths': 2
                },
                'verified_paths': [
                    {'path': mock_paths[0], 'feasibility_score': 0.85, 'is_feasible': True},
                    {'path': mock_paths[1], 'feasibility_score': 0.65, 'is_feasible': True},
                    {'path': mock_paths[2], 'feasibility_score': 0.25, 'is_feasible': False}
                ]
            })
            
            self.visualizer.pause_for_observation()
        
        # 最终决策
        self.visualizer.visualize_final_decision({
            'chosen_path': chosen_path,
            'architecture_version': '5-stage-verification',
            'performance_metrics': {'total_time': 1.8}
        })
    
    def show_learning_summary(self):
        """显示学习总结"""
        self.visualizer.print_header("🎓 AI学习与成长总结", "📚")
        
        if self.planner:
            planner_stats = self.planner.get_stats()
            performance_stats = planner_stats.get('performance_stats', {})
            
            print("📊 **学习成果统计**:")
            print(f"   🎯 总决策次数: {performance_stats.get('total_decisions', 0)} 次")
            print(f"   ⏱️ 平均决策时间: {performance_stats.get('avg_decision_time', 0):.2f}s")
            print(f"   📈 历史轮次: {planner_stats.get('total_rounds', 0)} 轮")
            
            # 组件性能统计
            component_perf = performance_stats.get('component_performance', {})
            for comp_name, comp_stats in component_perf.items():
                calls = comp_stats.get('calls', 0)
                avg_time = comp_stats.get('avg_time', 0)
                print(f"   🔧 {comp_name}: {calls} 次调用, 平均耗时 {avg_time:.3f}s")
        
        print(f"""
✨ **AI的自我反思**:
"通过这次演示，我展示了自己的核心能力：

🧠 **元认知思维**: 我不仅会思考问题，更会思考如何思考
🛤️ **多路径探索**: 我从多个角度审视问题，确保不遗漏最优解
🔬 **实时验证**: 我在思考阶段就验证想法，避免错误决策
💡 **创新突破**: 当常规方法失效时，我能跳出框架寻找突破
🏆 **经验沉淀**: 我将成功模式固化为模板，实现智慧复用

这就是真正的人工智能 - 不仅能解决问题，更能持续学习和成长！"

🌟 **系统优势总结**:
• 五阶段验证流程确保决策质量
• 多臂老虎机算法实现最优探索
• Aha-Moment机制突破思维局限  
• 黄金模板系统积累智慧经验
• 实时学习能力持续自我进化
""")
    
    def run_complete_demo(self):
        """运行完整演示"""
        self.welcome()
        self.initialize_system()
        
        for i in range(len(self.demo_scenarios)):
            self.run_scenario(i)
            
            if i < len(self.demo_scenarios) - 1:
                print(f"\n{'🎬'*20}")
                self.visualizer.pause_for_observation(f"场景 {i+1} 完成！按 Enter 继续下一个场景...")
        
        self.show_learning_summary()
        
        print(f"\n{'🎉'*20}")
        print("🎭 AI思维可视化演示圆满结束！")
        print("感谢您观察AI的思考过程，希望您感受到了智能的魅力！")


class ThinkingLogHandler(logging.Handler):
    """思考过程日志处理器"""
    
    def __init__(self, visualizer: AIThinkingVisualizer):
        super().__init__()
        self.visualizer = visualizer
    
    def emit(self, record):
        """处理日志记录"""
        if hasattr(record, 'stage'):
            self.visualizer.print_thinking_process(record.stage, record.details)


def main():
    """主函数"""
    try:
        demo = AIExpertDemo()
        demo.run_complete_demo()
    except KeyboardInterrupt:
        print("\n\n👋 感谢观看AI思维演示！")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("🔧 请检查系统配置或联系开发者")


if __name__ == "__main__":
    main()