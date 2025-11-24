# EmbyBot 一键部署指南

## 快速开始

### 使用部署脚本（推荐）

1. **下载项目**
   ```bash
   git clone https://github.com/OmniHelm/Emby-bot.git
   cd Emby-bot
   ```

2. **运行部署脚本**
   ```bash
   ./deploy.sh
   ```

3. **按照提示输入配置**
   - 脚本会引导你完成所有必要的配置
   - 支持默认值，直接回车使用默认配置
   - 敏感信息（如密码）会隐藏输入

### 部署脚本功能

部署脚本会帮你完成以下步骤：

#### ✅ 自动配置
- **基础配置**: Bot Token、API ID/Hash、拥有者 ID
- **Emby 配置**: 服务器地址、API Key、访问线路
- **数据库配置**: 自动适配 Docker/本地模式
- **功能开关**: 签到、兑换、白名单等功能
- **定时任务**: 榜单生成、到期检测、数据库备份
- **高级功能**: MoviePilot 集成、代理配置、Web API

#### ✅ 自动部署
- **Docker 模式**: 自动启动 docker-compose 服务
- **本地模式**: 自动安装依赖并启动 Bot

#### ✅ 安全特性
- 自动备份现有配置文件
- 密码输入隐藏显示
- 参数验证和错误提示

## 配置说明

