# EmbyBot 多服务器支持改造方案（方案A）

## 文档版本
- **版本**: v1.0
- **日期**: 2025-11-24
- **状态**: 实施方案

---

## 一、方案概述

### 1.1 改造目标
将 EmbyBot 从单服务器架构升级为多服务器架构，支持：
- ✅ 配置并管理多个 Emby 服务器
- ✅ 用户创建时自动分配或手动选择服务器
- ✅ 智能负载均衡和服务器健康检查
- ✅ 服务器故障隔离和切换
- ✅ 向后兼容现有单服务器数据

### 1.2 核心设计
- **配置层**: 支持多服务器配置列表
- **数据库层**: 添加 `server_id` 字段关联用户与服务器
- **服务层**: `EmbyServerManager` 管理多个 `Embyservice` 实例
- **业务层**: 动态获取用户对应的服务实例

### 1.3 架构对比

#### 改造前
```
┌─────────────┐
│   Bot 启动  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  全局单例 emby  │ ◄─── 所有用户共享
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  Emby Server A  │
└─────────────────┘
```

#### 改造后
```
┌─────────────────────┐
│      Bot 启动       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ EmbyServerManager   │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┐
    ▼             ▼          ▼
┌────────┐   ┌────────┐  ┌────────┐
│ emby_1 │   │ emby_2 │  │ emby_3 │
└───┬────┘   └───┬────┘  └───┬────┘
    │            │           │
    ▼            ▼           ▼
┌────────┐   ┌────────┐  ┌────────┐
│Server A│   │Server B│  │Server C│
└────────┘   └────────┘  └────────┘
```

---

## 二、实施步骤

### 阶段一：配置结构重构

#### 步骤 1.1：更新配置文件模板

**文件**: `config_example.json`

**原配置**:
```json
{
  "emby_api": "xxxxx",
  "emby_url": "http://255.255.255.255:8096",
  "emby_line": "susuyyds.com",
  "emby_whitelist_line": null
}
```

**新配置**:
```json
{
  "emby_servers": [
    {
      "id": "main",
      "name": "主服务器",
      "api_key": "xxxxx",
      "url": "http://255.255.255.255:8096",
      "line": "susuyyds.com",
      "whitelist_line": null,
      "is_default": true,
      "max_users": 500,
      "priority": 1,
      "enabled": true
    },
    {
      "id": "backup",
      "name": "备用服务器",
      "api_key": "yyyyy",
      "url": "http://192.168.1.100:8096",
      "line": "backup.susuyyds.com",
      "whitelist_line": "vip.backup.susuyyds.com",
      "is_default": false,
      "max_users": 300,
      "priority": 2,
      "enabled": true
    }
  ],

  "emby_block": ["XXX"],
  "extra_emby_libs": [],
  "blocked_clients": [],
  "client_filter_terminate_session": true,
  "client_filter_block_user": false
}
```

**配置字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 服务器唯一标识，用于数据库关联 |
| `name` | string | ✅ | 服务器显示名称 |
| `api_key` | string | ✅ | Emby API 密钥 |
| `url` | string | ✅ | Emby 服务器地址 |
| `line` | string | ✅ | 普通用户线路地址 |
| `whitelist_line` | string | ❌ | 白名单用户专属线路 |
| `is_default` | boolean | ❌ | 是否为默认服务器（默认 false） |
| `max_users` | integer | ❌ | 最大用户数限制 |
| `priority` | integer | ❌ | 优先级（数字越小优先级越高，默认 99） |
| `enabled` | boolean | ❌ | 是否启用（默认 true） |

#### 步骤 1.2：更新 Pydantic 配置模型

**文件**: `bot/schemas/schemas.py`

**添加服务器配置模型**:
```python
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class EmbyServerConfig(BaseModel):
    """单个 Emby 服务器配置"""
    id: str = Field(..., description="服务器唯一标识")
    name: str = Field(..., description="服务器显示名称")
    api_key: str = Field(..., description="API 密钥")
    url: str = Field(..., description="服务器地址")
    line: str = Field(..., description="线路地址")
    whitelist_line: Optional[str] = Field(None, description="白名单线路")
    is_default: bool = Field(False, description="是否为默认服务器")
    max_users: Optional[int] = Field(None, description="最大用户数")
    priority: int = Field(99, description="优先级，数字越小优先级越高")
    enabled: bool = Field(True, description="是否启用")

    @validator('id')
    def validate_id(cls, v):
        """验证 ID 格式"""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("服务器 ID 必须是字母数字或下划线组合")
        return v

    @validator('url')
    def validate_url(cls, v):
        """验证并标准化 URL"""
        v = v.rstrip('/')
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        return v

    @validator('max_users')
    def validate_max_users(cls, v):
        """验证用户数限制"""
        if v is not None and v <= 0:
            raise ValueError("最大用户数必须大于 0")
        return v

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "id": "main",
                "name": "主服务器",
                "api_key": "xxxxx",
                "url": "http://emby.example.com:8096",
                "line": "emby.example.com",
                "whitelist_line": "vip.emby.example.com",
                "is_default": True,
                "max_users": 500,
                "priority": 1,
                "enabled": True
            }
        }
```

**修改主配置类**:
```python
class Config(BaseModel):
    """主配置类"""
    # ... 保留其他字段 ...

    # 替换单服务器配置
    emby_servers: List[EmbyServerConfig] = Field(
        ...,
        min_items=1,
        description="Emby 服务器列表"
    )

    # 保留共享配置
    emby_block: Optional[List[str]] = Field(
        default_factory=list,
        description="屏蔽的媒体库列表"
    )
    extra_emby_libs: Optional[List[str]] = Field(
        default_factory=list,
        description="额外媒体库列表"
    )
    blocked_clients: Optional[List[str]] = Field(
        default_factory=list,
        description="屏蔽的客户端列表"
    )
    client_filter_terminate_session: bool = Field(
        True,
        description="是否终止屏蔽客户端的会话"
    )
    client_filter_block_user: bool = Field(
        False,
        description="是否封禁使用屏蔽客户端的用户"
    )

    @validator('emby_servers')
    def validate_emby_servers(cls, v):
        """验证服务器列表"""
        if not v:
            raise ValueError("至少需要配置一个 Emby 服务器")

        # 检查 ID 唯一性
        ids = [server.id for server in v]
        if len(ids) != len(set(ids)):
            raise ValueError("服务器 ID 必须唯一")

        # 检查默认服务器数量
        default_count = sum(1 for server in v if server.is_default)
        if default_count == 0:
            raise ValueError("至少需要设置一个默认服务器")
        if default_count > 1:
            raise ValueError("只能设置一个默认服务器")

        return v

    def get_default_server(self) -> Optional[EmbyServerConfig]:
        """获取默认服务器配置"""
        for server in self.emby_servers:
            if server.is_default and server.enabled:
                return server
        # 如果没有默认服务器，返回第一个启用的服务器
        for server in self.emby_servers:
            if server.enabled:
                return server
        return None

    def get_server_by_id(self, server_id: str) -> Optional[EmbyServerConfig]:
        """根据 ID 获取服务器配置"""
        for server in self.emby_servers:
            if server.id == server_id and server.enabled:
                return server
        return None

    def get_enabled_servers(self) -> List[EmbyServerConfig]:
        """获取所有启用的服务器"""
        return [s for s in self.emby_servers if s.enabled]

    def get_servers_sorted_by_priority(self) -> List[EmbyServerConfig]:
        """按优先级排序获取服务器"""
        return sorted(
            [s for s in self.emby_servers if s.enabled],
            key=lambda s: (s.priority, s.id)
        )
```

