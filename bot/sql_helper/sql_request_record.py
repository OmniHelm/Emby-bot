from sqlalchemy import Column, String, DateTime, BigInteger, Text, Float
import datetime
from bot.sql_helper import Base, Session, engine
from cacheout import Cache

cache = Cache()


class RequestRecord(Base):
    __tablename__ = 'request_records'
    download_id = Column(String(255), primary_key=True, autoincrement=False)
    tg = Column(BigInteger, nullable=False)
    request_name = Column(String(255), nullable=False)
    cost = Column(String(255), nullable=False)
    detail = Column(Text, nullable=False)
    left_time = Column(String(255))
    download_state= Column(String(50), default='pending')  # pending, downloading, completed, failed
    transfer_state = Column(String(50))  # success, failed
    progress = Column(Float, default=0)
    create_at = Column(DateTime, default=datetime.datetime.utcnow)
    update_at = Column(DateTime, default=datetime.datetime.utcnow,
                      onupdate=datetime.datetime.utcnow)


RequestRecord.__table__.create(bind=engine, checkfirst=True)


def sql_add_request_record(tg: int, download_id: str, request_name: str, detail: str, cost: str):
    with Session() as session:
        try:
            request_record = RequestRecord(
                tg=tg, download_id=download_id, request_name=request_name, detail=detail, cost=cost, left_time='一万年吧')
            session.add(request_record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False


def sql_get_request_record_by_tg(tg: int, page: int = 1, limit: int = 5):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(
            RequestRecord.tg == tg).order_by(RequestRecord.create_at.desc()).limit(limit + 1).offset((page - 1) * limit).all()
        if len(request_record) == 0:
            return None, False, False
        if len(request_record) == limit + 1:
            has_next = True
            request_record = request_record[:-1]
        else:
            has_next = False
        if page > 1:
            has_prev = True
        else:
            has_prev = False
        return request_record, has_prev, has_next

def sql_get_request_record_by_download_id(download_id: str):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(RequestRecord.download_id == download_id).first()
        return request_record

def sql_get_request_record_by_transfer_state(transfer_state: str = None):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(RequestRecord.transfer_state == transfer_state).all()
        return request_record


def sql_update_request_status(download_id: str, download_state: str, transfer_state: str = None, progress: float = None, left_time: str = None):
    """更新下载状态"""
    with Session() as session:
        try:
            record = session.query(RequestRecord).filter(
                RequestRecord.download_id == download_id).first()
            if record:
                if download_state is not None:
                    record.download_state = download_state
                if transfer_state is not None:
                    record.transfer_state = transfer_state
                if progress is not None:
                    record.progress = progress
                if left_time is not None:
                    record.left_time = left_time
                session.commit()
                return True
        except Exception as e:
            session.rollback()
            return False


def sql_get_movie_requests(status: str = None, page: int = 1, limit: int = 10):
    """
    获取求片记录（download_id 以 'tmdb_' 开头的记录）

    :param status: 状态筛选 (pending/completed/failed 等)，None 表示所有状态
    :param page: 页码
    :param limit: 每页数量
    :return: (记录列表, 是否有上一页, 是否有下一页)
    """
    with Session() as session:
        query = session.query(RequestRecord).filter(
            RequestRecord.download_id.like('tmdb_%')
        )

        if status:
            query = query.filter(RequestRecord.download_state == status)

        query = query.order_by(RequestRecord.create_at.desc())

        # 获取 limit + 1 条记录来判断是否有下一页
        records = query.limit(limit + 1).offset((page - 1) * limit).all()

        if len(records) == 0:
            return None, False, False

        has_next = len(records) == limit + 1
        if has_next:
            records = records[:-1]

        has_prev = page > 1

        return records, has_prev, has_next


def sql_get_all_movie_requests_for_export():
    """
    获取所有求片记录用于导出

    :return: 所有求片记录列表
    """
    with Session() as session:
        records = session.query(RequestRecord).filter(
            RequestRecord.download_id.like('tmdb_%')
        ).order_by(RequestRecord.create_at.desc()).all()
        return records


def sql_get_movie_request_stats():
    """
    获取求片统计信息

    :return: 字典，包含总数、待处理、已完成等统计
    """
    with Session() as session:
        total = session.query(RequestRecord).filter(
            RequestRecord.download_id.like('tmdb_%')
        ).count()

        pending = session.query(RequestRecord).filter(
            RequestRecord.download_id.like('tmdb_%'),
            RequestRecord.download_state == 'pending'
        ).count()

        completed = session.query(RequestRecord).filter(
            RequestRecord.download_id.like('tmdb_%'),
            RequestRecord.download_state == 'completed'
        ).count()

        return {
            'total': total,
            'pending': pending,
            'completed': completed
        }
