#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 一键启动AI思维可视化演示
Quick Start Script for AI Thinking Visualization Demo
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    required_packages = [
        'numpy', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("📦 正在安装...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} 安装成功")
            except subprocess.CalledProcessError:
                print(f"❌ {package} 安装失败")
                return False
    
    return True

def setup_environment():
    """设置环境"""
    print("\n🔧 设置演示环境...")
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("⚠️ 未检测到 DEEPSEEK_API_KEY 环境变量")
        print("💡 您可以:")
        print("   1. 设置环境变量: export DEEPSEEK_API_KEY='your-key'")
        print("   2. 直接运行演示模式（功能受限）")
        
        choice = input("\n🤔 是否继续演示模式？ (y/n): ")
        if choice.lower() != 'y':
            return False
    else:
        print("✅ DEEPSEEK_API_KEY 已配置")
    
    # 创建必要的目录
    demo_dir = Path(__file__).parent
    logs_dir = demo_dir / "demo_logs"
    logs_dir.mkdir(exist_ok=True)
    
    print("✅ 环境设置完成")
    return True

def run_demo():
    """运行演示"""
    print("\n" + "="*60)
    print("🎭 启动AI思维可视化演示")
    print("="*60)
    
    demo_script = Path(__file__).parent / "interactive_demo.py"
    
    if not demo_script.exists():
        print("❌ 找不到演示脚本 interactive_demo.py")
        return False
    
    try:
        # 运行演示
        subprocess.run([sys.executable, str(demo_script)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 演示运行失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 演示已终止")
        return True

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎭 AI思维可视化演示 - 启动器                                ║
║                                                              ║
║    准备观察AI如何像专家一样思考...                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    print(f"✅ Python {sys.version}")
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败")
        return False
    
    # 设置环境
    if not setup_environment():
        print("❌ 环境设置失败")
        return False
    
    # 运行演示
    success = run_demo()
    
    if success:
        print("\n🎉 演示完成！感谢观看AI的思考过程！")
    else:
        print("\n😔 演示未能正常完成")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
    except Exception as e:
        print(f"\n❌ 启动器错误: {e}")