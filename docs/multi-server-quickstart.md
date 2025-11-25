# 多服务器功能快速开始指南

## 📋 概述

EmbyBot 现已支持多服务器配置，可以同时管理多个不同内容类型的 Emby 服务器。

**典型使用场景**：
- 🎨 **动漫服务器** - 专门提供动漫内容
- 🎬 **电影服务器** - 专门提供电影内容
- 📺 **剧集服务器** - 专门提供电视剧内容
- 🎵 **音乐服务器** - 专门提供音乐内容

**核心特点**：
- ✅ 每个服务器独立运行，内容互不干扰
- ✅ 用户手动选择访问哪个服务器
- ✅ 支持为不同服务器配置独立的访问线路
- ✅ 完全向后兼容旧的单服务器配置

---

## 🚀 快速开始（3 步）

### 第 1 步：数据库迁移

新架构中，emby 用户基础表不再存放 `server_id`，用户与服务器的对应关系存放在绑定表 `emby_server_bindings` 中。

请执行绑定迁移脚本，将历史用户写入绑定表（默认绑定到 `main` 或你指定的服务器）：

```bash
# 方式一：统一绑定到指定服务器（推荐）
python3 scripts/migrate_bindings.py --server-id main

# 方式二：如历史上 emby 表存在 server_id 列，可读取该列进行绑定
python3 scripts/migrate_bindings.py --use-emby-server-id

# 仅预览（不写入）
python3 scripts/migrate_bindings.py --server-id main --dry-run
```

同时，非TG用户表与收藏表仍按服务器分离存储：

```bash
# 如尚未执行过，请确保为 emby2 / emby_favorites 添加 server_id 字段（仅首次部署需要）
mysql -u your_user -p your_database < migrations/002_add_server_id_to_emby2_favorites.sql
```

---

### 第 2 步：更新配置文件

编辑 `config.json`，添加多服务器配置：

```json
{
  "emby_servers": [
    {
      "id": "anime",
      "name": "动漫服务器",
      "api_key": "your_anime_api_key",
      "url": "http://192.168.1.100:8096",
      "line": "https://anime.example.com",
      "whitelist_line": "https://vip-anime.example.com",
      "enabled": true
    },
    {
      "id": "movie",
      "name": "电影服务器",
      "api_key": "your_movie_api_key",
      "url": "http://192.168.1.101:8096",
      "line": "https://movie.example.com",
      "enabled": true
    },
    {
      "id": "series",
      "name": "剧集服务器",
      "api_key": "your_series_api_key",
      "url": "http://192.168.1.102:8096",
      "line": "https://series.example.com",
      "enabled": true
    }
  ]
}
```

**配置说明**：
- `id`：服务器唯一标识（**必填**，只能包含字母、数字、下划线、连字符）
- `name`：服务器显示名称（用于界面显示）
- `api_key`：Emby API 密钥
- `url`：服务器内部 API 访问地址
- `line`：用户访问线路地址
- `whitelist_line`：白名单用户专属访问地址（**可选**）
- `enabled`：是否启用该服务器

---

### 第 3 步：重启 Bot

```bash
# Docker 部署
docker restart embybot

# 直接运行
# 停止当前进程，然后：
python3 main.py
```

启动日志应显示：
```
✓ Emby 服务器初始化完成，已注册 3 个服务器: ['anime', 'movie', 'series']
```

---

## 💡 使用方法

### 创建用户（管理员）

**新命令格式**：
```bash
/ucr [用户名] [天数] [服务器ID]
```

**示例**：
```bash
# 在动漫服务器创建用户
/ucr testuser001 30 anime

# 在电影服务器创建用户
/ucr testuser002 30 movie

# 在剧集服务器创建用户
/ucr testuser003 30 series
```

**获取帮助**：
```bash
/ucr
# Bot 会显示使用格式和所有可用服务器列表
```

---

### 查看服务器列表

Bot 会在需要时自动显示可用服务器列表，包含：
- 服务器名称和 ID
- 当前用户数
- 访问线路地址

---

### 用户体验

用户注册后会收到：
```
🎉 成功创建有效期30天 #testuser001

• 服务器 | 动漫服务器 (anime)
• 用户名称 | testuser001
• 用户密码 | ****
• 访问线路 |
https://anime.example.com

• 到期时间 | 2024-12-24 10:30:00
```

用户使用对应的访问线路登录即可。

---

## 🔧 配置示例

### 示例 1：内容分类服务器

适合按内容类型分类的场景：

```json
{
  "emby_servers": [
    {
      "id": "anime",
      "name": "动漫服务器",
      "api_key": "xxx",
      "url": "http://anime.local:8096",
      "line": "https://anime.example.com",
      "enabled": true
    },
    {
      "id": "movie",
      "name": "电影服务器",
      "api_key": "yyy",
      "url": "http://movie.local:8096",
      "line": "https://movie.example.com",
      "enabled": true
    },
    {
      "id": "series",
      "name": "剧集服务器",
      "api_key": "zzz",
      "url": "http://series.local:8096",
      "line": "https://series.example.com",
      "enabled": true
    }
  ]
}
```

---

### 示例 2：地区分类服务器

适合按地区或语言分类的场景：

