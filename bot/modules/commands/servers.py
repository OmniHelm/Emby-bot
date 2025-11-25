"""
服务器管理命令
提供服务器列表查看和状态检查功能
"""

from pyrogram import filters
from pyrogram.types import Message

from bot import bot, LOGGER, admin_p, owner
from bot.func_helper.emby_utils import format_server_list_text
from bot.scheduler.health_check import get_server_status_text, manual_health_check


@bot.on_message(filters.command('servers') & filters.private)
async def servers_command(_, message: Message):
    """
    列出所有可用服务器
    命令: /servers
    权限: 管理员
    """
    tg = message.from_user.id

    # 权限检查
    if tg not in [cmd.command for cmd in admin_p] and tg != owner:
        # 对普通用户显示简化版本
        text = format_server_list_text()
        await message.reply(text)
        return

    # 管理员显示详细状态
    status_msg = await message.reply("⏳ 正在检查服务器状态...")

    try:
        text = await get_server_status_text()
        await status_msg.edit_text(text)
    except Exception as e:
        LOGGER.error(f"获取服务器状态失败: {e}")
        await status_msg.edit_text(f"❌ 获取服务器状态失败: {e}")


@bot.on_message(filters.command('servercheck') & filters.private)
async def server_check_command(_, message: Message):
    """
    手动触发健康检查
    命令: /servercheck
    权限: 管理员
    """
    tg = message.from_user.id

    # 权限检查 - 仅管理员可用
    admin_ids = [owner] + [a for a in admin_p if isinstance(a, int)]
    if tg not in admin_ids and tg != owner:
        await message.reply("❌ 您没有权限执行此操作")
        return

    status_msg = await message.reply("⏳ 正在执行健康检查...")

    try:
        results = await manual_health_check()

        # 统计结果
        healthy = sum(1 for v in results.values() if v.get('healthy'))
        total = len(results)

        text = f"**🔍 健康检查结果**\n\n"
        text += f"状态: {healthy}/{total} 个服务器正常\n\n"

        for server_id, status in results.items():
            if status.get('healthy'):
                icon = "✅"
                latency = status.get('latency', 0)
                text += f"{icon} `{server_id}` - {latency:.0f}ms\n"
            else:
                icon = "❌"
                error = status.get('error', '未知')
                text += f"{icon} `{server_id}` - {error}\n"

        await status_msg.edit_text(text)

    except Exception as e:
        LOGGER.error(f"健康检查失败: {e}")
        await status_msg.edit_text(f"❌ 健康检查失败: {e}")
