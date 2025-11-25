"""
用户-服务器绑定表操作
管理用户在多个 Emby 服务器上的账号绑定关系
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Index

from bot import LOGGER
from bot.sql_helper import Base, Session, engine


class EmbyServerBinding(Base):
    """
    用户-服务器绑定表
    记录用户在各 Emby 服务器上的账号信息
    """
    __tablename__ = 'emby_server_bindings'

    tg = Column(BigInteger, primary_key=True, comment='Telegram 用户 ID')
    server_id = Column(String(50), primary_key=True, comment='服务器 ID')
    embyid = Column(String(255), nullable=False, comment='该服务器上的 Emby 用户 ID')
    is_primary = Column(Boolean, default=False, comment='是否为主服务器')
    enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.now, comment='绑定时间')

    __table_args__ = (
        Index('idx_bindings_server_id', 'server_id'),
        Index('idx_bindings_embyid', 'server_id', 'embyid'),
        Index('idx_bindings_primary', 'tg', 'is_primary'),
    )


# 创建表（如果不存在）
EmbyServerBinding.__table__.create(bind=engine, checkfirst=True)


# ==================== 基础 CRUD 操作 ====================

def add_binding(tg: int, server_id: str, embyid: str, is_primary: bool = False) -> bool:
    """
    添加用户-服务器绑定

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID
        embyid: 该服务器上的 Emby 用户 ID
        is_primary: 是否为主服务器

    Returns:
        是否成功
    """
    with Session() as session:
        try:
            binding = EmbyServerBinding(
                tg=tg,
                server_id=server_id,
                embyid=embyid,
                is_primary=is_primary,
                enabled=True,
                created_at=datetime.now()
            )
            session.add(binding)
            session.commit()
            LOGGER.info(f"添加绑定成功: tg={tg}, server={server_id}, embyid={embyid}")
            return True
        except Exception as e:
            session.rollback()
            LOGGER.error(f"添加绑定失败 tg={tg}, server={server_id}: {e}")
            return False


def get_binding(tg: int, server_id: str) -> Optional[EmbyServerBinding]:
    """
    获取指定用户在指定服务器的绑定

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID

    Returns:
        EmbyServerBinding 对象或 None
    """
    with Session() as session:
        try:
            return session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg,
                EmbyServerBinding.server_id == server_id
            ).first()
        except Exception as e:
            LOGGER.error(f"查询绑定失败 tg={tg}, server={server_id}: {e}")
            return None


def get_user_bindings(tg: int, enabled_only: bool = True) -> List[EmbyServerBinding]:
    """
    获取用户的所有服务器绑定

    Args:
        tg: Telegram 用户 ID
        enabled_only: 是否只返回启用的绑定

    Returns:
        EmbyServerBinding 对象列表
    """
    with Session() as session:
        try:
            query = session.query(EmbyServerBinding).filter(EmbyServerBinding.tg == tg)
            if enabled_only:
                query = query.filter(EmbyServerBinding.enabled == True)
            return query.all()
        except Exception as e:
            LOGGER.error(f"查询用户绑定失败 tg={tg}: {e}")
            return []


def get_primary_binding(tg: int) -> Optional[EmbyServerBinding]:
    """
    获取用户的主服务器绑定

    Args:
        tg: Telegram 用户 ID

    Returns:
        EmbyServerBinding 对象或 None
    """
    with Session() as session:
        try:
            return session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg,
                EmbyServerBinding.is_primary == True
            ).first()
        except Exception as e:
            LOGGER.error(f"查询主绑定失败 tg={tg}: {e}")
            return None


def get_server_bindings(server_id: str, enabled_only: bool = True) -> List[EmbyServerBinding]:
    """
    获取指定服务器的所有用户绑定

    Args:
        server_id: 服务器 ID
        enabled_only: 是否只返回启用的绑定

    Returns:
        EmbyServerBinding 对象列表
    """
    with Session() as session:
        try:
            query = session.query(EmbyServerBinding).filter(
                EmbyServerBinding.server_id == server_id
            )
            if enabled_only:
                query = query.filter(EmbyServerBinding.enabled == True)
            return query.all()
        except Exception as e:
            LOGGER.error(f"查询服务器绑定失败 server={server_id}: {e}")
            return []


def update_binding(tg: int, server_id: str, **kwargs) -> bool:
    """
    更新绑定信息

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID
        **kwargs: 要更新的字段 (embyid, is_primary, enabled)

    Returns:
        是否成功
    """
    with Session() as session:
        try:
            binding = session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg,
                EmbyServerBinding.server_id == server_id
            ).first()
            if not binding:
                LOGGER.warning(f"绑定不存在 tg={tg}, server={server_id}")
                return False
            for k, v in kwargs.items():
                if hasattr(binding, k):
                    setattr(binding, k, v)
            session.commit()
            LOGGER.info(f"更新绑定成功: tg={tg}, server={server_id}")
            return True
        except Exception as e:
            session.rollback()
            LOGGER.error(f"更新绑定失败 tg={tg}, server={server_id}: {e}")
            return False


def delete_binding(tg: int, server_id: str) -> bool:
    """
    删除绑定

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID

    Returns:
        是否成功
    """
    with Session() as session:
        try:
            result = session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg,
                EmbyServerBinding.server_id == server_id
            ).delete()
            session.commit()
            if result:
                LOGGER.info(f"删除绑定成功: tg={tg}, server={server_id}")
            return result > 0
        except Exception as e:
            session.rollback()
            LOGGER.error(f"删除绑定失败 tg={tg}, server={server_id}: {e}")
            return False


def delete_user_bindings(tg: int) -> int:
    """
    删除用户的所有绑定

    Args:
        tg: Telegram 用户 ID

    Returns:
        删除的记录数
    """
    with Session() as session:
        try:
            result = session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg
            ).delete()
            session.commit()
            LOGGER.info(f"删除用户所有绑定: tg={tg}, count={result}")
            return result
        except Exception as e:
            session.rollback()
            LOGGER.error(f"删除用户绑定失败 tg={tg}: {e}")
            return 0


# ==================== 业务操作 ====================

def set_primary_binding(tg: int, server_id: str) -> bool:
    """
    设置主服务器（会取消其他绑定的主服务器标记）

    Args:
        tg: Telegram 用户 ID
        server_id: 要设为主服务器的服务器 ID

    Returns:
        是否成功
    """
    with Session() as session:
        try:
            # 先取消所有主服务器标记
            session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg,
                EmbyServerBinding.is_primary == True
            ).update({EmbyServerBinding.is_primary: False})

            # 设置新的主服务器
            result = session.query(EmbyServerBinding).filter(
                EmbyServerBinding.tg == tg,
                EmbyServerBinding.server_id == server_id
            ).update({EmbyServerBinding.is_primary: True})

            session.commit()
            if result:
                LOGGER.info(f"设置主服务器成功: tg={tg}, server={server_id}")
            return result > 0
        except Exception as e:
            session.rollback()
            LOGGER.error(f"设置主服务器失败 tg={tg}, server={server_id}: {e}")
            return False


def get_embyid_by_server(tg: int, server_id: str) -> Optional[str]:
    """
    获取用户在指定服务器的 embyid

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID

    Returns:
        embyid 或 None
    """
    binding = get_binding(tg, server_id)
    return binding.embyid if binding else None


def get_user_server_ids(tg: int, enabled_only: bool = True) -> List[str]:
    """
    获取用户绑定的所有服务器 ID

    Args:
        tg: Telegram 用户 ID
        enabled_only: 是否只返回启用的

    Returns:
        服务器 ID 列表
    """
    bindings = get_user_bindings(tg, enabled_only)
    return [b.server_id for b in bindings]


def count_server_users(server_id: str, enabled_only: bool = True) -> int:
    """
    统计服务器的用户数

    Args:
        server_id: 服务器 ID
        enabled_only: 是否只统计启用的

    Returns:
        用户数量
    """
    with Session() as session:
        try:
            query = session.query(EmbyServerBinding).filter(
                EmbyServerBinding.server_id == server_id
            )
            if enabled_only:
                query = query.filter(EmbyServerBinding.enabled == True)
            return query.count()
        except Exception as e:
            LOGGER.error(f"统计服务器用户失败 server={server_id}: {e}")
            return 0


def has_binding(tg: int, server_id: str) -> bool:
    """
    检查用户是否已绑定指定服务器

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID

    Returns:
        是否已绑定
    """
    return get_binding(tg, server_id) is not None


def add_or_update_binding(tg: int, server_id: str, embyid: str, is_primary: bool = False) -> bool:
    """
    添加或更新绑定（如果已存在则更新）

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID
        embyid: Emby 用户 ID
        is_primary: 是否为主服务器

    Returns:
        是否成功
    """
    if has_binding(tg, server_id):
        return update_binding(tg, server_id, embyid=embyid, is_primary=is_primary)
    else:
        return add_binding(tg, server_id, embyid, is_primary)
