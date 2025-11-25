from bot.sql_helper import Base, Session, engine
from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from bot import LOGGER


class Emby2(Base):
    """
    emby2 用户表（非 TG 用户）
    新增 server_id 字段支持多服务器
    """
    __tablename__ = 'emby2'
    embyid = Column(String(255), primary_key=True, autoincrement=False, comment='Emby 用户 ID')

    # 新增：服务器标识字段
    server_id = Column(
        String(50),
        nullable=False,
        default='main',
        index=True,
        comment='关联的 Emby 服务器 ID'
    )

    name = Column(String(255), nullable=True, comment='用户名')
    pwd = Column(String(255), nullable=True, comment='密码')
    pwd2 = Column(String(255), nullable=True, comment='备用密码')
    lv = Column(String(1), default='d', comment='用户等级')
    cr = Column(DateTime, nullable=True, comment='创建时间')
    ex = Column(DateTime, nullable=True, comment='过期时间')
    expired = Column(Integer, nullable=True, comment='过期标记')

    # 添加联合索引
    __table_args__ = (
        Index('idx_emby2_server_id', 'server_id'),
        Index('idx_emby2_server_name', 'server_id', 'name'),
        Index('idx_emby2_server_lv', 'server_id', 'lv'),
    )


Emby2.__table__.create(bind=engine, checkfirst=True)


def sql_add_emby2(embyid, name, cr, ex, server_id='main', pwd='5210', pwd2='1234', lv='b', expired=0):
    """
    添加一条 emby2 记录（多服务器版本）

    Args:
        embyid: Emby 用户 ID
        name: 用户名
        cr: 创建时间
        ex: 过期时间
        server_id: 服务器 ID，默认 'main'
        pwd: 密码
        pwd2: 备用密码
        lv: 用户等级
        expired: 过期标记

    Returns:
        是否成功
    """
    with Session() as session:
        try:
            emby = Emby2(
                embyid=embyid,
                server_id=server_id,
                name=name,
                pwd=pwd,
                pwd2=pwd2,
                lv=lv,
                cr=cr,
                ex=ex,
                expired=expired
            )
            session.add(emby)
            session.commit()
            LOGGER.info(f"添加 emby2 记录成功: embyid={embyid}, server={server_id}, name={name}")
            return True
        except IntegrityError:
            session.rollback()
            LOGGER.debug(f"emby2 记录已存在 embyid={embyid}")
            return False
        except Exception as e:
            session.rollback()
            LOGGER.error(f"添加 emby2 记录失败 embyid={embyid} err={e}")
            return False


def sql_get_emby2(name, server_id=None):
    """
    查询一条 emby2 记录（多服务器版本）

    Args:
        name: 用户名或 embyid
        server_id: 可选，指定服务器 ID。如果为 None，返回任意服务器的用户

    Returns:
        Emby2 对象或 None
    """
    with Session() as session:
        try:
            query = session.query(Emby2).filter(
                or_(Emby2.name == name, Emby2.embyid == name)
            )
            if server_id:
                query = query.filter(Emby2.server_id == server_id)
            emby = query.first()
            return emby
        except Exception as e:
            LOGGER.error(f"查询 emby2 记录失败 name={name}, server_id={server_id} err={e}")
            return None


def get_all_emby2(condition):
    """
    查询所有emby记录
    """
    with Session() as session:
        try:
            embies = session.query(Emby2).filter(condition).all()
            return embies
        except Exception as e:
            LOGGER.error(f"查询 emby2 列表失败: {e}")
            return None


def sql_update_emby2(condition, **kwargs):
    """
    更新一条emby记录，根据condition来匹配，然后更新其他的字段
    """
    with Session() as session:
        try:
            # 用filter来过滤，注意要加括号
            emby = session.query(Emby2).filter(condition).first()
            if emby is None:
                return False
            # 然后用setattr方法来更新其他的字段，如果有就更新，如果没有就保持原样
            for k, v in kwargs.items():
                setattr(emby, k, v)
            session.commit()
            return True
        except Exception as e:
            LOGGER.error(f"更新 emby2 记录失败: {e}")
            session.rollback()
            return False


def sql_delete_emby2(embyid):
    """
    根据tg删除一条emby记录
    """
    with Session() as session:
        try:
            emby = session.query(Emby2).filter_by(embyid=embyid).first()
            if emby:
                session.delete(emby)
                try:
                    session.commit()
                    return True
                except Exception as e:
                    # 记录错误信息
                    print(e)
                    # 回滚事务
                    session.rollback()
                    return False
            else:
                return None
        except Exception as e:
            # 记录错误信息
            print(e)
            return False
def sql_delete_emby2_by_name(name):
    """
    根据name删除一条emby记录
    """
    with Session() as session:
        try:
            emby = session.query(Emby2).filter_by(name=name).first()
            if emby:
                session.delete(emby)
                session.commit()
                return True
            else:
                return False
        except Exception as e:
            # 记录错误信息
            print(e)
            return False


# ==================== 多服务器支持函数 ====================

def get_all_emby2_by_server(server_id: str):
    """
    获取指定服务器的所有 emby2 用户

    Args:
        server_id: 服务器 ID

    Returns:
        Emby2 对象列表
    """
    with Session() as session:
        try:
            result = session.query(Emby2).filter(Emby2.server_id == server_id).all()
            return result
        except Exception as e:
            LOGGER.error(f"查询 emby2 服务器用户失败 server_id={server_id}: {e}")
            return []


def count_emby2_by_server(server_id: str) -> int:
    """
    统计指定服务器的 emby2 用户数

    Args:
        server_id: 服务器 ID

    Returns:
        用户数量
    """
    with Session() as session:
        try:
            count = session.query(Emby2).filter(Emby2.server_id == server_id).count()
            return count
        except Exception as e:
            LOGGER.error(f"统计 emby2 用户失败 server_id={server_id}: {e}")
            return 0


def get_expired_emby2_users(server_id: str = None):
    """
    获取已过期的 emby2 用户列表

    Args:
        server_id: 可选，服务器 ID

    Returns:
        Emby2 对象列表
    """
    from datetime import datetime
    with Session() as session:
        try:
            query = session.query(Emby2).filter(
                Emby2.ex.isnot(None),
                Emby2.ex < datetime.now()
            )
            if server_id:
                query = query.filter(Emby2.server_id == server_id)
            result = query.all()
            return result
        except Exception as e:
            LOGGER.error(f"查询过期 emby2 用户失败 server_id={server_id}: {e}")
            return []
