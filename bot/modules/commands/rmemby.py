from pyrogram import filters
from datetime import datetime

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, editMessage, sendMessage
from bot.func_helper.utils import tem_deluser
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby, sql_delete_emby_by_tg, sql_delete_emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2_by_name

# 导入优化模块
from bot.constants.messages import Messages
from bot.func_helper.message_formatter import MessageFormatter


# 删除账号命令
@bot.on_message(filters.command('rmemby', prefixes) & admins_on_filter)
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

        # 执行删除
        if await emby.emby_del(emby_id=e.embyid):
            sql_update_emby(Emby.embyid == e.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
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
• Emby ID：`{e.embyid}`

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

            LOGGER.info(f"【admin】：管理员 {sign_name} 执行删除 {first.first_name}-{e.tg} 账户 {e.name}")
    else:
        # 优化：未注册账户的提示
        error_msg = f"""
⚠️ **用户未注册账户**

目标用户：{MessageFormatter.format_user_link(b, "此用户")}

该用户尚未创建 Emby 账户，无需删除。
"""
        await reply.edit(error_msg)
@bot.on_message(filters.command('only_rm_record', prefixes) & admins_on_filter)
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
        return await sendMessage(msg, "❌ 使用格式：/only_rm_record tg_id或回复用户的消息")

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


@bot.on_message(filters.command('only_rm_emby', prefixes) & admins_on_filter)
async def only_rm_emby(_, msg):
    await deleteMessage(msg)
    try:
        emby_id = msg.command[1]
    except (IndexError, ValueError):
        return await sendMessage(msg, "❌ 使用格式：/only_rm_emby embyid或者embyname")
    
    res = await emby.emby_del(emby_id=emby_id)
    if not res:
        # 使用 emby_name 获取此用户的 emby_id
        success, embyuser = await emby.get_emby_user_by_name(emby_name=emby_id)
        if not success:
            return await sendMessage(msg, f"❌ 未找到此用户 {emby_id} 的记录")
        res = await emby.emby_del(emby_id=embyuser.get("Id"))
        if not res:
            return await sendMessage(msg, f"❌ 删除用户 {emby_id} 失败")
        sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
        await sendMessage(msg, f"管理员 {sign_name} 已删除用户 {emby_id} 的Emby账号")
        LOGGER.info(
            f"管理员 {sign_name} 删除了用户 {emby_id} 的Emby账号")