### 必填项

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `bot_token` | Bot Token | 从 [@BotFather](https://t.me/BotFather) 创建 Bot 获取 |
| `owner_api` | Telegram API ID | 从 [https://my.telegram.org](https://my.telegram.org) 获取 |
| `owner_hash` | Telegram API Hash | 从 [https://my.telegram.org](https://my.telegram.org) 获取 |
| `owner` | 拥有者 Telegram ID | 从 [@userinfobot](https://t.me/userinfobot) 获取 |
| `emby_url` | Emby 服务器地址 | 如 `http://192.168.1.100:8096` |
| `emby_api` | Emby API Key | Emby 控制台 → 设置 → 高级 → API 密钥 |
| `db_*` | 数据库配置 | MySQL 连接信息 |

### 可选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `group` | 管理群组 ID 列表 | `[]` |
| `main_group` | 主群组用户名 | `null` |
| `chanel` | 公告频道用户名 | `null` |
| `bot_photo` | Bot 头像 URL | `null` |
| `emby_line` | Emby 访问域名 | `emby.example.com` |
| `emby_whitelist_line` | 白名单专用线路 | `null` |
| `kk_gift_days` | /kk 指令赠送资格天数 | `30` |
| `fuxx_pitao` | 是否狙杀皮套人 | `true` |
| `activity_check_days` | 活跃度检测天数 | `21` |
| `freeze_days` | 账号封存天数（不活跃后） | `5` |

### 功能开关

| 功能 | 配置项 | 默认值 |
|------|--------|--------|
| 签到 | `open.checkin` | `true` |
| 兑换码 | `open.exchange` | `true` |
| 白名单申请 | `open.whitelist` | `true` |
| 邀请功能 | `open.invite` | `false` |
| 退群封禁 | `open.leave_ban` | `true` |
| 播放统计 | `open.uplays` | `true` |
| 红包功能 | `red_envelope.status` | `true` |
| 专属红包 | `red_envelope.allow_private` | `true` |

### 定时任务

| 任务 | 配置项 | 说明 |
|------|--------|------|
| 日榜生成 | `schedall.dayrank` | 每日生成播放榜单 |
| 周榜生成 | `schedall.weekrank` | 每周生成播放榜单 |
| 到期检测 | `schedall.check_ex` | 检测并处理过期用户 |
| 低活跃度检测 | `schedall.low_activity` | 检测不活跃用户 |
| 数据库备份 | `schedall.backup_db` | 定时备份数据库 |

## 部署模式

### Docker 部署（推荐）

**优点**:
- ✅ 环境隔离，依赖完整
- ✅ 一键启动，易于管理
- ✅ 自动重启，稳定可靠

**前置要求**:
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker 服务
systemctl start docker
systemctl enable docker
```

**使用脚本部署**:
```bash
./deploy.sh
# 选择 "是否使用 Docker 部署？" → 输入 y
```

**手动管理**:
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f embyboss

# 重启服务
docker-compose restart embyboss

# 停止服务
docker-compose down

# 更新镜像
docker-compose pull
docker-compose up -d
```

### 本地部署

**优点**:
- ✅ 开发调试方便
- ✅ 资源占用更少

**前置要求**:
```bash
# Python 3.8 或更高版本
python3 --version

# pip
pip3 --version
```

**使用脚本部署**:
```bash
./deploy.sh
# 选择 "是否使用 Docker 部署？" → 输入 n
```

**手动部署**:
```bash
# 安装依赖
pip3 install -r requirements.txt

# 运行 Bot
python3 main.py
```

**使用 systemd 管理服务**:

创建服务文件 `/etc/systemd/system/embybot.service`:
```ini
[Unit]
Description=EmbyBot Telegram Bot
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/Emby-bot
ExecStart=/usr/bin/python3 /root/Emby-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

管理命令:
```bash
# 启动服务
systemctl start embybot

# 开机自启
systemctl enable embybot

# 查看状态
systemctl status embybot

# 查看日志
journalctl -u embybot -f
```

## 常见问题

### 1. 如何获取 Telegram ID？

发送任意消息给 [@userinfobot](https://t.me/userinfobot)，它会回复你的 ID。

### 2. 如何获取群组 ID？

1. 将 Bot 添加到群组
2. 发送任意消息
3. 访问 `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. 在返回的 JSON 中找到 `chat.id`（负数）

### 3. Emby API Key 在哪里？

1. 登录 Emby 控制台
2. 设置 → 高级 → API 密钥
3. 创建新的 API 密钥

### 4. 数据库连接失败？

**Docker 模式**:
- 确保 `db_host` 设置为 `mysql`（容器名）
- 检查 `docker-compose.yml` 中的数据库配置是否匹配

**本地模式**:
- 确保 MySQL 服务已启动
- 检查用户名、密码、数据库名是否正确
- 确保数据库已创建：`CREATE DATABASE embyboss CHARACTER SET utf8mb4;`

### 5. Bot 无法启动？

1. **检查日志**:
   ```bash
   # Docker 模式
   docker-compose logs -f embyboss

   # 本地模式
   tail -f log/bot.log
   ```

2. **常见错误**:
   - `Invalid bot token`: 检查 Bot Token 是否正确
   - `Database error`: 检查数据库连接配置
   - `API error`: 检查 Emby API Key 和 URL 是否正确

### 6. 如何重新配置？

```bash
# 备份当前配置
cp config.json config.json.backup

# 重新运行部署脚本
./deploy.sh
```

### 7. 如何更新 Bot？

**Docker 模式**:
```bash
git pull
docker-compose pull
docker-compose up -d
```

**本地模式**:
```bash
git pull
pip3 install -r requirements.txt --upgrade
systemctl restart embybot  # 或 python3 main.py
```

### 8. 如何启用 MoviePilot 集成？

1. 在部署脚本中选择 "是否配置 MoviePilot 集成？" → `y`
2. 配置以下信息：
   - **服务地址**: MoviePilot 的 URL（如 `http://192.168.1.100:3000`）
   - **用户名**: MoviePilot 管理员用户名
   - **密码**: MoviePilot 管理员密码
   - **电影请求花费**: 用户求片需要的虚拟货币数量
   - **求片通知群组 ID**: 接收求片通知的群组（可选）
   - **下载日志群组 ID**: 接收下载进度通知的群组（可选）
   - **求片用户默认等级**: `a`=白名单、`b`=正常、`c`=临时

**注意**:
- 字段名为 `moviepilot.url`，而非 `moviepilot.host`
- 如果不填写群组 ID，将使用配置中的第一个授权群组
- 详细使用说明请查看 `MOVIE_REQUEST_GUIDE.md`

### 9. 如何配置代理？

1. 在部署脚本中选择 "是否配置代理？" → `y`
2. 输入代理信息：
   - 协议: `socks5` 或 `http`
   - 地址: 如 `127.0.0.1`
   - 端口: 如 `1080`
   - 用户名/密码（可选）

## 配置字段完整参考

### MoviePilot 配置 (moviepilot)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | bool | 是 | 是否启用 MoviePilot 集成 |
| `url` | string | 是* | MoviePilot 服务地址（注意是 `url` 不是 `host`） |
| `username` | string | 是* | MoviePilot 用户名 |
| `password` | string | 是* | MoviePilot 密码 |
| `access_token` | string | 否 | 访问令牌（自动获取） |
| `price` | int | 否 | 求片花费，默认 `1` |
| `download_log_chatid` | int | 否 | 下载日志推送群组 ID |
| `movie_request_chatid` | int | 否 | 求片通知群组 ID（未设置则使用第一个授权群组） |
| `lv` | string | 否 | 求片用户默认等级，默认 `"b"` |

\* 当 `status=true` 时必填

### 红包配置 (red_envelope)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | bool | 否 | 是否启用红包功能，默认 `true` |
| `allow_private` | bool | 否 | 是否允许专属红包，默认 `true` |

### 高级配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kk_gift_days` | int | `30` | `/kk` 指令赠送资格时的天数 |
| `fuxx_pitao` | bool | `true` | 是否狙杀皮套人（检测异常行为） |
| `activity_check_days` | int | `21` | 活跃度检测周期（天） |
| `freeze_days` | int | `5` | 不活跃后账号封存天数 |
| `w_anti_channel_ids` | array | `[]` | 频道反制列表（注意是 `channel` 不是 `chanel`） |

### Open 配置已移除的字段

⚠️ 以下字段已从配置模型中移除，脚本不再生成：
- ~~`open.allow_code`~~ - 已移除

### Open 配置新增字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `open_us` | int | `30` | 开放注册时长 |
| `invite_lv` | string | `"b"` | 邀请用户默认等级 |
| `checkin_reward` | array | `[1, 10]` | 签到奖励范围 [最小值, 最大值] |

## 管理命令速查

### Docker 模式

| 命令 | 说明 |
|------|------|
| `docker-compose up -d` | 启动服务 |
| `docker-compose down` | 停止服务 |
| `docker-compose restart embyboss` | 重启 Bot |
| `docker-compose logs -f embyboss` | 查看日志 |
| `docker-compose pull` | 更新镜像 |
| `docker exec -it embyboss bash` | 进入容器 |

### 本地模式 (systemd)

| 命令 | 说明 |
|------|------|
| `systemctl start embybot` | 启动服务 |
| `systemctl stop embybot` | 停止服务 |
| `systemctl restart embybot` | 重启服务 |
| `systemctl status embybot` | 查看状态 |
| `journalctl -u embybot -f` | 查看日志 |

## 安全建议

1. **保护敏感信息**
   - 不要将 `config.json` 提交到公开仓库
   - 定期更换 API Key 和密码
   - 使用强密码

2. **权限控制**
   - 合理设置管理员权限
   - 定期检查 `admins` 列表
   - 谨慎使用 `/addadmin` 命令

3. **数据备份**
   - 启用定时数据库备份
   - 定期手动备份 `config.json`
   - 测试备份恢复流程

4. **监控**
   - 定期查看日志
   - 监控 Emby 服务器资源使用
   - 关注异常用户行为

## 技术支持

- **项目主页**: [https://github.com/OmniHelm/Emby-bot](https://github.com/OmniHelm/Emby-bot)
- **问题反馈**: [GitHub Issues](https://github.com/OmniHelm/Emby-bot/issues)
- **文档**: 查看项目 `CLAUDE.md` 了解架构细节

---

**祝使用愉快！** 🎉
