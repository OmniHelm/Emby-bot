from pyrogram import filters
from datetime import datetime

from bot import bot, prefixes, LOGGER, config
from bot.func_helper.emby_utils import get_user_emby_service, get_user_emby_services
from bot.func_helper.emby_manager import emby_manager
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, editMessage, sendMessage
from bot.func_helper.utils import tem_deluser
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby, sql_delete_emby_by_tg, sql_delete_emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2_by_name
from bot.sql_helper.sql_server_bindings import delete_user_bindings

# 导入优化模块
from bot.constants.messages import Messages
from bot.func_helper.message_formatter import MessageFormatter


# 删除账号命令
@bot.on_message(filters.command('user_remove', prefixes) & admins_on_filter)
async def rmemby_user(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply("🔄 正在处理...")

    # 获取目标用户
    if msg.reply_to_message is None:
        try:
            b = msg.command[1]  # tg_id or username
        except (IndexError, KeyError, ValueError):
            # 优化：使用标准化的使用说明
            return await editMessage(reply, Messages.USAGE_RMEMBY)
        e = sql_get_emby(tg=b)
    else:
        b = msg.reply_to_message.from_user.id
        e = sql_get_emby(tg=b)

    # 优化：用户未找到的提示
    if e is None:
        error_msg = Messages.ERROR_USER_NOT_FOUND.format(user_id=b)
        return await reply.edit(error_msg)

    # 检查是否有账户
    if e.embyid is not None:
        first = await bot.get_chat(e.tg)

        # 多服务器：遍历所有绑定服务器逐个删除
        services = get_user_emby_services(e.tg)
        if not services:
            return await reply.edit('❌ 未找到该用户的服务器绑定记录')

        any_success = False
        for svc, server_cfg, bind_eid in services:
            try:
                if await svc.emby_del(emby_id=bind_eid):
                    any_success = True
                else:
                    LOGGER.warning(f"删除服务器 {server_cfg.id} 上的账号失败: embyid={bind_eid}")
            except Exception as ex:
                LOGGER.warning(f"删除服务器 {server_cfg.id} 上的账号异常: embyid={bind_eid}, err={ex}")

        if any_success:
            # 清空数据库记录并删除所有绑定
            sql_update_emby(Emby.tg == e.tg, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
            delete_user_bindings(e.tg)
            tem_deluser()

            # 获取管理员信息
            sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else MessageFormatter.format_user_link(msg.from_user.id, msg.from_user.first_name)

            # 优化：删除成功消息
            success_msg = f"""
✅ **账户删除成功**

**被删除账户：**
{MessageFormatter.format_user_link(e.tg, first.first_name)}

**账户信息：**
• 用户名：`{e.name}`
• 绑定服务器：已全部删除

**执行人：**
{sign_name}

**操作时间：**
{MessageFormatter.format_time(datetime.now())}
"""

            # 优化：用户通知消息
            user_notification = f"""
📢 **账户删除通知**

你的 Emby 账户已被管理员删除。

**账户信息：**
• 用户名：`{e.name}`

**删除原因：**
管理员操作

**执行人：**
{sign_name}

如有疑问，请联系管理员。
"""

            try:
                await reply.edit(success_msg)
                await bot.send_message(e.tg, user_notification)
            except Exception as ex:
                LOGGER.warning(f"通知删除账户失败 tg={e.tg}: {ex}")

            LOGGER.info(f"【admin】：管理员 {sign_name} 执行删除 {first.first_name}-{e.tg} 账户 {e.name}（已删除所有绑定服务器账号）")
        else:
            await reply.edit('❌ 无法在任何服务器删除该用户账号，请检查服务器连接或绑定关系')
    else:
        # 优化：未注册账户的提示
        error_msg = f"""
⚠️ **用户未注册账户**

目标用户：{MessageFormatter.format_user_link(b, "此用户")}

该用户尚未创建 Emby 账户，无需删除。
"""
        await reply.edit(error_msg)
@bot.on_message(filters.command('del_record', prefixes) & admins_on_filter)
async def only_rm_record(_, msg):
    await deleteMessage(msg)
    tg_id = None
    if msg.reply_to_message is None:
        try:
            tg_id = msg.command[1]
        except (IndexError, ValueError):
            tg_id = None
    else:
        tg_id = msg.reply_to_message.from_user.id
    if tg_id is None:
        return await sendMessage(msg, "❌ 使用格式：/del_record tg_id或回复用户的消息")

    emby1 = sql_get_emby(tg=tg_id)
    # 获取 emby2 表中的用户信息
    emby2 = sql_get_emby2(name=tg_id)
    if not emby1 and not emby2:
        return await sendMessage(msg, f"❌ 未找到 {tg_id} 的记录")
    try:
        res1 = False
        res2 = False
        if emby1:
            res1 = sql_delete_emby_by_tg(tg_id)
        if emby2:
            res2 = sql_delete_emby2_by_name(name=tg_id)
        sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
        if res1 or res2:
            await sendMessage(msg, f"管理员 {sign_name} 已删除 TG ID: {tg_id} 的数据库记录")
            LOGGER.info(
                f"管理员 {sign_name} 删除了用户 {tg_id} 的数据库记录")
        else:
            await sendMessage(msg, "❌ 删除记录失败")
            LOGGER.error(
                f"管理员 {sign_name} 删除用户 {tg_id} 的数据库记录失败")
    except Exception as ex:
        await sendMessage(msg, "❌ 删除记录失败")
        LOGGER.error(f"删除用户 {tg_id} 的数据库记录失败, {ex}")


@bot.on_message(filters.command('del_emby', prefixes) & admins_on_filter)
async def only_rm_emby(_, msg):
    await deleteMessage(msg)
    try:
        emby_id = msg.command[1]
    except (IndexError, ValueError):
        return await sendMessage(msg, "❌ 使用格式：/del_emby embyid或者embyname")

    # 多服务器适配：遍历所有服务器查找并删除用户
    all_servers = emby_manager.get_all_servers()
    if not all_servers:
        return await sendMessage(msg, "❌ 没有可用的服务器")

    deleted = False
    found_server = None

    for server_id, emby_service in all_servers.items():
        try:
            # 先尝试直接删除（按 emby_id）
            res = await emby_service.emby_del(emby_id=emby_id)
            if res:
                deleted = True
                found_server = server_id
                break

            # 如果失败，尝试按名称查找
            success, embyuser = await emby_service.get_emby_user_by_name(emby_name=emby_id)
            if success and embyuser:
                res = await emby_service.emby_del(emby_id=embyuser.get("Id"))
                if res:
                    deleted = True
                    found_server = server_id
                    break
        except Exception as e:
            LOGGER.warning(f"在服务器 {server_id} 删除用户失败: {e}")
            continue

    if not deleted:
        return await sendMessage(msg, f"❌ 在所有服务器上都未找到或删除失败: {emby_id}")

    sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
    server_config = config.get_server_by_id(found_server)
    server_name = server_config.name if server_config else found_server
    await sendMessage(msg, f"✅ 管理员 {sign_name} 已删除用户 {emby_id} 的Emby账号\n**服务器**: {server_name}")
    LOGGER.info(f"管理员 {sign_name} 在服务器 {server_name} 删除了用户 {emby_id} 的Emby账号")
