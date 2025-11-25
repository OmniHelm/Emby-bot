#! /usr/bin/python3
# -*- coding: utf-8 -*-
import contextlib

from .func_helper.logger_config import logu, Now

LOGGER = logu(__name__)

from .schemas import Config

config = Config.load_config()


def save_config():
    config.save_config()


'''从config对象中获取属性值'''
# bot
bot_name = config.bot_name
bot_token = config.bot_token
owner_api = config.owner_api
owner_hash = config.owner_hash
owner = config.owner
group = config.group
main_group = config.main_group
chanel = config.chanel
bot_photo = config.bot_photo
_open = config.open
admins = config.admins
credits = config.credits_name
ranks = config.ranks
prefixes = ['/', '!', '.', '，', '。']
schedall = config.schedall
# emby设置（多服务器）
from .func_helper.emby_manager import emby_manager

# 初始化所有 Emby 服务器
LOGGER.info("开始初始化 Emby 服务器...")
for server_config in config.emby_servers:
    if not server_config.enabled:
        LOGGER.warning(f"服务器 {server_config.name} ({server_config.id}) 已禁用，跳过")
        continue

    success = emby_manager.register_server(server_config)
    if not success:
        LOGGER.error(f"注册服务器失败: {server_config.name}")

LOGGER.success(
    f"Emby 服务器初始化完成，"
    f"已注册 {emby_manager.get_server_count()} 个服务器: "
    f"{emby_manager.list_server_ids()}"
)

# 共享配置（保留向后兼容）
emby_api = config.emby_api
emby_url = config.emby_url
emby_line = config.emby_line
emby_whitelist_line = config.emby_whitelist_line
emby_block = config.emby_block
extra_emby_libs = config.extra_emby_libs
# # 数据库
db_host = config.db_host
db_user = config.db_user
db_pwd = config.db_pwd
db_name = config.db_name
db_port = config.db_port
db_is_docker = config.db_is_docker
db_docker_name = config.db_docker_name
db_backup_dir = config.db_backup_dir
db_backup_maxcount = config.db_backup_maxcount
# 探针
tz_ad = config.tz_ad
tz_api = config.tz_api
tz_id = config.tz_id

w_anti_channel_ids = config.w_anti_channel_ids
kk_gift_days = config.kk_gift_days
fuxx_pitao = config.fuxx_pitao
activity_check_days = config.activity_check_days
red_envelope = config.red_envelope

moviepilot = config.moviepilot
auto_update = config.auto_update
api = config.api

LOGGER.info("配置文件加载完毕")
from pyrogram.types import BotCommand

'''定义不同等级的人使用不同命令'''
user_p = [
    BotCommand("start", "[私聊] 开启用户面板"),
    BotCommand("myinfo", "[用户] 查看状态"),
    BotCommand("count", "[用户] 媒体库数量"),
    BotCommand("red", "[用户/禁言] 发红包"),
    BotCommand("srank", "[用户/禁言] 查看计分")]

