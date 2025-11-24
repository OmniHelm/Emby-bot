"""
启动面板start命令 返回面ban

+ myinfo 个人数据
+ count  服务器媒体数
"""
import asyncio
from pyrogram import filters

from bot.func_helper.emby import Embyservice
from bot.func_helper.utils import judge_admins, members_info, open_check
from bot.modules.commands.exchange import rgs_code
from bot.sql_helper.sql_emby import sql_add_emby
from bot.func_helper.filters import user_in_group_filter, user_in_group_on_filter
from bot.func_helper.msg_utils import deleteMessage, sendMessage, sendPhoto, callAnswer, editMessage
from bot.func_helper.fix_bottons import group_f, judge_start_ikb, judge_group_ikb, cr_kk_ikb
from bot.modules.extra import user_cha_ip
from bot import bot, prefixes, group, bot_photo, ranks, credits

# 导入优化模块
from bot.constants.messages import Messages
from bot.func_helper.message_formatter import MessageFormatter


# 反命令提示
@bot.on_message((filters.command('start', prefixes) | filters.command('count', prefixes)) & filters.chat(group))
async def ui_g_command(_, msg):
    await asyncio.gather(deleteMessage(msg),
                         sendMessage(msg,
                                     f"🤖 亲爱的 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 这是一条私聊命令",
                                     buttons=group_f, timer=60))


# 查看自己的信息
@bot.on_message(filters.command('myinfo', prefixes) & user_in_group_on_filter)
async def my_info(_, msg):
    await msg.delete()
    if msg.sender_chat:
        return
    text, keyboard = await cr_kk_ikb(uid=msg.from_user.id, first=msg.from_user.first_name)
    await sendMessage(msg, text, timer=60)


@bot.on_message(filters.command('count', prefixes) & user_in_group_on_filter & filters.private)
async def count_info(_, msg):
    await deleteMessage(msg)
    text = await Embyservice.get_medias_count()
    await sendMessage(msg, text, timer=60)


# 私聊开启面板
@bot.on_message(filters.command('start', prefixes) & filters.private)
async def p_start(_, msg):
    if not await user_in_group_filter(_, msg):
        # 优化：使用消息模板
        group_links = "请点击下方按钮加入"  # 这里可以从配置读取
        error_msg = Messages.ERROR_NOT_IN_GROUP.format(group_links=group_links)
        return await asyncio.gather(deleteMessage(msg),
                                    sendMessage(msg, error_msg, buttons=judge_group_ikb))
    try:
        u = msg.command[1].split('-')[0]
        if u == 'userip':
            name = msg.command[1].split('-')[1]
            if judge_admins(msg.from_user.id):
                return await user_cha_ip(_, msg, name)
            else:
                return await sendMessage(msg, '💢 你不是管理员，无法使用此命令')
        if u in f'{ranks.logo}' or u == str(msg.from_user.id):
            await asyncio.gather(msg.delete(), rgs_code(_, msg, register_code=msg.command[1]))
        else:
            await asyncio.gather(sendMessage(msg, '🤺 你也想和bot击剑吗 ?'), msg.delete())
    except (IndexError, TypeError):
        data = await members_info(tg=msg.from_user.id)
        is_admin = judge_admins(msg.from_user.id)

        # 新用户首次使用
        if not data:
            sql_add_emby(msg.from_user.id)

            # 优化：使用欢迎消息模板
            welcome_msg = Messages.SYSTEM_WELCOME.format(
                first_name=msg.from_user.first_name
            )

            # 添加注册提示
            register_tip = "\n\n**已完成数据库录入**\n请再次点击 /start 召唤主面板"

            await asyncio.gather(
                deleteMessage(msg),
                sendPhoto(msg, bot_photo, welcome_msg + register_tip)
            )
            return

        name, lv, ex, us, embyid, pwd2 = data
        stat, all_user, tem, timing = await open_check()

        # 优化：美化用户面板信息
        status_text = MessageFormatter.format_status(lv) if lv in ['a', 'b', 'c', 'd'] else lv
        stat_text = "✅ 开放注册" if stat else "❌ 已关闭"
        available_slots = all_user - tem

        text = f"""
╭─────────────────╮
│  🏠 **主面板**
╰─────────────────╯

欢迎回来，{msg.from_user.first_name}！

**个人信息：**
• 🆔 **Telegram ID**
  `{msg.from_user.id}`

• 📊 **账户状态**
  {status_text}

• 🍒 **持有{credits}**
  {us}

**系统状态：**
• ®️ **注册状态**
  {stat_text}

• 🎫 **总注册限制**
  {all_user} 个

• 🎟️ **可注册席位**
  {available_slots} 个

---

请选择下方功能 👇
"""

        if not embyid:
            # 未创建账户
            await asyncio.gather(
                deleteMessage(msg),
                sendPhoto(msg, bot_photo, caption=text, buttons=judge_start_ikb(is_admin, False))
            )
        else:
            # 已有账户 - 简化欢迎消息
            welcome_text = f"""
✨ **欢迎回来！**

你好，{MessageFormatter.format_user_link(msg.from_user.id, msg.from_user.first_name)}

请选择功能 👇
"""
            await asyncio.gather(
                deleteMessage(msg),
                sendPhoto(msg, bot_photo, welcome_text, buttons=judge_start_ikb(is_admin, True))
            )


# 返回面板
@bot.on_callback_query(filters.regex('back_start'))
async def b_start(_, call):
    if await user_in_group_filter(_, call):
        is_admin = judge_admins(call.from_user.id)
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             editMessage(call,
                                         text=f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n🍉__你好鸭 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 请选择功能__👇",
                                         buttons=judge_start_ikb(is_admin, account=True)))
    elif not await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             editMessage(call, text='💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？\n\n'
                                                    '⁉️ ps：如果您已在群组中且收到此消息，请联系管理员解除您的权限限制，因为被限制用户无法使用本bot。',
                                         buttons=judge_group_ikb))


@bot.on_callback_query(filters.regex('store_all'))
async def store_alls(_, call):
    if not await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             deleteMessage(call), sendPhoto(call, bot_photo,
                                                            '💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                                                            judge_group_ikb))
    elif await user_in_group_filter(_, call):
        await callAnswer(call, '⭕ 正在编辑', True)