**向后兼容处理** (可选):
```python
class Config(BaseModel):
    # ... 其他字段 ...

    # 兼容旧配置字段（标记为 deprecated）
    emby_api: Optional[str] = Field(None, deprecated=True)
    emby_url: Optional[str] = Field(None, deprecated=True)
    emby_line: Optional[str] = Field(None, deprecated=True)
    emby_whitelist_line: Optional[str] = Field(None, deprecated=True)

    @validator('emby_servers', pre=True, always=True)
    def convert_legacy_config(cls, v, values):
        """自动转换旧配置为新格式"""
        # 如果新配置存在，直接使用
        if v:
            return v

        # 如果是旧配置，自动转换
        if 'emby_api' in values and values['emby_api']:
            return [{
                "id": "main",
                "name": "主服务器",
                "api_key": values.get('emby_api'),
                "url": values.get('emby_url', ''),
                "line": values.get('emby_line', ''),
                "whitelist_line": values.get('emby_whitelist_line'),
                "is_default": True,
                "priority": 1,
                "enabled": True
            }]

        raise ValueError("必须配置 emby_servers 或提供旧版配置")
```

---

### 阶段二：数据库结构升级

#### 步骤 2.1：添加 server_id 字段

**文件**: `bot/sql_helper/sql_emby.py`

**修改 Emby 模型**:
```python
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Index

class Emby(Base):
    """
    emby 用户表
    新增 server_id 字段支持多服务器
    """
    __tablename__ = 'emby'

    tg = Column(BigInteger, primary_key=True, autoincrement=False, comment='Telegram 用户 ID')

    # 新增：服务器标识字段
    server_id = Column(
        String(50),
        nullable=False,
        default='main',
        index=True,
        comment='关联的 Emby 服务器 ID'
    )

    embyid = Column(String(255), nullable=True, comment='Emby 用户 ID')
    name = Column(String(255), nullable=True, comment='Emby 用户名')
    pwd = Column(String(255), nullable=True, comment='密码')
    pwd2 = Column(String(255), nullable=True, comment='备用密码')
    lv = Column(String(1), default='d', comment='用户等级 a/b/c/d')
    cr = Column(DateTime, nullable=True, comment='创建时间')
    ex = Column(DateTime, nullable=True, comment='过期时间')
    us = Column(Integer, default=0, comment='用户积分')
    iv = Column(Integer, default=0, comment='邀请信息标记')
    ch = Column(DateTime, nullable=True, comment='修改时间')

    # 添加联合索引，优化查询性能
    __table_args__ = (
        Index('idx_server_embyid', 'server_id', 'embyid'),
        Index('idx_server_lv', 'server_id', 'lv'),
        Index('idx_server_ex', 'server_id', 'ex'),
    )

    def __repr__(self):
        return (
            f"<Emby(tg={self.tg}, server_id={self.server_id}, "
            f"name={self.name}, embyid={self.embyid}, lv={self.lv})>"
        )
```

#### 步骤 2.2：数据库迁移 SQL

**文件**: `migrations/add_server_id.sql`

```sql
-- ============================================
-- EmbyBot 多服务器支持数据库迁移脚本
-- 版本: v1.0
-- 日期: 2025-11-24
-- ============================================

-- 1. 备份现有表（可选但强烈建议）
CREATE TABLE IF NOT EXISTS emby_backup_20251124 AS SELECT * FROM emby;

-- 2. 添加 server_id 字段
ALTER TABLE emby ADD COLUMN server_id VARCHAR(50) NOT NULL DEFAULT 'main' COMMENT '关联的 Emby 服务器 ID' AFTER tg;

-- 3. 创建索引
CREATE INDEX idx_server_id ON emby(server_id);
CREATE INDEX idx_server_embyid ON emby(server_id, embyid);
CREATE INDEX idx_server_lv ON emby(server_id, lv);
CREATE INDEX idx_server_ex ON emby(server_id, ex);

-- 4. 验证迁移结果
SELECT
    COUNT(*) as total_users,
    server_id,
    COUNT(DISTINCT embyid) as unique_emby_ids
FROM emby
GROUP BY server_id;

-- 5. 查看表结构
DESCRIBE emby;
```

**执行迁移**:
```bash
# 连接到数据库
mysql -u root -p embybot

# 执行迁移脚本
source migrations/add_server_id.sql

# 或直接执行
mysql -u root -p embybot < migrations/add_server_id.sql
```

#### 步骤 2.3：更新数据库操作函数

**文件**: `bot/sql_helper/sql_emby.py`

