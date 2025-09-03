#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neogenesis System - Persistent Storage Engine
企业级持久化存储引擎：支持多种存储后端和高级特性
"""

import json
import pickle
import gzip
import hashlib
import logging
import time
import threading
import shutil
import sqlite3
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import lmdb
    LMDB_AVAILABLE = True
except ImportError:
    LMDB_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# 存储配置和枚举
# =============================================================================

class StorageBackend(Enum):
    """存储后端类型"""
    FILE_SYSTEM = "file_system"
    SQLITE = "sqlite"
    REDIS = "redis"
    LMDB = "lmdb"
    MEMORY = "memory"

class CompressionType(Enum):
    """压缩类型"""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"

class SerializationType(Enum):
    """序列化类型"""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"

@dataclass
class StorageConfig:
    """存储配置"""
    backend: StorageBackend = StorageBackend.FILE_SYSTEM
    storage_path: str = "./neogenesis_storage"
    compression: CompressionType = CompressionType.GZIP
    serialization: SerializationType = SerializationType.PICKLE
    enable_encryption: bool = False
    enable_versioning: bool = True
    enable_backup: bool = True
    backup_interval: int = 3600  # 备份间隔（秒）
    max_versions: int = 10
    cache_size: int = 1000
    auto_sync: bool = True
    sync_interval: float = 5.0
    compression_level: int = 6

@dataclass
class StorageMetadata:
    """存储元数据"""
    key: str
    size: int
    created_at: float
    updated_at: float
    version: int
    checksum: str
    compressed: bool = False
    encrypted: bool = False
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

# =============================================================================
# 抽象存储接口
# =============================================================================

class BaseStorageBackend(ABC):
    """存储后端抽象基类"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.metadata_cache = {}
        self._lock = threading.RLock()
    
    @abstractmethod
    def store(self, key: str, data: Any) -> bool:
        """存储数据"""
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """检索数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        pass
    
    @abstractmethod
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """获取元数据"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理资源"""
        pass

# =============================================================================
# 文件系统存储后端
# =============================================================================

