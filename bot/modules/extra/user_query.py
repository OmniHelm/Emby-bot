import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import CallbackQuery

from bot import bot, prefixes, LOGGER, owner, bot_photo, schedall, config
from bot.func_helper.emby_utils import get_user_emby_service, get_emby_line, get_server_by_id_or_none, format_server_list_text, get_user_primary_server_id
from bot.func_helper.emby_manager import emby_manager
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import cv_user_playback_reporting, close_it_ikb
from bot.func_helper.msg_utils import sendMessage, editMessage, sendPhoto
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2, sql_add_emby2
from bot.sql_helper.sql_server_bindings import delete_user_bindings


@bot.on_message(filters.command('user_create', prefixes) & admins_on_filter & filters.private)
async def login_account(_, msg):
    """
    创建非 TG 绑定用户（多服务器版本）

    用法：/user_create [用户名] [使用天数] [服务器ID]

    示例：
        /user_create testuser 30 anime     # 在动漫服务器创建用户
        /user_create testuser 30 movie     # 在电影服务器创建用户
    """
    try:
        name = msg.command[1]
        days = int(msg.command[2])
        server_id = msg.command[3]  # 必须指定服务器ID
    except (IndexError, ValueError, KeyError):
        # 显示帮助信息和可用服务器列表
        help_text = (
            "🔍 **使用格式：**\n\n"
            "`/user_create [用户名] [使用天数] [服务器ID]`\n\n"
            "**示例：**\n"
            "`/user_create testuser 30 anime`\n\n"
        )
        # 添加可用服务器列表
        server_list = format_server_list_text()
        return await sendMessage(msg, help_text + "\n" + server_list, timer=120)

    # 获取指定的服务器配置
    server_config = get_server_by_id_or_none(server_id)
    if not server_config:
        # 服务器不存在，显示可用服务器列表
        error_text = f"❌ 服务器 `{server_id}` 不存在或未启用\n\n"
        server_list = format_server_list_text()
        return await sendMessage(msg, error_text + server_list, timer=120)

    # 获取服务实例
    emby_service = emby_manager.get_server(server_config.id)
    if not emby_service:
        return await sendMessage(msg, f"❌ 无法连接到服务器 {server_config.name}")

    send = await msg.reply(
        f'🆗 收到设置\n\n'
        f'用户名：**{name}**\n'
        f'服务器：**{server_config.name}** (`{server_id}`)\n\n'
        f'__正在为您初始化账户，更新用户策略__......')

    result = await emby_service.emby_create(name=name, days=days)
    if not result:
        await send.edit(
            '创建失败，原因可能如下：\n\n'
            '❎ 已有此账户名，请重新输入注册\n'
            '❔ __emby服务器未知错误！！！请自行排查服务器__\n\n'
            ' 会话已结束！')
        LOGGER.error(f"【创建非tg账户】未知错误，检查是否重复id {name} 或 emby状态，服务器: {server_config.name}")
    else:
        embyid, pwd, ex = result
        sql_add_emby2(embyid=embyid, name=name, cr=datetime.now(), ex=ex, pwd=pwd, pwd2=pwd, server_id=server_config.id)

        # 获取线路地址
        line = get_emby_line(server_config.id, is_whitelist=False)

        await send.edit(
            f'**🎉 成功创建有效期{days}天 #{name}\n\n'
            f'• 服务器 | {server_config.name} (`{server_id}`)\n'
            f'• 用户名称 | `{name}`\n'
            f'• 用户密码 | `{pwd}`\n'
            f'• 访问线路 | \n{line}\n\n'
            f'• 到期时间 | {ex}**')

        if msg.from_user.id != owner:
            await bot.send_message(owner,
                                   f"®️ 管理员 {msg.from_user.first_name} - `{msg.from_user.id}` "
                                   f"已经创建了一个非tg绑定用户 #{name} 有效期**{days}**天\n"
                                   f"服务器: {server_config.name} (`{server_id}`)")
        LOGGER.info(
            f"【创建非tg账户】：管理员 {msg.from_user.first_name}[{msg.from_user.id}] - "
            f"建立了账户 {name}，有效期{days}天，服务器: {server_config.name} ({server_id})")


