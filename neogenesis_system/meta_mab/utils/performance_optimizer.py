#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能优化工具类 - Performance Optimization Utils
实现并行化、缓存、自适应算法等性能优化功能
"""

import asyncio
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    data: Any
    timestamp: float
    access_count: int = 0
    ttl: float = 3600  # 默认1小时过期
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl
    
    def access(self):
        """记录访问"""
        self.access_count += 1


class IntelligentCache:
    """智能缓存系统"""
    
    def __init__(self, default_ttl: float = 3600, max_size: int = 1000):
        """
        初始化智能缓存
        
        Args:
            default_ttl: 默认过期时间(秒)
            max_size: 最大缓存大小
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        logger.info(f"🧠 智能缓存系统初始化 - TTL:{default_ttl}s, 最大容量:{max_size}")
    
    def _generate_cache_key(self, query: str, context: Optional[Dict] = None) -> str:
        """生成缓存键"""
        content = f"{query}_{str(context) if context else ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, context: Optional[Dict] = None) -> Optional[Any]:
        """获取缓存数据"""
        cache_key = self._generate_cache_key(query, context)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            if entry.is_expired():
                # 缓存过期，删除
                del self.cache[cache_key]
                self.stats['misses'] += 1
                logger.debug(f"📋 缓存过期: {cache_key[:16]}...")
                return None
            
            # 缓存命中
            entry.access()
            self.stats['hits'] += 1
            logger.debug(f"✅ 缓存命中: {cache_key[:16]}... (访问次数: {entry.access_count})")
            return entry.data
        
        # 缓存未命中
        self.stats['misses'] += 1
        logger.debug(f"❌ 缓存未命中: {cache_key[:16]}...")
        return None
    
    def set(self, query: str, data: Any, context: Optional[Dict] = None, ttl: Optional[float] = None):
        """设置缓存数据"""
        cache_key = self._generate_cache_key(query, context)
        
        # 检查是否需要清理缓存
        if len(self.cache) >= self.max_size:
            self._evict_least_used()
        
        # 创建缓存条目
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )
        
        self.cache[cache_key] = entry
        logger.debug(f"💾 缓存已设置: {cache_key[:16]}... (TTL: {entry.ttl}s)")
    
    def _evict_least_used(self):
        """清理最少使用的缓存条目"""
        if not self.cache:
            return
        
        # 找到访问次数最少的条目
        least_used_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].access_count)
        
        del self.cache[least_used_key]
        self.stats['evictions'] += 1
        logger.debug(f"🗑️ 缓存清理: {least_used_key[:16]}...")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / max(total_requests, 1)
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("🧹 缓存已清空")