class FileSystemBackend(BaseStorageBackend):
    """文件系统存储后端"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.data_dir = self.storage_path / "data"
        self.metadata_dir = self.storage_path / "metadata"
        self.versions_dir = self.storage_path / "versions"
        self.backup_dir = self.storage_path / "backup"
        
        for dir_path in [self.data_dir, self.metadata_dir, self.versions_dir, self.backup_dir]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info(f"📁 文件系统存储后端初始化: {self.storage_path}")
    
    def _get_file_path(self, key: str, directory: Path = None) -> Path:
        """获取文件路径"""
        if directory is None:
            directory = self.data_dir
        
        # 安全的键名处理
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return directory / f"{safe_key}.dat"
    
    def _serialize_data(self, data: Any) -> bytes:
        """序列化数据"""
        if self.config.serialization == SerializationType.JSON:
            serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
        elif self.config.serialization == SerializationType.PICKLE:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            # 默认使用pickle
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        
        # 压缩
        if self.config.compression == CompressionType.GZIP:
            serialized = gzip.compress(serialized, compresslevel=self.config.compression_level)
        
        return serialized
    
    def _deserialize_data(self, data: bytes) -> Any:
        """反序列化数据"""
        # 解压缩
        if self.config.compression == CompressionType.GZIP:
            try:
                data = gzip.decompress(data)
            except gzip.BadGzipFile:
                # 可能是未压缩的旧数据
                pass
        
        # 反序列化
        if self.config.serialization == SerializationType.JSON:
            return json.loads(data.decode('utf-8'))
        elif self.config.serialization == SerializationType.PICKLE:
            return pickle.loads(data)
        else:
            return pickle.loads(data)
    
    def _calculate_checksum(self, data: bytes) -> str:
        """计算校验和"""
        return hashlib.sha256(data).hexdigest()
    
    def store(self, key: str, data: Any) -> bool:
        """存储数据"""
        try:
            with self._lock:
                # 序列化数据
                serialized_data = self._serialize_data(data)
                
                # 获取文件路径
                file_path = self._get_file_path(key)
                
                # 版本控制
                if self.config.enable_versioning and file_path.exists():
                    self._backup_version(key)
                
                # 写入数据
                with open(file_path, 'wb') as f:
                    f.write(serialized_data)
                
                # 创建元数据
                metadata = StorageMetadata(
                    key=key,
                    size=len(serialized_data),
                    created_at=time.time(),
                    updated_at=time.time(),
                    version=self._get_next_version(key),
                    checksum=self._calculate_checksum(serialized_data),
                    compressed=self.config.compression != CompressionType.NONE,
                    encrypted=self.config.enable_encryption
                )
                
                # 保存元数据
                self._save_metadata(key, metadata)
                
                logger.debug(f"✅ 存储成功: {key} ({len(serialized_data)} bytes)")
                return True
                
        except Exception as e:
            logger.error(f"❌ 存储失败: {key} - {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索数据"""
        try:
            with self._lock:
                file_path = self._get_file_path(key)
                
                if not file_path.exists():
                    return None
                
                # 读取数据
                with open(file_path, 'rb') as f:
                    serialized_data = f.read()
                
                # 验证校验和
                metadata = self.get_metadata(key)
                if metadata:
                    current_checksum = self._calculate_checksum(serialized_data)
                    if current_checksum != metadata.checksum:
                        logger.warning(f"⚠️ 校验和不匹配: {key}")
                
                # 反序列化
                data = self._deserialize_data(serialized_data)
                
                # 更新访问统计
                if metadata:
                    metadata.access_count += 1
                    metadata.last_accessed = time.time()
                    self._save_metadata(key, metadata)
                
                logger.debug(f"✅ 检索成功: {key}")
                return data
                
        except Exception as e:
            logger.error(f"❌ 检索失败: {key} - {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除数据"""
        try:
            with self._lock:
                file_path = self._get_file_path(key)
                metadata_path = self._get_file_path(key, self.metadata_dir)
                
                # 删除数据文件
                if file_path.exists():
                    file_path.unlink()
                
                # 删除元数据文件
                if metadata_path.exists():
                    metadata_path.unlink()
                
                # 清理版本文件
                if self.config.enable_versioning:
                    self._cleanup_versions(key)
                
                logger.debug(f"✅ 删除成功: {key}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 删除失败: {key} - {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        keys = []
        try:
            for metadata_file in self.metadata_dir.glob("*.dat"):
                try:
                    metadata = self._load_metadata_from_file(metadata_file)
                    if metadata and metadata.key.startswith(prefix):
                        keys.append(metadata.key)
                except:
                    continue
        except Exception as e:
            logger.error(f"❌ 列出键失败: {e}")
        
        return keys
    
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """获取元数据"""
        metadata_path = self._get_file_path(key, self.metadata_dir)
        
        if not metadata_path.exists():
            return None
        
        return self._load_metadata_from_file(metadata_path)
    
    def _save_metadata(self, key: str, metadata: StorageMetadata):
        """保存元数据"""
        metadata_path = self._get_file_path(key, self.metadata_dir)
        
        try:
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
        except Exception as e:
            logger.error(f"❌ 保存元数据失败: {key} - {e}")
    
    def _load_metadata_from_file(self, metadata_path: Path) -> Optional[StorageMetadata]:
        """从文件加载元数据"""
        try:
            with open(metadata_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"❌ 加载元数据失败: {metadata_path} - {e}")
            return None
    
    def _get_next_version(self, key: str) -> int:
        """获取下一个版本号"""
        metadata = self.get_metadata(key)
        return (metadata.version + 1) if metadata else 1
    
    def _backup_version(self, key: str):
        """备份版本"""
        if not self.config.enable_versioning:
            return
        
        try:
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return
            
            metadata = self.get_metadata(key)
            if not metadata:
                return
            
            # 创建版本文件名
            version_filename = f"{hashlib.md5(key.encode()).hexdigest()}_v{metadata.version}.dat"
            version_path = self.versions_dir / version_filename
            
            # 复制当前文件到版本目录
            shutil.copy2(file_path, version_path)
            
            # 清理旧版本
            self._cleanup_old_versions(key)
            
        except Exception as e:
            logger.error(f"❌ 备份版本失败: {key} - {e}")
    
    def _cleanup_old_versions(self, key: str):
        """清理旧版本"""
        if not self.config.enable_versioning:
            return
        
        try:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            version_files = list(self.versions_dir.glob(f"{key_hash}_v*.dat"))
            
            # 按版本号排序
            version_files.sort(key=lambda x: int(x.stem.split('_v')[1]))
            
            # 删除超出限制的版本
            while len(version_files) > self.config.max_versions:
                old_version = version_files.pop(0)
                old_version.unlink()
                
        except Exception as e:
            logger.error(f"❌ 清理旧版本失败: {key} - {e}")
    
    def _cleanup_versions(self, key: str):
        """清理所有版本"""
        try:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            version_files = list(self.versions_dir.glob(f"{key_hash}_v*.dat"))
            
            for version_file in version_files:
                version_file.unlink()
                
        except Exception as e:
            logger.error(f"❌ 清理版本失败: {key} - {e}")
    
    def cleanup(self):
        """清理资源"""
        logger.info("📁 文件系统存储后端清理完成")

# =============================================================================
# SQLite存储后端
# =============================================================================

class SQLiteBackend(BaseStorageBackend):
    """SQLite存储后端"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.db_path = Path(config.storage_path) / "neogenesis.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        logger.info(f"🗄️ SQLite存储后端初始化: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS storage_data (
                    key TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    size INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    checksum TEXT NOT NULL,
                    compressed BOOLEAN DEFAULT FALSE,
                    encrypted BOOLEAN DEFAULT FALSE,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_storage_data_updated_at 
                ON storage_data(updated_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_storage_data_last_accessed 
                ON storage_data(last_accessed)
            """)
            
            conn.commit()
    
    def _serialize_data(self, data: Any) -> bytes:
        """序列化数据"""
        if self.config.serialization == SerializationType.JSON:
            serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
        else:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        
        if self.config.compression == CompressionType.GZIP:
            serialized = gzip.compress(serialized, compresslevel=self.config.compression_level)
        
        return serialized
    
    def _deserialize_data(self, data: bytes) -> Any:
        """反序列化数据"""
        if self.config.compression == CompressionType.GZIP:
            try:
                data = gzip.decompress(data)
            except gzip.BadGzipFile:
                pass
        
        if self.config.serialization == SerializationType.JSON:
            return json.loads(data.decode('utf-8'))
        else:
            return pickle.loads(data)
    
    def _calculate_checksum(self, data: bytes) -> str:
        """计算校验和"""
        return hashlib.sha256(data).hexdigest()
    
    def store(self, key: str, data: Any) -> bool:
        """存储数据"""
        try:
            with self._lock:
                serialized_data = self._serialize_data(data)
                checksum = self._calculate_checksum(serialized_data)
                current_time = time.time()
                
                with sqlite3.connect(self.db_path) as conn:
                    # 检查是否已存在
                    cursor = conn.execute("SELECT version FROM storage_data WHERE key = ?", (key,))
                    existing = cursor.fetchone()
                    version = (existing[0] + 1) if existing else 1
                    
                    # 插入或更新
                    conn.execute("""
                        INSERT OR REPLACE INTO storage_data 
                        (key, data, size, created_at, updated_at, version, checksum, 
                         compressed, encrypted, access_count, last_accessed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """, (
                        key, serialized_data, len(serialized_data),
                        current_time if not existing else None,
                        current_time, version, checksum,
                        self.config.compression != CompressionType.NONE,
                        self.config.enable_encryption, current_time
                    ))
                    
                    conn.commit()
                
                logger.debug(f"✅ SQLite存储成功: {key}")
                return True
                
        except Exception as e:
            logger.error(f"❌ SQLite存储失败: {key} - {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索数据"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT data, checksum FROM storage_data WHERE key = ?
                    """, (key,))
                    
                    result = cursor.fetchone()
                    if not result:
                        return None
                    
                    data_blob, stored_checksum = result
                    
                    # 验证校验和
                    current_checksum = self._calculate_checksum(data_blob)
                    if current_checksum != stored_checksum:
                        logger.warning(f"⚠️ SQLite校验和不匹配: {key}")
                    
                    # 更新访问统计
                    conn.execute("""
                        UPDATE storage_data 
                        SET access_count = access_count + 1, last_accessed = ?
                        WHERE key = ?
                    """, (time.time(), key))
                    conn.commit()
                    
                    # 反序列化
                    data = self._deserialize_data(data_blob)
                    
                    logger.debug(f"✅ SQLite检索成功: {key}")
                    return data
                    
        except Exception as e:
            logger.error(f"❌ SQLite检索失败: {key} - {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除数据"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM storage_data WHERE key = ?", (key,))
                    conn.commit()
                
                logger.debug(f"✅ SQLite删除成功: {key}")
                return True
                
        except Exception as e:
            logger.error(f"❌ SQLite删除失败: {key} - {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT 1 FROM storage_data WHERE key = ? LIMIT 1", (key,))
                return cursor.fetchone() is not None
        except:
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if prefix:
                    cursor = conn.execute("SELECT key FROM storage_data WHERE key LIKE ?", (f"{prefix}%",))
                else:
                    cursor = conn.execute("SELECT key FROM storage_data")
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ SQLite列出键失败: {e}")
            return []
    
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """获取元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT size, created_at, updated_at, version, checksum, 
                           compressed, encrypted, access_count, last_accessed
                    FROM storage_data WHERE key = ?
                """, (key,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return StorageMetadata(
                    key=key,
                    size=result[0],
                    created_at=result[1],
                    updated_at=result[2],
                    version=result[3],
                    checksum=result[4],
                    compressed=bool(result[5]),
                    encrypted=bool(result[6]),
                    access_count=result[7],
                    last_accessed=result[8]
                )
                
        except Exception as e:
            logger.error(f"❌ SQLite获取元数据失败: {key} - {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        logger.info("🗄️ SQLite存储后端清理完成")

# =============================================================================
# LMDB存储后端
# =============================================================================

class LMDBBackend(BaseStorageBackend):
    """LMDB存储后端"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        
        if not LMDB_AVAILABLE:
            raise ImportError("LMDB 模块未安装。请运行: pip install lmdb")
        
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # LMDB环境配置
        self.env_path = self.storage_path / "lmdb_data"
        self.env_path.mkdir(exist_ok=True)
        
        # 初始化LMDB环境
        self.env = lmdb.open(
            str(self.env_path),
            map_size=1024 * 1024 * 1024 * 10,  # 10GB max size
            subdir=True,
            readonly=False,
            create=True,
            max_dbs=2  # 数据库和元数据
        )
        
        # 创建数据库
        with self.env.begin(write=True) as txn:
            self.data_db = self.env.open_db(b'data', txn=txn, create=True)
            self.metadata_db = self.env.open_db(b'metadata', txn=txn, create=True)
        
        logger.info(f"⚡ LMDB存储后端初始化: {self.env_path}")
    
    def _serialize_data(self, data: Any) -> bytes:
        """序列化数据"""
        if self.config.serialization == SerializationType.JSON:
            serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
        else:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        
        if self.config.compression == CompressionType.GZIP:
            serialized = gzip.compress(serialized, compresslevel=self.config.compression_level)
        
        return serialized
    
    def _deserialize_data(self, data: bytes) -> Any:
        """反序列化数据"""
        if self.config.compression == CompressionType.GZIP:
            try:
                data = gzip.decompress(data)
            except gzip.BadGzipFile:
                pass
        
        if self.config.serialization == SerializationType.JSON:
            return json.loads(data.decode('utf-8'))
        else:
            return pickle.loads(data)
    
    def _calculate_checksum(self, data: bytes) -> str:
        """计算校验和"""
        return hashlib.sha256(data).hexdigest()
    
    def store(self, key: str, data: Any) -> bool:
        """存储数据"""
        try:
            with self._lock:
                serialized_data = self._serialize_data(data)
                checksum = self._calculate_checksum(serialized_data)
                current_time = time.time()
                key_bytes = key.encode('utf-8')
                
                with self.env.begin(write=True) as txn:
                    # 检查是否已存在
                    existing_metadata = txn.get(key_bytes, db=self.metadata_db)
                    version = 1
                    created_at = current_time
                    
                    if existing_metadata:
                        try:
                            old_metadata = pickle.loads(existing_metadata)
                            version = old_metadata.version + 1
                            created_at = old_metadata.created_at
                        except:
                            pass
                    
                    # 存储数据
                    txn.put(key_bytes, serialized_data, db=self.data_db)
                    
                    # 创建并存储元数据
                    metadata = StorageMetadata(
                        key=key,
                        size=len(serialized_data),
                        created_at=created_at,
                        updated_at=current_time,
                        version=version,
                        checksum=checksum,
                        compressed=self.config.compression != CompressionType.NONE,
                        encrypted=self.config.enable_encryption,
                        access_count=0,
                        last_accessed=current_time
                    )
                    
                    metadata_bytes = pickle.dumps(metadata)
                    txn.put(key_bytes, metadata_bytes, db=self.metadata_db)
                
                logger.debug(f"✅ LMDB存储成功: {key}")
                return True
                
        except Exception as e:
            logger.error(f"❌ LMDB存储失败: {key} - {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索数据"""
        try:
            with self._lock:
                key_bytes = key.encode('utf-8')
                
                with self.env.begin(write=True) as txn:
                    # 获取数据
                    data_bytes = txn.get(key_bytes, db=self.data_db)
                    if data_bytes is None:
                        return None
                    
                    # 获取并更新元数据
                    metadata_bytes = txn.get(key_bytes, db=self.metadata_db)
                    if metadata_bytes:
                        try:
                            metadata = pickle.loads(metadata_bytes)
                            
                            # 验证校验和
                            current_checksum = self._calculate_checksum(data_bytes)
                            if current_checksum != metadata.checksum:
                                logger.warning(f"⚠️ LMDB校验和不匹配: {key}")
                            
                            # 更新访问统计
                            metadata.access_count += 1
                            metadata.last_accessed = time.time()
                            
                            # 保存更新的元数据
                            updated_metadata_bytes = pickle.dumps(metadata)
                            txn.put(key_bytes, updated_metadata_bytes, db=self.metadata_db)
                        except:
                            pass
                    
                    # 反序列化数据
                    data = self._deserialize_data(data_bytes)
                    
                    logger.debug(f"✅ LMDB检索成功: {key}")
                    return data
                    
        except Exception as e:
            logger.error(f"❌ LMDB检索失败: {key} - {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除数据"""
        try:
            with self._lock:
                key_bytes = key.encode('utf-8')
                
                with self.env.begin(write=True) as txn:
                    # 删除数据和元数据
                    data_deleted = txn.delete(key_bytes, db=self.data_db)
                    metadata_deleted = txn.delete(key_bytes, db=self.metadata_db)
                    
                    if data_deleted or metadata_deleted:
                        logger.debug(f"✅ LMDB删除成功: {key}")
                        return True
                    else:
                        return False
                        
        except Exception as e:
            logger.error(f"❌ LMDB删除失败: {key} - {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            key_bytes = key.encode('utf-8')
            with self.env.begin() as txn:
                return txn.get(key_bytes, db=self.data_db) is not None
        except:
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        keys = []
        try:
            prefix_bytes = prefix.encode('utf-8') if prefix else b''
            
            with self.env.begin() as txn:
                cursor = txn.cursor(db=self.data_db)
                
                if prefix_bytes:
                    # 从前缀开始遍历
                    if cursor.set_range(prefix_bytes):
                        for key_bytes, _ in cursor:
                            if key_bytes.startswith(prefix_bytes):
                                keys.append(key_bytes.decode('utf-8'))
                            else:
                                break
                else:
                    # 遍历所有键
                    for key_bytes, _ in cursor:
                        keys.append(key_bytes.decode('utf-8'))
                        
        except Exception as e:
            logger.error(f"❌ LMDB列出键失败: {e}")
            
        return keys
    
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """获取元数据"""
        try:
            key_bytes = key.encode('utf-8')
            
            with self.env.begin() as txn:
                metadata_bytes = txn.get(key_bytes, db=self.metadata_db)
                if metadata_bytes:
                    return pickle.loads(metadata_bytes)
                return None
                
        except Exception as e:
            logger.error(f"❌ LMDB获取元数据失败: {key} - {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'env') and self.env:
                self.env.close()
                logger.info("⚡ LMDB存储后端清理完成")
        except Exception as e:
            logger.error(f"❌ LMDB清理失败: {e}")

# =============================================================================
# 内存存储后端
# =============================================================================

class MemoryBackend(BaseStorageBackend):
    """内存存储后端（用于测试和缓存）"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.data_store = {}
        self.metadata_store = {}
        logger.info("💾 内存存储后端初始化")
    
    def store(self, key: str, data: Any) -> bool:
        """存储数据"""
        try:
            with self._lock:
                import copy
                
                # 深拷贝以避免引用问题
                stored_data = copy.deepcopy(data)
                self.data_store[key] = stored_data
                
                # 创建元数据
                metadata = StorageMetadata(
                    key=key,
                    size=len(str(data)),  # 简化的大小计算
                    created_at=time.time(),
                    updated_at=time.time(),
                    version=self.metadata_store.get(key, StorageMetadata(key, 0, 0, 0, 0, "")).version + 1,
                    checksum=hashlib.md5(str(data).encode()).hexdigest()
                )
                
                self.metadata_store[key] = metadata
                
                logger.debug(f"✅ 内存存储成功: {key}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 内存存储失败: {key} - {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索数据"""
        try:
            with self._lock:
                if key not in self.data_store:
                    return None
                
                # 更新访问统计
                if key in self.metadata_store:
                    metadata = self.metadata_store[key]
                    metadata.access_count += 1
                    metadata.last_accessed = time.time()
                
                import copy
                return copy.deepcopy(self.data_store[key])
                
        except Exception as e:
            logger.error(f"❌ 内存检索失败: {key} - {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除数据"""
        try:
            with self._lock:
                if key in self.data_store:
                    del self.data_store[key]
                
                if key in self.metadata_store:
                    del self.metadata_store[key]
                
                return True
                
        except Exception as e:
            logger.error(f"❌ 内存删除失败: {key} - {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self.data_store
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        if prefix:
            return [key for key in self.data_store.keys() if key.startswith(prefix)]
        return list(self.data_store.keys())
    
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """获取元数据"""
        return self.metadata_store.get(key)
    
    def cleanup(self):
        """清理资源"""
        with self._lock:
            self.data_store.clear()
            self.metadata_store.clear()
        logger.info("💾 内存存储后端清理完成")

# =============================================================================
# 存储引擎工厂
# =============================================================================

class PersistentStorageEngine:
    """持久化存储引擎"""
    
    def __init__(self, config: StorageConfig = None):
        """
        初始化存储引擎
        
        Args:
            config: 存储配置
        """
        self.config = config or StorageConfig()
        self.backend = self._create_backend()
        
        logger.info(f"🚀 持久化存储引擎初始化: {self.config.backend.value}")
    
    def _create_backend(self) -> BaseStorageBackend:
        """创建存储后端"""
        if self.config.backend == StorageBackend.FILE_SYSTEM:
            return FileSystemBackend(self.config)
        elif self.config.backend == StorageBackend.SQLITE:
            return SQLiteBackend(self.config)
        elif self.config.backend == StorageBackend.LMDB:
            return LMDBBackend(self.config)
        elif self.config.backend == StorageBackend.MEMORY:
            return MemoryBackend(self.config)
        else:
            logger.warning(f"⚠️ 不支持的存储后端: {self.config.backend}，使用文件系统")
            return FileSystemBackend(self.config)
    
    def store(self, key: str, data: Any) -> bool:
        """存储数据"""
        return self.backend.store(key, data)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索数据"""
        return self.backend.retrieve(key)
    
    def delete(self, key: str) -> bool:
        """删除数据"""
        return self.backend.delete(key)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.backend.exists(key)
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        return self.backend.list_keys(prefix)
    
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """获取元数据"""
        return self.backend.get_metadata(key)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        keys = self.list_keys()
        total_size = 0
        total_access_count = 0
        
        for key in keys[:100]:  # 限制统计数量
            metadata = self.get_metadata(key)
            if metadata:
                total_size += metadata.size
                total_access_count += metadata.access_count
        
        return {
            "backend_type": self.config.backend.value,
            "total_keys": len(keys),
            "total_size_bytes": total_size,
            "total_access_count": total_access_count,
            "compression_enabled": self.config.compression != CompressionType.NONE,
            "versioning_enabled": self.config.enable_versioning
        }
    
    def cleanup(self):
        """清理资源"""
        self.backend.cleanup()

# =============================================================================
# 工厂函数
# =============================================================================

def create_storage_engine(
    backend_type: str = "file_system",
    storage_path: str = "./neogenesis_storage",
    **kwargs
) -> PersistentStorageEngine:
    """
    创建存储引擎
    
    Args:
        backend_type: 后端类型
        storage_path: 存储路径
        **kwargs: 其他配置参数
        
    Returns:
        存储引擎实例
    """
    config = StorageConfig(
        backend=StorageBackend(backend_type),
        storage_path=storage_path,
        **kwargs
    )
    
    return PersistentStorageEngine(config)

# =============================================================================
# 测试和演示
# =============================================================================

if __name__ == "__main__":
    # 测试持久化存储引擎
    print("🧪 测试持久化存储引擎...")
    
    # 测试文件系统后端
    print("\n📁 测试文件系统后端:")
    fs_engine = create_storage_engine("file_system", "./test_storage")
    
    # 存储测试数据
    test_data = {"message": "Hello, Neogenesis!", "timestamp": time.time()}
    success = fs_engine.store("test_key", test_data)
    print(f"✅ 存储{'成功' if success else '失败'}")
    
    # 检索测试数据
    retrieved_data = fs_engine.retrieve("test_key")
    print(f"✅ 检索{'成功' if retrieved_data else '失败'}: {retrieved_data}")
    
    # 获取元数据
    metadata = fs_engine.get_metadata("test_key")
    if metadata:
        print(f"✅ 元数据: 大小={metadata.size}, 版本={metadata.version}")
    
    # 获取统计信息
    stats = fs_engine.get_storage_stats()
    print(f"✅ 存储统计: {stats}")
    
    # 测试SQLite后端
    print("\n🗄️ 测试SQLite后端:")
    sqlite_engine = create_storage_engine("sqlite", "./test_storage_sqlite")
    
    success = sqlite_engine.store("sqlite_test", {"data": "SQLite测试数据"})
    print(f"✅ SQLite存储{'成功' if success else '失败'}")
    
    sqlite_data = sqlite_engine.retrieve("sqlite_test")
    print(f"✅ SQLite检索{'成功' if sqlite_data else '失败'}: {sqlite_data}")
    
    # 测试LMDB后端
    print("\n⚡ 测试LMDB后端:")
    if LMDB_AVAILABLE:
        try:
            lmdb_engine = create_storage_engine("lmdb", "./test_storage_lmdb")
            
            success = lmdb_engine.store("lmdb_test", {"data": "LMDB测试数据", "performance": "高性能"})
            print(f"✅ LMDB存储{'成功' if success else '失败'}")
            
            lmdb_data = lmdb_engine.retrieve("lmdb_test")
            print(f"✅ LMDB检索{'成功' if lmdb_data else '失败'}: {lmdb_data}")
            
            # 测试批量操作
            for i in range(5):
                lmdb_engine.store(f"batch_test_{i}", {"index": i, "value": f"测试数据{i}"})
            
            keys = lmdb_engine.list_keys("batch_test_")
            print(f"✅ LMDB批量测试: 找到 {len(keys)} 个键")
            
            lmdb_engine.cleanup()
        except ImportError:
            print("❌ LMDB模块未安装，跳过LMDB测试")
    else:
        print("❌ LMDB不可用，跳过LMDB测试")
    
    # 清理
    fs_engine.cleanup()
    sqlite_engine.cleanup()
    
    print("✅ 持久化存储引擎测试完成")
