#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态思维路径库 - Dynamic Reasoning Path Library
可成长的"大脑皮层"，支持持久化存储和动态扩展

这个模块实现了从静态模板到动态路径库的升级：
1. 持久化存储：支持JSON文件和SQLite数据库存储
2. 动态管理：可以在运行时添加、修改、删除思维路径
3. 版本控制：支持路径版本管理和演化追踪
4. 性能分析：跟踪每个路径的使用效果和成功率
5. 智能推荐：基于历史表现推荐最佳路径

核心理念：让AI的思维模式能够持续学习和进化
"""

import os
import json
import time
import sqlite3
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
from pathlib import Path
from collections import defaultdict
import threading

from .data_structures import ReasoningPath

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """存储后端类型"""
    JSON = "json"
    SQLITE = "sqlite"
    MEMORY = "memory"  # 内存模式，用于测试


class PathCategory(Enum):
    """路径分类"""
    ANALYTICAL = "analytical"           # 分析型
    CREATIVE = "creative"              # 创造型
    CRITICAL = "critical"              # 批判型
    PRACTICAL = "practical"           # 实用型
    COLLABORATIVE = "collaborative"    # 协作型
    ADAPTIVE = "adaptive"             # 适应型
    SYSTEMATIC = "systematic"         # 系统型
    INTUITIVE = "intuitive"           # 直觉型
    STRATEGIC = "strategic"           # 战略型
    EXPERIMENTAL = "experimental"     # 实验型


class PathStatus(Enum):
    """路径状态"""
    ACTIVE = "active"                 # 激活状态
    DEPRECATED = "deprecated"         # 已废弃
    EXPERIMENTAL = "experimental"     # 实验性
    RETIRED = "retired"              # 已退役


@dataclass
class PathMetadata:
    """路径元数据"""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: str = "1.0.0"
    author: str = "system"
    category: PathCategory = PathCategory.ANALYTICAL
    status: PathStatus = PathStatus.ACTIVE
    
    # 使用统计
    usage_count: int = 0
    success_rate: float = 0.0
    average_rating: float = 0.0
    total_execution_time: float = 0.0
    
    # 标签和描述
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    complexity_level: str = "medium"  # "low", "medium", "high"
    
    # 关联信息
    parent_path_id: Optional[str] = None
    derived_from: List[str] = field(default_factory=list)
    similar_paths: List[str] = field(default_factory=list)


@dataclass
class EnhancedReasoningPath:
    """增强版思维路径，包含完整元数据"""
    # 基本信息（继承自ReasoningPath）
    path_id: str
    path_type: str
    description: str
    prompt_template: str
    strategy_id: str = ""
    instance_id: str = ""
    
    # 增强元数据
    metadata: PathMetadata = field(default_factory=PathMetadata)
    
    # 动态属性
    is_learned: bool = False  # 是否为学习得到的路径
    learning_source: str = ""  # 学习来源
    effectiveness_score: float = 0.5  # 效果评分
    
    def to_reasoning_path(self) -> ReasoningPath:
        """转换为标准ReasoningPath对象"""
        return ReasoningPath(
            path_id=self.path_id,
            path_type=self.path_type,
            description=self.description,
            prompt_template=self.prompt_template,
            strategy_id=self.strategy_id,
            instance_id=self.instance_id
        )
    
    def update_usage_stats(self, success: bool, execution_time: float, rating: Optional[float] = None):
        """更新使用统计"""
        self.metadata.usage_count += 1
        
        # 更新成功率
        if success:
            total_successes = self.metadata.success_rate * (self.metadata.usage_count - 1) + 1
        else:
            total_successes = self.metadata.success_rate * (self.metadata.usage_count - 1)
        
        self.metadata.success_rate = total_successes / self.metadata.usage_count
        
        # 更新执行时间
        self.metadata.total_execution_time += execution_time
        
        # 更新评分
        if rating is not None:
            if self.metadata.usage_count == 1:
                self.metadata.average_rating = rating
            else:
                total_rating = self.metadata.average_rating * (self.metadata.usage_count - 1) + rating
                self.metadata.average_rating = total_rating / self.metadata.usage_count
        
        # 更新时间戳
        self.metadata.updated_at = time.time()


class DynamicPathLibrary:
    """
    🧠 动态思维路径库 - 可成长的"大脑皮层"
    
    核心功能：
    1. 持久化存储管理 - 支持JSON和SQLite后端
    2. 动态路径管理 - 运行时增删改查路径
    3. 版本控制系统 - 追踪路径演化历史
    4. 性能分析跟踪 - 监控路径使用效果
    5. 智能推荐系统 - 基于历史推荐最佳路径
    
    设计原则：
    - 向后兼容：支持现有静态模板的无缝迁移
    - 高性能：内存缓存+延迟写入优化
    - 线程安全：支持多线程并发访问
    - 扩展性：支持自定义存储后端
    """
    
    def __init__(self, 
                 storage_backend: StorageBackend = StorageBackend.JSON,
                 storage_path: str = "data/reasoning_paths",
                 auto_backup: bool = True,
                 cache_size: int = 1000):
        """
        初始化动态路径库
        
        Args:
            storage_backend: 存储后端类型
            storage_path: 存储路径（不含扩展名）
            auto_backup: 是否自动备份
            cache_size: 内存缓存大小
        """
        self.storage_backend = storage_backend
        self.storage_path = storage_path
        self.auto_backup = auto_backup
        self.cache_size = cache_size
        
        # 确保存储目录存在
        self.storage_dir = Path(storage_path).parent
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._cache: Dict[str, EnhancedReasoningPath] = {}
        self._cache_lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            "total_paths": 0,
            "active_paths": 0,
            "learned_paths": 0,
            "total_usages": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # 初始化存储
        self._init_storage()
        self._load_all_paths()
        
        logger.info("🧠 动态思维路径库已初始化")
        logger.info(f"   存储后端: {storage_backend.value}")
        logger.info(f"   存储路径: {storage_path}")
        logger.info(f"   缓存大小: {cache_size}")
        logger.info(f"   已加载路径: {len(self._cache)}")
    
    def _init_storage(self):
        """初始化存储后端"""
        if self.storage_backend == StorageBackend.SQLITE:
            self._init_sqlite_storage()
        elif self.storage_backend == StorageBackend.JSON:
            self._init_json_storage()
        # MEMORY模式不需要初始化
    
    def _init_sqlite_storage(self):
        """初始化SQLite存储"""
        self.db_path = f"{self.storage_path}.db"
        
        with self._get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reasoning_paths (
                    path_id TEXT PRIMARY KEY,
                    path_type TEXT NOT NULL,
                    description TEXT,
                    prompt_template TEXT NOT NULL,
                    strategy_id TEXT,
                    instance_id TEXT,
                    metadata TEXT,  -- JSON格式的元数据
                    is_learned BOOLEAN DEFAULT FALSE,
                    learning_source TEXT,
                    effectiveness_score REAL DEFAULT 0.5,
                    created_at REAL DEFAULT (datetime('now')),
                    updated_at REAL DEFAULT (datetime('now'))
                )
            ''')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_strategy_id ON reasoning_paths(strategy_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_path_type ON reasoning_paths(path_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON reasoning_paths(created_at)')
            
            conn.commit()
        
        logger.info(f"✅ SQLite存储已初始化: {self.db_path}")
    
    def _init_json_storage(self):
        """初始化JSON存储"""
        self.json_path = f"{self.storage_path}.json"
        
        if not Path(self.json_path).exists():
            # 创建空的JSON文件
            empty_library = {
                "metadata": {
                    "version": "1.0.0",
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "total_paths": 0
                },
                "paths": {}
            }
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(empty_library, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON存储已初始化: {self.json_path}")
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        if self.storage_backend != StorageBackend.SQLITE:
            raise ValueError("只有SQLite后端支持数据库连接")
        
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()
    
    def _load_all_paths(self):
        """从存储后端加载所有路径到内存缓存"""
        if self.storage_backend == StorageBackend.MEMORY:
            return  # 内存模式不需要加载
        
        try:
            if self.storage_backend == StorageBackend.SQLITE:
                self._load_from_sqlite()
            elif self.storage_backend == StorageBackend.JSON:
                self._load_from_json()
            
            # 更新统计信息
            self._update_stats()
            
            logger.info(f"📚 已加载 {len(self._cache)} 个思维路径")
            
        except Exception as e:
            logger.error(f"❌ 加载思维路径失败: {e}")
    
    def _load_from_sqlite(self):
        """从SQLite加载路径"""
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM reasoning_paths 
                WHERE metadata->>'$.status' != 'retired'
                ORDER BY created_at DESC
            ''')
            
            for row in cursor:
                try:
                    # 解析元数据
                    metadata_dict = json.loads(row['metadata']) if row['metadata'] else {}
                    metadata = PathMetadata(**metadata_dict)
                    
                    # 创建增强路径对象
                    enhanced_path = EnhancedReasoningPath(
                        path_id=row['path_id'],
                        path_type=row['path_type'],
                        description=row['description'] or "",
                        prompt_template=row['prompt_template'],
                        strategy_id=row['strategy_id'] or "",
                        instance_id=row['instance_id'] or "",
                        metadata=metadata,
                        is_learned=bool(row['is_learned']),
                        learning_source=row['learning_source'] or "",
                        effectiveness_score=row['effectiveness_score'] or 0.5
                    )
                    
                    self._cache[row['path_id']] = enhanced_path
                    
                except Exception as e:
                    logger.warning(f"⚠️ 跳过损坏的路径记录 {row['path_id']}: {e}")
    
    def _load_from_json(self):
        """从JSON文件加载路径"""
        try:
            # 检查文件是否存在且不为空
            json_path_obj = Path(self.json_path)
            if not json_path_obj.exists() or json_path_obj.stat().st_size == 0:
                logger.info(f"📝 JSON文件 '{self.json_path}' 不存在或为空，跳过加载。")
                return

            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            paths_data = data.get('paths', {})
            
            for path_id, path_data in paths_data.items():
                try:
                    # 解析元数据
                    metadata_dict = path_data.get('metadata', {})
                    metadata = PathMetadata(**metadata_dict)
                    
                    # 创建增强路径对象
                    enhanced_path = EnhancedReasoningPath(
                        path_id=path_id,
                        path_type=path_data.get('path_type', ''),
                        description=path_data.get('description', ''),
                        prompt_template=path_data.get('prompt_template', ''),
                        strategy_id=path_data.get('strategy_id', ''),
                        instance_id=path_data.get('instance_id', ''),
                        metadata=metadata,
                        is_learned=path_data.get('is_learned', False),
                        learning_source=path_data.get('learning_source', ''),
                        effectiveness_score=path_data.get('effectiveness_score', 0.5)
                    )
                    
                    self._cache[path_id] = enhanced_path
                    
                except Exception as e:
                    logger.warning(f"⚠️ 跳过损坏的路径记录 {path_id}: {e}")
        
        except FileNotFoundError:
            logger.info(f"📝 JSON文件 '{self.json_path}' 不存在，创建新的空库。")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON文件 '{self.json_path}' 格式错误或为空: {e}")
            # 这里可以选择性地备份损坏的文件并重新初始化
            # os.rename(self.json_path, f"{self.json_path}.broken.{int(time.time())}")
            # self._init_json_storage()
    
    def add_path(self, path: Union[ReasoningPath, EnhancedReasoningPath]) -> bool:
        """
        添加新的思维路径
        
        Args:
            path: 要添加的路径对象
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 转换为增强路径对象
            if isinstance(path, ReasoningPath):
                enhanced_path = EnhancedReasoningPath(
                    path_id=path.path_id,
                    path_type=path.path_type,
                    description=path.description,
                    prompt_template=path.prompt_template,
                    strategy_id=path.strategy_id,
                    instance_id=path.instance_id,
                    metadata=PathMetadata(
                        created_at=time.time(),
                        author="path_generator"
                    )
                )
            else:
                enhanced_path = path
            
            # 检查是否已存在
            if enhanced_path.path_id in self._cache:
                logger.warning(f"⚠️ 路径已存在，跳过添加: {enhanced_path.path_id}")
                return False
            
            # 添加到缓存
            with self._cache_lock:
                self._cache[enhanced_path.path_id] = enhanced_path
            
            # 持久化存储
            self._persist_path(enhanced_path)
            
            # 更新统计
            self.stats["total_paths"] += 1
            if enhanced_path.metadata.status == PathStatus.ACTIVE:
                self.stats["active_paths"] += 1
            if enhanced_path.is_learned:
                self.stats["learned_paths"] += 1
            
            logger.info(f"✅ 新增思维路径: {enhanced_path.path_id}")
            logger.debug(f"   类型: {enhanced_path.path_type}")
            logger.debug(f"   来源: {enhanced_path.learning_source or 'manual'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加思维路径失败: {e}")
            return False
    
    def get_path(self, path_id: str) -> Optional[EnhancedReasoningPath]:
        """
        获取指定的思维路径
        
        Args:
            path_id: 路径ID
            
        Returns:
            路径对象或None
        """
        with self._cache_lock:
            if path_id in self._cache:
                self.stats["cache_hits"] += 1
                return self._cache[path_id]
            else:
                self.stats["cache_misses"] += 1
                return None
    
    def get_all_paths(self, 
                     status: Optional[PathStatus] = None,
                     category: Optional[PathCategory] = None,
                     include_retired: bool = False) -> Dict[str, EnhancedReasoningPath]:
        """
        获取所有满足条件的思维路径
        
        Args:
            status: 过滤状态
            category: 过滤分类
            include_retired: 是否包含已退役的路径
            
        Returns:
            路径字典
        """
        filtered_paths = {}
        
        with self._cache_lock:
            for path_id, path in self._cache.items():
                # 状态过滤
                if not include_retired and path.metadata.status == PathStatus.RETIRED:
                    continue
                
                if status and path.metadata.status != status:
                    continue
                
                if category and path.metadata.category != category:
                    continue
                
                filtered_paths[path_id] = path
        
        return filtered_paths
    
    def get_paths_by_strategy(self, strategy_id: str) -> List[EnhancedReasoningPath]:
        """根据策略ID获取路径"""
        paths = []
        
        with self._cache_lock:
            for path in self._cache.values():
                if path.strategy_id == strategy_id:
                    paths.append(path)
        
        return paths
    
    def update_path_performance(self, 
                               path_id: str, 
                               success: bool, 
                               execution_time: float,
                               rating: Optional[float] = None) -> bool:
        """
        更新路径性能统计
        
        Args:
            path_id: 路径ID
            success: 是否成功
            execution_time: 执行时间
            rating: 用户评分(0-1)
            
        Returns:
            bool: 是否更新成功
        """
        path = self.get_path(path_id)
        if not path:
            logger.warning(f"⚠️ 路径不存在: {path_id}")
            return False
        
        try:
            # 更新统计信息
            path.update_usage_stats(success, execution_time, rating)
            
            # 更新效果评分
            if success:
                # 成功时提升效果评分
                path.effectiveness_score = min(1.0, path.effectiveness_score * 1.05)
            else:
                # 失败时降低效果评分
                path.effectiveness_score = max(0.1, path.effectiveness_score * 0.95)
            
            # 持久化更新
            self._persist_path(path)
            
            # 更新全局统计
            self.stats["total_usages"] += 1
            
            logger.debug(f"📊 更新路径性能: {path_id}")
            logger.debug(f"   成功率: {path.metadata.success_rate:.2%}")
            logger.debug(f"   效果评分: {path.effectiveness_score:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新路径性能失败: {e}")
            return False
    
    def recommend_paths(self, 
                       task_context: Optional[Dict[str, Any]] = None,
                       max_recommendations: int = 5,
                       min_effectiveness: float = 0.3) -> List[EnhancedReasoningPath]:
        """
        基于历史表现推荐最佳路径
        
        Args:
            task_context: 任务上下文信息
            max_recommendations: 最大推荐数量
            min_effectiveness: 最小效果分数
            
        Returns:
            推荐的路径列表
        """
        candidates = []
        
        # 收集候选路径
        with self._cache_lock:
            for path in self._cache.values():
                if (path.metadata.status == PathStatus.ACTIVE and 
                    path.effectiveness_score >= min_effectiveness):
                    candidates.append(path)
        
        # 计算推荐分数
        scored_paths = []
        for path in candidates:
            score = self._calculate_recommendation_score(path, task_context)
            scored_paths.append((score, path))
        
        # 排序并返回前N个
        scored_paths.sort(key=lambda x: x[0], reverse=True)
        recommended_paths = [path for score, path in scored_paths[:max_recommendations]]
        
        logger.info(f"💡 推荐 {len(recommended_paths)} 个最佳路径")
        for i, path in enumerate(recommended_paths, 1):
            logger.debug(f"   {i}. {path.path_type} (效果: {path.effectiveness_score:.2f})")
        
        return recommended_paths
    
    def _calculate_recommendation_score(self, 
                                      path: EnhancedReasoningPath, 
                                      task_context: Optional[Dict[str, Any]]) -> float:
        """计算路径推荐分数"""
        score = 0.0
        
        # 基础效果分数 (40%)
        score += path.effectiveness_score * 0.4
        
        # 成功率 (30%)
        score += path.metadata.success_rate * 0.3
        
        # 使用频次 (15%) - 使用越多，经验越丰富
        usage_factor = min(1.0, path.metadata.usage_count / 100)
        score += usage_factor * 0.15
        
        # 平均评分 (15%)
        score += path.metadata.average_rating * 0.15
        
        # 上下文匹配加成
        if task_context:
            context_boost = self._calculate_context_match(path, task_context)
            score *= (1 + context_boost)
        
        return score
    
    def _calculate_context_match(self, 
                               path: EnhancedReasoningPath, 
                               task_context: Dict[str, Any]) -> float:
        """计算路径与任务上下文的匹配度"""
        match_score = 0.0
        
        # 任务类型匹配
        task_type = task_context.get('task_type', '').lower()
        if task_type in path.metadata.keywords:
            match_score += 0.2
        
        # 复杂度匹配
        task_complexity = task_context.get('complexity', 'medium')
        if task_complexity == path.metadata.complexity_level:
            match_score += 0.1
        
        # 标签匹配
        task_tags = task_context.get('tags', [])
        if task_tags:
            common_tags = set(task_tags).intersection(set(path.metadata.tags))
            if common_tags:
                match_score += len(common_tags) / len(task_tags) * 0.3
        
        return match_score
    
    def learn_from_exploration(self, 
                             exploration_result: Dict[str, Any],
                             source: str = "knowledge_explorer") -> List[str]:
        """
        从知识探索结果中学习新的思维路径
        
        Args:
            exploration_result: 探索结果
            source: 学习来源
            
        Returns:
            新增路径的ID列表
        """
        new_path_ids = []
        
        try:
            # 从探索结果中提取思维种子
            thinking_seeds = exploration_result.get('generated_thinking_seeds', [])
            
            for seed_data in thinking_seeds:
                # 生成新的思维路径
                new_path = self._create_path_from_seed(seed_data, source)
                if new_path and self.add_path(new_path):
                    new_path_ids.append(new_path.path_id)
            
            logger.info(f"🌱 从探索结果学习到 {len(new_path_ids)} 个新路径")
            
        except Exception as e:
            logger.error(f"❌ 从探索结果学习失败: {e}")
        
        return new_path_ids
    
    def _create_path_from_seed(self, 
                             seed_data: Dict[str, Any], 
                             source: str) -> Optional[EnhancedReasoningPath]:
        """从思维种子创建新的路径"""
        try:
            seed_id = seed_data.get('seed_id', '')
            seed_content = seed_data.get('seed_content', '')
            creativity_level = seed_data.get('creativity_level', 'medium')
            
            if not seed_content:
                return None
            
            # 生成路径ID
            path_id = f"learned_{hashlib.md5(seed_content.encode()).hexdigest()[:8]}"
            
            # 确定路径类型和分类
            if creativity_level == 'high':
                path_type = "学习创新型"
                category = PathCategory.CREATIVE
            elif 'cross_domain' in seed_data.get('cross_domain_connections', []):
                path_type = "学习跨域型"
                category = PathCategory.ADAPTIVE
            else:
                path_type = "学习分析型"
                category = PathCategory.ANALYTICAL
            
            # 构建提示模板
            prompt_template = f"""基于学习到的思维模式解决任务：{{task}}

🧠 **学习到的思维路径**：
{seed_content}

💡 **应用策略**：
1. **模式识别**: 识别任务中的关键模式和结构
2. **知识应用**: 应用学习到的思维方式和方法
3. **创新融合**: 结合已有知识进行创新思考
4. **效果验证**: 验证解决方案的有效性和可行性

基于思维种子：{{thinking_seed}}
请应用学习到的思维模式提供解决方案。"""
            
            # 创建元数据
            metadata = PathMetadata(
                created_at=time.time(),
                author=source,
                category=category,
                status=PathStatus.EXPERIMENTAL,  # 新学习的路径先标记为实验性
                tags=["learned", "adaptive", creativity_level],
                keywords=seed_data.get('potential_applications', []),
                complexity_level=creativity_level
            )
            
            # 创建增强路径
            enhanced_path = EnhancedReasoningPath(
                path_id=path_id,
                path_type=path_type,
                description=f"从{source}学习到的思维路径：{seed_content[:100]}...",
                prompt_template=prompt_template,
                strategy_id=f"learned_{creativity_level}",
                instance_id=f"{path_id}_{int(time.time())}",
                metadata=metadata,
                is_learned=True,
                learning_source=source,
                effectiveness_score=0.5  # 初始效果分数
            )
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"❌ 从种子创建路径失败: {e}")
            return None
    
    def _persist_path(self, path: EnhancedReasoningPath):
        """持久化路径到存储后端"""
        if self.storage_backend == StorageBackend.MEMORY:
            return  # 内存模式不持久化
        
        try:
            if self.storage_backend == StorageBackend.SQLITE:
                self._persist_to_sqlite(path)
            elif self.storage_backend == StorageBackend.JSON:
                self._persist_to_json(path)
        
        except Exception as e:
            logger.error(f"❌ 持久化路径失败 {path.path_id}: {e}")
    
    def _persist_to_sqlite(self, path: EnhancedReasoningPath):
        """持久化到SQLite数据库"""
        with self._get_db_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO reasoning_paths 
                (path_id, path_type, description, prompt_template, strategy_id, instance_id,
                 metadata, is_learned, learning_source, effectiveness_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                path.path_id,
                path.path_type,
                path.description,
                path.prompt_template,
                path.strategy_id,
                path.instance_id,
                json.dumps(asdict(path.metadata), ensure_ascii=False),
                path.is_learned,
                path.learning_source,
                path.effectiveness_score,
                time.time()
            ))
            
            conn.commit()
    
    def _persist_to_json(self, path: EnhancedReasoningPath):
        """持久化到JSON文件"""
        try:
            # 读取现有数据
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新路径数据
            path_data = {
                "path_type": path.path_type,
                "description": path.description,
                "prompt_template": path.prompt_template,
                "strategy_id": path.strategy_id,
                "instance_id": path.instance_id,
                "metadata": asdict(path.metadata),
                "is_learned": path.is_learned,
                "learning_source": path.learning_source,
                "effectiveness_score": path.effectiveness_score
            }
            
            data["paths"][path.path_id] = path_data
            data["metadata"]["updated_at"] = time.time()
            data["metadata"]["total_paths"] = len(data["paths"])
            
            # 写回文件
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"❌ JSON持久化失败: {e}")
    
    def _update_stats(self):
        """更新统计信息"""
        with self._cache_lock:
            self.stats["total_paths"] = len(self._cache)
            self.stats["active_paths"] = sum(1 for path in self._cache.values() 
                                           if path.metadata.status == PathStatus.ACTIVE)
            self.stats["learned_paths"] = sum(1 for path in self._cache.values() 
                                            if path.is_learned)
            self.stats["total_usages"] = sum(path.metadata.usage_count 
                                           for path in self._cache.values())
    
    def migrate_from_templates(self, templates_dict: Dict[str, ReasoningPath]) -> int:
        """
        从静态模板迁移到动态库
        
        Args:
            templates_dict: 静态模板字典
            
        Returns:
            迁移的路径数量
        """
        migrated_count = 0
        
        logger.info("🚚 开始从静态模板迁移...")
        
        for template_id, template in templates_dict.items():
            try:
                # 检查是否已存在
                if template.path_id in self._cache:
                    continue
                
                # 创建增强路径
                enhanced_path = EnhancedReasoningPath(
                    path_id=template.path_id,
                    path_type=template.path_type,
                    description=template.description,
                    prompt_template=template.prompt_template,
                    strategy_id=template.strategy_id or template_id,
                    instance_id=template.instance_id or template.path_id,
                    metadata=PathMetadata(
                        created_at=time.time(),
                        author="legacy_migration",
                        category=self._infer_category_from_type(template.path_type),
                        status=PathStatus.ACTIVE,
                        tags=["legacy", "migrated"],
                        keywords=self._extract_keywords_from_description(template.description)
                    ),
                    is_learned=False,
                    learning_source="static_template",
                    effectiveness_score=0.6  # 给予中等的初始评分
                )
                
                if self.add_path(enhanced_path):
                    migrated_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ 迁移模板失败 {template_id}: {e}")
        
        logger.info(f"✅ 迁移完成: {migrated_count} 个路径")
        return migrated_count
    
    def _infer_category_from_type(self, path_type: str) -> PathCategory:
        """从路径类型推断分类"""
        type_lower = path_type.lower()
        
        if "分析" in type_lower or "系统" in type_lower:
            return PathCategory.ANALYTICAL
        elif "创新" in type_lower or "创造" in type_lower:
            return PathCategory.CREATIVE
        elif "批判" in type_lower or "质疑" in type_lower:
            return PathCategory.CRITICAL
        elif "实用" in type_lower or "务实" in type_lower:
            return PathCategory.PRACTICAL
        elif "协作" in type_lower:
            return PathCategory.COLLABORATIVE
        elif "适应" in type_lower or "灵活" in type_lower:
            return PathCategory.ADAPTIVE
        else:
            return PathCategory.ANALYTICAL  # 默认
    
    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """从描述中提取关键词"""
        # 简单的关键词提取
        import re
        words = re.findall(r'\b[\u4e00-\u9fff]+\b', description)
        return [word for word in words if len(word) > 1][:5]  # 取前5个关键词
    
    def backup(self, backup_path: Optional[str] = None) -> bool:
        """
        备份路径库
        
        Args:
            backup_path: 备份路径，如果为None则自动生成
            
        Returns:
            bool: 备份是否成功
        """
        try:
            if backup_path is None:
                timestamp = int(time.time())
                backup_path = f"{self.storage_path}_backup_{timestamp}"
            
            if self.storage_backend == StorageBackend.JSON:
                import shutil
                shutil.copy2(self.json_path, f"{backup_path}.json")
                logger.info(f"💾 JSON备份完成: {backup_path}.json")
                
            elif self.storage_backend == StorageBackend.SQLITE:
                import shutil
                shutil.copy2(self.db_path, f"{backup_path}.db")
                logger.info(f"💾 SQLite备份完成: {backup_path}.db")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 备份失败: {e}")
            return False
    
    def get_library_stats(self) -> Dict[str, Any]:
        """获取路径库统计信息"""
        self._update_stats()
        
        return {
            **self.stats,
            "storage_backend": self.storage_backend.value,
            "storage_path": self.storage_path,
            "cache_efficiency": (self.stats["cache_hits"] / 
                               max(1, self.stats["cache_hits"] + self.stats["cache_misses"])),
            "top_performers": self._get_top_performing_paths(5),
            "category_distribution": self._get_category_distribution()
        }
    
    def _get_top_performing_paths(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取表现最佳的路径"""
        paths = list(self._cache.values())
        paths.sort(key=lambda p: p.effectiveness_score, reverse=True)
        
        return [
            {
                "path_id": path.path_id,
                "path_type": path.path_type,
                "effectiveness_score": path.effectiveness_score,
                "success_rate": path.metadata.success_rate,
                "usage_count": path.metadata.usage_count
            }
            for path in paths[:limit]
        ]
    
    def _get_category_distribution(self) -> Dict[str, int]:
        """获取分类分布"""
        distribution = defaultdict(int)
        
        for path in self._cache.values():
            distribution[path.metadata.category.value] += 1
        
        return dict(distribution)