# 删除指定用户名账号命令
@bot.on_message(filters.command('user_delete', prefixes) & admins_on_filter)
async def urm_user(_, msg):
    """删除指定用户（多服务器版本）"""
    reply = await msg.reply("🍉 正在处理ing....")
    try:
        b = msg.command[1]  # name
    except IndexError:
        return await asyncio.gather(editMessage(reply,
                                                "🔔 **使用格式：**/user_delete [emby用户名]，此命令用于删除指定用户名的用户"),
                                    msg.delete())

    # 尝试从 emby 表查询
    e = sql_get_emby(tg=b)
    stats = None
    if not e:
        # 尝试从 emby2 表查询
        e2 = sql_get_emby2(name=b)
        if not e2:
            return await reply.edit(f"♻️ 没有检索到 {b} 账户，请确认重试或手动检查。")
        e = e2
        stats = 1

    # 获取用户对应的服务器实例
    # emby2 表有 server_id 字段，emby 表需要从 bindings 表获取
    if stats:  # emby2 表
        server_id = e.server_id if hasattr(e, 'server_id') else 'main'
    else:  # emby 表
        server_id = get_user_primary_server_id(e.tg) or 'main'

    emby_service = emby_manager.get_server(server_id)
    if not emby_service:
        return await reply.edit(f"❌ 无法连接到服务器 {server_id}")

    # 删除 Emby 账户
    if await emby_service.emby_del(emby_id=e.embyid):
        # 更新数据库
        if not stats:
            sql_update_emby(Emby.tg == e.tg, lv='d', name=None, embyid=None, cr=None, ex=None)
            delete_user_bindings(e.tg)  # 同时删除绑定记录
        else:
            sql_delete_emby2(e.embyid)

        try:
            await reply.edit(
                f'🎯 done，管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n'
                f'您对Emby账户 {e.name} 的删除操作已完成。\n'
                f'服务器: {server_id}')
        except Exception as ex:
            LOGGER.warning(f"删除 emby 账户后通知失败: {ex}")
        LOGGER.info(
            f"【admin】：管理员 {msg.from_user.first_name} 成功执行删除 emby 账户 {e.name}，服务器: {server_id}")
    else:
        await reply.edit(f"❌ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n"
                         f"您对Emby账户 {e.name} 的删除操作失败。")
        LOGGER.error(
            f"【admin】：管理员 {msg.from_user.first_name} 执行删除失败 emby 账户 {e.name}，服务器: {server_id}")


@bot.on_message(filters.command('user_info', prefixes) & admins_on_filter)
async def uun_info(_, msg, name = None):
    if msg.reply_to_message is None:
        try:
            if name:
                user_id = name
            else:
                user_id = msg.command[1]
        except (IndexError, ValueError):
            user_id = None
    else:
        user_id = msg.reply_to_message.from_user.id
    if not user_id:
        return await asyncio.gather(msg.delete(), sendMessage(msg, "⭕ 用法：/user_info + emby用户名或tgid 或回复用户消息"))
    else:
        text = ''
        e = sql_get_emby(user_id)
        if not e:
            e2 = sql_get_emby2(user_id)
            if not e2:
                return await sendMessage(msg, f'数据库中未查询到 {user_id}，请手动确认')
            e = e2
    try:
        a = f'**· 🆔 查询 TG** | {e.tg}\n'
    except AttributeError:
        a = ''

    if e.name and schedall.low_activity and not schedall.check_ex:
        ex = f'__若{config.activity_check_days}天无观看将封禁__'

    elif e.name and not schedall.low_activity and not schedall.check_ex:
        ex = ' __无需保号，放心食用__'
    else:
        ex = e.ex or '无账户信息'
    text += f"▎ 查询返回\n" \
            f"**· 🍉 账户名称** | {e.name}\n{a}" \
            f"**· 🍓 当前状态** | {e.lv}\n" \
            f"**· 🍒 创建时间** | {e.cr}\n" \
            f"**· 🚨 到期时间** | **{ex}**\n"

    await asyncio.gather(sendPhoto(msg, photo=bot_photo, caption=text, buttons=cv_user_playback_reporting(e.embyid)), msg.delete())


