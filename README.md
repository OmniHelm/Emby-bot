# EmbyBot

基于 Telegram Bot 的 Emby 服务器用户管理系统。通过 Telegram 机器人实现 Emby 用户的创建、续期、权限控制等自动化管理。

## 功能特性

### 用户管理
- 用户注册与邀请码系统
- 自动创建 Emby 账户并同步
- 用户到期自动检测与处理
- 白名单/黑名单管理
- 批量用户操作（封禁、解封、清理）
- 低活跃度用户检测

### 电影请求系统
- TMDB 电影搜索与展示
- 电影请求提交与审核流程
- 管理员审核面板（通过/拒绝）
- 请求状态跟踪
- MoviePilot 集成（自动添加订阅）

### 积分与激励
- 签到系统
- 积分兑换天数
- 红包功能
- 榜单系统（日榜/周榜海报推送）

### 定时任务
- 到期用户自动检测
- 低活跃度检测
- 数据库自动备份
- 收藏记录同步
- 榜单海报定时生成

### Web API（可选）
- RESTful API 接口
- 用户数据查询
- 外部系统集成支持

## 技术栈

- **Bot 框架**: Pyrogram/Pyromod (Telegram MTProto API)
- **数据库**: MySQL + SQLAlchemy ORM
- **定时任务**: APScheduler
- **Web 框架**: FastAPI + Uvicorn
- **HTTP 客户端**: aiohttp
- **图像处理**: Pillow
- **日志**: Loguru

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- Telegram Bot Token
- Emby 服务器（含 API 访问权限）

### 本地部署

1. 克隆项目
```bash
git clone https://github.com/your-repo/EmbyBot.git
cd EmbyBot
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置文件
```bash
cp config_example.json config.json
# 编辑 config.json 填入必要信息
```

4. 运行项目
```bash
python3 main.py
```

### Docker 部署

使用 Docker Compose:
```bash
docker-compose up -d
```

或使用预构建镜像:
```bash
docker pull ghcr.io/omnihelm/emby-bot:latest
docker run -d \
  -v /path/to/config.json:/app/config.json \
  -v /path/to/data:/app/data \
  ghcr.io/omnihelm/emby-bot:latest
