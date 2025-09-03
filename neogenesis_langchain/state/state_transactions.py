#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - State Transactions
状态事务管理：ACID特性保障和分布式事务支持
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

from ..storage.persistent_storage import PersistentStorageEngine
from .distributed_state import DistributedStateManager

logger = logging.getLogger(__name__)

# =============================================================================
# 事务配置和枚举
# =============================================================================

class TransactionStatus(Enum):
    """事务状态"""
    PENDING = "pending"       # 待处理
    ACTIVE = "active"         # 活跃
    PREPARING = "preparing"   # 准备提交
    COMMITTED = "committed"   # 已提交
    ABORTED = "aborted"      # 已中止
    FAILED = "failed"        # 失败

class IsolationLevel(Enum):
    """隔离级别"""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"

class OperationType(Enum):
    """操作类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"

@dataclass
class TransactionOperation:
    """事务操作"""
    operation_id: str
    operation_type: OperationType
    key: str
    value: Any = None
    old_value: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TransactionLog:
    """事务日志"""
    log_id: str
    transaction_id: str
    operation: TransactionOperation
    log_type: str  # before, after, compensation
    timestamp: float = field(default_factory=time.time)
    checksum: str = ""

@dataclass
class Transaction:
    """事务"""
    transaction_id: str
    operations: List[TransactionOperation] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
    
    # 时间相关
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    committed_at: Optional[float] = None
    timeout: float = 30.0
    
    # 锁和依赖
    read_locks: Set[str] = field(default_factory=set)
    write_locks: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """检查事务是否过期"""
        if self.started_at is None:
            return time.time() - self.created_at > self.timeout
        return time.time() - self.started_at > self.timeout
    
    @property
    def duration(self) -> float:
        """获取事务持续时间"""
        if self.started_at is None:
            return 0.0
        end_time = self.committed_at or time.time()
        return end_time - self.started_at

# =============================================================================
# 死锁检测器
# =============================================================================

class DeadlockDetector:
    """死锁检测器"""
    
    def __init__(self):
        self.wait_graph = defaultdict(set)  # 等待图
        self.resource_locks = defaultdict(set)  # 资源锁
        self._lock = threading.RLock()
    
    def add_wait_edge(self, waiting_tx: str, holding_tx: str, resource: str):
        """添加等待边"""
        with self._lock:
            self.wait_graph[waiting_tx].add(holding_tx)
            self.resource_locks[resource].add(holding_tx)
    
    def remove_wait_edge(self, waiting_tx: str, holding_tx: str):
        """移除等待边"""
        with self._lock:
            if waiting_tx in self.wait_graph:
                self.wait_graph[waiting_tx].discard(holding_tx)
                if not self.wait_graph[waiting_tx]:
                    del self.wait_graph[waiting_tx]
    
    def detect_deadlock(self) -> List[List[str]]:
        """检测死锁，返回死锁环"""
        with self._lock:
            visited = set()
            rec_stack = set()
            deadlock_cycles = []
            
            def dfs(node: str, path: List[str]) -> bool:
                visited.add(node)
                rec_stack.add(node)
                current_path = path + [node]
                
                for neighbor in self.wait_graph.get(node, []):
                    if neighbor not in visited:
                        if dfs(neighbor, current_path):
                            return True
                    elif neighbor in rec_stack:
                        # 找到环
                        cycle_start = current_path.index(neighbor)
                        cycle = current_path[cycle_start:]
                        deadlock_cycles.append(cycle)
                        return True
                
                rec_stack.remove(node)
                return False
            
            # 检查所有节点
            for node in self.wait_graph:
                if node not in visited:
                    dfs(node, [])
            
            return deadlock_cycles
    
    def resolve_deadlock(self, deadlock_cycles: List[List[str]]) -> List[str]:
        """解决死锁，返回需要中止的事务"""
        victims = []
        
        for cycle in deadlock_cycles:
            if cycle:
                # 选择最年轻的事务作为牺牲者（简单策略）
                victim = max(cycle, key=lambda tx: tx)  # 字典序最大的
                victims.append(victim)
                
                # 从等待图中移除受害者
                with self._lock:
                    if victim in self.wait_graph:
                        del self.wait_graph[victim]
                    
                    # 移除指向受害者的边
                    for node in self.wait_graph:
                        self.wait_graph[node].discard(victim)
        
        return victims
    
    def cleanup_transaction(self, transaction_id: str):
        """清理事务相关的等待信息"""
        with self._lock:
            # 移除事务的所有等待边
            if transaction_id in self.wait_graph:
                del self.wait_graph[transaction_id]
            
            # 移除指向该事务的边
            for node in list(self.wait_graph.keys()):
                self.wait_graph[node].discard(transaction_id)
                if not self.wait_graph[node]:
                    del self.wait_graph[node]
            
            # 清理资源锁
            for resource in list(self.resource_locks.keys()):
                self.resource_locks[resource].discard(transaction_id)
                if not self.resource_locks[resource]:
                    del self.resource_locks[resource]

# =============================================================================
# 事务日志管理器
# =============================================================================

class TransactionLogManager:
    """事务日志管理器"""
    
    def __init__(self, storage_engine: PersistentStorageEngine):
        self.storage_engine = storage_engine
        self.log_buffer = deque(maxlen=1000)
        self._lock = threading.RLock()
        
        # 启动日志刷新线程
        self.flush_thread = threading.Thread(target=self._flush_logs_periodically, daemon=True)
        self.flush_thread.start()
        
        logger.info("📝 事务日志管理器初始化完成")
    
    def log_operation(self, 
                     transaction_id: str,
                     operation: TransactionOperation,
                     log_type: str = "before") -> str:
        """记录操作日志"""
        log_id = f"log_{uuid.uuid4().hex[:8]}"
        
        transaction_log = TransactionLog(
            log_id=log_id,
            transaction_id=transaction_id,
            operation=operation,
            log_type=log_type
        )
        
        with self._lock:
            self.log_buffer.append(transaction_log)
        
        # 如果是关键操作，立即刷新
        if log_type in ["commit", "abort"]:
            self._flush_logs()
        
        return log_id
    
    def _flush_logs(self):
        """刷新日志到存储"""
        with self._lock:
            if not self.log_buffer:
                return
            
            # 获取要刷新的日志
            logs_to_flush = list(self.log_buffer)
            self.log_buffer.clear()
        
        try:
            # 批量保存日志
            log_data = [asdict(log) for log in logs_to_flush]
            
            # 按事务ID分组保存
            transaction_logs = defaultdict(list)
            for log in log_data:
                transaction_logs[log["transaction_id"]].append(log)
            
            for transaction_id, logs in transaction_logs.items():
                log_key = f"transaction_log:{transaction_id}"
                existing_logs = self.storage_engine.retrieve(log_key) or []
                existing_logs.extend(logs)
                
                # 限制日志数量
                if len(existing_logs) > 500:
                    existing_logs = existing_logs[-500:]
                
                self.storage_engine.store(log_key, existing_logs)
            
            logger.debug(f"📝 刷新事务日志: {len(logs_to_flush)} 条")
            
        except Exception as e:
            logger.error(f"❌ 刷新事务日志失败: {e}")
    
    def _flush_logs_periodically(self):
        """定期刷新日志"""
        while True:
            try:
                time.sleep(5.0)  # 每5秒刷新一次
                self._flush_logs()
            except Exception as e:
                logger.error(f"❌ 定期刷新日志异常: {e}")
    
    def get_transaction_logs(self, transaction_id: str) -> List[TransactionLog]:
        """获取事务日志"""
        log_key = f"transaction_log:{transaction_id}"
        log_data = self.storage_engine.retrieve(log_key) or []
        
        logs = []
        for data in log_data:
            # 重建操作对象
            op_data = data["operation"]
            op_data["operation_type"] = OperationType(op_data["operation_type"])
            operation = TransactionOperation(**op_data)
            
            # 重建日志对象
            data["operation"] = operation
            logs.append(TransactionLog(**data))
        
        return logs
    
    def cleanup_transaction_logs(self, transaction_id: str, keep_committed: bool = True):
        """清理事务日志"""
        if keep_committed:
            # 只保留提交相关的日志
            logs = self.get_transaction_logs(transaction_id)
            commit_logs = [log for log in logs if log.log_type in ["commit", "after"]]
            
            if commit_logs:
                log_key = f"transaction_log:{transaction_id}"
                log_data = [asdict(log) for log in commit_logs]
                self.storage_engine.store(log_key, log_data)
            else:
                self._delete_transaction_logs(transaction_id)
        else:
            self._delete_transaction_logs(transaction_id)
    
    def _delete_transaction_logs(self, transaction_id: str):
        """删除事务日志"""
        log_key = f"transaction_log:{transaction_id}"
        self.storage_engine.delete(log_key)

# =============================================================================
# 事务管理器
# =============================================================================

class TransactionManager:
    """
    事务管理器
    
    功能：
    - ACID事务支持
    - 多种隔离级别
    - 死锁检测和解决
    - 事务日志和恢复
    - 分布式事务支持
    """
    
    def __init__(self,
                 storage_engine: PersistentStorageEngine,
                 distributed_state_manager: DistributedStateManager = None):
        """
        初始化事务管理器
        
        Args:
            storage_engine: 存储引擎
            distributed_state_manager: 分布式状态管理器
        """
        self.storage_engine = storage_engine
        self.distributed_state_manager = distributed_state_manager
        
        # 事务管理
        self.active_transactions: Dict[str, Transaction] = {}
        self.transaction_locks = defaultdict(set)  # 资源锁映射
        
        # 死锁检测
        self.deadlock_detector = DeadlockDetector()
        
        # 事务日志
        self.log_manager = TransactionLogManager(storage_engine)
        
        # 性能统计
        self.transaction_stats = {
            "total_transactions": 0,
            "committed_transactions": 0,
            "aborted_transactions": 0,
            "deadlock_detections": 0,
            "average_duration": 0.0
        }
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_transactions, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("🔄 事务管理器初始化完成")
    
    def begin_transaction(self,
                         transaction_id: str = None,
                         isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
                         timeout: float = 30.0) -> str:
        """
        开始事务
        
        Args:
            transaction_id: 事务ID，None表示自动生成
            isolation_level: 隔离级别
            timeout: 超时时间
            
        Returns:
            事务ID
        """
        transaction_id = transaction_id or f"tx_{uuid.uuid4().hex[:8]}"
        
        with self._lock:
            if transaction_id in self.active_transactions:
                raise ValueError(f"事务已存在: {transaction_id}")
            
            transaction = Transaction(
                transaction_id=transaction_id,
                isolation_level=isolation_level,
                timeout=timeout,
                started_at=time.time()
            )
            transaction.status = TransactionStatus.ACTIVE
            
            self.active_transactions[transaction_id] = transaction
            self.transaction_stats["total_transactions"] += 1
            
            # 记录日志
            begin_operation = TransactionOperation(
                operation_id=f"begin_{uuid.uuid4().hex[:8]}",
                operation_type=OperationType.CREATE,
                key="transaction",
                value={"action": "begin", "isolation": isolation_level.value}
            )
            self.log_manager.log_operation(transaction_id, begin_operation, "begin")
            
            logger.debug(f"🔄 事务开始: {transaction_id}")
            return transaction_id
    
    def read(self, transaction_id: str, key: str) -> Any:
        """
        事务读取
        
        Args:
            transaction_id: 事务ID
            key: 键
            
        Returns:
            值
        """
        with self._lock:
            transaction = self._get_active_transaction(transaction_id)
            if not transaction:
                raise ValueError(f"事务不存在或未激活: {transaction_id}")
            
            # 检查隔离级别
            if transaction.isolation_level in [IsolationLevel.REPEATABLE_READ, IsolationLevel.SERIALIZABLE]:
                # 需要读锁
                if not self._acquire_read_lock(transaction_id, key):
                    raise RuntimeError(f"无法获取读锁: {key}")
                transaction.read_locks.add(key)
            
            # 读取数据
            if self.distributed_state_manager:
                value = self.distributed_state_manager.get_state(key)
            else:
                value = self.storage_engine.retrieve(key)
            
            # 记录操作
            read_operation = TransactionOperation(
                operation_id=f"read_{uuid.uuid4().hex[:8]}",
                operation_type=OperationType.READ,
                key=key,
                value=value
            )
            transaction.operations.append(read_operation)
            self.log_manager.log_operation(transaction_id, read_operation, "before")
            
            logger.debug(f"📖 事务读取: {transaction_id} -> {key}")
            return value
    
    def write(self, transaction_id: str, key: str, value: Any) -> bool:
        """
        事务写入
        
        Args:
            transaction_id: 事务ID
            key: 键
            value: 值
            
        Returns:
            是否成功
        """
        with self._lock:
            transaction = self._get_active_transaction(transaction_id)
            if not transaction:
                raise ValueError(f"事务不存在或未激活: {transaction_id}")
            
            # 获取写锁
            if not self._acquire_write_lock(transaction_id, key):
                raise RuntimeError(f"无法获取写锁: {key}")
            transaction.write_locks.add(key)
            
            # 获取旧值用于回滚
            if self.distributed_state_manager:
                old_value = self.distributed_state_manager.get_state(key)
            else:
                old_value = self.storage_engine.retrieve(key)
            
            # 记录操作
            write_operation = TransactionOperation(
                operation_id=f"write_{uuid.uuid4().hex[:8]}",
                operation_type=OperationType.WRITE,
                key=key,
                value=value,
                old_value=old_value
            )
            transaction.operations.append(write_operation)
            self.log_manager.log_operation(transaction_id, write_operation, "before")
            
            logger.debug(f"✏️ 事务写入: {transaction_id} -> {key}")
            return True
    
    def delete(self, transaction_id: str, key: str) -> bool:
        """
        事务删除
        
        Args:
            transaction_id: 事务ID
            key: 键
            
        Returns:
            是否成功
        """
        with self._lock:
            transaction = self._get_active_transaction(transaction_id)
            if not transaction:
                raise ValueError(f"事务不存在或未激活: {transaction_id}")
            
            # 获取写锁
            if not self._acquire_write_lock(transaction_id, key):
                raise RuntimeError(f"无法获取写锁: {key}")
            transaction.write_locks.add(key)
            
            # 获取旧值用于回滚
            if self.distributed_state_manager:
                old_value = self.distributed_state_manager.get_state(key)
            else:
                old_value = self.storage_engine.retrieve(key)
            
            # 记录操作
            delete_operation = TransactionOperation(
                operation_id=f"delete_{uuid.uuid4().hex[:8]}",
                operation_type=OperationType.DELETE,
                key=key,
                old_value=old_value
            )
            transaction.operations.append(delete_operation)
            self.log_manager.log_operation(transaction_id, delete_operation, "before")
            
            logger.debug(f"🗑️ 事务删除: {transaction_id} -> {key}")
            return True
    
    def commit(self, transaction_id: str) -> bool:
        """
        提交事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否提交成功
        """
        with self._lock:
            transaction = self._get_active_transaction(transaction_id)
            if not transaction:
                raise ValueError(f"事务不存在或未激活: {transaction_id}")
            
            try:
                transaction.status = TransactionStatus.PREPARING
                
                # 应用所有写操作
                for operation in transaction.operations:
                    if operation.operation_type == OperationType.WRITE:
                        if self.distributed_state_manager:
                            success = self.distributed_state_manager.set_state(operation.key, operation.value)
                        else:
                            success = self.storage_engine.store(operation.key, operation.value)
                        
                        if not success:
                            raise RuntimeError(f"写入失败: {operation.key}")
                    
                    elif operation.operation_type == OperationType.DELETE:
                        if self.distributed_state_manager:
                            success = self.distributed_state_manager.delete_state(operation.key)
                        else:
                            success = self.storage_engine.delete(operation.key)
                        
                        if not success:
                            raise RuntimeError(f"删除失败: {operation.key}")
                
                # 提交成功
                transaction.status = TransactionStatus.COMMITTED
                transaction.committed_at = time.time()
                
                # 记录提交日志
                commit_operation = TransactionOperation(
                    operation_id=f"commit_{uuid.uuid4().hex[:8]}",
                    operation_type=OperationType.UPDATE,
                    key="transaction",
                    value={"action": "commit", "operations_count": len(transaction.operations)}
                )
                self.log_manager.log_operation(transaction_id, commit_operation, "commit")
                
                # 释放锁
                self._release_locks(transaction_id)
                
                # 更新统计
                self.transaction_stats["committed_transactions"] += 1
                duration = transaction.duration
                current_avg = self.transaction_stats["average_duration"]
                count = self.transaction_stats["committed_transactions"]
                self.transaction_stats["average_duration"] = (current_avg * (count - 1) + duration) / count
                
                # 清理事务
                del self.active_transactions[transaction_id]
                
                logger.info(f"✅ 事务提交成功: {transaction_id} ({duration:.3f}s)")
                return True
                
            except Exception as e:
                # 提交失败，回滚事务
                logger.error(f"❌ 事务提交失败: {transaction_id} - {e}")
                transaction.error_message = str(e)
                self.abort(transaction_id)
                return False
    
    def abort(self, transaction_id: str) -> bool:
        """
        中止事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否中止成功
        """
        with self._lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                logger.warning(f"⚠️ 事务不存在: {transaction_id}")
                return False
            
            transaction.status = TransactionStatus.ABORTED
            
            # 回滚操作（逆序）
            for operation in reversed(transaction.operations):
                try:
                    if operation.operation_type == OperationType.WRITE:
                        # 恢复旧值
                        if operation.old_value is not None:
                            if self.distributed_state_manager:
                                self.distributed_state_manager.set_state(operation.key, operation.old_value)
                            else:
                                self.storage_engine.store(operation.key, operation.old_value)
                        else:
                            # 原来不存在，删除
                            if self.distributed_state_manager:
                                self.distributed_state_manager.delete_state(operation.key)
                            else:
                                self.storage_engine.delete(operation.key)
                    
                    elif operation.operation_type == OperationType.DELETE:
                        # 恢复删除的数据
                        if operation.old_value is not None:
                            if self.distributed_state_manager:
                                self.distributed_state_manager.set_state(operation.key, operation.old_value)
                            else:
                                self.storage_engine.store(operation.key, operation.old_value)
                
                except Exception as e:
                    logger.error(f"❌ 回滚操作失败: {operation.key} - {e}")
            
            # 记录中止日志
            abort_operation = TransactionOperation(
                operation_id=f"abort_{uuid.uuid4().hex[:8]}",
                operation_type=OperationType.UPDATE,
                key="transaction",
                value={"action": "abort", "reason": transaction.error_message}
            )
            self.log_manager.log_operation(transaction_id, abort_operation, "abort")
            
            # 释放锁
            self._release_locks(transaction_id)
            
            # 更新统计
            self.transaction_stats["aborted_transactions"] += 1
            
            # 清理事务
            del self.active_transactions[transaction_id]
            
            logger.info(f"🔄 事务中止: {transaction_id}")
            return True
    
    def _get_active_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """获取活跃事务"""
        transaction = self.active_transactions.get(transaction_id)
        if transaction and transaction.status == TransactionStatus.ACTIVE:
            return transaction
        return None
    
    def _acquire_read_lock(self, transaction_id: str, key: str) -> bool:
        """获取读锁"""
        # 检查是否已有写锁
        for holder in self.transaction_locks[key]:
            holder_tx = self.active_transactions.get(holder)
            if holder_tx and key in holder_tx.write_locks:
                # 检查死锁
                self.deadlock_detector.add_wait_edge(transaction_id, holder, key)
                deadlocks = self.deadlock_detector.detect_deadlock()
                if deadlocks:
                    self._handle_deadlocks(deadlocks)
                    return False
                
                # 等待写锁释放（这里简化处理）
                return False
        
        # 获取读锁
        self.transaction_locks[key].add(transaction_id)
        return True
    
    def _acquire_write_lock(self, transaction_id: str, key: str) -> bool:
        """获取写锁"""
        # 检查是否已有其他锁
        current_holders = self.transaction_locks[key]
        other_holders = current_holders - {transaction_id}
        
        if other_holders:
            # 有其他事务持有锁
            for holder in other_holders:
                self.deadlock_detector.add_wait_edge(transaction_id, holder, key)
            
            deadlocks = self.deadlock_detector.detect_deadlock()
            if deadlocks:
                self._handle_deadlocks(deadlocks)
                return False
            
            # 等待锁释放（这里简化处理）
            return False
        
        # 获取写锁
        self.transaction_locks[key].add(transaction_id)
        return True
    
    def _release_locks(self, transaction_id: str):
        """释放事务的所有锁"""
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            return
        
        # 释放读锁
        for key in transaction.read_locks:
            self.transaction_locks[key].discard(transaction_id)
            if not self.transaction_locks[key]:
                del self.transaction_locks[key]
        
        # 释放写锁
        for key in transaction.write_locks:
            self.transaction_locks[key].discard(transaction_id)
            if not self.transaction_locks[key]:
                del self.transaction_locks[key]
        
        # 清理死锁检测器
        self.deadlock_detector.cleanup_transaction(transaction_id)
    
    def _handle_deadlocks(self, deadlock_cycles: List[List[str]]):
        """处理死锁"""
        self.transaction_stats["deadlock_detections"] += 1
        
        victims = self.deadlock_detector.resolve_deadlock(deadlock_cycles)
        
        for victim_id in victims:
            if victim_id in self.active_transactions:
                victim_tx = self.active_transactions[victim_id]
                victim_tx.error_message = "死锁检测，事务被中止"
                self.abort(victim_id)
                logger.warning(f"⚠️ 死锁解决：中止事务 {victim_id}")
    
    def _cleanup_expired_transactions(self):
        """清理过期事务"""
        while True:
            try:
                time.sleep(10.0)  # 每10秒检查一次
                
                with self._lock:
                    expired_transactions = [
                        tx_id for tx_id, tx in self.active_transactions.items()
                        if tx.is_expired
                    ]
                
                for tx_id in expired_transactions:
                    logger.warning(f"⏰ 事务超时，自动中止: {tx_id}")
                    transaction = self.active_transactions[tx_id]
                    transaction.error_message = "事务超时"
                    self.abort(tx_id)
                    
            except Exception as e:
                logger.error(f"❌ 清理过期事务异常: {e}")
                time.sleep(30)
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """获取事务状态"""
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            return None
        
        return {
            "transaction_id": transaction_id,
            "status": transaction.status.value,
            "isolation_level": transaction.isolation_level.value,
            "operations_count": len(transaction.operations),
            "read_locks": list(transaction.read_locks),
            "write_locks": list(transaction.write_locks),
            "created_at": transaction.created_at,
            "started_at": transaction.started_at,
            "duration": transaction.duration,
            "is_expired": transaction.is_expired,
            "error_message": transaction.error_message
        }
    
    def get_transaction_statistics(self) -> Dict[str, Any]:
        """获取事务统计信息"""
        with self._lock:
            active_count = len(self.active_transactions)
            
            # 按状态统计
            status_counts = defaultdict(int)
            for tx in self.active_transactions.values():
                status_counts[tx.status.value] += 1
            
            # 按隔离级别统计
            isolation_counts = defaultdict(int)
            for tx in self.active_transactions.values():
                isolation_counts[tx.isolation_level.value] += 1
            
            return {
                "active_transactions": active_count,
                "status_distribution": dict(status_counts),
                "isolation_distribution": dict(isolation_counts),
                "total_locks": len(self.transaction_locks),
                **self.transaction_stats
            }
    
    def cleanup(self):
        """清理资源"""
        # 中止所有活跃事务
        with self._lock:
            active_tx_ids = list(self.active_transactions.keys())
        
        for tx_id in active_tx_ids:
            self.abort(tx_id)
        
        # 最终刷新日志
        self.log_manager._flush_logs()
        
        logger.info("🧹 事务管理器清理完成")

# =============================================================================
# 工厂函数
# =============================================================================

def create_transaction_manager(
    storage_engine: PersistentStorageEngine,
    distributed_state_manager: DistributedStateManager = None
) -> TransactionManager:
    """
    创建事务管理器
    
    Args:
        storage_engine: 存储引擎
        distributed_state_manager: 分布式状态管理器
        
    Returns:
        事务管理器实例
    """
    return TransactionManager(storage_engine, distributed_state_manager)

# =============================================================================
# 测试和演示
# =============================================================================

if __name__ == "__main__":
    # 测试事务管理器
    print("🧪 测试事务管理器...")
    
    from ..storage.persistent_storage import create_storage_engine
    
    # 创建存储引擎和事务管理器
    storage_engine = create_storage_engine("memory")
    tx_manager = TransactionManager(storage_engine)
    
    # 测试基本事务操作
    print("\n🔄 测试基本事务:")
    
    # 开始事务
    tx_id = tx_manager.begin_transaction()
    print(f"✅ 事务开始: {tx_id}")
    
    # 执行操作
    tx_manager.write(tx_id, "key1", "value1")
    tx_manager.write(tx_id, "key2", "value2")
    print("✅ 执行写操作")
    
    # 读取操作
    value1 = tx_manager.read(tx_id, "key1")
    print(f"✅ 读取操作: key1 = {value1}")
    
    # 提交事务
    commit_success = tx_manager.commit(tx_id)
    print(f"✅ 事务提交: {'成功' if commit_success else '失败'}")
    
    # 测试事务回滚
    print("\n🔄 测试事务回滚:")
    
    tx_id2 = tx_manager.begin_transaction()
    tx_manager.write(tx_id2, "key1", "modified_value")
    
    # 获取事务状态
    status = tx_manager.get_transaction_status(tx_id2)
    print(f"✅ 事务状态: {status['status']}, 操作数: {status['operations_count']}")
    
    # 中止事务
    abort_success = tx_manager.abort(tx_id2)
    print(f"✅ 事务中止: {'成功' if abort_success else '失败'}")
    
    # 验证回滚
    final_value = storage_engine.retrieve("key1")
    print(f"✅ 回滚验证: key1 = {final_value}")
    
    # 获取统计信息
    print("\n📊 事务统计:")
    stats = tx_manager.get_transaction_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 清理
    tx_manager.cleanup()
    
    print("✅ 事务管理器测试完成")
