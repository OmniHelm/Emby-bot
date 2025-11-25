"""
Emby 用户表操作
用户基础信息管理（不含多服务器绑定，绑定信息在 sql_server_bindings.py）
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, Integer, case, Index
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from bot import LOGGER
from bot.sql_helper import Base, Session, engine


class Emby(Base):
    """
    Emby 用户表
    存储用户基础信息，embyid 为首次注册的服务器 ID（向后兼容）
    多服务器绑定关系存储在 emby_server_bindings 表
    """
    __tablename__ = 'emby'

    tg = Column(BigInteger, primary_key=True, autoincrement=False, comment='Telegram 用户 ID')
    embyid = Column(String(255), nullable=True, index=True, comment='首次注册的 Emby 用户 ID（向后兼容）')
    name = Column(String(255), nullable=True, index=True, comment='Emby 用户名（所有服务器统一）')
    pwd = Column(String(255), nullable=True, comment='密码（所有服务器统一）')
    pwd2 = Column(String(255), nullable=True, comment='备用密码')
    lv = Column(String(1), default='d', index=True, comment='用户等级 a=白名单/b=正常/c=临时/d=未注册')
    cr = Column(DateTime, nullable=True, comment='创建时间')
    ex = Column(DateTime, nullable=True, index=True, comment='到期时间（所有服务器统一）')
    us = Column(Integer, default=0, comment='用户积分')
    iv = Column(Integer, default=0, comment='用户币/credits')
    ch = Column(DateTime, nullable=True, comment='修改时间')


# 创建表（如果不存在）
Emby.__table__.create(bind=engine, checkfirst=True)


# ==================== 基础 CRUD 操作 ====================

def sql_add_emby(tg: int):
    """
    添加一条 emby 记录，如果 tg 已存在则忽略
    """
    with Session() as session:
        try:
            emby = Emby(tg=tg)
            session.add(emby)
            session.commit()
            LOGGER.debug(f"添加 emby 记录成功 tg={tg}")
            return True
        except IntegrityError:
            session.rollback()
            LOGGER.debug(f"emby 记录已存在 tg={tg}")
            return False
        except Exception as e:
            session.rollback()
            LOGGER.error(f"添加 emby 记录失败 tg={tg} err={e}")
            return False


def sql_get_emby(tg):
    """
    查询一条 emby 记录，可以根据 tg, embyid 或者 name 来查询
    """
    with Session() as session:
        try:
            emby = session.query(Emby).filter(
                or_(Emby.tg == tg, Emby.name == tg, Emby.embyid == tg)
            ).first()
            return emby
        except Exception as e:
            LOGGER.error(f"查询 emby 记录失败 tg={tg} err={e}")
            return None


def sql_update_emby(condition, **kwargs):
    """
    更新一条 emby 记录，根据 condition 来匹配，然后更新其他的字段
    """
    with Session() as session:
        try:
            emby = session.query(Emby).filter(condition).first()
            if emby is None:
                return False
            for k, v in kwargs.items():
                if hasattr(Emby, k):
                    setattr(emby, k, v)
            session.commit()
            return True
        except Exception as e:
            LOGGER.error(f"更新 emby 记录失败: {e}")
            session.rollback()
            return False


def sql_delete_emby(tg=None, embyid=None, name=None):
    """
    根据 tg, embyid 或 name 删除一条 emby 记录
    至少需要提供一个参数
    """
    with Session() as session:
        try:
            conditions = []
            if tg is not None:
                conditions.append(Emby.tg == tg)
            if embyid is not None:
                conditions.append(Emby.embyid == embyid)
            if name is not None:
                conditions.append(Emby.name == name)

            if not conditions:
                LOGGER.warning("sql_delete_emby: 所有参数都为 None，无法删除记录")
                return False

            condition = or_(*conditions)
            emby = session.query(Emby).filter(condition).with_for_update().first()
            if emby:
                LOGGER.info(f"删除数据库记录 {emby.name} - {emby.embyid} - {emby.tg}")
                session.delete(emby)
                session.commit()
                return True
            else:
                LOGGER.info(f"数据库记录不存在: tg={tg}, embyid={embyid}, name={name}")
                return False
        except Exception as e:
            LOGGER.error(f"删除数据库记录时发生异常 {e}")
            session.rollback()
            return False


def sql_delete_emby_by_tg(tg):
    """
    根据 tg 删除一条 emby 记录
    """
    with Session() as session:
        try:
            emby = session.query(Emby).filter(Emby.tg == tg).first()
            if emby:
                session.delete(emby)
                session.commit()
                LOGGER.info(f"删除数据库记录成功 {tg}")
                return True
            else:
                LOGGER.info(f"数据库记录不存在 {tg}")
                return False
        except Exception as e:
            LOGGER.error(f"删除数据库记录时发生异常 {e}")
            session.rollback()
            return False


# ==================== 批量操作 ====================

def sql_update_embys(some_list: list, method=None):
    """
    根据 list 中的 tg 值批量更新，此方法不可更新主键
    """
    with Session() as session:
        if method == 'iv':
            try:
                mappings = [{"tg": c[0], "iv": c[1]} for c in some_list]
                session.bulk_update_mappings(Emby, mappings)
                session.commit()
                return True
            except Exception as e:
                LOGGER.error(f"批量更新 iv 失败: {e}")
                session.rollback()
                return False
        if method == 'ex':
            try:
                mappings = [{"tg": c[0], "ex": c[1]} for c in some_list]
                session.bulk_update_mappings(Emby, mappings)
                session.commit()
                return True
            except Exception as e:
                LOGGER.error(f"批量更新 ex 失败: {e}")
                session.rollback()
                return False
        if method == 'bind':
            try:
                mappings = [{"tg": c[0], "name": c[1], "embyid": c[2]} for c in some_list]
                session.bulk_update_mappings(Emby, mappings)
                session.commit()
                return True
            except Exception as e:
                LOGGER.error(f"批量更新 bind 失败: {e}")
                session.rollback()
                return False


def sql_clear_emby_iv():
    """
    清除所有 emby 的 iv
    """
    with Session() as session:
        try:
            session.query(Emby).update({Emby.iv: 0})
            session.commit()
            return True
        except Exception as e:
            LOGGER.error(f"清除所有 emby 的 iv 时发生异常 {e}")
            session.rollback()
            return False


# ==================== 查询操作 ====================

def get_all_emby(condition):
    """
    查询所有符合条件的 emby 记录
    """
    with Session() as session:
        try:
            embies = session.query(Emby).filter(condition).all()
            return embies
        except Exception as e:
            LOGGER.error(f"查询 emby 列表失败: {e}")
            return None


def sql_count_emby():
    """
    统计 emby 记录数量
    :return: (tg_count, embyid_count, lv_a_count)
    """
    with Session() as session:
        try:
            count = session.query(
                func.count(Emby.tg).label("tg_count"),
                func.count(Emby.embyid).label("embyid_count"),
                func.count(case((Emby.lv == "a", 1))).label("lv_a_count")
            ).first()
            return count.tg_count, count.embyid_count, count.lv_a_count
        except Exception as e:
            LOGGER.error(f"统计 emby 失败: {e}")
            return None, None, None


def get_expired_users():
    """
    获取所有已过期的用户列表
    """
    with Session() as session:
        try:
            result = session.query(Emby).filter(
                Emby.ex.isnot(None),
                Emby.ex < datetime.now(),
                Emby.lv != 'a'  # 白名单用户不过期
            ).all()
            return result
        except Exception as e:
            LOGGER.error(f"查询过期用户失败: {e}")
            return []


def get_users_by_level(lv: str):
    """
    获取指定等级的所有用户
    """
    with Session() as session:
        try:
            return session.query(Emby).filter(Emby.lv == lv).all()
        except Exception as e:
            LOGGER.error(f"查询等级用户失败 lv={lv}: {e}")
            return []


def get_registered_users():
    """
    获取所有已注册用户（有 embyid 的）
    """
    with Session() as session:
        try:
            return session.query(Emby).filter(Emby.embyid.isnot(None)).all()
        except Exception as e:
            LOGGER.error(f"查询已注册用户失败: {e}")
            return []