```

## 配置说明

编辑 \`config.json\`，必填字段：

\`\`\`json
{
  "bot_token": "你的 Telegram Bot Token",
  "owner_api": "你的 Telegram API ID",
  "owner_hash": "你的 Telegram API Hash",
  "owner": 你的 Telegram 用户 ID,

  "emby_api": "Emby API Key",
  "emby_url": "http://your-emby-server:8096",

  "db_host": "localhost",
  "db_user": "root",
  "db_pwd": "password",
  "db_name": "embybot",
  "db_port": 3306,

  "tmdb_api_key": "TMDB API Key (用于电影搜索功能)"
}
\`\`\`

完整配置参考 \`config_example.json\`。

## 主要命令

### 用户命令
- \`/start\` - 开始使用，显示主面板
- \`/checkin\` - 每日签到
- \`/info\` - 查看个人信息
- \`/jh\` - 使用积分兑换天数
- \`/movie\` - 请求电影

### 管理员命令
- \`/kk\` - 综合用户管理（创建/续期/封禁等）
- \`/renew\` - 调整用户到期时间
- \`/rmemby\` - 删除用户
- \`/prouser\` / \`/revuser\` - 白名单管理
- \`/hide\` / \`/show\` - 隐藏/显示用户
- \`/banned\` / \`/unbanned\` - 封禁/解封用户

### 高级管理命令（需确认）
- \`/deleted\` - 删除指定天数未登录用户
- \`/syncgroupm\` - 同步群组成员
- \`/coinsclear\` - 清空所有用户积分
- \`/unbanall\` / \`/banall\` - 批量解封/封禁
- \`/paolu\` - 跑路模式（删除所有用户）

### 定时任务命令
- \`/check_ex\` - 手动触发到期检测
- \`/low_activity\` - 检测低活跃度用户
- \`/backup_db\` - 备份数据库

## 项目结构

\`\`\`
bot/
├── __init__.py              # 全局配置与 Bot 初始化
├── modules/
│   ├── commands/           # 命令处理器
│   │   ├── movie_request.py  # 电影请求命令
│   │   └── ...
│   ├── callback/           # 回调查询处理
│   ├── panel/              # 用户面板
│   │   └── request_movie_panel.py  # 电影请求面板
│   └── extra/              # 红包等额外功能
├── func_helper/            # 核心功能
│   ├── emby.py            # Emby API 封装
│   ├── tmdb_utils.py      # TMDB API 封装
│   ├── utils.py           # 通用工具
│   ├── scheduler.py       # 定时任务管理
│   └── msg_utils.py       # 消息发送工具
├── sql_helper/             # 数据库操作
│   ├── sql_emby.py        # 用户表
│   ├── sql_code.py        # 邀请码表
│   ├── sql_request_record.py  # 电影请求记录
│   └── ...
├── schemas/
│   └── schemas.py         # Pydantic 配置模型
├── scheduler/              # 定时任务实现
├── ranks_helper/           # 榜单海报生成
└── web/                    # FastAPI Web 服务
\`\`\`

## 权限系统

三级权限体系：
- **普通用户** (user_p): 基础功能（签到、查询、兑换）
- **管理员** (admin_p): 用户管理、审核功能
- **所有者** (owner_p): 全部功能（包括危险操作）

用户等级：
- \`a\` - 白名单用户（永不过期）
- \`b\` - 正常用户
- \`c\` - 临时用户
- \`d\` - 未注册用户

## 开发说明

### 添加新命令

1. 在 \`bot/modules/commands/\` 创建命令文件
2. 使用 \`@bot.on_message()\` 装饰器注册命令
3. 在 \`bot/__init__.py\` 的 \`BotCommand\` 列表中添加命令定义

示例：
\`\`\`python
from bot import bot, LOGGER, admin_p
from pyrogram import filters

@bot.on_message(filters.command("mycommand") & admin_p)
async def my_command_handler(client, message):
    await message.reply("Hello!")
\`\`\`

### 数据库操作

使用 SQLAlchemy ORM，所有表模型在 \`bot/sql_helper/\` 定义：

\`\`\`python
from bot.sql_helper.sql_emby import add_emby, get_emby

# 添加用户
add_emby(tg=123456, embyid="abc123", name="username")

# 查询用户
user = get_emby(tg=123456)
\`\`\`

### Emby API 调用

通过 \`Embyservice\` 单例类：

\`\`\`python
from bot.func_helper.emby import Embyservice

emby = Embyservice()
result = await emby.create_user(name="username", pwd="password")
if result.success:
    emby_id = result.data.get("Id")
\`\`\`

## 注意事项

1. **首次运行**: 数据表会自动创建，无需手动建表
2. **代理配置**: 如需代理访问 Telegram，在 \`config.json\` 配置 \`proxy\` 字段
3. **定时任务**: 通过 \`schedall\` 字段控制各定时任务开关
4. **Docker 备份**: Docker 环境下设置 \`db_is_docker: true\`
5. **电影请求**: 需配置 TMDB API Key 才能使用电影搜索功能
6. **MoviePilot**: 如需自动订阅，配置 \`moviepilot\` 相关字段

## 相关文档

- [快速开始指南](QUICK_START.md)
- [电影请求功能说明](MOVIE_REQUEST_GUIDE.md)
- [实现总结](IMPLEMENTATION_SUMMARY.md)
- [开发指南](CLAUDE.md)

## 许可证

GPL-3.0 License

## 致谢

- Pyrogram - Telegram MTProto API 框架
- Emby - 媒体服务器
- TMDB - 电影数据库 API