**新增/修改函数**:
```python
from typing import List, Optional
from sqlalchemy import and_, or_
from bot.sql_helper import session, commit
from loguru import logger

# ==================== 基础查询函数 ====================

def get_emby(tg: int, server_id: Optional[str] = None) -> Optional[Emby]:
    """
    获取用户信息

    Args:
        tg: Telegram 用户 ID
        server_id: 可选，指定服务器 ID。如果为 None，返回任意服务器的用户

    Returns:
        Emby 对象或 None
    """
    try:
        query = session.query(Emby).filter(Emby.tg == tg)
        if server_id:
            query = query.filter(Emby.server_id == server_id)
        result = query.first()
        return result
    except Exception as e:
        logger.error(f"查询用户失败 tg={tg}, server_id={server_id}: {e}")
        return None
    finally:
        session.close()

def get_emby_by_server(tg: int, server_id: str) -> Optional[Emby]:
    """
    根据服务器 ID 获取用户信息

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID

    Returns:
        Emby 对象或 None
    """
    return get_emby(tg, server_id)

def get_emby_by_embyid(emby_id: str, server_id: Optional[str] = None) -> Optional[Emby]:
    """
    根据 Emby ID 获取用户信息

    Args:
        emby_id: Emby 用户 ID
        server_id: 可选，服务器 ID

    Returns:
        Emby 对象或 None
    """
    try:
        query = session.query(Emby).filter(Emby.embyid == emby_id)
        if server_id:
            query = query.filter(Emby.server_id == server_id)
        result = query.first()
        return result
    except Exception as e:
        logger.error(f"查询用户失败 emby_id={emby_id}, server_id={server_id}: {e}")
        return None
    finally:
        session.close()

def get_emby_by_name(name: str, server_id: Optional[str] = None) -> Optional[Emby]:
    """
    根据用户名获取用户信息

    Args:
        name: Emby 用户名
        server_id: 可选，服务器 ID

    Returns:
        Emby 对象或 None
    """
    try:
        query = session.query(Emby).filter(Emby.name == name)
        if server_id:
            query = query.filter(Emby.server_id == server_id)
        result = query.first()
        return result
    except Exception as e:
        logger.error(f"查询用户失败 name={name}, server_id={server_id}: {e}")
        return None
    finally:
        session.close()

# ==================== 批量查询函数 ====================

def get_all_users_by_server(server_id: str) -> List[Emby]:
    """
    获取指定服务器的所有用户

    Args:
        server_id: 服务器 ID

    Returns:
        Emby 对象列表
    """
    try:
        result = session.query(Emby).filter(Emby.server_id == server_id).all()
        return result
    except Exception as e:
        logger.error(f"查询服务器用户失败 server_id={server_id}: {e}")
        return []
    finally:
        session.close()

def get_users_by_level(lv: str, server_id: Optional[str] = None) -> List[Emby]:
    """
    根据等级获取用户列表

    Args:
        lv: 用户等级 (a/b/c/d)
        server_id: 可选，服务器 ID

    Returns:
        Emby 对象列表
    """
    try:
        query = session.query(Emby).filter(Emby.lv == lv)
        if server_id:
            query = query.filter(Emby.server_id == server_id)
        result = query.all()
        return result
    except Exception as e:
        logger.error(f"查询用户失败 lv={lv}, server_id={server_id}: {e}")
        return []
    finally:
        session.close()

def get_expired_users(server_id: Optional[str] = None) -> List[Emby]:
    """
    获取已过期的用户列表

    Args:
        server_id: 可选，服务器 ID

    Returns:
        Emby 对象列表
    """
    try:
        from datetime import datetime
        query = session.query(Emby).filter(
            Emby.ex.isnot(None),
            Emby.ex < datetime.now()
        )
        if server_id:
            query = query.filter(Emby.server_id == server_id)
        result = query.all()
        return result
    except Exception as e:
        logger.error(f"查询过期用户失败 server_id={server_id}: {e}")
        return []
    finally:
        session.close()

def count_users_by_server(server_id: str) -> int:
    """
    统计指定服务器的用户数

    Args:
        server_id: 服务器 ID

    Returns:
        用户数量
    """
    try:
        count = session.query(Emby).filter(Emby.server_id == server_id).count()
        return count
    except Exception as e:
        logger.error(f"统计用户失败 server_id={server_id}: {e}")
        return 0
    finally:
        session.close()

def get_server_stats() -> dict:
    """
    获取所有服务器的统计信息

    Returns:
        字典，格式: {server_id: {total: int, by_level: {lv: int}}}
    """
    try:
        from sqlalchemy import func

        # 统计每个服务器的用户数和等级分布
        stats = {}
        servers = session.query(Emby.server_id).distinct().all()

        for (server_id,) in servers:
            total = session.query(Emby).filter(Emby.server_id == server_id).count()

            level_stats = session.query(
                Emby.lv,
                func.count(Emby.tg)
            ).filter(
                Emby.server_id == server_id
            ).group_by(Emby.lv).all()

            stats[server_id] = {
                'total': total,
                'by_level': {lv: count for lv, count in level_stats}
            }

        return stats
    except Exception as e:
        logger.error(f"获取服务器统计失败: {e}")
        return {}
    finally:
        session.close()

# ==================== 修改操作函数 ====================

def add_emby(tg: int, server_id: str, embyid: str, name: str, pwd: str,
             lv: str = 'b', **kwargs) -> bool:
    """
    添加新用户

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID
        embyid: Emby 用户 ID
        name: 用户名
        pwd: 密码
        lv: 用户等级，默认 'b'
        **kwargs: 其他字段（pwd2, cr, ex, us, iv, ch）

    Returns:
        是否成功
    """
    try:
        from datetime import datetime

        user = Emby(
            tg=tg,
            server_id=server_id,
            embyid=embyid,
            name=name,
            pwd=pwd,
            lv=lv,
            cr=kwargs.get('cr', datetime.now()),
            ex=kwargs.get('ex'),
            pwd2=kwargs.get('pwd2'),
            us=kwargs.get('us', 0),
            iv=kwargs.get('iv', 0),
            ch=kwargs.get('ch')
        )

        session.add(user)
        session.commit()
        logger.info(f"添加用户成功: tg={tg}, server={server_id}, name={name}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"添加用户失败 tg={tg}, server_id={server_id}: {e}")
        return False
    finally:
        session.close()

def update_emby_server_id(tg: int, old_server_id: str, new_server_id: str) -> bool:
    """
    迁移用户到新服务器

    Args:
        tg: Telegram 用户 ID
        old_server_id: 原服务器 ID
        new_server_id: 新服务器 ID

    Returns:
        是否成功
    """
    try:
        result = session.query(Emby).filter(
            Emby.tg == tg,
            Emby.server_id == old_server_id
        ).update({'server_id': new_server_id})

        session.commit()

        if result > 0:
            logger.info(f"迁移用户成功: tg={tg}, {old_server_id} -> {new_server_id}")
            return True
        else:
            logger.warning(f"未找到用户 tg={tg}, server_id={old_server_id}")
            return False
    except Exception as e:
        session.rollback()
        logger.error(f"迁移用户失败 tg={tg}: {e}")
        return False
    finally:
        session.close()

def delete_emby(tg: int, server_id: Optional[str] = None) -> bool:
    """
    删除用户

    Args:
        tg: Telegram 用户 ID
        server_id: 可选，服务器 ID。如果为 None，删除该用户在所有服务器的记录

    Returns:
        是否成功
    """
    try:
        query = session.query(Emby).filter(Emby.tg == tg)
        if server_id:
            query = query.filter(Emby.server_id == server_id)

        result = query.delete()
        session.commit()

        if result > 0:
            logger.info(f"删除用户成功: tg={tg}, server_id={server_id}")
            return True
        else:
            logger.warning(f"未找到用户 tg={tg}, server_id={server_id}")
            return False
    except Exception as e:
        session.rollback()
        logger.error(f"删除用户失败 tg={tg}: {e}")
        return False
    finally:
        session.close()

# ==================== 兼容性函数（向后兼容）====================

def get_emby_all() -> List[Emby]:
    """获取所有用户（兼容旧代码）"""
    try:
        result = session.query(Emby).all()
        return result
    except Exception as e:
        logger.error(f"查询所有用户失败: {e}")
        return []
    finally:
        session.close()
```

---

### 阶段三：服务层重构

#### 步骤 3.1：创建服务器管理器

**文件**: `bot/func_helper/emby_manager.py` (新建)

```python
"""
Emby 服务器管理器
管理多个 Emby 服务器实例
"""

from typing import Dict, Optional, List
from loguru import logger

from bot.func_helper.emby import Embyservice
from bot.schemas.schemas import EmbyServerConfig


class EmbyServerManager:
    """
    Emby 服务器管理器（单例模式）
    负责管理多个 Emby 服务器实例
    """

    _instance: Optional['EmbyServerManager'] = None
    _initialized: bool = False

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化管理器"""
        if not self._initialized:
            self._servers: Dict[str, Embyservice] = {}
            self._configs: Dict[str, EmbyServerConfig] = {}
            self._initialized = True
            logger.info("EmbyServerManager 初始化完成")

    def register_server(self, server_config: EmbyServerConfig) -> bool:
        """
        注册一个 Emby 服务器实例

        Args:
            server_config: 服务器配置对象

        Returns:
            是否注册成功
        """
        try:
            server_id = server_config.id

            if server_id in self._servers:
                logger.warning(f"服务器 {server_id} 已存在，跳过注册")
                return True

            # 创建独立的 Embyservice 实例（不使用单例）
            instance = Embyservice.__new__(Embyservice)
            instance.__init__(
                url=server_config.url,
                api_key=server_config.api_key,
                timeout=10,
                max_retries=1
            )

            self._servers[server_id] = instance
            self._configs[server_id] = server_config

            logger.success(
                f"注册 Emby 服务器成功: {server_config.name} "
                f"({server_id}) - {server_config.url}"
            )
            return True

        except Exception as e:
            logger.error(f"注册服务器失败 {server_config.id}: {e}")
            return False

    def unregister_server(self, server_id: str) -> bool:
        """
        注销服务器实例

        Args:
            server_id: 服务器 ID

        Returns:
            是否成功
        """
        try:
            if server_id not in self._servers:
                logger.warning(f"服务器 {server_id} 不存在")
                return False

            # 关闭连接
            import asyncio
            server = self._servers[server_id]
            asyncio.create_task(server.close())

            del self._servers[server_id]
            del self._configs[server_id]

            logger.info(f"注销服务器成功: {server_id}")
            return True

        except Exception as e:
            logger.error(f"注销服务器失败 {server_id}: {e}")
            return False

    def get_server(self, server_id: str) -> Optional[Embyservice]:
        """
        获取指定服务器实例

        Args:
            server_id: 服务器 ID

        Returns:
            Embyservice 实例或 None
        """
        return self._servers.get(server_id)

    def get_config(self, server_id: str) -> Optional[EmbyServerConfig]:
        """
        获取指定服务器配置

        Args:
            server_id: 服务器 ID

        Returns:
            EmbyServerConfig 对象或 None
        """
        return self._configs.get(server_id)

    def get_all_servers(self) -> Dict[str, Embyservice]:
        """
        获取所有服务器实例

        Returns:
            字典，格式: {server_id: Embyservice}
        """
        return self._servers.copy()

    def get_all_configs(self) -> Dict[str, EmbyServerConfig]:
        """
        获取所有服务器配置

        Returns:
            字典，格式: {server_id: EmbyServerConfig}
        """
        return self._configs.copy()

    def list_server_ids(self) -> List[str]:
        """
        列出所有服务器 ID

        Returns:
            服务器 ID 列表
        """
        return list(self._servers.keys())

    def has_server(self, server_id: str) -> bool:
        """
        检查服务器是否存在

        Args:
            server_id: 服务器 ID

        Returns:
            是否存在
        """
        return server_id in self._servers

    def get_server_count(self) -> int:
        """
        获取服务器数量

        Returns:
            服务器数量
        """
        return len(self._servers)

    async def close_all(self) -> None:
        """
        关闭所有服务器连接
        用于程序退出时清理资源
        """
        logger.info("开始关闭所有 Emby 服务器连接...")

        for server_id, server in self._servers.items():
            try:
                await server.close()
                logger.info(f"关闭服务器连接成功: {server_id}")
            except Exception as e:
                logger.error(f"关闭服务器连接失败 {server_id}: {e}")

        logger.success("所有 Emby 服务器连接已关闭")

    async def health_check(self, server_id: Optional[str] = None) -> Dict[str, bool]:
        """
        健康检查

        Args:
            server_id: 可选，指定服务器 ID。如果为 None，检查所有服务器

        Returns:
            字典，格式: {server_id: is_healthy}
        """
        results = {}

        servers_to_check = (
            {server_id: self._servers[server_id]}
            if server_id and server_id in self._servers
            else self._servers
        )

        for sid, server in servers_to_check.items():
            try:
                # 尝试获取系统信息
                result = await server.get_system_info()
                is_healthy = result.success
                results[sid] = is_healthy

                status = "✅ 正常" if is_healthy else "⚠️ 异常"
                logger.info(f"健康检查 [{self._configs[sid].name}]: {status}")

            except Exception as e:
                results[sid] = False
                logger.error(f"健康检查失败 [{sid}]: {e}")

        return results

    def __repr__(self):
        """字符串表示"""
        return (
            f"<EmbyServerManager(servers={self.get_server_count()}, "
            f"ids={self.list_server_ids()})>"
        )


# 创建全局单例
emby_manager = EmbyServerManager()
```

