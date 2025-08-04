#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统关闭管理器 - System Shutdown Manager
管理系统的优雅关闭和资源释放
"""

import logging
import atexit
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SystemShutdownManager:
    """系统关闭管理器"""
    
    def __init__(self):
        self.shutdown_callbacks = []
        self.is_shutdown = False
        
        # 注册程序退出时的清理函数
        atexit.register(self.emergency_shutdown)
    
    def register_shutdown_callback(self, callback, name: str = "unknown"):
        """注册关闭回调函数"""
        # 检查是否已经注册了同名回调，避免重复注册
        for existing in self.shutdown_callbacks:
            if existing['name'] == name:
                logger.debug(f"⚠️ 关闭回调已存在，跳过注册: {name}")
                return
        
        self.shutdown_callbacks.append({
            'callback': callback,
            'name': name
        })
        logger.debug(f"📝 已注册关闭回调: {name}")
    
    def clear_shutdown_callbacks(self):
        """清理所有关闭回调"""
        logger.debug(f"🧹 清理 {len(self.shutdown_callbacks)} 个关闭回调")
        self.shutdown_callbacks.clear()
        self.is_shutdown = False
    
    def shutdown_system(self, controller):
        """优雅关闭系统"""
        if self.is_shutdown:
            logger.warning("⚠️ 系统已经关闭")
            return
        
        logger.info("🔚 开始关闭Neogenesis系统...")
        
        try:
            # 关闭性能优化器
            if hasattr(controller, 'performance_optimizer') and controller.performance_optimizer:
                logger.info("🚀 关闭性能优化器...")
                controller.performance_optimizer.shutdown()
                controller.performance_optimizer = None
            
            # 清理缓存
            if hasattr(controller, 'prior_reasoner') and hasattr(controller.prior_reasoner, 'assessment_cache'):
                controller.prior_reasoner.assessment_cache.clear()
                logger.debug("🧹 已清理先验推理器缓存")
            
            if hasattr(controller, 'path_generator') and hasattr(controller.path_generator, 'path_generation_cache'):
                controller.path_generator.path_generation_cache.clear()
                logger.debug("🧹 已清理路径生成器缓存")
            
            # 执行注册的关闭回调
            for callback_info in self.shutdown_callbacks:
                try:
                    callback_info['callback']()
                    logger.debug(f"✅ 已执行关闭回调: {callback_info['name']}")
                except Exception as e:
                    logger.error(f"❌ 关闭回调执行失败 ({callback_info['name']}): {e}")
            
            # 记录最终统计
            if hasattr(controller, 'performance_stats'):
                self._log_final_statistics(controller)
            
            self.is_shutdown = True
            logger.info("✅ Neogenesis系统已成功关闭")
            
        except Exception as e:
            logger.error(f"❌ 系统关闭过程中发生错误: {e}")
            self.is_shutdown = True
    
    def _log_final_statistics(self, controller):
        """记录最终统计信息"""
        try:
            stats = controller.performance_stats
            logger.info(f"📊 系统运行统计:")
            logger.info(f"   - 总决策轮数: {getattr(controller, 'total_rounds', 0)}")
            logger.info(f"   - 总决策数: {stats.get('total_decisions', 0)}")
            logger.info(f"   - 成功决策数: {stats.get('successful_decisions', 0)}")
            
            if stats.get('total_decisions', 0) > 0:
                success_rate = stats['successful_decisions'] / stats['total_decisions']
                logger.info(f"   - 成功率: {success_rate:.1%}")
                logger.info(f"   - 平均决策时间: {stats.get('avg_decision_time', 0):.3f}秒")
            
            # 性能优化统计
            if hasattr(controller, 'performance_optimizer') and controller.performance_optimizer:
                opt_report = controller.performance_optimizer.get_performance_report()
                cache_stats = opt_report.get('cache_stats', {})
                if cache_stats.get('total_requests', 0) > 0:
                    logger.info(f"   - 缓存命中率: {cache_stats.get('hit_rate', 0):.1%}")
                    logger.info(f"   - 缓存请求数: {cache_stats.get('total_requests', 0)}")
                
        except Exception as e:
            logger.error(f"❌ 记录最终统计失败: {e}")
    
    def emergency_shutdown(self):
        """紧急关闭（程序退出时调用）"""
        if not self.is_shutdown:
            logger.warning("⚠️ 执行紧急关闭程序")
            # 执行基本清理
            for callback_info in self.shutdown_callbacks:
                try:
                    callback_info['callback']()
                except:
                    pass  # 忽略紧急关闭中的错误
            
            self.is_shutdown = True


# 全局关闭管理器实例
shutdown_manager = SystemShutdownManager()


def register_for_shutdown(callback, name: str = "unknown"):
    """便捷函数：注册关闭回调"""
    shutdown_manager.register_shutdown_callback(callback, name)


def shutdown_neogenesis_system(controller):
    """便捷函数：关闭系统"""
    shutdown_manager.shutdown_system(controller)


def clear_shutdown_callbacks():
    """便捷函数：清理关闭回调"""
    shutdown_manager.clear_shutdown_callbacks()