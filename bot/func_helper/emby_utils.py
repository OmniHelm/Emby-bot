"""
Emby 多服务器辅助工具
提供统一的服务器选择、用户查询等功能
"""

from typing import Optional, Tuple, List
from loguru import logger

from bot import config, emby_manager
from bot.func_helper.emby import Embyservice
from bot.schemas.schemas import EmbyServerConfig


def get_user_emby_service(tg: int, server_id: str = None) -> Tuple[Optional[Embyservice], Optional[EmbyServerConfig], Optional['Emby']]:
    """
    根据用户 TG ID 获取对应的 Emby 服务实例

    Args:
        tg: Telegram 用户 ID
        server_id: 可选，指定服务器 ID。如果不指定则使用主服务器

    Returns:
        元组 (Embyservice实例, 服务器配置, 用户对象) 或 (None, None, None)

    Example:
        >>> emby_service, server_config, user = get_user_emby_service(123456)
        >>> if emby_service:
        >>>     result = await emby_service.user(emby_id=user.embyid)
    """
    from bot.sql_helper.sql_emby import sql_get_emby
    from bot.sql_helper.sql_server_bindings import get_primary_binding, get_binding

    # 查询用户基础信息
    user = sql_get_emby(tg)
    if not user:
        logger.warning(f"用户不存在: tg={tg}")
        return None, None, None

    # 确定服务器 ID
    if server_id:
        # 指定了服务器，验证用户是否绑定
        binding = get_binding(tg, server_id)
        if not binding:
            logger.warning(f"用户未绑定该服务器: tg={tg}, server_id={server_id}")
            return None, None, None
    else:
        # 未指定服务器，使用主服务器
        binding = get_primary_binding(tg)
        if binding:
            server_id = binding.server_id
        else:
            # 没有绑定记录，使用默认服务器（向后兼容）
            server_id = 'main'
            logger.warning(f"用户 tg={tg} 无绑定记录，使用 fallback 服务器: main")

    # 获取服务器配置
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


def get_user_emby_services(tg: int) -> List[Tuple[Embyservice, EmbyServerConfig, str]]:
    """
    获取用户绑定的所有服务器实例

    Args:
        tg: Telegram 用户 ID

    Returns:
        列表 [(Embyservice实例, 服务器配置, embyid), ...]
    """
    from bot.sql_helper.sql_server_bindings import get_user_bindings

    results = []
    bindings = get_user_bindings(tg, enabled_only=True)

    for binding in bindings:
        server_config = config.get_server_by_id(binding.server_id)
        emby_service = emby_manager.get_server(binding.server_id)
        if server_config and emby_service:
            results.append((emby_service, server_config, binding.embyid))

    return results


def get_emby_line(server_id: str, is_whitelist: bool = False) -> str:
    """
    获取服务器线路地址

    Args:
        server_id: 服务器 ID
        is_whitelist: 是否为白名单用户

    Returns:
        线路地址字符串
    """
    server_config = config.get_server_by_id(server_id)
    if not server_config:
        logger.error(f"服务器配置不存在: server_id={server_id}")
        return ""

    if is_whitelist and server_config.whitelist_line:
        return server_config.whitelist_line
    return server_config.line


def get_user_emby_line(server_id: str, user_lv: str = 'b') -> str:
    """
    根据用户信息获取线路展示文本

    Args:
        server_id: 服务器 ID
        user_lv: 用户等级 ('a'=白名单, 'b'=普通, 'c'=禁用, 'd'=未注册)

    Returns:
        格式化的线路文本
    """
    server_config = config.get_server_by_id(server_id)
    if not server_config:
        return ' - **无法获取线路**'

    line = server_config.line or ''

    if user_lv == 'a' and server_config.whitelist_line:
        line += f'\n{server_config.whitelist_line}'

    return line if line else ' - **无权查看**'


def get_server_by_id_or_none(server_id: str) -> Optional[EmbyServerConfig]:
    """
    根据 ID 获取服务器配置并验证其可用性

    Args:
        server_id: 服务器唯一标识

    Returns:
        服务器配置对象，如果不存在或不可用则返回 None
    """
    server_config = config.get_server_by_id(server_id)
    if not server_config:
        logger.error(f"服务器配置不存在: server_id={server_id}")
        return None

    if not emby_manager.has_server(server_id):
        logger.error(f"服务器实例未注册: server_id={server_id}")
        return None

    return server_config


def format_server_list_text() -> str:
    """
    格式化服务器列表文本（用于 Telegram 消息）

    Returns:
        格式化的文本字符串
    """
    from bot.sql_helper.sql_server_bindings import count_server_users

    servers = config.get_enabled_servers()

    if not servers:
        return "❌ 暂无可用服务器"

    text = "**📡 Emby 服务器列表**\n\n"

    for server in servers:
        current_users = count_server_users(server.id)
        icon = "🟢" if emby_manager.has_server(server.id) else "🔴"

        text += (
            f"{icon} **{server.name}**\n"
            f"   • ID: `{server.id}`\n"
            f"   • 用户数: {current_users}\n"
            f"   • 线路: {server.line}\n"
        )

        if server.whitelist_line:
            text += f"   • 白名单线路: {server.whitelist_line}\n"

        text += "\n"

    text += f"**提示**：创建用户时需要指定服务器 ID\n"
    text += f"例如：`/user_create username 30 {servers[0].id}`"

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


def get_user_primary_server_id(tg: int) -> Optional[str]:
    """
    获取用户的主服务器 ID

    Args:
        tg: Telegram 用户 ID

    Returns:
        主服务器 ID 或 None
    """
    from bot.sql_helper.sql_server_bindings import get_primary_binding

    binding = get_primary_binding(tg)
    return binding.server_id if binding else None


def get_user_server_embyid(tg: int, server_id: str) -> Optional[str]:
    """
    获取用户在指定服务器的 embyid

    Args:
        tg: Telegram 用户 ID
        server_id: 服务器 ID

    Returns:
        embyid 或 None
    """
    from bot.sql_helper.sql_server_bindings import get_embyid_by_server

    return get_embyid_by_server(tg, server_id)