#### 步骤 3.2：修改 Embyservice 单例限制

**文件**: `bot/func_helper/emby.py`

**修改点**:
```python
# 原代码使用单例模式
class Embyservice(metaclass=Singleton):
    pass

# 修改为普通类（移除 metaclass）
class Embyservice:
    """
    Emby API 服务类 - 使用 aiohttp 重构版本
    提供统一的异步HTTP请求、错误处理、重试机制和资源管理

    注意: 此类不再使用单例模式，每个 Emby 服务器使用独立实例
    """

    def __init__(self, url: str, api_key: str, timeout: int = 10, max_retries: int = 1):
        # ... 保持原有初始化逻辑 ...
        pass
```

**移除全局实例创建**:
```python
# 删除原有的全局实例创建
# emby = Embyservice(emby_url, emby_api)  # <-- 删除这行
```

#### 步骤 3.3：修改 bot 初始化

**文件**: `bot/__init__.py`

**修改内容**:
```python
from loguru import logger
from bot.schemas.schemas import Config
from bot.func_helper.emby_manager import emby_manager

# ... 其他导入 ...

# 加载配置
config = Config.load_config()

# ... 其他初始化代码 ...

# ==================== Emby 服务器初始化 ====================

# 初始化所有 Emby 服务器
logger.info("开始初始化 Emby 服务器...")

for server_config in config.emby_servers:
    if not server_config.enabled:
        logger.warning(f"服务器 {server_config.name} ({server_config.id}) 已禁用，跳过")
        continue

    success = emby_manager.register_server(server_config)
    if not success:
        logger.error(f"注册服务器失败: {server_config.name}")

logger.success(
    f"Emby 服务器初始化完成，"
    f"已注册 {emby_manager.get_server_count()} 个服务器: "
    f"{emby_manager.list_server_ids()}"
)

# ==================== 共享配置 ====================

# 保留原有的共享配置变量（向后兼容）
emby_block = config.emby_block
extra_emby_libs = config.extra_emby_libs
blocked_clients = config.blocked_clients

# ==================== 导出 ====================

__all__ = [
    'config',
    'emby_manager',  # 替换原来的 emby 实例
    'emby_block',
    'extra_emby_libs',
    'blocked_clients',
    # ... 其他导出 ...
]
```

---

### 阶段四：业务层适配

#### 步骤 4.1：创建辅助工具函数

**文件**: `bot/func_helper/emby_utils.py` (新建)

```python
"""
Emby 多服务器辅助工具
提供统一的服务器选择、用户查询等功能
"""

from typing import Optional, Tuple, List
from loguru import logger

from bot import config, emby_manager
from bot.sql_helper.sql_emby import get_emby, get_all_users_by_server, count_users_by_server
from bot.func_helper.emby import Embyservice
from bot.schemas.schemas import EmbyServerConfig


def get_user_emby_service(tg: int) -> Tuple[Optional[Embyservice], Optional[EmbyServerConfig], Optional['Emby']]:
    """
    根据用户 TG ID 获取对应的 Emby 服务实例

    Args:
        tg: Telegram 用户 ID

    Returns:
        元组 (Embyservice实例, 服务器配置, 用户对象) 或 (None, None, None)

    Example:
        >>> emby_service, server_config, user = get_user_emby_service(123456)
        >>> if emby_service:
        >>>     result = await emby_service.user(emby_id=user.embyid)
    """
    # 查询用户信息
    user = get_emby(tg)
    if not user:
        logger.warning(f"用户不存在: tg={tg}")
        return None, None, None

    # 获取服务器配置
    server_id = user.server_id
    if not server_id:
        # 如果用户没有 server_id，尝试使用默认服务器
        default_server = config.get_default_server()
        if default_server:
            server_id = default_server.id
            logger.warning(f"用户 tg={tg} 缺少 server_id，使用默认服务器: {server_id}")
        else:
            logger.error(f"用户 tg={tg} 缺少 server_id 且无默认服务器")
            return None, None, None

    server_config = config.get_server_by_id(server_id)
    if not server_config:
        logger.error(f"服务器配置不存在: server_id={server_id}")
        return None, None, None

    # 获取服务实例
    emby_service = emby_manager.get_server(server_id)
    if not emby_service:
        logger.error(f"服务器实例不存在: server_id={server_id}")
        return None, None, None

    return emby_service, server_config, user


def get_emby_line(server_id: str, is_whitelist: bool = False) -> str:
    """
    获取服务器线路地址

    Args:
        server_id: 服务器 ID
        is_whitelist: 是否为白名单用户

    Returns:
        线路地址字符串

    Example:
        >>> line = get_emby_line('main', is_whitelist=True)
        >>> print(f"访问地址: {line}")
    """
    server_config = config.get_server_by_id(server_id)
    if not server_config:
        logger.error(f"服务器配置不存在: server_id={server_id}")
        return ""

    if is_whitelist and server_config.whitelist_line:
        return server_config.whitelist_line
    return server_config.line


def select_available_server() -> Optional[EmbyServerConfig]:
    """
    智能选择可用服务器
    策略: 按优先级排序，选择未达到用户上限的服务器

    Returns:
        EmbyServerConfig 对象或 None

    Example:
        >>> server = select_available_server()
        >>> if server:
        >>>     print(f"选择的服务器: {server.name}")
    """
    # 获取按优先级排序的服务器列表
    servers = config.get_servers_sorted_by_priority()

    for server in servers:
        # 检查是否达到最大用户数
        if server.max_users:
            current_users = count_users_by_server(server.id)
            if current_users >= server.max_users:
                logger.info(
                    f"服务器 {server.name} 已达到用户上限: "
                    f"{current_users}/{server.max_users}"
                )
                continue

        # 检查服务器是否可用
        if not emby_manager.has_server(server.id):
            logger.warning(f"服务器 {server.name} 未注册，跳过")
            continue

        logger.info(f"选择服务器: {server.name} ({server.id})")
        return server

    logger.error("没有可用的服务器")
    return None


def select_server_by_load() -> Optional[EmbyServerConfig]:
    """
    根据负载选择服务器
    策略: 选择用户数占比最低的服务器

    Returns:
        EmbyServerConfig 对象或 None
    """
    servers = config.get_enabled_servers()

    if not servers:
        return None

    # 计算每个服务器的负载
    loads = []
    for server in servers:
        if not emby_manager.has_server(server.id):
            continue

        current_users = count_users_by_server(server.id)
        max_users = server.max_users or 999999
        load_ratio = current_users / max_users

        loads.append((load_ratio, server))

    if not loads:
        return None

    # 返回负载最低的服务器
    loads.sort(key=lambda x: x[0])
    selected_server = loads[0][1]

    logger.info(
        f"根据负载选择服务器: {selected_server.name} "
        f"(负载: {loads[0][0]:.2%})"
    )
    return selected_server


def get_server_display_info(server_id: str) -> dict:
    """
    获取服务器显示信息（用于前端展示）

    Args:
        server_id: 服务器 ID

    Returns:
        字典，包含服务器信息

    Example:
        >>> info = get_server_display_info('main')
        >>> print(info['name'], info['users_count'])
    """
    server_config = config.get_server_by_id(server_id)
    if not server_config:
        return {}

    current_users = count_users_by_server(server_id)

    return {
        'id': server_config.id,
        'name': server_config.name,
        'line': server_config.line,
        'users_count': current_users,
        'max_users': server_config.max_users,
        'load_ratio': (
            current_users / server_config.max_users
            if server_config.max_users
            else 0
        ),
        'priority': server_config.priority,
        'is_default': server_config.is_default,
        'enabled': server_config.enabled
    }


def format_server_list_text() -> str:
    """
    格式化服务器列表文本（用于 Telegram 消息）

    Returns:
        格式化的文本字符串

    Example:
        >>> text = format_server_list_text()
        >>> await message.reply(text)
    """
    servers = config.get_enabled_servers()

    if not servers:
        return "❌ 暂无可用服务器"

    text = "**📡 Emby 服务器列表**\n\n"

    for server in servers:
        info = get_server_display_info(server.id)

        # 状态图标
        if info['is_default']:
            icon = "🟢"
        elif info['load_ratio'] > 0.8:
            icon = "🔴"
        elif info['load_ratio'] > 0.5:
            icon = "🟡"
        else:
            icon = "🟢"

        # 用户数显示
        user_info = (
            f"{info['users_count']}/{info['max_users']}"
            if info['max_users']
            else str(info['users_count'])
        )

        text += (
            f"{icon} **{info['name']}**\n"
            f"   • ID: `{info['id']}`\n"
            f"   • 用户数: {user_info}\n"
            f"   • 线路: {info['line']}\n"
            f"   • 优先级: {info['priority']}\n"
        )

        if info['is_default']:
            text += "   • 🏷️ 默认服务器\n"

        text += "\n"

    return text


def validate_server_id(server_id: str) -> bool:
    """
    验证服务器 ID 是否有效

    Args:
        server_id: 服务器 ID

    Returns:
        是否有效
    """
    return (
        server_id is not None and
        config.get_server_by_id(server_id) is not None and
        emby_manager.has_server(server_id)
    )
```