class ParallelPathVerifier:
    """并行路径验证器"""
    
    def __init__(self, max_workers: int = 3):
        """
        初始化并行验证器
        
        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"⚡ 并行路径验证器初始化 - 最大并发数: {max_workers}")
    
    def verify_paths_parallel(self, verification_tasks: List[Tuple[Any, Callable]]) -> List[Any]:
        """
        并行验证多条路径
        
        Args:
            verification_tasks: 验证任务列表，每个任务是(路径, 验证函数)的元组
            
        Returns:
            验证结果列表
        """
        if not verification_tasks:
            return []
        
        logger.info(f"🔄 开始并行验证 {len(verification_tasks)} 条路径...")
        start_time = time.time()
        
        # 提交任务到线程池
        future_to_path = {}
        for path, verify_func in verification_tasks:
            future = self.executor.submit(verify_func, path)
            future_to_path[future] = path
        
        # 收集结果
        results = []
        completed_count = 0
        
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                logger.debug(f"✅ 路径验证完成 ({completed_count}/{len(verification_tasks)}): {path}")
                
            except Exception as e:
                logger.error(f"❌ 路径验证失败: {path} - {e}")
                # 添加失败结果，保持结果数量一致
                results.append(None)
        
        duration = time.time() - start_time
        logger.info(f"🎯 并行验证完成 - 耗时: {duration:.2f}s, 成功: {len([r for r in results if r is not None])}/{len(verification_tasks)}")
        
        return results
    
    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)
        logger.info("🔚 并行验证器已关闭")


class AdaptivePathSelector:
    """自适应路径选择器"""
    
    def __init__(self, performance_config: Dict[str, Any]):
        """
        初始化自适应路径选择器
        
        Args:
            performance_config: 性能配置
        """
        self.config = performance_config
        self.path_performance_history = defaultdict(list)
        
        logger.info("🎯 自适应路径选择器初始化")
    
    def get_optimal_path_count(self, confidence: float, complexity: float) -> int:
        """
        基于置信度和复杂度确定最优路径数量
        
        Args:
            confidence: 置信度 (0.0-1.0)
            complexity: 复杂度 (0.0-1.0)
            
        Returns:
            最优路径数量
        """
        if not self.config.get("enable_adaptive_path_count", False):
            return self.config.get("max_verification_paths", 6)
        
        # 基于置信度的映射
        confidence_mapping = self.config.get("confidence_path_mapping", {})
        
        # 找到合适的路径数量
        path_count = self.config.get("max_verification_paths", 6)
        for conf_threshold in sorted(confidence_mapping.keys(), reverse=True):
            if confidence >= conf_threshold:
                path_count = confidence_mapping[conf_threshold]
                break
        
        # 复杂度调整
        if complexity > 0.8:
            path_count = min(path_count + 1, self.config.get("max_verification_paths", 6))
        elif complexity < 0.3:
            path_count = max(path_count - 1, self.config.get("min_verification_paths", 2))
        
        logger.info(f"🎯 自适应路径选择: 置信度={confidence:.2f}, 复杂度={complexity:.2f} -> {path_count}条路径")
        
        return path_count
    
    def should_early_terminate(self, verified_results: List[Any], min_consistent: int = 3) -> bool:
        """
        判断是否应该早期终止验证
        
        Args:
            verified_results: 已验证的结果列表
            min_consistent: 最小一致性结果数
            
        Returns:
            是否应该早期终止
        """
        if not self.config.get("enable_early_termination", False):
            return False
        
        if len(verified_results) < min_consistent:
            return False
        
        # 检查结果一致性
        consistency_threshold = self.config.get("path_consistency_threshold", 0.8)
        
        # 简单一致性检查：计算成功/失败的比例
        success_count = sum(1 for result in verified_results 
                          if result and getattr(result, 'success', False))
        
        success_rate = success_count / len(verified_results)
        
        # 如果一致性足够高，可以早期终止
        if success_rate >= consistency_threshold or success_rate <= (1 - consistency_threshold):
            logger.info(f"🔄 早期终止条件满足: 成功率={success_rate:.2f}, 已验证={len(verified_results)}条路径")
            return True
        
        return False
    
    def record_path_performance(self, path_id: str, performance_score: float):
        """记录路径性能"""
        self.path_performance_history[path_id].append(performance_score)
        
        # 限制历史长度
        if len(self.path_performance_history[path_id]) > 50:
            self.path_performance_history[path_id] = self.path_performance_history[path_id][-25:]


class PerformanceOptimizer:
    """性能优化器主类"""
    
    def __init__(self, performance_config: Dict[str, Any]):
        """
        初始化性能优化器
        
        Args:
            performance_config: 性能配置
        """
        self.config = performance_config
        
        # 初始化组件
        self.cache = IntelligentCache(
            default_ttl=performance_config.get("cache_ttl_seconds", 3600),
            max_size=performance_config.get("cache_max_size", 1000)
        )
        
        self.parallel_verifier = ParallelPathVerifier(
            max_workers=performance_config.get("max_concurrent_verifications", 3)
        )
        
        self.adaptive_selector = AdaptivePathSelector(performance_config)
        
        # 性能统计
        self.performance_stats = {
            'optimization_enabled_time': time.time(),
            'total_optimized_decisions': 0,
            'time_saved_seconds': 0,
            'cache_hits': 0,
            'parallel_speedup_factor': 0
        }
        
        logger.info("🚀 性能优化器初始化完成")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        cache_stats = self.cache.get_stats()
        
        return {
            'optimization_stats': self.performance_stats,
            'cache_stats': cache_stats,
            'config': self.config,
            'uptime_hours': (time.time() - self.performance_stats['optimization_enabled_time']) / 3600
        }
    
    def shutdown(self):
        """关闭优化器"""
        self.parallel_verifier.shutdown()
        logger.info("🔚 性能优化器已关闭")