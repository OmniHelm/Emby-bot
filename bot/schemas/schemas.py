import json
import os
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional, Union
from typing_extensions import Self

# 嵌套式的数据设计，规范数据 config.json

MAX_INT_VALUE = 2147483647  # 2^31 - 1
MIN_INT_VALUE = -2147483648  # -2^31

class ExDate(BaseModel):
    mon: int = 30
    sea: int = 90
    half: int = 180
    year: int = 365
    used: int = 0
    unused: int = -1
    code: str = 'code'
    link: str = 'link'


class EmbyServerConfig(BaseModel):
    """
    单个 Emby 服务器配置

    用于管理不同内容类型的服务器（如：动漫服、电影服、剧集服）
    每个服务器独立运行，用户手动选择访问哪个服务器
    """
    id: str = Field(..., description="服务器唯一标识（如：anime, movie, series）")
    name: str = Field(..., description="服务器显示名称（如：动漫服务器、电影服务器）")
    api_key: str = Field(..., description="Emby API 密钥")
    url: str = Field(..., description="服务器内部访问地址")
    line: str = Field(..., description="用户访问线路地址")
    whitelist_line: Optional[str] = Field(None, description="白名单用户专属线路（可选）")
    enabled: bool = Field(True, description="是否启用该服务器")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """验证 ID 格式：只能包含字母、数字、下划线、连字符"""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("服务器 ID 必须是字母数字或下划线、连字符组合")
        return v

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证并标准化 URL"""
        v = v.rstrip('/')
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        return v


# class UserBuy(BaseModel):
#     stat: StrictBool
#
#     # 转换 字符串为布尔
#     @field_validator('stat', mode='before')
#     def convert_to_bool(cls, v):
#         if isinstance(v, str):
#             return v.lower() == 'y'
#         return v
#
#     text: bool
#     button: List[str]


class Open(BaseModel):
    stat: bool
    open_us: int = 30
    all_user: int
    timing: int = 0
    tem: Optional[int] = 0
    # allow_code: StrictBool
    # @field_validator('allow_code', mode='before')
    # def convert_to_bool(cls, v):
    #     if isinstance(v, str):
    #         return v.lower() == 'y'
    #     return v

    checkin: bool
    exchange: bool
    whitelist: bool
    invite: bool
    invite_lv: Optional[str] = 'b'
    leave_ban: bool
    uplays: bool = True
    checkin_reward: Optional[List[int]] = [1, 10]
    exchange_cost: int = 300
    whitelist_cost: int = 9999
    invite_cost: int = 1000

    @model_validator(mode='after')
    def reset_timing(self) -> Self:
        """每次创建 Open 对象时将 timing 重置为 0"""
        self.timing = 0
        return self


class Ranks(BaseModel):
    logo: str = "EmbyBot"
    backdrop: bool = False


class Schedall(BaseModel):
    dayrank: bool = True
    weekrank: bool = True
    dayplayrank: bool = False
    weekplayrank: bool = True
    check_ex: bool = True
    low_activity: bool = False
    day_ranks_message_id: int = 0
    week_ranks_message_id: int = 0
    restart_chat_id: int = 0
    restart_msg_id: int = 0
    backup_db: bool = True

    @model_validator(mode='after')
    def load_rank_ids(self) -> Self:
        """从 rank.json 加载 message_id"""
        if self.day_ranks_message_id == 0 or self.week_ranks_message_id == 0:
            if os.path.exists("log/rank.json"):
                with open("log/rank.json", "r") as f:
                    i = json.load(f)
                    self.day_ranks_message_id = i.get("day_ranks_message_id", 0)
                    self.week_ranks_message_id = i.get("week_ranks_message_id", 0)
        return self


class Proxy(BaseModel):
    scheme: Optional[str] = ""  # "socks4", "socks5" and "http" are supported
    hostname: Optional[str] = ""
    port: Optional[int] = None
    username: Optional[str] = ""
    password: Optional[str] = ""


class MP(BaseModel):
    status: bool = False
    url: Optional[str] = ""
    username: Optional[str] = ""
    password: Optional[str] = ""
    access_token: Optional[str] = ""
    price: int = 1
    download_log_chatid: Optional[int] = None
    movie_request_chatid: Optional[int] = None  # 求片通知群组ID（可选，默认使用第一个授权群组）
    lv: Optional[str] = "b"

class AutoUpdate(BaseModel):
    status: bool = True
    git_repo: Optional[str] = "OmniHelm/Emby-bot"  # github仓库名/魔改的请填自己的仓库
    commit_sha: Optional[str] = None  # 最近一次commit
    up_description: Optional[str] = None  # 更新描述


class API(BaseModel):
    status: bool = False  # 默认关闭
    http_url: Optional[str] = "0.0.0.0"
    http_port: Optional[int] = 8838
    allow_origins: Optional[List[Union[str, int]]] = Field(default_factory=lambda: ["*"])

    # 不再需要 __init__ 方法，使用 Field(default_factory) 设置默认值

class RedEnvelope(BaseModel):
    status: bool = True  # 是否开启红包
    allow_private: bool = True # 是否允许专属红包

class Config(BaseModel):
    bot_name: str
    bot_token: str
    owner_api: int
    owner_hash: str
    owner: int
    group: List[int]
    main_group: str
    chanel: str
    bot_photo: str
    open: Open
    admins: Optional[List[int]] = []
    credits_name: str

    # 多服务器配置（新增）
    emby_servers: Optional[List[EmbyServerConfig]] = None

    # 向后兼容旧配置（保留但标记为可选）
    emby_api: Optional[str] = None
    emby_url: Optional[str] = None
    emby_line: Optional[str] = None
    emby_whitelist_line: Optional[str] = None

    # 共享配置
    emby_block: Optional[List[str]] = []
    extra_emby_libs: Optional[List[str]] = []
    db_host: str
    db_user: str
    db_pwd: str
    db_name: str
    db_port: int = 3306
    tz_ad: Optional[str] = None
    tz_api: Optional[str] = None
    tz_id: Optional[List[int]] = []
    ranks: Ranks
    schedall: Schedall
    db_is_docker: bool = False
    db_docker_name: str = "mysql"
    db_backup_dir: str = "./db_backup"
    db_backup_maxcount: int = 7
    # another_line: Optional[List[str]] = []
    # 如果使用的是 Python 3.10+ ，|运算符能用
    # w_anti_channel_ids: Optional[List[str | int]] = []
    w_anti_channel_ids: Optional[List[Union[str, int]]] = []
    proxy: Optional[Proxy] = Proxy()
    # kk指令中赠送资格的天数
    kk_gift_days: int = 30
    # 是否狙杀皮套人
    fuxx_pitao: bool = True
    # 活跃检测天数，默认21天
    activity_check_days: int = 21
    # 封存账号天数，默认5天
    freeze_days: int = 5
    # 白名单用户专属的emby线路
    emby_whitelist_line: Optional[str] = None
    # 被拦截的user-agent模式列表
    blocked_clients: Optional[List[str]] = None
    # 是否在检测到可疑客户端时终止会话
    client_filter_terminate_session: bool = True
    # 是否在检测到可疑客户端时封禁用户
    client_filter_block_user: bool = False
    moviepilot: MP = Field(default_factory=MP)
    auto_update: AutoUpdate = Field(default_factory=AutoUpdate)
    red_envelope: RedEnvelope = Field(default_factory=RedEnvelope)
    api: API = Field(default_factory=API)

    @model_validator(mode='before')
    @classmethod
    def convert_legacy_config(cls, data: dict) -> dict:
        """自动转换旧配置为新格式"""
        # 如果新配置存在，直接使用
        if data.get('emby_servers'):
            return data

        # 如果是旧配置，自动转换
        if data.get('emby_api') and data.get('emby_url'):
            from loguru import logger
            logger.warning("检测到旧版配置格式，自动转换为多服务器格式")

            data['emby_servers'] = [{
                "id": "main",
                "name": "主服务器",
                "api_key": data.get('emby_api'),
                "url": data.get('emby_url'),
                "line": data.get('emby_line', ''),
                "whitelist_line": data.get('emby_whitelist_line'),
                "enabled": True
            }]

        return data

    @field_validator('emby_servers')
    @classmethod
    def validate_emby_servers(cls, v: Optional[List[EmbyServerConfig]]) -> List[EmbyServerConfig]:
        """验证服务器列表"""
        if not v:
            raise ValueError("必须配置至少一个 Emby 服务器")

        # 检查 ID 唯一性
        ids = [server.id for server in v]
        if len(ids) != len(set(ids)):
            raise ValueError("服务器 ID 必须唯一")

        return v

    @model_validator(mode='after')
    def remove_owner_from_admins(self) -> Self:
        """确保 owner 不在 admins 列表中"""
        if self.owner in self.admins:
            self.admins.remove(self.owner)
        return self

    @classmethod
    def load_config(cls):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return cls(**config)

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)

    def get_server_by_id(self, server_id: str) -> Optional[EmbyServerConfig]:
        """
        根据 ID 获取服务器配置

        Args:
            server_id: 服务器唯一标识（如：anime, movie, series）

        Returns:
            服务器配置对象，如果不存在或未启用则返回 None
        """
        if not self.emby_servers:
            return None

        for server in self.emby_servers:
            if server.id == server_id and server.enabled:
                return server

        return None

    def get_enabled_servers(self) -> List[EmbyServerConfig]:
        """
        获取所有启用的服务器列表

        Returns:
            启用的服务器配置列表
        """
        if not self.emby_servers:
            return []

        return [s for s in self.emby_servers if s.enabled]

    def list_server_ids(self) -> List[str]:
        """
        列出所有启用的服务器 ID

        Returns:
            服务器 ID 列表（如：['anime', 'movie', 'series']）
        """
        return [s.id for s in self.get_enabled_servers()]


class Yulv(BaseModel):
    wh_msg: List[str]
    red_bag: List[str]

    @classmethod
    def load_yulv(cls):
        with open("bot/func_helper/yvlu.json", "r", encoding="utf-8") as f:
            yulv = json.load(f)
            return cls(**yulv)