#### 步骤 4.2：修改核心命令处理器

**示例：修改 `bot/modules/panel/kk.py`**

```python
# 导入修改
from bot import emby_manager, config, emby_block, extra_emby_libs
from bot.func_helper.emby_utils import (
    get_user_emby_service,
    get_emby_line,
    select_available_server
)
from bot.sql_helper.sql_emby import add_emby, get_emby

# 移除旧导入
# from bot.func_helper.emby import emby


@Client.on_message(filters=filters.command('kk') & filters.private)
async def kk_handler(client: Client, message: Message):
    """用户管理命令 - 多服务器适配版本"""

    tg = message.from_user.id

    # 获取用户的 Emby 服务实例
    emby_service, server_config, user = get_user_emby_service(tg)

    if not emby_service:
        await message.reply(
            "❌ 无法找到您的 Emby 服务器配置\n"
            "请联系管理员检查配置"
        )
        return

    if not user:
        await message.reply("❌ 您还没有注册 Emby 账号")
        return

    # 获取用户信息
    success, user_data = await emby_service.user(emby_id=user.embyid)

    if not success:
        await message.reply("❌ 获取用户信息失败")
        return

    # 获取线路地址（根据用户等级）
    is_whitelist = (user.lv == 'a')
    server_line = get_emby_line(server_config.id, is_whitelist=is_whitelist)

    # 格式化用户信息
    info_text = (
        f"**👤 用户信息**\n\n"
        f"**服务器**: {server_config.name}\n"
        f"**线路**: `{server_line}`\n"
        f"**用户名**: `{user.name}`\n"
        f"**密码**: `{user.pwd}`\n"
        f"**等级**: {get_level_name(user.lv)}\n"
        f"**到期时间**: {user.ex.strftime('%Y-%m-%d %H:%M') if user.ex else '永久'}\n"
        f"**积分**: {user.us}\n"
    )

    await message.reply(info_text)


@Client.on_message(filters=filters.command('newuser') & filters.private)
async def create_user_handler(client: Client, message: Message):
    """创建新用户 - 多服务器适配版本"""

    # 权限检查
    tg = message.from_user.id
    if tg not in admin_p:
        await message.reply("❌ 您没有权限执行此操作")
        return

    # 解析命令参数
    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply(
                "❌ 参数不足\n"
                "用法: `/newuser <用户名> <密码> [服务器ID]`"
            )
            return

        username = parts[1]
        password = parts[2]
        server_id = parts[3] if len(parts) > 3 else None

    except Exception as e:
        await message.reply(f"❌ 参数解析失败: {e}")
        return

    # 选择服务器
    if server_id:
        # 使用指定的服务器
        target_server = config.get_server_by_id(server_id)
        if not target_server:
            await message.reply(f"❌ 服务器不存在: {server_id}")
            return
    else:
        # 自动选择可用服务器
        target_server = select_available_server()
        if not target_server:
            await message.reply("❌ 当前没有可用的服务器")
            return

    # 获取服务实例
    emby_service = emby_manager.get_server(target_server.id)
    if not emby_service:
        await message.reply(f"❌ 服务器实例不存在: {target_server.id}")
        return

    # 创建用户
    status_msg = await message.reply(
        f"⏳ 正在创建用户...\n"
        f"服务器: {target_server.name}"
    )

    try:
        result = await emby_service.create_user(username, password)

        if not result.success:
            await status_msg.edit_text(f"❌ 创建失败: {result.message}")
            return

        # 保存到数据库
        emby_id = result.data.get('Id')
        from datetime import datetime, timedelta

        success = add_emby(
            tg=tg,
            server_id=target_server.id,  # 关键：记录服务器 ID
            embyid=emby_id,
            name=username,
            pwd=password,
            lv='b',
            cr=datetime.now(),
            ex=datetime.now() + timedelta(days=30)
        )

        if success:
            line = get_emby_line(target_server.id, is_whitelist=False)
            await status_msg.edit_text(
                f"✅ 创建成功！\n\n"
                f"**服务器**: {target_server.name}\n"
                f"**线路**: `{line}`\n"
                f"**用户名**: `{username}`\n"
                f"**密码**: `{password}`\n"
                f"**到期时间**: 30天后"
            )
        else:
            await status_msg.edit_text("❌ 保存到数据库失败")

    except Exception as e:
        await status_msg.edit_text(f"❌ 创建过程出错: {e}")
        logger.error(f"创建用户失败: {e}")


@Client.on_message(filters=filters.command('switchserver') & filters.private)
async def switch_server_handler(client: Client, message: Message):
    """切换用户服务器 - 新增功能"""

    # 仅管理员可用
    tg = message.from_user.id
    if tg not in admin_p:
        await message.reply("❌ 您没有权限执行此操作")
        return

    # 解析参数
    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply(
                "❌ 参数不足\n"
                "用法: `/switchserver <目标用户TG_ID> <新服务器ID>`"
            )
            return

        target_tg = int(parts[1])
        new_server_id = parts[2]

    except ValueError:
        await message.reply("❌ 参数格式错误")
        return

    # 检查目标服务器
    new_server_config = config.get_server_by_id(new_server_id)
    if not new_server_config:
        await message.reply(f"❌ 目标服务器不存在: {new_server_id}")
        return

    # 获取用户当前信息
    emby_service, old_server_config, user = get_user_emby_service(target_tg)
    if not user:
        await message.reply(f"❌ 用户不存在: {target_tg}")
        return

    old_server_id = user.server_id

    # 确认操作
    await message.reply(
        f"⚠️ 确认迁移用户？\n\n"
        f"**用户**: {user.name} (TG: {target_tg})\n"
        f"**原服务器**: {old_server_config.name if old_server_config else '未知'}\n"
        f"**新服务器**: {new_server_config.name}\n\n"
        f"请回复 `确认` 继续"
    )

    # TODO: 实现确认逻辑和实际迁移
    # 1. 在新服务器创建用户
    # 2. 迁移用户数据
    # 3. 删除旧服务器用户
    # 4. 更新数据库


def get_level_name(lv: str) -> str:
    """获取等级名称"""
    level_map = {
        'a': '🌟 白名单',
        'b': '✅ 正常',
        'c': '⏰ 临时',
        'd': '❌ 未注册'
    }
    return level_map.get(lv, '❓ 未知')
```

