# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

EmbyBot 是一个基于 Telegram Bot 的 Emby 服务器用户管理系统。通过 Telegram 机器人管理 Emby 用户的创建、续期、权限控制等操作。

## 核心架构

### 1. 技术栈
- **Bot 框架**: Pyrogram/Pyromod - 异步 Telegram MTProto API 客户端
- **数据库**: MySQL (通过 SQLAlchemy ORM)
- **定时任务**: APScheduler
- **Web API**: FastAPI + Uvicorn (可选)
- **HTTP 客户端**: aiohttp (用于 Emby API 调用)
- **图像处理**: Pillow (用于榜单海报生成)

### 2. 项目结构

```
bot/
├── __init__.py              # 全局配置加载、Bot 实例初始化、命令权限定义
├── modules/                 # 功能模块
│   ├── commands/           # 所有 Bot 命令处理器
│   ├── callback/           # 回调查询处理器
│   ├── panel/              # 用户面板相关
│   └── extra/              # 额外功能（如红包等）
├── func_helper/            # 核心辅助功能
│   ├── emby.py            # Emby API 封装 (Embyservice 单例类)
│   ├── utils.py           # 通用工具函数
│   ├── scheduler.py       # 定时任务管理
│   ├── msg_utils.py       # 消息发送工具
│   ├── logger_config.py   # 日志配置
│   └── moviepilot.py      # MoviePilot 集成
├── sql_helper/             # 数据库操作
│   ├── sql_emby.py        # Emby 用户表操作
│   ├── sql_server_bindings.py  # 用户-服务器绑定表操作
│   ├── sql_code.py        # 邀请码表操作
│   └── sql_favorites.py   # 收藏记录表操作
├── schemas/                # 数据模型
│   └── schemas.py         # Pydantic 配置模型定义
├── scheduler/              # 定时任务实现
│   ├── check_ex.py        # 到期检测
│   ├── ranks_task.py      # 榜单生成
│   ├── backup_db.py       # 数据库备份
│   └── sync_favorites.py  # 同步收藏记录
├── ranks_helper/           # 榜单海报生成
└── web/                    # FastAPI Web 服务
    └── api/               # API 路由
```

### 3. 核心设计模式

#### 配置系统
- 使用 Pydantic 进行配置验证 (`bot/schemas/schemas.py`)
- 配置文件: `config.json` (示例: `config_example.json`)
- 配置在 `bot/__init__.py` 中加载并作为全局变量导出

#### 数据库架构
- 使用 SQLAlchemy ORM
- 会话管理在 `bot/sql_helper/__init__.py`
- 完整表结构见 `schema.sql`

**主要表：**

| 表名 | 说明 | 主键 |
|------|------|------|
| `emby` | TG 用户表 | tg |
| `emby_server_bindings` | 用户-服务器绑定表 | (tg, server_id) |
| `emby2` | 非 TG 用户表 | embyid |
| `Rcode` | 注册码表 | code |
| `emby_favorites` | 收藏记录表 | id |
| `request_records` | 求片记录表 | download_id |

**多服务器设计（一号通用模式）：**
```
emby 表（用户基础信息）
├── tg (主键)
├── embyid (首次注册的服务器，向后兼容)
├── name, pwd, pwd2 (所有服务器统一)
├── lv, cr, ex (所有服务器统一)
└── us, iv (积分/币，全局)

emby_server_bindings 表（多服务器绑定）
├── tg + server_id (联合主键)
├── embyid (该服务器上的 Emby ID)
├── is_primary (是否主服务器)
└── enabled (是否启用)
```

**业务流程：**
1. 用户注册 → 写入 `emby` 表 + 所有启用服务器的 `emby_server_bindings`
2. 续期/封禁 → 更新 `emby.ex/lv`，同步操作所有绑定服务器
3. 查询用户 → `emby` 获取基础信息，`emby_server_bindings` 获取各服务器 embyid

