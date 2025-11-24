"""
管理员命令：求片管理

提供查看、导出求片记录等功能
"""

from pyrogram import filters
from bot import bot, prefixes, LOGGER
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage, editMessage, callAnswer
from bot.sql_helper.sql_request_record import (
    sql_get_movie_requests,
    sql_get_all_movie_requests_for_export,
    sql_get_movie_request_stats,
    sql_update_request_status
)
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.tmdb_utils import get_media_type_cn
import csv
import os
import math
from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@bot.on_message(filters.command('viewrequests', prefixes) & admins_on_filter)
async def view_movie_requests(_, msg):
    """查看求片记录（支持分页）"""
    await msg.delete()

    # 获取统计信息
    stats = sql_get_movie_request_stats()

    # 获取第一页数据
    records, has_prev, has_next = sql_get_movie_requests(status='pending', page=1, limit=10)

    if not records:
        text = (
            f"📋 求片记录统计\n\n"
            f"总数: {stats['total']}\n"
            f"待处理: {stats['pending']}\n"
            f"已完成: {stats['completed']}\n\n"
            f"✅ 暂无待处理的求片记录"
        )
        await sendMessage(msg, text, timer=60)
        return

    text = await create_request_list_text(records, page=1, stats=stats)
    keyboard = create_request_page_keyboard(page=1, has_prev=has_prev, has_next=has_next)

    await sendMessage(msg, text, buttons=keyboard, timer=120)


@bot.on_callback_query(filters.regex('^movie_request_page:') & admins_on_filter)
async def handle_request_page(_, call):
    """处理求片记录翻页"""
    page = int(call.data.split(':')[1])
    await callAnswer(call, f'📃 第 {page} 页')

    records, has_prev, has_next = sql_get_movie_requests(status='pending', page=page, limit=10)

    if not records:
        await callAnswer(call, '❌ 没有更多记录了', True)
        return

    stats = sql_get_movie_request_stats()
    text = await create_request_list_text(records, page=page, stats=stats)
    keyboard = create_request_page_keyboard(page=page, has_prev=has_prev, has_next=has_next)

    await editMessage(call, text, buttons=keyboard)


@bot.on_callback_query(filters.regex('^movie_request_complete:') & admins_on_filter)
async def handle_request_complete(_, call):
    """标记求片为已完成"""
    download_id = call.data.split(':', 1)[1]
    await callAnswer(call, '✅ 标记为已完成')

    success = sql_update_request_status(
        download_id=download_id,
        download_state='completed'
    )

    if success:
        await callAnswer(call, '✅ 已标记为完成', True)
        # 刷新当前页
        await callAnswer(call, '🔄 刷新列表')
        # TODO: 刷新当前页面
    else:
        await callAnswer(call, '❌ 操作失败', True)


@bot.on_message(filters.command('exportrequests', prefixes) & admins_on_filter)
async def export_movie_requests(_, msg):
    """导出所有求片记录为 CSV 文件"""
    await msg.delete()

    try:
        # 获取所有求片记录
        records = sql_get_all_movie_requests_for_export()

        if not records:
            await sendMessage(msg, '❌ 暂无求片记录可导出', timer=30)
            return

        # 生成 CSV 文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'movie_requests_{timestamp}.csv'
        filepath = f'/tmp/{filename}'

        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow([
                '用户TG ID',
                '用户名',
                '片名',
                '类型',
                'TMDB ID',
                '链接',
                '状态',
                '创建时间',
                '更新时间'
            ])

            # 写入数据
            for record in records:
                # 提取信息
                download_id = record.download_id
                tmdb_info = parse_download_id(download_id)

                # 获取用户信息
                user = sql_get_emby(tg=record.tg)
                username = user.name if user else '未知'

                # 提取链接
                link = ''
                if record.detail and '链接:' in record.detail:
                    link = record.detail.split('链接:')[1].split('\n')[0].strip()

                writer.writerow([
                    record.tg,
                    username,
                    record.request_name,
                    tmdb_info['media_type_cn'],
                    tmdb_info['tmdb_id'],
                    link,
                    record.download_state,
                    record.create_at.strftime('%Y-%m-%d %H:%M:%S'),
                    record.update_at.strftime('%Y-%m-%d %H:%M:%S') if record.update_at else ''
                ])

        # 发送文件
        await bot.send_document(
            chat_id=msg.chat.id,
            document=filepath,
            caption=f"📊 求片记录导出\n\n总计: {len(records)} 条记录"
        )

        # 删除临时文件
        os.remove(filepath)
        LOGGER.info(f"求片记录已导出: {len(records)} 条")

    except Exception as e:
        LOGGER.error(f"导出求片记录失败: {str(e)}")
        await sendMessage(msg, f'❌ 导出失败: {str(e)}', timer=30)


async def create_request_list_text(records, page: int, stats: dict) -> str:
    """创建求片列表文本"""
    text = (
        f"📋 求片记录（第 {page} 页）\n\n"
        f"📊 统计: 总计 {stats['total']} | 待处理 {stats['pending']} | 已完成 {stats['completed']}\n\n"
    )

    for i, record in enumerate(records, start=1):
        # 解析 download_id
        tmdb_info = parse_download_id(record.download_id)

        # 获取用户信息
        user = sql_get_emby(tg=record.tg)
        username = user.name if user else '未知'

        # 提取链接
        link = ''
        if record.detail and '链接:' in record.detail:
            link = record.detail.split('链接:')[1].split('\n')[0].strip()

        text += (
            f"{i}. 《{record.request_name}》\n"
            f"   类型: {tmdb_info['media_type_cn']} | TMDB ID: {tmdb_info['tmdb_id']}\n"
            f"   用户: {username} ({record.tg})\n"
            f"   状态: {record.download_state}\n"
            f"   时间: {record.create_at.strftime('%Y-%m-%d %H:%M')}\n"
        )

        if link:
            text += f"   链接: {link}\n"

        text += "\n"

    text += "💡 使用 /exportrequests 导出完整记录"

    return text


def create_request_page_keyboard(page: int, has_prev: bool, has_next: bool):
    """创建翻页键盘"""
    buttons = []

    # 翻页按钮
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton('⬅️ 上一页', callback_data=f'movie_request_page:{page-1}'))
    if has_next:
        nav_row.append(InlineKeyboardButton('➡️ 下一页', callback_data=f'movie_request_page:{page+1}'))

    if nav_row:
        buttons.append(nav_row)

    # 刷新按钮
    buttons.append([InlineKeyboardButton('🔄 刷新', callback_data=f'movie_request_page:{page}')])

    return InlineKeyboardMarkup(buttons)


def parse_download_id(download_id: str) -> dict:
    """
    解析 download_id，提取 TMDB 信息

    :param download_id: 格式为 'tmdb_movie_12345' 或 'tmdb_tv_67890'
    :return: {'tmdb_id': '12345', 'media_type': 'movie', 'media_type_cn': '电影'}
    """
    try:
        parts = download_id.split('_')
        if len(parts) >= 3 and parts[0] == 'tmdb':
            media_type = parts[1]  # 'movie' or 'tv'
            tmdb_id = parts[2]

            return {
                'tmdb_id': tmdb_id,
                'media_type': media_type,
                'media_type_cn': get_media_type_cn(media_type)
            }
    except Exception:
        pass

    # 默认值
    return {
        'tmdb_id': '未知',
        'media_type': 'unknown',
        'media_type_cn': '未知'
    }
