# 并发播放监控功能

> **版本**: v1.0
> **更新日期**: 2025-11-25
> **适用对象**: 管理员

---

## 📖 目录

- [功能概述](#功能概述)
- [实现原理](#实现原理)
- [文件清单](#文件清单)
- [配置说明](#配置说明)
- [代码实现](#代码实现)
- [使用方法](#使用方法)
- [通知示例](#通知示例)
- [扩展功能](#扩展功能)

---

## 功能概述

### 需求背景

防止用户分享账号，检测同一个 Emby 用户同时播放超过 2 路视频流的情况，并通知管理员。

### 功能特性

| 特性 | 说明 |
|------|------|
| 定时巡检 | 每隔指定时间检查一次所有活跃会话 |
| 多服务器支持 | 支持检测所有已注册的 Emby 服务器 |
| 用户关联 | 自动关联 Emby 用户与 Telegram ID |
| 管理员通知 | 超标时发送详细信息到管理群 |
| 可选自动处理 | 支持自动终止超标会话（可配置） |

---

## 实现原理

```
┌─────────────────────────────────────────────────────────┐
│                    定时任务触发                          │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│     调用 Emby API: GET /emby/Sessions                   │
│     获取所有活跃播放会话                                  │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│     按 UserId 分组统计每个用户的并发播放数                │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│     并发数 > 阈值?                                       │
│     ├─ 是 → 查询数据库获取 TG ID → 发送通知给管理员       │
│     └─ 否 → 跳过                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 文件清单

需要修改/新增的文件：

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `bot/func_helper/emby.py` | 修改 | 添加 `get_active_sessions()` 方法 |
| `bot/scheduler/stream_monitor.py` | **新建** | 定时检测任务主逻辑 |
| `bot/schemas/schemas.py` | 修改 | 添加 `StreamMonitor` 配置模型 |
| `config_example.json` | 修改 | 添加 `stream_monitor` 配置项 |
| `main.py` | 修改 | 注册定时任务 |

---

## 配置说明

### config.json 配置项

```json
{
  "stream_monitor": {
    "enabled": true,
    "interval": 60,
    "max_streams": 2,
    "auto_terminate": false,
    "notify_user": false
  }
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `false` | 是否启用并发监控 |
| `interval` | int | `60` | 检测间隔（秒） |
| `max_streams` | int | `2` | 最大允许同时播放数 |
| `auto_terminate` | bool | `false` | 超标时是否自动终止多余会话 |
| `notify_user` | bool | `false` | 是否私信通知违规用户 |

---

## 代码实现

### 1. Emby API 新增方法

**文件**: `bot/func_helper/emby.py`

在 `Embyservice` 类中添加：

```python
async def get_active_sessions(self) -> List[Dict]:
    """
    获取所有活跃播放会话

    Returns:
        List[Dict]: 正在播放的会话列表，每个会话包含:
            - user_id: Emby 用户 ID
            - user_name: Emby 用户名
            - session_id: 会话 ID（用于终止会话）
            - device_name: 设备名称
            - client_name: 客户端名称
            - now_playing: 正在播放的内容名称
            - play_method: 播放方式（Direct/Transcode）
    """
    try:
        result = await self._request('GET', '/emby/Sessions')
        if not result.success:
            LOGGER.error(f"获取活跃会话失败: {result.error}")
            return []

        sessions = []
        for session in result.data:
            # 只关注正在播放内容的会话
            now_playing = session.get("NowPlayingItem")
            if now_playing:
                sessions.append({
                    'user_id': session.get('UserId'),
                    'user_name': session.get('UserName'),
                    'session_id': session.get('Id'),
                    'device_name': session.get('DeviceName', '未知设备'),
                    'client_name': session.get('Client', '未知客户端'),
                    'now_playing': now_playing.get('Name', '未知内容'),
                    'play_method': session.get('PlayState', {}).get('PlayMethod', 'Unknown')
                })

        LOGGER.debug(f"获取到 {len(sessions)} 个活跃播放会话")
        return sessions

    except Exception as e:
        LOGGER.error(f"获取活跃会话异常: {str(e)}")
        return []
```

### 2. 配置模型

**文件**: `bot/schemas/schemas.py`

添加配置类：

```python
class StreamMonitor(BaseModel):
    """并发播放监控配置"""
    enabled: bool = False
    interval: int = 60
    max_streams: int = 2
    auto_terminate: bool = False
    notify_user: bool = False
```

在 `Config` 类中添加：

```python
class Config(BaseModel):
    # ... 其他配置 ...
    stream_monitor: StreamMonitor = StreamMonitor()
```

### 3. 定时任务

**文件**: `bot/scheduler/stream_monitor.py`（新建）

```python
"""
并发播放监控 - 检测同一用户同时播放超过阈值的情况
"""
from collections import defaultdict
from pyrogram.errors import FloodWait
from asyncio import sleep

from bot import bot, group, LOGGER, config
from bot.func_helper.emby_manager import emby_manager
from bot.sql_helper.sql_emby import sql_get_emby


async def check_concurrent_streams():
    """
    检测多路并发播放

    遍历所有 Emby 服务器，检查是否有用户同时播放超过阈值的视频流
    """
    max_streams = config.stream_monitor.max_streams
    auto_terminate = config.stream_monitor.auto_terminate
    notify_user = config.stream_monitor.notify_user

    LOGGER.debug(f"【并发监控】开始检测，阈值: {max_streams} 路")

    for server_id in emby_manager.list_server_ids():
        emby_service = emby_manager.get_server(server_id)
        if not emby_service:
            continue

        server_name = emby_manager.get_server_config(server_id).name

        # 获取所有活跃会话
        sessions = await emby_service.get_active_sessions()
        if not sessions:
            continue

        # 按用户分组
        user_streams = defaultdict(list)
        for session in sessions:
            user_streams[session['user_id']].append(session)

        # 检测超标用户
        for user_id, streams in user_streams.items():
            stream_count = len(streams)

            if stream_count > max_streams:
                await handle_violation(
                    server_id=server_id,
                    server_name=server_name,
                    user_id=user_id,
                    streams=streams,
                    max_streams=max_streams,
                    emby_service=emby_service,
                    auto_terminate=auto_terminate,
                    notify_user=notify_user
                )


async def handle_violation(
    server_id: str,
    server_name: str,
    user_id: str,
    streams: list,
    max_streams: int,
    emby_service,
    auto_terminate: bool,
    notify_user: bool
):
    """
    处理违规用户

    Args:
        server_id: 服务器 ID
        server_name: 服务器名称
        user_id: Emby 用户 ID
        streams: 该用户的所有播放会话
        max_streams: 最大允许流数
        emby_service: Emby 服务实例
        auto_terminate: 是否自动终止
        notify_user: 是否通知用户
    """
    stream_count = len(streams)
    emby_name = streams[0]['user_name']

    # 查询对应的 TG ID
    user = sql_get_emby(user_id)
    tg_id = user.tg if user else None
    tg_display = f"`{tg_id}`" if tg_id else "未关联"

    # 构建设备详情
    device_lines = []
    for i, s in enumerate(streams, 1):
        device_lines.append(
            f"  {i}. {s['device_name']} ({s['client_name']})\n"
            f"     └─ {s['now_playing']}"
        )
    devices_text = "\n".join(device_lines)

    # 构建管理员通知消息
    admin_text = (
        f"⚠️ **并发播放超标**\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 用户: `{emby_name}`\n"
        f"🆔 TG ID: {tg_display}\n"
        f"🖥️ 服务器: {server_name}\n"
        f"📺 当前播放: **{stream_count}** 路（上限 {max_streams}）\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📱 设备详情:\n{devices_text}"
    )

    # 自动终止处理
    terminated = []
    if auto_terminate and stream_count > max_streams:
        # 保留最早的 max_streams 个会话，终止其余的
        sessions_to_terminate = streams[max_streams:]
        for session in sessions_to_terminate:
            success = await emby_service.terminate_session(
                session['session_id'],
                reason="超出并发播放限制"
            )
            if success:
                terminated.append(session['device_name'])

        if terminated:
            admin_text += f"\n\n🔴 已自动终止: {', '.join(terminated)}"

    # 发送管理员通知
    try:
        await bot.send_message(group[0], admin_text)
        LOGGER.warning(
            f"【并发监控】超标用户: {emby_name} (TG:{tg_id}) "
            f"- {stream_count}路 @ {server_name}"
        )
    except FloodWait as f:
        await sleep(f.value * 1.2)
        await bot.send_message(group[0], admin_text)
    except Exception as e:
        LOGGER.error(f"【并发监控】发送通知失败: {e}")

    # 私信通知用户
    if notify_user and tg_id:
        user_text = (
            f"⚠️ **播放提醒**\n\n"
            f"检测到您的账户 `{emby_name}` 同时播放 **{stream_count}** 路视频，"
            f"超出了允许的 {max_streams} 路限制。\n\n"
            f"请关闭多余的播放设备，否则可能影响您的账户使用。"
        )
        if terminated:
            user_text += f"\n\n已自动断开: {', '.join(terminated)}"

        try:
            await bot.send_message(tg_id, user_text)
        except Exception as e:
            LOGGER.error(f"【并发监控】通知用户失败 TG:{tg_id} - {e}")
```

### 4. 注册定时任务

**文件**: `main.py`

在定时任务注册区域添加：

```python
# 并发播放监控
if config.stream_monitor.enabled:
    from bot.scheduler.stream_monitor import check_concurrent_streams
    scheduler.add_job(
        check_concurrent_streams,
        'interval',
        seconds=config.stream_monitor.interval,
        id='stream_monitor',
        name='并发播放监控'
    )
    LOGGER.info(f"【定时任务】并发播放监控已启用，间隔 {config.stream_monitor.interval} 秒")
```

---

## 使用方法

### 1. 启用功能

编辑 `config.json`：

```json
{
  "stream_monitor": {
    "enabled": true,
    "interval": 60,
    "max_streams": 2,
    "auto_terminate": false,
    "notify_user": false
  }
}
```

### 2. 重启 Bot

```bash
# Docker 方式
docker restart embybot

# 直接运行
python main.py
```

### 3. 验证运行

查看日志确认任务已注册：

```
INFO - 【定时任务】并发播放监控已启用，间隔 60 秒
```

---

## 通知示例

### 管理员收到的通知

```
⚠️ 并发播放超标
━━━━━━━━━━━━━━━━
👤 用户: test_user
🆔 TG ID: 123456789
🖥️ 服务器: 主服务器
📺 当前播放: 3 路（上限 2）
━━━━━━━━━━━━━━━━
📱 设备详情:
  1. iPhone 15 (Infuse)
     └─ 甄嬛传 S01E05
  2. MacBook Pro (Emby Web)
     └─ 狂飙 S01E12
  3. 小米电视 (Emby Theater)
     └─ 三体 S01E01
```

### 开启自动终止后

```
⚠️ 并发播放超标
...（同上）...

🔴 已自动终止: 小米电视
```

---

## 扩展功能

### 1. 白名单用户豁免

可以为白名单用户（`lv='a'`）设置更高的并发限制：

```python
# 在 handle_violation 函数开头添加
if user and user.lv == 'a':
    whitelist_max = max_streams + 2  # 白名单多给2路
    if stream_count <= whitelist_max:
        return  # 白名单用户未超标，跳过
```

### 2. 违规计数与自动封禁

记录用户违规次数，多次违规后自动封禁：

```python
# 使用 Redis 或数据库记录违规次数
violation_count = get_violation_count(user_id)
if violation_count >= 3:
    await emby_service.emby_change_policy(user_id, disable=True)
    # 通知用户已被封禁
```

### 3. 手动触发检测

添加管理员命令手动触发检测：

```python
@bot.on_message(filters.command("check_streams") & filters.user(admins + [owner]))
async def cmd_check_streams(client, message):
    await message.reply("正在检测并发播放...")
    await check_concurrent_streams()
    await message.reply("检测完成")
```

---

## 注意事项

1. **检测间隔**：建议不要设置过短（<30秒），避免对 Emby 服务器造成压力
2. **自动终止**：谨慎开启，可能影响用户体验，建议先观察一段时间
3. **网络延迟**：用户切换设备时可能短暂出现多路情况，可考虑添加容忍时间
4. **Emby 自带限制**：Emby 本身有 `SimultaneousStreamLimit` 限制，本功能主要用于监控和通知

---

## 相关文件

- [用户指南](./USER_GUIDE.md)
- [命令列表](./COMMANDS.md)
- [多服务器配置](./multi-server-quickstart.md)