---

### 阶段五：定时任务适配

#### 步骤 5.1：修改到期检查任务

**文件**: `bot/scheduler/check_ex.py`

```python
"""
到期检查定时任务 - 多服务器适配版本
"""

import asyncio
from datetime import datetime
from loguru import logger

from bot import config, emby_manager
from bot.sql_helper.sql_emby import get_expired_users, get_all_users_by_server
from bot.func_helper.msg_utils import send_message


async def check_expired_users_task():
    """
    检查所有服务器的过期用户
    对每个服务器并行处理
    """
    logger.info("开始检查过期用户...")

    # 获取所有启用的服务器
    servers = config.get_enabled_servers()

    if not servers:
        logger.warning("没有启用的服务器")
        return

    # 并行处理所有服务器
    tasks = []
    for server in servers:
        task = check_server_expired_users(server.id, server.name)
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计结果
    total_checked = 0
    total_disabled = 0

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"检查任务异常: {result}")
            continue

        checked, disabled = result
        total_checked += checked
        total_disabled += disabled

    logger.success(
        f"过期检查完成: 检查 {total_checked} 个用户，"
        f"禁用 {total_disabled} 个过期用户"
    )


async def check_server_expired_users(server_id: str, server_name: str) -> tuple:
    """
    检查单个服务器的过期用户

    Args:
        server_id: 服务器 ID
        server_name: 服务器名称

    Returns:
        元组 (检查数量, 禁用数量)
    """
    logger.info(f"开始检查服务器 [{server_name}] 的过期用户...")

    # 获取服务实例
    emby_service = emby_manager.get_server(server_id)
    if not emby_service:
        logger.error(f"服务器实例不存在: {server_id}")
        return 0, 0

    # 获取过期用户
    expired_users = get_expired_users(server_id=server_id)

    if not expired_users:
        logger.info(f"服务器 [{server_name}] 没有过期用户")
        return 0, 0

    logger.info(f"服务器 [{server_name}] 发现 {len(expired_users)} 个过期用户")

    # 处理过期用户
    disabled_count = 0

    for user in expired_users:
        try:
            # 禁用用户
            result = await emby_service.emby_change_policy(
                emby_id=user.embyid,
                disable=True
            )

            if result:
                disabled_count += 1
                logger.info(
                    f"[{server_name}] 禁用过期用户: "
                    f"{user.name} (TG: {user.tg})"
                )

                # 发送通知给用户
                await send_message(
                    user.tg,
                    f"⚠️ 您的 Emby 账号已过期\n\n"
                    f"**服务器**: {server_name}\n"
                    f"**用户名**: {user.name}\n"
                    f"**过期时间**: {user.ex.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"请联系管理员续期"
                )
            else:
                logger.warning(
                    f"[{server_name}] 禁用用户失败: {user.name}"
                )

        except Exception as e:
            logger.error(
                f"[{server_name}] 处理过期用户失败 {user.name}: {e}"
            )

    logger.info(
        f"服务器 [{server_name}] 完成: "
        f"检查 {len(expired_users)} 个，禁用 {disabled_count} 个"
    )

    return len(expired_users), disabled_count


async def check_low_activity_users_task():
    """
    检查不活跃用户 - 多服务器版本
    """
    logger.info("开始检查不活跃用户...")

    servers = config.get_enabled_servers()

    for server in servers:
        await check_server_low_activity(server.id, server.name)


async def check_server_low_activity(server_id: str, server_name: str):
    """检查单个服务器的不活跃用户"""
    logger.info(f"检查服务器 [{server_name}] 的活跃度...")

    emby_service = emby_manager.get_server(server_id)
    if not emby_service:
        return

    # 获取该服务器的所有用户
    users = get_all_users_by_server(server_id)

    for user in users:
        try:
            # 获取用户播放统计
            result = await emby_service.get_user_stats(user.embyid)

            # TODO: 根据播放统计判断活跃度

        except Exception as e:
            logger.error(f"获取用户统计失败 {user.name}: {e}")
```

#### 步骤 5.2：修改榜单生成任务

**文件**: `bot/scheduler/ranks_task.py`

```python
"""
榜单生成任务 - 多服务器适配版本
"""

import asyncio
from datetime import datetime, timedelta
from loguru import logger

from bot import config, emby_manager
from bot.sql_helper.sql_emby import get_all_users_by_server
from bot.ranks_helper import generate_rank_poster


async def generate_daily_ranks():
    """生成每日榜单（所有服务器）"""
    logger.info("开始生成每日榜单...")

    servers = config.get_enabled_servers()

    # 为每个服务器生成独立榜单
    for server in servers:
        try:
            await generate_server_daily_rank(server.id, server.name)
        except Exception as e:
            logger.error(f"生成服务器 [{server.name}] 榜单失败: {e}")


async def generate_server_daily_rank(server_id: str, server_name: str):
    """生成单个服务器的每日榜单"""
    logger.info(f"生成服务器 [{server_name}] 的每日榜单...")

    emby_service = emby_manager.get_server(server_id)
    if not emby_service:
        return

    # 获取播放统计
    result = await emby_service.get_activity_stats(
        start_date=(datetime.now() - timedelta(days=1)).isoformat(),
        end_date=datetime.now().isoformat()
    )

    if not result.success:
        logger.error(f"获取 [{server_name}] 活动统计失败")
        return

    # 生成榜单海报
    poster_path = await generate_rank_poster(
        stats_data=result.data,
        server_name=server_name,
        rank_type='daily'
    )

    if poster_path:
        logger.success(f"服务器 [{server_name}] 榜单生成成功: {poster_path}")
        # TODO: 推送到频道
    else:
        logger.error(f"服务器 [{server_name}] 榜单生成失败")
```

---

### 阶段六：数据迁移

#### 步骤 6.1：创建迁移脚本

**文件**: `scripts/migrate_to_multi_server.py` (新建)