#### Emby API 交互
- `Embyservice` 单例类封装所有 Emby API 操作 (`bot/func_helper/emby.py`)
- 使用 aiohttp 异步请求
- 提供统一的错误处理和重试机制
- 核心方法: `create_user()`, `delete_user()`, `update_policy()`, `get_users()` 等

#### 权限系统
- 三级权限: `user_p` < `admin_p` < `owner_p`
- 命令权限在 `bot/__init__.py` 中通过 BotCommand 列表定义
- 等级字段 `lv`: 'a'=白名单, 'b'=正常, 'c'=临时, 'd'=未注册

### 4. 关键功能模块

#### 用户管理命令
- `/kk` - 综合用户管理 (创建/续期/封禁等)
- `/renew` - 调整到期时间
- `/rmemby` - 删除用户
- `/prouser` / `/revuser` - 白名单管理

#### 定时任务
- 到期检测 (`check_ex.py`) - 自动处理过期用户
- 活跃度检测 (`low_activity`) - 检测不活跃用户
- 榜单生成 (`ranks_task.py`) - 日榜/周榜海报推送
- 数据库备份 (`backup_db.py`)

#### Web API (可选)
- 如果 `config.json` 中 `api.status = true` 则启动
- FastAPI 应用在 `bot/web/__init__.py` 初始化
- 路由定义在 `bot/web/api/` 目录

## 开发命令

### 运行项目
```bash
python3 main.py
```

### Docker 部署
```bash
# 使用 docker-compose
docker-compose up -d

# 或使用预构建镜像
docker pull ghcr.io/omnihelm/emby-bot:latest
```

### 数据库操作
项目使用 MySQL，需要先配置 `config.json` 中的数据库连接信息:
```json
{
  "db_host": "localhost",
  "db_user": "root",
  "db_pwd": "password",
  "db_name": "embybot",
  "db_port": 3306
}
```

数据表会在首次运行时自动创建 (通过 SQLAlchemy 的 `create()`)。

### 配置文件
首次使用需复制并修改配置:
```bash
cp config_example.json config.json
# 然后编辑 config.json 填入必要信息
```

必填字段:
- `bot_token`: Telegram Bot Token
- `owner_api`, `owner_hash`: Telegram API 凭据
- `owner`: 拥有者的 Telegram ID
- `emby_api`, `emby_url`: Emby 服务器信息
- 数据库连接信息

## 代码规范

### 导入顺序
1. 标准库
2. 第三方库
3. 本地模块 (从 `bot` 包导入)

### 异步编程
- 所有 Telegram 命令处理器和 Emby API 调用都是异步的
- 使用 `async/await` 语法
- Emby API 通过 `aiohttp` 异步调用

### 错误处理
- 数据库操作使用 try-except 并记录日志
- Emby API 调用统一返回 `EmbyApiResult` 对象
- 使用 `loguru` 进行日志记录 (通过 `bot.LOGGER`)

### 命令确认机制
部分危险命令 (如 `deleted`, `syncgroupm`, `coinsclear`, `unbanall`, `banall`, `paolu`) 需要用户确认才能执行。在命令处理器中使用 `confirmation` 参数验证。

## 注意事项

1. **Emby API 版本**: 使用 Emby API (非 Jellyfin)，具体文档参考 https://swagger.emby.media/
2. **用户策略**: 创建用户时使用 `create_policy()` 函数生成标准策略，默认限制同时播放数为 2
3. **定时任务控制**: 所有定时任务在 `config.json` 的 `schedall` 字段中控制开关
4. **Docker 模式**: 如果在 Docker 中运行且需要备份数据库，设置 `db_is_docker: true`
5. **代理支持**: 如果 Telegram API 需要代理，在 `config.json` 的 `proxy` 字段配置
6. **红包功能**: 在 `bot/modules/extra/` 实现，使用 Pillow 生成红包图片
7. **榜单海报**: 使用 `bot/ranks_helper/` 中的模板和字体资源生成
