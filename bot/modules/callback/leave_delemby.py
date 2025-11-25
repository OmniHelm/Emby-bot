from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated

from bot import bot, group, LOGGER, _open
from bot.func_helper.utils import tem_deluser
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.func_helper.emby_utils import get_user_emby_service
from bot.func_helper.emby_manager import emby_manager


@bot.on_chat_member_updated(filters.chat(group))
async def leave_del_emby(_, event: ChatMemberUpdated):
    if event.old_chat_member and not event.new_chat_member:
        if not event.old_chat_member.is_member and event.old_chat_member.user:
            user_id = event.old_chat_member.user.id
            user_fname = event.old_chat_member.user.first_name
            try:
                e = sql_get_emby(tg=user_id)
                if e is None or e.embyid is None:
                    return

                # 获取用户对应的服务实例（多服务器适配）
                emby_service, server_config, user = get_user_emby_service(user_id)
                if not emby_service:
                    LOGGER.warning(f'【退群删号】- {user_fname}-{user_id} 无法定位服务器，跳过删除')
                    return

                if await emby_service.emby_del(emby_id=e.embyid):
                    sql_update_emby(Emby.embyid == e.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
                    tem_deluser()
                    LOGGER.info(
                        f'【退群删号】- {user_fname}-{user_id} 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
                    await bot.send_message(chat_id=event.chat.id,
                                           text=f'✅ [{user_fname}](tg://user?id={user_id}) 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
                else:
                    LOGGER.error(
                        f'【退群删号】- {user_fname}-{user_id} 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
                    await bot.send_message(chat_id=event.chat.id,
                                           text=f'❎ [{user_fname}](tg://user?id={user_id}) 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
                if _open.leave_ban:
                    await bot.ban_chat_member(chat_id=event.chat.id, user_id=user_id)
            except Exception as e:
                LOGGER.error(f"【退群删号】- {user_id}: {e}")
            else:
                pass
    elif event.old_chat_member and event.new_chat_member:
        if event.new_chat_member.status is ChatMemberStatus.BANNED:
            # print(2)
            user_id = event.new_chat_member.user.id
            user_fname = event.new_chat_member.user.first_name
            try:
                e = sql_get_emby(tg=user_id)
                if e is None or e.embyid is None:
                    return

                # 获取用户对应的服务实例（多服务器适配）
                emby_service, server_config, user = get_user_emby_service(user_id)
                if not emby_service:
                    LOGGER.warning(f'【退群删号】- {user_fname}-{user_id} 无法定位服务器，跳过删除')
                    return

                if await emby_service.emby_del(emby_id=e.embyid):
                    sql_update_emby(Emby.embyid == e.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None,
                                    ex=None)
                    tem_deluser()
                    LOGGER.info(
                        f'【退群删号】- {user_fname}-{user_id} 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
                    await bot.send_message(chat_id=event.chat.id,
                                           text=f'✅ [{user_fname}](tg://user?id={user_id}) 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
                else:
                    LOGGER.error(
                        f'【退群删号】- {user_fname}-{user_id} 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
                    await bot.send_message(chat_id=event.chat.id,
                                           text=f'❎ [{user_fname}](tg://user?id={user_id}) 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
                if _open.leave_ban:
                    await bot.ban_chat_member(chat_id=event.chat.id, user_id=user_id)
            except Exception as e:
                LOGGER.error(f"【退群删号】- {user_id}: {e}")
            else:
                pass