```json
{
  "emby_servers": [
    {
      "id": "cn",
      "name": "国产内容服务器",
      "api_key": "xxx",
      "url": "http://cn.local:8096",
      "line": "https://cn.example.com",
      "enabled": true
    },
    {
      "id": "us",
      "name": "欧美内容服务器",
      "api_key": "yyy",
      "url": "http://us.local:8096",
      "line": "https://us.example.com",
      "enabled": true
    },
    {
      "id": "jp",
      "name": "日韩内容服务器",
      "api_key": "zzz",
      "url": "http://jp.local:8096",
      "line": "https://jp.example.com",
      "enabled": true
    }
  ]
}
```

---

### 示例 3：付费等级分类

适合提供不同等级服务的场景：

```json
{
  "emby_servers": [
    {
      "id": "free",
      "name": "免费服务器",
      "api_key": "xxx",
      "url": "http://free.local:8096",
      "line": "https://free.example.com",
      "enabled": true
    },
    {
      "id": "premium",
      "name": "高级服务器",
      "api_key": "yyy",
      "url": "http://premium.local:8096",
      "line": "https://premium.example.com",
      "whitelist_line": "https://vip-premium.example.com",
      "enabled": true
    }
  ]
}
```

---

## 📊 数据迁移说明

### 绑定表现状与统计

迁移完成后（或任意时刻），你可以统计每台服务器的绑定用户数：

```sql
SELECT server_id, COUNT(*) AS user_count
FROM emby_server_bindings
GROUP BY server_id;
```

如果想为某些用户补充或调整绑定，推荐使用 Bot 管理命令或在 Telegram 面板中进行变更。
（绑定表 `emby_server_bindings` 的主键为 `(tg, server_id)`，直接更新时需注意唯一约束。）

### 收藏与媒体通知（Webhook）

从本版本起，收藏与媒体库更新的 Webhook 需要携带服务器 ID：

- 收藏变更 Webhook（新）
  - `POST /emby/webhook/{server_id}/favorites?token=YOUR_BOT_TOKEN`
  - 兼容旧路由：`POST /emby/webhook/favorites?token=...`（默认按 `main`，请尽快迁移）

- 媒体库变更 Webhook（新）
  - `POST /emby/webhook/{server_id}/medias?token=YOUR_BOT_TOKEN`
  - 兼容旧路由：`POST /emby/webhook/medias?token=...`（默认按 `main`，请尽快迁移）

> 说明：`/emby` 为内置 API 前缀，`token` 为机器人 Token，用于简单鉴权。

---

## 🐛 故障排查

### 问题 1：Bot 启动失败

**错误信息**：`服务器配置不存在: server_id=xxx`

**解决**：
1. 检查 `config.json` 中是否配置了该服务器
2. 检查服务器的 `enabled` 字段是否为 `true`
3. 检查服务器 `id` 是否拼写正确

---

### 问题 2：创建用户时提示服务器不存在

**错误信息**：`❌ 服务器 anime 不存在或未启用`

**解决**：
1. 执行 `/ucr` 命令（不带参数）查看可用服务器列表
2. 确认服务器 ID 拼写正确（区分大小写）
3. 检查配置文件中该服务器的 `enabled` 是否为 `true`

---

### 问题 3：无法连接到服务器

**错误信息**：`❌ 无法连接到服务器 XXX`

**解决**：
1. 检查服务器 `url` 是否正确
2. 检查 `api_key` 是否有效
3. 测试网络连接：`curl http://your_server:8096/System/Info?api_key=xxx`
4. 查看 Bot 启动日志，确认服务器已成功注册

---

### 问题 4：用户看不到内容

**可能原因**：
- 用户使用了错误的服务器线路
- 服务器媒体库权限未正确配置

**解决**：
1. 确认用户使用的登录地址与配置的 `line` 一致
2. 检查 Emby 服务器端的用户权限配置
3. 检查媒体库是否正确授权给用户

---

## 🔄 向后兼容

### 旧配置自动转换

如果你的 `config.json` 仍使用旧格式：
```json
{
  "emby_api": "xxxxx",
  "emby_url": "http://xxx:8096",
  "emby_line": "xxx.com"
}
```

Bot 会自动转换为单服务器配置（id=main）：
```json
{
  "emby_servers": [
    {
      "id": "main",
      "name": "主服务器",
      "api_key": "xxxxx",
      "url": "http://xxx:8096",
      "line": "xxx.com",
      "enabled": true
    }
  ]
}
```

**使用旧配置时的命令格式**：
```bash
# 仍需指定服务器ID（默认为 main）
/ucr testuser 30 main
```

---

## 📚 相关文档

- [多服务器技术方案](./multi-server-migration-plan.md) - 详细的技术设计
- [迁移完成报告](./MIGRATION_COMPLETED.md) - 完整的迁移记录

---

## 💡 最佳实践

1. **清晰的服务器命名**：使用简短、易记的 ID（如：anime, movie, series）
2. **服务器分类**：按内容类型、地区或服务等级分类
3. **访问线路配置**：为每个服务器配置独立的访问域名
4. **白名单线路**：为高级用户配置专属访问线路（可选）
5. **定期备份**：定期备份数据库和配置文件
6. **监控告警**：定期检查服务器状态和用户分布

---

## 🆘 获取帮助

- 问题反馈：[GitHub Issues](https://github.com/OmniHelm/Emby-bot/issues)
- 技术文档：查看 `docs/` 目录

---

**更新时间**：2024-11-24
**适用版本**：v2.0.0+
**配置方式**：手动指定服务器（内容分类管理）
