"""
服务器讯息打印

"""
from datetime import datetime, timezone, timedelta
from pyrogram import filters
from bot import bot
from bot.func_helper.emby_utils import get_user_emby_service, get_user_emby_line, get_user_primary_server_id
from bot.func_helper.emby_manager import emby_manager
from bot.func_helper.filters import user_in_group_on_filter
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.fix_bottons import cr_page_server
from bot.func_helper.msg_utils import callAnswer, editMessage


@bot.on_callback_query(filters.regex('server') & user_in_group_on_filter)
async def server(_, call):
    data = sql_get_emby(tg=call.from_user.id)
    if not data:
        return await editMessage(call, '⚠️ 数据库没有你，请重新 /start录入')
    await callAnswer(call, '🌐查询中...')
    try:
        j = int(call.data.split(':')[1])
    except IndexError:
        # 第一次查看
        send = await editMessage(call, "**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 点击按钮查看相应服务器状态**")
        if send is False:
            return

        keyboard, sever = await cr_page_server()
        server_info = sever[0]['server'] if sever else ''
    else:
        keyboard, sever = await cr_page_server()
        server_info = ''.join([item['server'] for item in sever if item['id'] == j])

    pwd = '空' if not data.pwd else data.pwd
    # 根据用户所属服务器和等级获取对应线路
    user_server_id = get_user_primary_server_id(call.from_user.id) or 'main'
    line = get_user_emby_line(user_server_id, data.lv)
    try:
        # 多服务器适配：聚合所有服务器的在线人数
        all_servers = emby_manager.get_all_servers()
        online = 0
        if all_servers:
            for server_id, emby_service in all_servers.items():
                try:
                    count = await emby_service.get_current_playing_count()
                    if count != -1:
                        online += count
                except Exception:
                    pass
        else:
            online = 'Emby服务器断连 ·0'
    except Exception:
        online = 'Emby服务器断连 ·0'
    text = f'**▎↓目前线路(主服务器 {user_server_id}) & 用户密码：**`{pwd}`\n' \
           f'{line}\n\n' \
           f'{server_info}' \
           f'· 🎬 在线 | **{online}** 人\n\n' \
           f'**· 🌏 [{(datetime.now(timezone(timedelta(hours=8)))).strftime("%Y-%m-%d %H:%M:%S")}]**'
    await editMessage(call, text, buttons=keyboard)
