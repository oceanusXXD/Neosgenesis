#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - Distributed State Management
分布式状态管理：企业级状态同步、事务管理和一致性保障
"""

import asyncio
import json
import logging
import time
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future
import hashlib

from ..storage.persistent_storage import PersistentStorageEngine, StorageConfig, StorageBackend

logger = logging.getLogger(__name__)

# =============================================================================
# 分布式状态配置和枚举
# =============================================================================

class ConsistencyLevel(Enum):
    """一致性级别"""
    EVENTUAL = "eventual"       # 最终一致性
    STRONG = "strong"          # 强一致性
    CAUSAL = "causal"          # 因果一致性
    SESSION = "session"        # 会话一致性

class ConflictResolution(Enum):
    """冲突解决策略"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    MANUAL = "manual"
    TIMESTAMP_BASED = "timestamp_based"

class LockType(Enum):
    """锁类型"""
    READ = "read"
    WRITE = "write"
    EXCLUSIVE = "exclusive"

@dataclass
class StateVersion:
    """状态版本"""
    version: int
    timestamp: float
    node_id: str
    checksum: str
    operation: str = ""

@dataclass
class DistributedLock:
    """分布式锁"""
    lock_id: str
    key: str
    lock_type: LockType
    owner_id: str
    acquired_at: float
    expires_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class StateTransaction:
    """状态事务"""
    transaction_id: str
    operations: List[Dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, committed, aborted
    timeout: float = 30.0
    isolation_level: str = "read_committed"

@dataclass
class StateSnapshot:
    """状态快照"""
    snapshot_id: str
    timestamp: float
    state_data: Dict[str, Any]
    version: StateVersion
    metadata: Dict[str, Any] = field(default_factory=dict)

# =============================================================================
# 分布式锁管理器
# =============================================================================

class DistributedLockManager:
    """分布式锁管理器"""
    
    def __init__(self, storage_engine: PersistentStorageEngine, node_id: str = None):
        self.storage_engine = storage_engine
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.local_locks = {}
        self._lock = threading.RLock()
        
        # 锁清理定时器
        self.cleanup_timer = None
        self._start_cleanup_timer()
        
        logger.info(f"🔒 分布式锁管理器初始化: {self.node_id}")
    
    def acquire_lock(self, 
                    key: str, 
                    lock_type: LockType = LockType.EXCLUSIVE,
                    timeout: float = 30.0,
                    wait_timeout: float = 10.0) -> Optional[DistributedLock]:
        """
        获取分布式锁
        
        Args:
            key: 锁定的键
            lock_type: 锁类型
            timeout: 锁超时时间
            wait_timeout: 等待超时时间
            
        Returns:
            分布式锁对象或None
        """
        lock_id = f"lock_{uuid.uuid4().hex}"
        current_time = time.time()
        expires_at = current_time + timeout
        
        # 尝试获取锁
        start_wait = time.time()
        while time.time() - start_wait < wait_timeout:
            if self._try_acquire_lock(key, lock_id, lock_type, expires_at):
                distributed_lock = DistributedLock(
                    lock_id=lock_id,
                    key=key,
                    lock_type=lock_type,
                    owner_id=self.node_id,
                    acquired_at=current_time,
                    expires_at=expires_at
                )
                
                with self._lock:
                    self.local_locks[lock_id] = distributed_lock
                
                logger.debug(f"🔒 获取锁成功: {key} ({lock_type.value})")
                return distributed_lock
            
            # 短暂等待后重试
            time.sleep(0.1)
        
        logger.warning(f"⚠️ 获取锁超时: {key}")
        return None
    
    def _try_acquire_lock(self, key: str, lock_id: str, lock_type: LockType, expires_at: float) -> bool:
        """尝试获取锁"""
        lock_key = f"distributed_lock:{key}"
        
        try:
            # 检查现有锁
            existing_locks = self.storage_engine.retrieve(lock_key) or []
            current_time = time.time()
            
            # 清理过期锁
            active_locks = [lock for lock in existing_locks 
                          if lock['expires_at'] > current_time]
            
            # 检查锁冲突
            if self._has_lock_conflict(active_locks, lock_type):
                return False
            
            # 添加新锁
            new_lock = {
                'lock_id': lock_id,
                'key': key,
                'lock_type': lock_type.value,
                'owner_id': self.node_id,
                'acquired_at': current_time,
                'expires_at': expires_at
            }
            
            active_locks.append(new_lock)
            
            # 存储锁信息
            return self.storage_engine.store(lock_key, active_locks)
            
        except Exception as e:
            logger.error(f"❌ 尝试获取锁失败: {key} - {e}")
            return False
    
    def _has_lock_conflict(self, existing_locks: List[Dict], new_lock_type: LockType) -> bool:
        """检查锁冲突"""
        for lock in existing_locks:
            existing_type = LockType(lock['lock_type'])
            
            # 排他锁与任何锁冲突
            if new_lock_type == LockType.EXCLUSIVE or existing_type == LockType.EXCLUSIVE:
                return True
            
            # 写锁与写锁冲突
            if new_lock_type == LockType.WRITE and existing_type == LockType.WRITE:
                return True
        
        return False
    
    def release_lock(self, distributed_lock: DistributedLock) -> bool:
        """释放分布式锁"""
        lock_key = f"distributed_lock:{distributed_lock.key}"
        
        try:
            # 从存储中移除锁
            existing_locks = self.storage_engine.retrieve(lock_key) or []
            updated_locks = [lock for lock in existing_locks 
                           if lock['lock_id'] != distributed_lock.lock_id]
            
            success = self.storage_engine.store(lock_key, updated_locks)
            
            # 从本地锁中移除
            with self._lock:
                if distributed_lock.lock_id in self.local_locks:
                    del self.local_locks[distributed_lock.lock_id]
            
            if success:
                logger.debug(f"🔓 释放锁成功: {distributed_lock.key}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 释放锁失败: {distributed_lock.key} - {e}")
            return False
    
    def _start_cleanup_timer(self):
        """启动锁清理定时器"""
        def cleanup_expired_locks():
            while True:
                try:
                    self._cleanup_expired_locks()
                    time.sleep(10)  # 每10秒清理一次
                except Exception as e:
                    logger.error(f"❌ 锁清理异常: {e}")
                    time.sleep(30)
        
        cleanup_thread = threading.Thread(target=cleanup_expired_locks, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_locks(self):
        """清理过期锁"""
        current_time = time.time()
        
        # 清理本地锁
        with self._lock:
            expired_local = [lock_id for lock_id, lock in self.local_locks.items()
                           if lock.expires_at <= current_time]
            
            for lock_id in expired_local:
                del self.local_locks[lock_id]
        
        # 清理存储中的过期锁
        try:
            lock_keys = self.storage_engine.list_keys("distributed_lock:")
            for lock_key in lock_keys:
                locks = self.storage_engine.retrieve(lock_key) or []
                active_locks = [lock for lock in locks if lock['expires_at'] > current_time]
                
                if len(active_locks) < len(locks):
                    self.storage_engine.store(lock_key, active_locks)
                    
        except Exception as e:
            logger.error(f"❌ 清理存储锁失败: {e}")

# =============================================================================
# 状态版本管理器
# =============================================================================

class StateVersionManager:
    """状态版本管理器"""
    
    def __init__(self, storage_engine: PersistentStorageEngine, node_id: str = None):
        self.storage_engine = storage_engine
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.version_cache = {}
        self._lock = threading.RLock()
        
        logger.info(f"📦 状态版本管理器初始化: {self.node_id}")
    
    def create_version(self, key: str, data: Any, operation: str = "update") -> StateVersion:
        """创建新版本"""
        current_time = time.time()
        
        # 获取当前版本号
        current_version = self.get_latest_version(key)
        new_version_number = (current_version.version + 1) if current_version else 1
        
        # 计算校验和
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()
        
        # 创建版本对象
        version = StateVersion(
            version=new_version_number,
            timestamp=current_time,
            node_id=self.node_id,
            checksum=checksum,
            operation=operation
        )
        
        # 存储版本信息
        version_key = f"state_version:{key}"
        versions = self.storage_engine.retrieve(version_key) or []
        versions.append(asdict(version))
        
        # 限制版本历史长度
        max_versions = 50
        if len(versions) > max_versions:
            versions = versions[-max_versions:]
        
        self.storage_engine.store(version_key, versions)
        
        # 更新缓存
        with self._lock:
            self.version_cache[key] = version
        
        logger.debug(f"📦 创建版本: {key} v{new_version_number}")
        return version
    
    def get_latest_version(self, key: str) -> Optional[StateVersion]:
        """获取最新版本"""
        # 先检查缓存
        with self._lock:
            if key in self.version_cache:
                return self.version_cache[key]
        
        # 从存储加载
        version_key = f"state_version:{key}"
        versions = self.storage_engine.retrieve(version_key) or []
        
        if not versions:
            return None
        
        # 获取最新版本
        latest_version_data = max(versions, key=lambda v: v['version'])
        latest_version = StateVersion(**latest_version_data)
        
        # 更新缓存
        with self._lock:
            self.version_cache[key] = latest_version
        
        return latest_version
    
    def get_version_history(self, key: str, limit: int = 10) -> List[StateVersion]:
        """获取版本历史"""
        version_key = f"state_version:{key}"
        versions = self.storage_engine.retrieve(version_key) or []
        
        # 按版本号排序并限制数量
        sorted_versions = sorted(versions, key=lambda v: v['version'], reverse=True)[:limit]
        
        return [StateVersion(**v) for v in sorted_versions]
    
    def detect_conflict(self, key: str, expected_version: int) -> bool:
        """检测版本冲突"""
        latest_version = self.get_latest_version(key)
        if not latest_version:
            return False
        
        return latest_version.version != expected_version

# =============================================================================
# 状态快照管理器
# =============================================================================

class StateSnapshotManager:
    """状态快照管理器"""
    
    def __init__(self, storage_engine: PersistentStorageEngine):
        self.storage_engine = storage_engine
        self.snapshot_cache = {}
        self._lock = threading.RLock()
        
        logger.info("📸 状态快照管理器初始化")
    
    def create_snapshot(self, 
                       keys: List[str] = None,
                       snapshot_id: str = None) -> StateSnapshot:
        """
        创建状态快照
        
        Args:
            keys: 要快照的键列表，None表示全部
            snapshot_id: 快照ID，None表示自动生成
            
        Returns:
            状态快照对象
        """
        snapshot_id = snapshot_id or f"snapshot_{uuid.uuid4().hex}"
        current_time = time.time()
        
        # 获取要快照的键
        if keys is None:
            keys = self.storage_engine.list_keys()
            # 过滤掉内部键
            keys = [k for k in keys if not k.startswith(('distributed_lock:', 'state_version:', 'snapshot:'))]
        
        # 收集状态数据
        state_data = {}
        for key in keys:
            data = self.storage_engine.retrieve(key)
            if data is not None:
                state_data[key] = data
        
        # 创建版本信息
        state_str = json.dumps(state_data, sort_keys=True, ensure_ascii=False)
        checksum = hashlib.sha256(state_str.encode()).hexdigest()
        
        version = StateVersion(
            version=1,
            timestamp=current_time,
            node_id="snapshot_manager",
            checksum=checksum,
            operation="snapshot"
        )
        
        # 创建快照
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=current_time,
            state_data=state_data,
            version=version,
            metadata={
                "keys_count": len(state_data),
                "total_size": len(state_str)
            }
        )
        
        # 存储快照
        snapshot_key = f"snapshot:{snapshot_id}"
        success = self.storage_engine.store(snapshot_key, asdict(snapshot))
        
        if success:
            # 更新缓存
            with self._lock:
                self.snapshot_cache[snapshot_id] = snapshot
            
            logger.info(f"📸 快照创建成功: {snapshot_id} ({len(state_data)} keys)")
        
        return snapshot
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        恢复状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否恢复成功
        """
        try:
            # 获取快照
            snapshot = self.get_snapshot(snapshot_id)
            if not snapshot:
                logger.error(f"❌ 快照不存在: {snapshot_id}")
                return False
            
            # 恢复状态数据
            success_count = 0
            total_count = len(snapshot.state_data)
            
            for key, data in snapshot.state_data.items():
                if self.storage_engine.store(key, data):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ 恢复失败: {key}")
            
            success = success_count == total_count
            
            if success:
                logger.info(f"✅ 快照恢复成功: {snapshot_id} ({success_count}/{total_count})")
            else:
                logger.warning(f"⚠️ 快照部分恢复: {snapshot_id} ({success_count}/{total_count})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 快照恢复失败: {snapshot_id} - {e}")
            return False
    
    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """获取快照"""
        # 先检查缓存
        with self._lock:
            if snapshot_id in self.snapshot_cache:
                return self.snapshot_cache[snapshot_id]
        
        # 从存储加载
        snapshot_key = f"snapshot:{snapshot_id}"
        snapshot_data = self.storage_engine.retrieve(snapshot_key)
        
        if not snapshot_data:
            return None
        
        # 重建快照对象
        snapshot_data['version'] = StateVersion(**snapshot_data['version'])
        snapshot = StateSnapshot(**snapshot_data)
        
        # 更新缓存
        with self._lock:
            self.snapshot_cache[snapshot_id] = snapshot
        
        return snapshot
    
    def list_snapshots(self) -> List[Tuple[str, float]]:
        """列出所有快照"""
        snapshot_keys = self.storage_engine.list_keys("snapshot:")
        snapshots = []
        
        for key in snapshot_keys:
            snapshot_id = key.replace("snapshot:", "")
            snapshot = self.get_snapshot(snapshot_id)
            if snapshot:
                snapshots.append((snapshot_id, snapshot.timestamp))
        
        # 按时间排序
        snapshots.sort(key=lambda x: x[1], reverse=True)
        return snapshots
    
    def cleanup_old_snapshots(self, keep_count: int = 10):
        """清理旧快照"""
        snapshots = self.list_snapshots()
        
        if len(snapshots) <= keep_count:
            return
        
        # 删除超出保留数量的快照
        old_snapshots = snapshots[keep_count:]
        deleted_count = 0
        
        for snapshot_id, _ in old_snapshots:
            snapshot_key = f"snapshot:{snapshot_id}"
            if self.storage_engine.delete(snapshot_key):
                deleted_count += 1
                
                # 从缓存中移除
                with self._lock:
                    if snapshot_id in self.snapshot_cache:
                        del self.snapshot_cache[snapshot_id]
        
        logger.info(f"🧹 清理快照: 删除 {deleted_count} 个旧快照")

# =============================================================================
# 分布式状态管理器
# =============================================================================

class DistributedStateManager:
    """
    分布式状态管理器
    
    功能：
    - 分布式锁管理
    - 状态版本控制
    - 冲突检测和解决
    - 状态快照和恢复
    - 事务管理
    """
    
    def __init__(self,
                 storage_config: StorageConfig = None,
                 node_id: str = None,
                 consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL,
                 conflict_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS):
        """
        初始化分布式状态管理器
        
        Args:
            storage_config: 存储配置
            node_id: 节点ID
            consistency_level: 一致性级别
            conflict_resolution: 冲突解决策略
        """
        self.storage_config = storage_config or StorageConfig()
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.consistency_level = consistency_level
        self.conflict_resolution = conflict_resolution
        
        # 初始化组件
        self.storage_engine = PersistentStorageEngine(self.storage_config)
        self.lock_manager = DistributedLockManager(self.storage_engine, self.node_id)
        self.version_manager = StateVersionManager(self.storage_engine, self.node_id)
        self.snapshot_manager = StateSnapshotManager(self.storage_engine)
        
        # 事务管理
        self.active_transactions = {}
        self._transaction_lock = threading.RLock()
        
        # 状态缓存
        self.state_cache = {}
        self.cache_lock = threading.RLock()
        
        logger.info(f"🌐 分布式状态管理器初始化: {self.node_id}")
        logger.info(f"   一致性级别: {consistency_level.value}")
        logger.info(f"   冲突解决: {conflict_resolution.value}")
    
    def set_state(self, 
                  key: str, 
                  value: Any,
                  timeout: float = 30.0,
                  consistency_level: ConsistencyLevel = None) -> bool:
        """
        设置状态
        
        Args:
            key: 状态键
            value: 状态值
            timeout: 超时时间
            consistency_level: 一致性级别
            
        Returns:
            是否设置成功
        """
        consistency_level = consistency_level or self.consistency_level
        
        try:
            # 强一致性需要获取写锁
            lock = None
            if consistency_level == ConsistencyLevel.STRONG:
                lock = self.lock_manager.acquire_lock(key, LockType.WRITE, timeout)
                if not lock:
                    logger.warning(f"⚠️ 获取写锁失败: {key}")
                    return False
            
            try:
                # 检查版本冲突
                if consistency_level in [ConsistencyLevel.STRONG, ConsistencyLevel.CAUSAL]:
                    current_version = self.version_manager.get_latest_version(key)
                    # 这里可以添加更复杂的冲突检测逻辑
                
                # 存储状态
                success = self.storage_engine.store(key, value)
                
                if success:
                    # 创建新版本
                    version = self.version_manager.create_version(key, value, "set")
                    
                    # 更新缓存
                    with self.cache_lock:
                        self.state_cache[key] = {
                            'value': value,
                            'version': version,
                            'timestamp': time.time()
                        }
                    
                    logger.debug(f"✅ 状态设置成功: {key}")
                
                return success
                
            finally:
                # 释放锁
                if lock:
                    self.lock_manager.release_lock(lock)
                    
        except Exception as e:
            logger.error(f"❌ 设置状态失败: {key} - {e}")
            return False
    
    def get_state(self, 
                  key: str,
                  consistency_level: ConsistencyLevel = None) -> Optional[Any]:
        """
        获取状态
        
        Args:
            key: 状态键
            consistency_level: 一致性级别
            
        Returns:
            状态值或None
        """
        consistency_level = consistency_level or self.consistency_level
        
        try:
            # 会话一致性可以使用缓存
            if consistency_level == ConsistencyLevel.SESSION:
                with self.cache_lock:
                    if key in self.state_cache:
                        cached = self.state_cache[key]
                        # 检查缓存是否过期（简单策略）
                        if time.time() - cached['timestamp'] < 60:  # 60秒缓存
                            return cached['value']
            
            # 从存储获取
            value = self.storage_engine.retrieve(key)
            
            if value is not None:
                # 更新缓存
                version = self.version_manager.get_latest_version(key)
                with self.cache_lock:
                    self.state_cache[key] = {
                        'value': value,
                        'version': version,
                        'timestamp': time.time()
                    }
                
                logger.debug(f"✅ 状态获取成功: {key}")
            
            return value
            
        except Exception as e:
            logger.error(f"❌ 获取状态失败: {key} - {e}")
            return None
    
    def delete_state(self, key: str, timeout: float = 30.0) -> bool:
        """删除状态"""
        try:
            # 获取写锁
            lock = self.lock_manager.acquire_lock(key, LockType.WRITE, timeout)
            if not lock:
                logger.warning(f"⚠️ 获取删除锁失败: {key}")
                return False
            
            try:
                # 删除状态
                success = self.storage_engine.delete(key)
                
                if success:
                    # 创建删除版本记录
                    self.version_manager.create_version(key, None, "delete")
                    
                    # 清除缓存
                    with self.cache_lock:
                        if key in self.state_cache:
                            del self.state_cache[key]
                    
                    logger.debug(f"✅ 状态删除成功: {key}")
                
                return success
                
            finally:
                self.lock_manager.release_lock(lock)
                
        except Exception as e:
            logger.error(f"❌ 删除状态失败: {key} - {e}")
            return False
    
    def create_snapshot(self, keys: List[str] = None) -> Optional[StateSnapshot]:
        """创建状态快照"""
        try:
            snapshot = self.snapshot_manager.create_snapshot(keys)
            logger.info(f"📸 状态快照创建: {snapshot.snapshot_id}")
            return snapshot
        except Exception as e:
            logger.error(f"❌ 创建快照失败: {e}")
            return None
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """恢复状态快照"""
        try:
            success = self.snapshot_manager.restore_snapshot(snapshot_id)
            if success:
                # 清除缓存
                with self.cache_lock:
                    self.state_cache.clear()
                logger.info(f"✅ 状态快照恢复: {snapshot_id}")
            return success
        except Exception as e:
            logger.error(f"❌ 恢复快照失败: {snapshot_id} - {e}")
            return False
    
    def get_state_statistics(self) -> Dict[str, Any]:
        """获取状态统计信息"""
        try:
            storage_stats = self.storage_engine.get_storage_stats()
            snapshots = self.snapshot_manager.list_snapshots()
            
            return {
                "node_id": self.node_id,
                "consistency_level": self.consistency_level.value,
                "conflict_resolution": self.conflict_resolution.value,
                "storage_stats": storage_stats,
                "cache_size": len(self.state_cache),
                "active_transactions": len(self.active_transactions),
                "snapshots_count": len(snapshots),
                "latest_snapshot": snapshots[0] if snapshots else None
            }
            
        except Exception as e:
            logger.error(f"❌ 获取状态统计失败: {e}")
            return {}
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理快照
            self.snapshot_manager.cleanup_old_snapshots()
            
            # 清理存储
            self.storage_engine.cleanup()
            
            # 清理缓存
            with self.cache_lock:
                self.state_cache.clear()
            
            logger.info("🧹 分布式状态管理器清理完成")
            
        except Exception as e:
            logger.error(f"❌ 分布式状态管理器清理失败: {e}")

# =============================================================================
# 工厂函数
# =============================================================================

def create_distributed_state_manager(
    storage_backend: str = "file_system",
    storage_path: str = "./neogenesis_distributed_state",
    node_id: str = None,
    consistency_level: str = "eventual",
    **kwargs
) -> DistributedStateManager:
    """
    创建分布式状态管理器
    
    Args:
        storage_backend: 存储后端类型
        storage_path: 存储路径
        node_id: 节点ID
        consistency_level: 一致性级别
        **kwargs: 其他配置参数
        
    Returns:
        分布式状态管理器实例
    """
    storage_config = StorageConfig(
        backend=StorageBackend(storage_backend),
        storage_path=storage_path,
        **kwargs
    )
    
    return DistributedStateManager(
        storage_config=storage_config,
        node_id=node_id,
        consistency_level=ConsistencyLevel(consistency_level)
    )

# =============================================================================
# 测试和演示
# =============================================================================

if __name__ == "__main__":
    # 测试分布式状态管理器
    print("🧪 测试分布式状态管理器...")
    
    # 创建管理器
    manager = create_distributed_state_manager(
        storage_backend="memory",
        consistency_level="strong"
    )
    
    # 测试状态设置和获取
    print("\n🌐 测试状态操作:")
    success = manager.set_state("test_key", {"data": "测试数据", "value": 42})
    print(f"✅ 设置状态: {'成功' if success else '失败'}")
    
    value = manager.get_state("test_key")
    print(f"✅ 获取状态: {value}")
    
    # 测试快照
    print("\n📸 测试状态快照:")
    snapshot = manager.create_snapshot()
    if snapshot:
        print(f"✅ 快照创建: {snapshot.snapshot_id}")
        
        # 修改状态
        manager.set_state("test_key", {"data": "修改后的数据", "value": 100})
        modified_value = manager.get_state("test_key")
        print(f"✅ 修改后状态: {modified_value}")
        
        # 恢复快照
        restore_success = manager.restore_snapshot(snapshot.snapshot_id)
        print(f"✅ 快照恢复: {'成功' if restore_success else '失败'}")
        
        restored_value = manager.get_state("test_key")
        print(f"✅ 恢复后状态: {restored_value}")
    
    # 测试统计信息
    print("\n📊 测试状态统计:")
    stats = manager.get_state_statistics()
    print(f"✅ 状态统计: {stats}")
    
    # 清理
    manager.cleanup()
    
    print("✅ 分布式状态管理器测试完成")
