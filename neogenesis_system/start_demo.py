#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎭 AI思维可视化演示 - 总启动器
Master Launcher for AI Thinking Visualization Demo
"""

import os
import sys
import subprocess
from pathlib import Path

def print_welcome():
    """显示欢迎界面"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🎭 AI思维可视化演示 - 选择体验模式                    ║
║                                                              ║
║           观察AI如何像专家一样思考和决策                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🌟 **三种体验模式**:

1. 🚀 **快速体验模式** (推荐新手)
   • 无需任何配置，开箱即用
   • 完整演示三大核心场景
   • 纯模拟演示，快速了解系统能力
   • 预计用时：10-15分钟

2. 🔧 **完整系统模式** (推荐技术用户)
   • 连接真实AI系统
   • 体验完整的智能分析能力
   • 需要API密钥（可选）
   • 预计用时：15-25分钟

3. 📚 **查看文档** 
   • 详细了解系统架构
   • 学习技术实现细节
   • 获取使用指南

🎯 **演示亮点**:
• 观察AI的"内心独白"和思考过程
• 见证五阶段智能决策流程
• 体验Aha-Moment创新突破
• 发现黄金模板智慧沉淀
""")

def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        print(f"   当前版本: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # 检查必要文件
    required_files = [
        "quick_demo.py",
        "interactive_demo.py", 
        "run_demo.py"
    ]
    
    for file_name in required_files:
        if not Path(file_name).exists():
            print(f"❌ 缺少文件: {file_name}")
            return False
    
    print("✅ 演示文件完整")
    return True

def run_quick_demo():
    """运行快速演示"""
    print("\n🚀 启动快速体验模式...")
    print("💡 这是一个完全模拟的演示，无需任何配置")
    
    try:
        result = subprocess.run([sys.executable, "quick_demo.py"], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 快速演示运行失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 演示已终止")
        return True

def run_full_demo():
    """运行完整演示"""
    print("\n🔧 启动完整系统模式...")
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        print("✅ 检测到API密钥，将体验完整功能")
    else:
        print("⚠️ 未检测到API密钥")
        print("💡 您仍然可以体验演示模式，或设置DEEPSEEK_API_KEY获得完整体验")
        
        choice = input("\n继续运行吗？(y/n): ")
        if choice.lower() != 'y':
            return False
    
    try:
        result = subprocess.run([sys.executable, "interactive_demo.py"], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 完整演示运行失败: {e}")
        print("🔄 尝试运行快速演示...")
        return run_quick_demo()
    except KeyboardInterrupt:
        print("\n👋 演示已终止")
        return True

def show_documentation():
    """显示文档"""
    print("\n📚 AI思维可视化系统文档")
    print("="*50)
    
    readme_file = Path("DEMO_README.md")
    if readme_file.exists():
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示文档前几段
            lines = content.split('\n')
            for i, line in enumerate(lines[:50]):  # 显示前50行
                print(line)
                if i > 0 and i % 20 == 0:
                    choice = input("\n继续阅读？(y/n): ")
                    if choice.lower() != 'y':
                        break
            
            print(f"\n📖 完整文档请查看: {readme_file}")
            
        except Exception as e:
            print(f"❌ 读取文档失败: {e}")
    else:
        print("❌ 未找到文档文件")
    
    input("\n按 Enter 返回主菜单...")

def main():
    """主函数"""
    if not check_system_requirements():
        print("\n❌ 系统环境检查失败，无法运行演示")
        return False
    
    while True:
        print_welcome()
        
        try:
            choice = input("\n请选择体验模式 (1/2/3) 或输入 'q' 退出: ").strip()
            
            if choice == '1':
                success = run_quick_demo()
                if success:
                    print("\n🎉 快速演示完成！")
                
            elif choice == '2':
                success = run_full_demo()
                if success:
                    print("\n🎉 完整演示完成！")
                
            elif choice == '3':
                show_documentation()
                continue
                
            elif choice.lower() == 'q':
                print("\n👋 感谢使用AI思维可视化演示！")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
                continue
            
            # 询问是否继续
            if choice in ['1', '2']:
                again = input("\n🔄 是否尝试其他模式？(y/n): ")
                if again.lower() != 'y':
                    print("\n👋 感谢体验AI思维可视化演示！")
                    break
        
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 运行出错: {e}")
            continue
    
    return True

if __name__ == "__main__":
    main()