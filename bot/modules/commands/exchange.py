"""
兑换注册码exchange
"""
from datetime import timedelta, datetime

from bot import bot, _open, LOGGER, bot_photo
from bot.func_helper.emby_utils import get_user_emby_service
from bot.func_helper.emby_manager import emby_manager
from bot.func_helper.fix_bottons import register_code_ikb
from bot.func_helper.msg_utils import sendMessage, sendPhoto
from bot.sql_helper.sql_code import Code
from bot.sql_helper.sql_emby import sql_get_emby, Emby
from bot.sql_helper import Session

# 导入优化模块
from bot.constants.messages import Messages
from bot.func_helper.message_formatter import MessageFormatter


def is_renew_code(input_string):
    if "Renew" in input_string:
        return True
    else:
        return False


async def rgs_code(_, msg, register_code):
    # 移除此检查：续期码应该始终可用，注册码的限制在后面处理
    # 开放注册时不影响续期码的使用，只影响注册码

    data = sql_get_emby(tg=msg.from_user.id)
    if not data:
        # 优化：使用标准错误消息
        return await sendMessage(msg, Messages.ERROR_NOT_IN_DATABASE)

    embyid = data.embyid
    ex = data.ex
    lv = data.lv

    if embyid:
        # 优化：区分注册码和续期码
        if not is_renew_code(register_code):
            error_msg = """
⚠️ **兑换码类型错误**

你使用的是 **注册码**，但你已有账户。

**说明：**
• 注册码仅用于创建新账户
• 已有账户请使用续期码延长时间

**如何续期：**
✅ 使用续期码兑换
✅ 联系管理员获取续期码

点击 /store 查看可用的续期码
"""
            return await sendMessage(msg, error_msg, timer=60)

        with Session() as session:
            # with_for_update 是一个排他锁
            r = session.query(Code).filter(Code.code == register_code).with_for_update().first()

            # 优化：续期码无效的提示
            if not r:
                error_msg = Messages.REDEEM_CODE_INVALID.format(code=register_code)
                return await sendMessage(msg, error_msg, timer=60)
            re = session.query(Code).filter(Code.code == register_code, Code.used.is_(None)).with_for_update().update(
                {Code.used: msg.from_user.id, Code.usedtime: datetime.now()})
            session.commit()  # 必要的提交。否则失效
            tg1 = r.tg
            us1 = r.us
            used = r.used

            # 优化：续期码已被使用的提示
            if re == 0:
                error_msg = f"""
❌ **续期码已被使用**

兑换码：`{register_code}`

**使用者：**
{MessageFormatter.format_user_link(used, "此用户")}

**说明：**
• 每个续期码只能使用一次
• 此码已被上述用户兑换

**如需续期：**
✅ 获取新的续期码
✅ 联系管理员获取帮助

点击 /store 查看可用的续期码
"""
                return await sendMessage(msg, error_msg)

            session.query(Code).filter(Code.code == register_code).with_for_update().update(
                {Code.used: msg.from_user.id, Code.usedtime: datetime.now()})
            first = await bot.get_chat(tg1)

            # 此处需要写一个判断 now和ex的大小比较。进行日期加减。
            ex_new = datetime.now()
            if ex_new > ex:
                # 账户已过期，从当前时间开始计算
                ex_new = ex_new + timedelta(days=us1)

                # 获取用户对应的服务实例（多服务器适配）
                emby_service, server_config, user = get_user_emby_service(msg.from_user.id)
                if not emby_service:
                    return await sendMessage(msg, '❌ 无法连接到您所在的服务器，续期失败', timer=60)

                await emby_service.emby_change_policy(emby_id=embyid, disable=False)
                if lv == 'c':
                    session.query(Emby).filter(Emby.tg == msg.from_user.id).update({Emby.ex: ex_new, Emby.lv: 'b'})
                else:
                    session.query(Emby).filter(Emby.tg == msg.from_user.id).update({Emby.ex: ex_new})

                # 优化：兑换成功消息（已过期账户）
                success_msg = f"""
🎉 **续期成功！**

**获得时长：** {us1} 天
**来自：** {MessageFormatter.format_user_link(tg1, first.first_name)}

✅ **账户已解封**
✅ **到期时间已延长**

📅 **新的到期时间**
   {MessageFormatter.format_time(ex_new)}

   {MessageFormatter.format_days_left(ex_new)}

继续享受服务吧！🎬
"""
                await sendMessage(msg, success_msg)

            elif ex_new < ex:
                # 账户未过期，在原到期时间基础上延长
                ex_new = data.ex + timedelta(days=us1)
                session.query(Emby).filter(Emby.tg == msg.from_user.id).update({Emby.ex: ex_new})

                # 优化：兑换成功消息（未过期账户）
                success_msg = f"""
🎉 **续期成功！**

**获得时长：** {us1} 天
**来自：** {MessageFormatter.format_user_link(tg1, first.first_name)}

📅 **新的到期时间**
   {MessageFormatter.format_time(ex_new)}

   {MessageFormatter.format_days_left(ex_new)}

感谢支持！🎬
"""
                await sendMessage(msg, success_msg)

            session.commit()
            new_code = register_code[:-7] + "░" * 7
            await sendMessage(msg,
                              f'· 🎟️ 续期码使用 - [{msg.from_user.first_name}](tg://user?id={msg.chat.id}) [{msg.from_user.id}] 使用了 {new_code}\n· 📅 实时到期 - {ex_new}',
                              send=True)
            LOGGER.info(f"【续期码】：{msg.from_user.first_name}[{msg.chat.id}] 使用了 {register_code}，到期时间：{ex_new}")

    else:
        if is_renew_code(register_code): return await sendMessage(msg,
                                                                  "🔔 很遗憾，您使用的是续期码，无法启用注册功能，请悉知",
                                                                  timer=60)
        if data.us > 0: return await sendMessage(msg, "已有注册资格，请先使用【创建账户】注册，勿重复使用其他注册码。")
        with Session() as session:
            # 我勒个豆，终于用 原子操作 + 排他锁 成功防止了并发更新
            # 在 UPDATE 语句中添加一个条件，只有当注册码未被使用时，才更新数据。这样，如果有两个用户同时尝试使用同一条注册码，只有一个用户的 UPDATE 语句会成功，因为另一个用户的 UPDATE 语句会发现注册码已经被使用。
            r = session.query(Code).filter(Code.code == register_code).with_for_update().first()
            if not r: return await sendMessage(msg, "⛔ **你输入了一个错误de注册码，请确认好重试。**")
            re = session.query(Code).filter(Code.code == register_code, Code.used.is_(None)).with_for_update().update(
                {Code.used: msg.from_user.id, Code.usedtime: datetime.now()})
            session.commit()  # 必要的提交。否则失效
            tg1 = r.tg
            us1 = r.us
            used = r.used
            if re == 0: return await sendMessage(msg,
                                                 f'此 `{register_code}` \n注册码已被使用,是 [{used}](tg://user?id={used}) 的形状了喔')
            first = await bot.get_chat(tg1)
            x = data.us + us1
            session.query(Emby).filter(Emby.tg == msg.from_user.id).update({Emby.us: x})
            session.commit()
            await sendPhoto(msg, photo=bot_photo,
                            caption=f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={tg1}) 发送的邀请注册资格\n\n请选择你的选项~',
                            buttons=register_code_ikb)
            new_code = register_code[:-7] + "░" * 7
            await sendMessage(msg,
                              f'· 🎟️ 注册码使用 - [{msg.from_user.first_name}](tg://user?id={msg.chat.id}) [{msg.from_user.id}] 使用了 {new_code}',
                              send=True)
            LOGGER.info(
                f"【注册码】：{msg.from_user.first_name}[{msg.chat.id}] 使用了 {register_code} - {us1}")

# @bot.on_message(filters.regex('exchange') & filters.private & user_in_group_on_filter)
# async def exchange_buttons(_, call):
#
#     await rgs_code(_, msg)