```python
#!/usr/bin/env python3
"""
EmbyBot 多服务器数据迁移脚本
将现有单服务器数据迁移到多服务器架构
"""

import sys
import os
from datetime import datetime
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot import config
from bot.sql_helper import session
from bot.sql_helper.sql_emby import Emby


def backup_database():
    """备份数据库"""
    logger.info("开始备份数据库...")

    backup_filename = f"emby_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

    # 使用 mysqldump 备份
    import subprocess

    try:
        cmd = [
            'mysqldump',
            '-h', config.db_host,
            '-P', str(config.db_port),
            '-u', config.db_user,
            f'-p{config.db_pwd}',
            config.db_name,
            '--single-transaction',
            '--result-file', backup_filename
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        logger.success(f"数据库备份成功: {backup_filename}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"数据库备份失败: {e.stderr.decode()}")
        return False
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return False


def check_server_id_column():
    """检查 server_id 列是否存在"""
    logger.info("检查数据库表结构...")

    try:
        result = session.execute("DESCRIBE emby")
        columns = [row[0] for row in result]

        if 'server_id' in columns:
            logger.info("✅ server_id 列已存在")
            return True
        else:
            logger.warning("❌ server_id 列不存在，需要先执行 SQL 迁移")
            return False

    except Exception as e:
        logger.error(f"检查表结构失败: {e}")
        return False
    finally:
        session.close()


def migrate_existing_users():
    """
    将现有用户迁移到默认服务器
    """
    logger.info("开始迁移用户数据...")

    # 获取默认服务器
    default_server = config.get_default_server()

    if not default_server:
        logger.error("未找到默认服务器配置")
        return False

    logger.info(f"目标服务器: {default_server.name} ({default_server.id})")

    try:
        # 查询所有 server_id 为空或默认值的用户
        users = session.query(Emby).filter(
            (Emby.server_id == None) |
            (Emby.server_id == '') |
            (Emby.server_id == 'main')
        ).all()

        if not users:
            logger.info("没有需要迁移的用户")
            return True

        logger.info(f"找到 {len(users)} 个需要迁移的用户")

        # 批量更新
        migrated_count = 0
        failed_count = 0

        for user in users:
            try:
                user.server_id = default_server.id
                session.add(user)
                migrated_count += 1

                if migrated_count % 100 == 0:
                    session.commit()
                    logger.info(f"已迁移 {migrated_count} 个用户...")

            except Exception as e:
                logger.error(f"迁移用户失败 tg={user.tg}: {e}")
                failed_count += 1

        # 提交剩余的
        session.commit()

        logger.success(
            f"用户迁移完成: "
            f"成功 {migrated_count} 个，失败 {failed_count} 个"
        )

        return failed_count == 0

    except Exception as e:
        session.rollback()
        logger.error(f"迁移过程失败: {e}")
        return False
    finally:
        session.close()


def verify_migration():
    """验证迁移结果"""
    logger.info("验证迁移结果...")

    try:
        # 统计各服务器的用户数
        from sqlalchemy import func

        stats = session.query(
            Emby.server_id,
            func.count(Emby.tg)
        ).group_by(Emby.server_id).all()

        logger.info("服务器用户分布:")
        for server_id, count in stats:
            logger.info(f"  {server_id}: {count} 个用户")

        # 检查是否有空 server_id
        null_count = session.query(Emby).filter(
            (Emby.server_id == None) | (Emby.server_id == '')
        ).count()

        if null_count > 0:
            logger.warning(f"⚠️ 仍有 {null_count} 个用户的 server_id 为空")
            return False
        else:
            logger.success("✅ 所有用户都已分配 server_id")
            return True

    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False
    finally:
        session.close()


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("EmbyBot 多服务器数据迁移工具")
    logger.info("=" * 60)

    # 步骤1: 备份数据库
    logger.info("\n步骤 1/4: 备份数据库")
    if not backup_database():
        logger.error("❌ 数据库备份失败，终止迁移")
        return 1

    # 步骤2: 检查表结构
    logger.info("\n步骤 2/4: 检查表结构")
    if not check_server_id_column():
        logger.error(
            "❌ 表结构检查失败\n"
            "请先执行 SQL 迁移脚本: migrations/add_server_id.sql"
        )
        return 1

    # 步骤3: 迁移用户数据
    logger.info("\n步骤 3/4: 迁移用户数据")
    if not migrate_existing_users():
        logger.error("❌ 用户数据迁移失败")
        return 1

    # 步骤4: 验证迁移结果
    logger.info("\n步骤 4/4: 验证迁移结果")
    if not verify_migration():
        logger.error("❌ 迁移验证失败")
        return 1

    logger.success("\n" + "=" * 60)
    logger.success("✅ 数据迁移完成！")
    logger.success("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

**赋予执行权限**:
```bash
chmod +x scripts/migrate_to_multi_server.py
```

#### 步骤 6.2：迁移执行流程

**完整迁移步骤**:

```bash
# 1. 停止 Bot 服务
docker-compose down
# 或
pkill -f main.py

# 2. 备份数据库（额外保险）
mysqldump -u root -p embybot > manual_backup_$(date +%Y%m%d).sql

# 3. 执行表结构迁移
mysql -u root -p embybot < migrations/add_server_id.sql

# 4. 更新配置文件
cp config.json config.json.backup
# 手动编辑 config.json，添加 emby_servers 配置

# 5. 执行数据迁移脚本
python3 scripts/migrate_to_multi_server.py

# 6. 验证迁移结果
mysql -u root -p embybot -e "SELECT server_id, COUNT(*) FROM emby GROUP BY server_id;"

# 7. 重启 Bot
docker-compose up -d
# 或
python3 main.py
```

**回滚方案**（如果迁移失败）:
```bash
# 1. 停止服务
docker-compose down

# 2. 恢复数据库
mysql -u root -p embybot < manual_backup_YYYYMMDD.sql

# 3. 恢复配置文件
cp config.json.backup config.json