@bot.on_callback_query(filters.regex('userip') & admins_on_filter)
@bot.on_message(filters.command('user_ip', prefixes) & admins_on_filter)
async def user_cha_ip(_, msg, name = None):
    """查看用户播放IP（多服务器版本）"""
    if isinstance(msg, CallbackQuery):
        user_id = msg.data.split('-')[1]
        msg = msg.message
    else:
        if msg.reply_to_message is None:
            try:
                if name:
                    user_id = name
                else:
                    user_id = msg.command[1]
            except (IndexError, ValueError):
                user_id = None
        else:
            user_id = msg.reply_to_message.from_user.id
    if not user_id:
        return await sendMessage(msg, "⭕ 用法：/user_ip + emby用户名或tgid 或回复用户消息")

    e = sql_get_emby(user_id)
    if not e:
        return await sendMessage(msg, f"数据库中未查询到 {user_id}，请手动确认")

    # 获取用户对应的服务实例
    emby_service, server_config, user = get_user_emby_service(e.tg)
    if not emby_service:
        return await sendMessage(msg, f"❌ 无法连接到用户所在服务器")

    success, result = await emby_service.get_emby_userip(emby_id=e.embyid)
    if not success or len(result) == 0:
        return await sendMessage(msg, 'TA好像没播放信息吖')
    else:
        device_count = 0
        ip_count = 0
        device_list = []
        ip_list = []
        device_details = ""
        ip_details = ""
        for r in result:
            device, client, ip = r
            # 统计ip
            if ip not in ip_list:
                ip_count += 1
                ip_list.append(ip)
                ip_details += f'{ip_count}: `{ip}`| [{ip}](https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true) \n'

            # 统计设备并拼接详情
            if device + client not in device_list:
                device_count += 1
                device_list.append(device + client)
                device_details += f'{device_count}: {device} | {client}  \n'
        text = '**🌏 以下为该用户播放过的设备&ip 共{}个设备，{}个ip：**\n\n'.format(device_count, ip_count) + '**设备:**\n' + device_details + '**IP:**\n'+ ip_details


        # 以\n分割文本，每20条发送一个消息
        messages = text.split('\n')
        # 每20条消息组成一组
        for i in range(0, len(messages), 20):
            chunk = messages[i:i+20]
            chunk_text = '\n'.join(chunk)
            if not chunk_text.strip():
                continue
            await sendMessage(msg, chunk_text)
@bot.on_message(filters.command('user_device', prefixes) & admins_on_filter)
async def get_user_by_deviceid(_, msg, deviceid = None):
    """根据设备ID查询用户（多服务器版本）"""
    try:
        deviceid = msg.command[1]
    except IndexError:
        return await sendMessage(msg, "⭕ 用法：/user_device + 设备ID")
    await msg.delete()

    # 遍历所有服务器查找设备
    all_servers = emby_manager.get_all_servers()
    result = None
    found_server = None

    for server_id, emby_service in all_servers.items():
        success, device_info = await emby_service.get_device_by_deviceid(deviceid=deviceid)
        if success and isinstance(device_info, dict) and len(device_info) > 0:
            result = device_info
            found_server = server_id
            break

    if not result:
        return await sendMessage(msg, '未在任何服务器找到该设备信息')
    else:
        server_name = config.get_server_by_id(found_server).name if found_server else "未知"
        text = f'▎ 查询返回 (服务器: {server_name}):\n'
        text += f'•🧢 设备名称: {result.get("Name", "无设备名称")}\n'
        text += f'•🙆‍ App名称: {result.get("AppName", "无App名称")}\n'
        text += f'•👔 App版本: {result.get("AppVersion", "无App版本")}\n'
        text += f'•👖 用户名称: {result.get("LastUserName", "无用户名称")}\n'
        text += f'•👟 用户Id: {result.get("LastUserId", "无用户Id")}\n'
        text += f'•💼 最后活动时间: {result.get("DateLastActivity", "无最后活动时间")}\n'
        text += f'•🔐 Ip地址: {result.get("IpAddress", "无Ip地址")}\n'
        icon = result.get("IconUrl")
        if icon:
            await sendPhoto(msg, photo=icon, caption=text, buttons=close_it_ikb)
        else:
            await sendMessage(msg, text, buttons=close_it_ikb)