# 取消 BotCommand("exchange", "[私聊] 使用注册码")
# 命令重构：新命令在前，旧命令作为别名保留兼容
admin_p = user_p + [
    BotCommand("user", "管理用户 [管理]"),
    BotCommand("score", "加/减积分 [管理]"),
    BotCommand("coins", f"加/减{credits} [管理]"),
    BotCommand("purge_dead", "清理死号 [管理]"),
    BotCommand("kick_nonemby", "踢出当前群内无号崽 [管理]"),
    BotCommand("renew", "调整到期时间 [管理]"),
    BotCommand("user_remove", "删除用户[包括非tg] [管理]"),
    BotCommand("vip_add", "增加白名单 [管理]"),
    BotCommand("vip_remove", "减少白名单 [管理]"),
    BotCommand("rev_white_channel", "移除皮套人白名单 [管理]"),
    BotCommand("white_channel", "添加皮套人白名单 [管理]"),
    BotCommand("unban_channel", "解封皮套人 [管理]"),
    BotCommand("purge_left", "清理不在群的人 [管理]"),
    BotCommand("purge_orphan", "清理未绑定bot的emby账户 [管理]"),
    BotCommand("scan_duplicate", "扫描同名的用户记录 [管理]"),
    BotCommand("check_activity", "手动运行活跃检测 [管理]"),
    BotCommand("check_expiry", "手动到期检测 [管理]"),
    BotCommand("ranks_playtime", "召唤观影时长榜 [管理]"),
    BotCommand("ranks_daily", "召唤播放次数日榜 [管理]"),
    BotCommand("ranks_weekly", "召唤播放次数周榜 [管理]"),
    BotCommand("sync_favorites", "同步收藏记录 [管理]"),
    BotCommand("emby_grant_admin", "开启emby控制台权限 [管理]"),
    BotCommand("user_create", "私聊创建非tg的emby用户 [管理]"),
    BotCommand("user_info", "查询指定用户名 [管理]"),
    BotCommand("user_delete", "删除指定用户名 [管理]"),
    BotCommand("user_ip", "查询指定用户播放过的设备&ip [管理]"),
    BotCommand("user_device", "查询指定设备ID [管理]"),
    BotCommand("auditip", "根据IP地址审计用户活动 [管理]"),
    BotCommand("auditdevice", "根据设备名审计用户 [管理]"),
    BotCommand("auditclient", "根据客户端名审计用户 [管理]"),
    BotCommand("renew_all", "一键派送天数给所有未封禁的用户 [管理]"),
    BotCommand("coins_all", "一键派送币币给指定等级的用户 [管理]"),
    BotCommand("coins_clear", "一键清除所有用户的币币 [管理]"),
    BotCommand("broadcast", "群发消息给每个人 [管理]"),
    BotCommand("del_emby", "删除指定的Emby账号 [管理]"),
    BotCommand("del_record", "删除指定的tgid数据库记录 [管理]"),
    BotCommand("restart", "重启bot [管理]"),
    BotCommand("update_bot", "更新bot [管理]"),
    BotCommand("servers", "查看服务器列表 [管理]"),
    BotCommand("servercheck", "手动健康检查 [管理]"),
]

owner_p = admin_p + [
    BotCommand("admin_add", "添加bot管理 [owner]"),
    BotCommand("admin_remove", "移除bot管理 [owner]"),
    BotCommand("sync_ids", "一键更新用户们Embyid [owner]"),
    BotCommand("backup_db", "手动备份数据库[owner]"),
    BotCommand("unban_all", "解除所有用户的禁用状态 [owner]"),
    BotCommand("ban_all", "禁用所有用户 [owner]"),
    BotCommand("nuke", "跑路!!!删除所有用户 [owner]"),
    BotCommand('restore_from_db', '恢复Emby账户[owner]'),
    BotCommand("config", "开启bot高级控制面板 [owner]"),
    BotCommand("lib_show_all", "一键开启所有用户的媒体库 [owner]"),
    BotCommand("lib_hide_all", "一键关闭所有用户的媒体库 [owner]")
]
if len(extra_emby_libs) > 0:
    owner_p += [BotCommand("lib_extra_hide", "一键关闭所有用户的额外媒体库 [owner]"),
                BotCommand("lib_extra_show", "一键开启所有用户的额外媒体库 [owner]")]

with contextlib.suppress(ImportError):
    import uvloop

    uvloop.install()
from pyrogram import enums
from pyromod import Client

proxy = {} if not config.proxy.scheme else config.proxy.model_dump()

bot = Client(bot_name, api_id=owner_api, api_hash=owner_hash, bot_token=bot_token, proxy=proxy,
             workers=300,
             max_concurrent_transmissions=1000, parse_mode=enums.ParseMode.MARKDOWN)

LOGGER.info("Clinet 客户端准备")
