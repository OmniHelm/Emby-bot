"""
服务器健康检查定时任务
定期检查所有 Emby 服务器的连接状态
"""

from datetime import datetime
from typing import Dict, List

from bot import bot, owner, group, config, LOGGER
from bot.func_helper.emby_manager import emby_manager


async def health_check_task():
    """
    健康检查任务
    定期检查所有服务器状态，异常时通知管理员
    """
    LOGGER.info("【健康检查】开始检查所有 Emby 服务器...")

    results = await check_all_servers()

    # 统计结果
    healthy_count = sum(1 for v in results.values() if v['healthy'])
    total_count = len(results)

    LOGGER.info(
        f"【健康检查】完成: {healthy_count}/{total_count} 个服务器正常"
    )

    # 检查是否有服务器异常
    unhealthy_servers = [
        server_id for server_id, status in results.items()
        if not status['healthy']
    ]

    if unhealthy_servers:
        await notify_unhealthy_servers(unhealthy_servers, results)


async def check_all_servers() -> Dict[str, dict]:
    """
    检查所有服务器状态

    Returns:
        字典，格式: {server_id: {'healthy': bool, 'latency': float, 'error': str}}
    """
    results = {}
    servers = config.get_enabled_servers()

    for server_config in servers:
        server_id = server_config.id
        emby_service = emby_manager.get_server(server_id)

        if not emby_service:
            results[server_id] = {
                'healthy': False,
                'latency': -1,
                'error': '服务实例未注册'
            }
            continue

        try:
            start_time = datetime.now()

            # 尝试获取用户列表作为健康检查
            success, data = await emby_service.users()

            latency = (datetime.now() - start_time).total_seconds() * 1000  # ms

            if success:
                results[server_id] = {
                    'healthy': True,
                    'latency': round(latency, 2),
                    'error': None,
                    'user_count': len(data) if isinstance(data, list) else 0
                }
                LOGGER.debug(f"【健康检查】{server_config.name} ✅ 正常 ({latency:.0f}ms)")
            else:
                error_msg = data.get('error', '未知错误') if isinstance(data, dict) else str(data)
                results[server_id] = {
                    'healthy': False,
                    'latency': round(latency, 2),
                    'error': error_msg
                }
                LOGGER.warning(f"【健康检查】{server_config.name} ❌ 异常: {error_msg}")

        except Exception as e:
            results[server_id] = {
                'healthy': False,
                'latency': -1,
                'error': str(e)
            }
            LOGGER.error(f"【健康检查】{server_config.name} ❌ 异常: {e}")

    return results


async def notify_unhealthy_servers(server_ids: List[str], results: Dict[str, dict]):
    """
    通知管理员服务器异常

    Args:
        server_ids: 异常服务器 ID 列表
        results: 完整的检查结果
    """
    text = "⚠️ **服务器健康检查告警**\n\n"
    text += f"检测到 {len(server_ids)} 个服务器异常:\n\n"

    for server_id in server_ids:
        server_config = config.get_server_by_id(server_id)
        status = results.get(server_id, {})

        server_name = server_config.name if server_config else server_id
        error = status.get('error', '未知错误')

        text += f"❌ **{server_name}** (`{server_id}`)\n"
        text += f"   错误: {error}\n\n"

    text += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # 发送给 owner
    try:
        await bot.send_message(owner, text)
        LOGGER.info(f"【健康检查】已发送告警通知给 owner: {owner}")
    except Exception as e:
        LOGGER.error(f"【健康检查】发送告警通知失败: {e}")


async def get_server_status_text() -> str:
    """
    获取服务器状态文本（用于命令响应）

    Returns:
        格式化的状态文本
    """
    results = await check_all_servers()
    servers = config.get_enabled_servers()

    text = "**📡 Emby 服务器状态**\n\n"

    for server_config in servers:
        server_id = server_config.id
        status = results.get(server_id, {})

        if status.get('healthy'):
            icon = "🟢"
            status_text = f"正常 ({status.get('latency', 0):.0f}ms)"
            user_count = status.get('user_count', 'N/A')
        else:
            icon = "🔴"
            status_text = f"异常: {status.get('error', '未知')}"
            user_count = "N/A"

        text += f"{icon} **{server_config.name}**\n"
        text += f"   • ID: `{server_id}`\n"
        text += f"   • 状态: {status_text}\n"
        text += f"   • Emby用户: {user_count}\n"
        text += f"   • 线路: {server_config.line}\n\n"

    text += f"⏰ 检查时间: {datetime.now().strftime('%H:%M:%S')}"

    return text


async def manual_health_check():
    """
    手动触发健康检查（供命令调用）
    """
    return await check_all_servers()
