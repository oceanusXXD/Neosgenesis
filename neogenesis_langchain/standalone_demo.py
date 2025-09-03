#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis LangChain - 独立演示程序
不依赖外部neogenesis_system的基础功能演示
"""

def basic_storage_demo():
    """基础存储功能演示"""
    print("🗃️ 基础存储功能演示")
    print("=" * 40)
    
    try:
        from .storage import StorageBackend, CompressionType
        
        print("✅ 可用的存储后端:")
        for backend in StorageBackend:
            print(f"   - {backend.value}")
            
        print("\n✅ 可用的压缩类型:")
        for comp in CompressionType:
            print(f"   - {comp.value}")
            
    except Exception as e:
        print(f"❌ 存储演示失败: {e}")

def basic_state_demo():
    """基础状态管理演示"""
    print("\n🧠 基础状态管理演示")
    print("=" * 40)
    
    try:
        from .state import DecisionStage
        
        print("✅ 可用的决策阶段:")
        for stage in DecisionStage:
            print(f"   - {stage.value}")
            
    except Exception as e:
        print(f"❌ 状态演示失败: {e}")

def package_info_demo():
    """包信息演示"""
    print("\n📦 包信息")
    print("=" * 40)
    
    import neogenesis_langchain as nlc
    
    if hasattr(nlc, 'get_info'):
        info = nlc.get_info()
        print("✅ 包信息:")
        for key, value in info.items():
            print(f"   - {key}: {value}")
    else:
        print(f"✅ 包版本: {getattr(nlc, '__version__', 'unknown')}")
        print(f"✅ 包作者: {getattr(nlc, '__author__', 'unknown')}")

def main():
    """主演示函数"""
    print("🎭 Neogenesis LangChain 独立演示")
    print("=" * 60)
    
    demos = [
        basic_storage_demo,
        basic_state_demo, 
        package_info_demo
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"❌ 演示失败: {e}")
    
    print("\n🎉 演示完成！")

if __name__ == "__main__":
    main()
