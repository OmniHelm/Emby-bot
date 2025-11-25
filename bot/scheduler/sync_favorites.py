from bot import LOGGER
from bot.sql_helper.sql_favorites import sql_add_favorites, sql_clear_favorites
from bot.sql_helper.sql_emby import get_all_emby, Emby
from bot.func_helper.emby_utils import get_user_emby_services


async def sync_favorites():
    """
    同步所有用户的Emby收藏记录到数据库
    """
    LOGGER.info("开始同步用户 Emby 收藏记录（按服务器分离）...")
    try:
        # 获取所有Emby用户（仅查询绑定了 embyid 的用户）
        users = get_all_emby(Emby.embyid.isnot(None))
        if not users:
            LOGGER.warning("没有找到Emby用户")
            return

        for user in users:
            # 多服务器适配：获取用户绑定的所有服务器实例与 embyid
            services = get_user_emby_services(user.tg)
            if not services:
                LOGGER.warning(f"无法定位服务器：{user.name}（无绑定记录）")
                continue

            # 逐台服务器同步收藏（避免不同服务器的收藏互相污染）
            for emby_service, server_config, embyid in services:
                server_id = server_config.id
                # 获取该服务器的收藏列表
                favorites = await emby_service.get_favorite_items(emby_id=embyid)
                if favorites is None:
                    LOGGER.debug(f"服务器 {server_id} 获取收藏失败或为空：{user.name}")
                    continue

                # 清除该服务器下该用户的收藏记录
                sql_clear_favorites(user.name, server_id=server_id)

                # 遍历收藏项目并添加到数据库（带 server_id）
                for item in favorites.get("Items", []):
                    item_id = item.get("Id")
                    if not item_id:
                        continue

                    # 获取项目名称
                    item_name = item.get("Name", "")
                    if not item_name:
                        item_name = await emby_service.item_id_name(emby_id=embyid, item_id=item_id) or "未知"

                    # 添加到数据库
                    sql_add_favorites(
                        embyid=embyid,
                        embyname=user.name,
                        item_id=item_id,
                        item_name=item_name,
                        server_id=server_id,
                    )

        LOGGER.info("Emby 收藏记录同步完成（按服务器分离）")

    except Exception as e:
        LOGGER.error(f"同步Emby收藏记录时出错: {str(e)}")