# 4. 重启服务
docker-compose up -d
```

---

### 阶段七：新增功能

#### 功能 7.1：服务器列表命令

**文件**: `bot/modules/commands/servers.py` (新建)

```python
"""
服务器管理命令
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from bot import config
from bot.func_helper.emby_utils import format_server_list_text, get_server_display_info
from bot.sql_helper.sql_emby import get_server_stats


@Client.on_message(filters.command('servers') & filters.private)
async def list_servers_handler(client: Client, message: Message):
    """
    列出所有可用服务器
    命令: /servers
    """
    text = format_server_list_text()
    await message.reply(text)


@Client.on_message(filters.command('serverinfo') & filters.private)
async def server_info_handler(client: Client, message: Message):
    """
    查看服务器详细信息
    命令: /serverinfo <server_id>
    """
    parts = message.text.split()

    if len(parts) < 2:
        await message.reply(
            "❌ 请指定服务器 ID\n"
            "用法: `/serverinfo <server_id>`\n\n"
            "查看所有服务器: /servers"
        )
        return

    server_id = parts[1]
    info = get_server_display_info(server_id)

    if not info:
        await message.reply(f"❌ 服务器不存在: {server_id}")
        return

    # 获取详细统计
    stats = get_server_stats().get(server_id, {})

    text = (
        f"**📊 服务器详情**\n\n"
        f"**名称**: {info['name']}\n"
        f"**ID**: `{info['id']}`\n"
        f"**线路**: `{info['line']}`\n"
        f"**优先级**: {info['priority']}\n"
        f"**用户数**: {info['users_count']}"
    )

    if info['max_users']:
        text += f"/{info['max_users']}"
        text += f" ({info['load_ratio']:.1%})"

    text += "\n"

    if info['is_default']:
        text += "**类型**: 🏷️ 默认服务器\n"

    # 用户等级分布
    if stats and 'by_level' in stats:
        text += "\n**用户等级分布**:\n"
        level_names = {'a': '白名单', 'b': '正常', 'c': '临时', 'd': '未注册'}
        for lv, count in stats['by_level'].items():
            text += f"  • {level_names.get(lv, lv)}: {count}\n"

    await message.reply(text)
```

**注册命令** (在 `bot/__init__.py` 中):
```python
# 导入新模块
from bot.modules.commands import servers

# 添加到命令列表
BotCommand('servers', '查看服务器列表'),
BotCommand('serverinfo', '查看服务器详情'),
```

#### 功能 7.2：服务器健康检查

**文件**: `bot/scheduler/health_check.py` (新建)

```python
"""
服务器健康检查定时任务
"""

import asyncio
from datetime import datetime
from loguru import logger

from bot import config, emby_manager
from bot.func_helper.msg_utils import send_message


async def health_check_task():
    """
    健康检查任务
    定期检查所有服务器状态
    """
    logger.info("开始服务器健康检查...")

    results = await emby_manager.health_check()

    # 统计结果
    healthy_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    logger.info(
        f"健康检查完成: {healthy_count}/{total_count} 个服务器正常"
    )

    # 检查是否有服务器异常
    unhealthy_servers = [
        server_id for server_id, is_healthy in results.items()
        if not is_healthy
    ]

    if unhealthy_servers:
        await notify_unhealthy_servers(unhealthy_servers)


async def notify_unhealthy_servers(server_ids: list):
    """通知管理员服务器异常"""
    from bot import owner

    text = "⚠️ **服务器健康检查告警**\n\n"
    text += f"检测到 {len(server_ids)} 个服务器异常:\n\n"

    for server_id in server_ids:
        server_config = config.get_server_by_id(server_id)
        if server_config:
            text += f"❌ {server_config.name} ({server_id})\n"
        else:
            text += f"❌ {server_id}\n"

    text += f"\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # 发送给所有管理员
    await send_message(owner, text)

    logger.warning(f"已发送健康检查告警: {server_ids}")


async def ping_server(server_id: str) -> bool:
    """
    Ping 单个服务器

    Returns:
        是否在线
    """
    emby_service = emby_manager.get_server(server_id)
    if not emby_service:
        return False

    try:
        result = await emby_service.get_system_info()
        return result.success
    except Exception as e:
        logger.error(f"Ping 服务器失败 {server_id}: {e}")
        return False
```

**注册定时任务** (在 `bot/func_helper/scheduler.py` 中):
```python
from bot.scheduler.health_check import health_check_task

# 添加健康检查任务（每 10 分钟）
scheduler.add_job(
    health_check_task,
    'interval',
    minutes=10,
    id='health_check',
    name='服务器健康检查'
)
```

---

## 三、测试方案

### 3.1 单元测试

**文件**: `tests/test_multi_server.py` (新建)

```python
"""
多服务器功能单元测试
"""

import pytest
import asyncio
from bot import config, emby_manager
from bot.func_helper.emby_utils import (
    get_user_emby_service,
    select_available_server,
    validate_server_id
)
from bot.sql_helper.sql_emby import add_emby, get_emby, delete_emby


class TestMultiServer:
    """多服务器功能测试"""

    def test_config_loading(self):
        """测试配置加载"""
        assert config is not None
        assert len(config.emby_servers) > 0
        assert config.get_default_server() is not None

    def test_server_registration(self):
        """测试服务器注册"""
        assert emby_manager.get_server_count() > 0

        for server_config in config.emby_servers:
            if server_config.enabled:
                assert emby_manager.has_server(server_config.id)

    def test_server_selection(self):
        """测试服务器选择"""
        server = select_available_server()
        assert server is not None
        assert server.enabled is True

    def test_server_validation(self):
        """测试服务器验证"""
        # 有效的服务器 ID
        default_server = config.get_default_server()
        assert validate_server_id(default_server.id) is True

        # 无效的服务器 ID
        assert validate_server_id('invalid_server') is False
        assert validate_server_id(None) is False

    @pytest.mark.asyncio
    async def test_user_operations(self):
        """测试用户操作"""
        test_tg = 999999999
        test_server_id = config.get_default_server().id

        # 添加测试用户
        result = add_emby(
            tg=test_tg,
            server_id=test_server_id,
            embyid='test_emby_id',
            name='test_user',
            pwd='test_pwd'
        )
        assert result is True

        # 查询用户
        user = get_emby(test_tg)
        assert user is not None
        assert user.server_id == test_server_id

        # 获取服务实例
        emby_service, server_config, user_obj = get_user_emby_service(test_tg)
        assert emby_service is not None
        assert server_config.id == test_server_id
        assert user_obj.tg == test_tg

        # 清理测试数据
        delete_emby(test_tg)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

### 3.2 集成测试

**测试脚本**: `scripts/test_integration.sh`

```bash
#!/bin/bash
# 集成测试脚本

echo "=== EmbyBot 多服务器集成测试 ==="

# 1. 测试配置加载
echo "1. 测试配置加载..."
python3 -c "from bot import config; print(f'服务器数量: {len(config.emby_servers)}')"

# 2. 测试服务器注册
echo "2. 测试服务器注册..."
python3 -c "from bot import emby_manager; print(f'已注册: {emby_manager.list_server_ids()}')"

# 3. 测试数据库连接
echo "3. 测试数据库连接..."
python3 -c "from bot.sql_helper.sql_emby import get_server_stats; print(get_server_stats())"

# 4. 测试健康检查
echo "4. 测试健康检查..."
python3 -c "import asyncio; from bot import emby_manager; asyncio.run(emby_manager.health_check())"

echo "=== 测试完成 ==="
```

---

## 四、部署指南

### 4.1 Docker 部署

**更新 Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p logs backups migrations scripts

# 运行迁移（如果需要）
# RUN python3 scripts/migrate_to_multi_server.py

CMD ["python3", "main.py"]
```

**更新 docker-compose.yml**:
```yaml
version: '3.8'

services:
  embybot:
    build: .
    container_name: embybot-multi
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
      - ./backups:/app/backups
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    depends_on:
      - mysql

  mysql:
    image: mysql:8.0
    container_name: embybot-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: embybot
    volumes:
      - mysql_data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d
    restart: unless-stopped

volumes:
  mysql_data:
```

### 4.2 生产环境部署清单

**部署前检查**:
- [ ] 完成数据库备份
- [ ] 更新配置文件格式
- [ ] 执行表结构迁移
- [ ] 运行数据迁移脚本
- [ ] 验证迁移结果
- [ ] 更新代码到最新版本
- [ ] 运行单元测试
- [ ] 准备回滚方案

**部署步骤**:
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 停止服务
docker-compose down

# 3. 执行迁移
python3 scripts/migrate_to_multi_server.py

# 4. 重新构建镜像
docker-compose build

# 5. 启动服务
docker-compose up -d

# 6. 查看日志
docker-compose logs -f embybot

# 7. 健康检查
python3 scripts/health_check.py
```

---

## 五、维护与监控

### 5.1 日志监控

**关键日志点**:
- 服务器注册: `EmbyServerManager 初始化完成`
- 用户操作: `获取用户 Emby 服务实例`
- 健康检查: `健康检查完成`
- 错误告警: `服务器实例不存在`

**日志查看**:
```bash
# 查看最近的错误日志
tail -f logs/error.log

# 查看特定服务器的日志
grep "server_id=main" logs/embybot.log

# 统计各服务器操作次数
grep "server_id=" logs/embybot.log | awk -F'server_id=' '{print $2}' | awk '{print $1}' | sort | uniq -c
```

### 5.2 性能监控

**监控指标**:
- 各服务器用户数分布
- API 请求成功率
- 响应时间
- 连接池使用情况

**监控脚本**: `scripts/monitor.py`
```python
#!/usr/bin/env python3
"""性能监控脚本"""

from bot.sql_helper.sql_emby import get_server_stats

def show_server_metrics():
    """显示服务器指标"""
    stats = get_server_stats()

    print("=== Emby 服务器统计 ===")
    for server_id, data in stats.items():
        print(f"\n服务器: {server_id}")
        print(f"  总用户数: {data['total']}")
        print(f"  等级分布: {data['by_level']}")

if __name__ == '__main__':
    show_server_metrics()
```

---

## 六、常见问题

### Q1: 如何添加新服务器？
**A**: 编辑 `config.json`，在 `emby_servers` 数组中添加新配置，重启 Bot 即可。

### Q2: 用户可以在多个服务器上吗？
**A**: 当前设计中，一个用户只能绑定一个服务器。如需支持多服务器，需要修改数据库主键。

### Q3: 如何迁移用户到其他服务器？
**A**: 使用 `/switchserver` 命令（管理员），或调用 `update_emby_server_id()` 函数。

### Q4: 服务器宕机如何处理？
**A**: 健康检查会自动发送告警。手动处理：禁用服务器、迁移用户、修复后重新启用。

### Q5: 如何回滚到单服务器模式？
**A**: 恢复数据库备份和旧版配置文件，重新部署旧版代码。

---

## 七、更新日志

### v1.0 (2025-11-24)
- ✅ 完成多服务器架构设计
- ✅ 实现服务器管理器
- ✅ 完成数据库迁移方案
- ✅ 适配所有核心业务逻辑
- ✅ 新增服务器管理命令
- ✅ 实现健康检查机制

---

## 八、参考资料

- Emby API 文档: https://swagger.emby.media/
- SQLAlchemy 文档: https://docs.sqlalchemy.org/
- Pyrogram 文档: https://docs.pyrogram.org/
- Pydantic 文档: https://docs.pydantic.dev/

---

**文档结束**

如有问题，请联系开发团队或提交 Issue。
