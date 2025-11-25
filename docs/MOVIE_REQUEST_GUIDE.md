# 求片功能使用指南

## 功能概述

新增的求片功能允许用户通过 TMDB 链接提交影片求片请求。系统会自动检查 Emby 库中是否已存在该影片，如果不存在则记录请求并通知管理员。

## 用户使用流程

### 1. 进入点播中心

在群组中发送命令或点击相应按钮进入点播中心，你会看到一个新的选项：

```
🍿 点播    📶 下载进度
📎 链接求片
🔙 返回
```

### 2. 点击"📎 链接求片"

点击后，Bot 会提示你发送 TMDB 链接：

```
📎 通过 TMDB 链接求片

请在120s内发送 TMDB 链接（电影或剧集）
例如: https://www.themoviedb.org/movie/12345

退出点 /cancel
```

### 3. 发送 TMDB 链接

#### 支持的链接格式：

- **电影**: `https://www.themoviedb.org/movie/12345-inception`
- **剧集**: `https://www.themoviedb.org/tv/67890-breaking-bad`
- 也支持不带标题的短链接: `https://www.themoviedb.org/movie/12345`

#### 如何获取 TMDB 链接？

1. 访问 [The Movie Database (TMDB)](https://www.themoviedb.org/)
2. 搜索你想要的电影或剧集
3. 在详情页复制浏览器地址栏中的链接

### 4. 系统自动检查

发送链接后，系统会：

1. ✅ **解析链接** - 提取 TMDB ID 和媒体类型
2. 🔍 **查询 Emby 库** - 检查是否已存在该影片

#### 情况 A：Emby 库中已存在

```
✅ Emby 库中已存在相关资源:

• Inception (2010)
• Inception: The Cobol Job (2010)

您求的《Inception》可能已经在库中了！
```

#### 情况 B：Emby 库中不存在

```
✅ 求片已提交

片名: Inception
类型: 电影
TMDB ID: 27205

管理员收到通知后会尽快处理，请耐心等待！
```

同时，管理员会收到通知：

```
📢 新求片请求

用户: 张三 (123456789)
片名: Inception
类型: 电影
TMDB ID: 27205
链接: https://www.themoviedb.org/movie/27205-inception

Emby 库查询: ❌ 未找到
```

## 管理员功能

### 1. 查看求片列表

**命令**: `/viewrequests`

显示所有待处理的求片请求（支持分页）：

```
📋 求片记录（第 1 页）

📊 统计: 总计 15 | 待处理 8 | 已完成 7

1. 《Inception》
   类型: 电影 | TMDB ID: 27205
   用户: 张三 (123456789)
   状态: pending
   时间: 2025-01-15 10:30
   链接: https://www.themoviedb.org/movie/27205-inception

2. 《Breaking Bad》
   类型: 剧集 | TMDB ID: 1396
   用户: 李四 (987654321)
   状态: pending
   时间: 2025-01-15 09:15
   链接: https://www.themoviedb.org/tv/1396-breaking-bad

...

💡 使用 /exportrequests 导出完整记录
```

**翻页操作**:
- ⬅️ 上一页
- ➡️ 下一页
- 🔄 刷新

### 2. 导出求片记录

**命令**: `/exportrequests`

导出所有求片记录为 CSV 文件，包含以下字段：

| 字段 | 说明 |
|------|------|
| 用户TG ID | 用户的 Telegram ID |
| 用户名 | Emby 用户名 |
| 片名 | 影片名称 |
| 类型 | 电影/剧集 |
| TMDB ID | TMDB 数据库 ID |
| 链接 | 原始 TMDB 链接 |
| 状态 | pending/completed/failed |
| 创建时间 | 求片提交时间 |
| 更新时间 | 最后更新时间 |

**用途**：
- 📊 统计分析用户需求
- 📝 制定采购计划
- 💾 数据备份

### 3. 更新求片状态

管理员添加影片到 Emby 库后，可以通过以下方式更新状态：

#### 方法 1：通过数据库（推荐）

```python
from bot.sql_helper.sql_request_record import sql_update_request_status

# 标记为已完成
sql_update_request_status(
    download_id='tmdb_movie_27205',
    download_state='completed'
)
```

#### 方法 2：直接修改数据库

```sql
UPDATE request_records
SET download_state = 'completed',
    update_at = NOW()
WHERE download_id = 'tmdb_movie_27205';
```

## 配置说明

### 可选配置项

在 `config.json` 中的 `moviepilot` 部分添加：

```json
{
  "moviepilot": {
    "status": true,
    "url": "http://moviepilot.example.com",
    "username": "admin",
    "password": "password",
    "download_log_chatid": -100123456789,
    "movie_request_chatid": -100987654321  // 新增：求片通知群组ID
  }
}
```

#### 配置项说明：

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `movie_request_chatid` | 否 | 求片通知发送的群组 ID。如果不配置，则使用第一个授权群组 (`group[0]`) |

### 获取群组 ID

1. 将 Bot 添加到目标群组
2. 在群组中发送任意消息
3. 使用 Bot API 或相关工具获取 `chat_id`（通常是负数，如 `-100123456789`）

## 数据库说明

### 存储方式

求片记录存储在 `request_records` 表中，通过 `download_id` 前缀 `tmdb_` 区分：

- **点播记录**: `download_id` 不以 `tmdb_` 开头
- **求片记录**: `download_id` 格式为 `tmdb_{媒体类型}_{TMDB_ID}`

示例：
- `tmdb_movie_27205` - 电影《Inception》的求片记录
- `tmdb_tv_1396` - 剧集《Breaking Bad》的求片记录

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `download_id` | VARCHAR(255) | 主键，格式：`tmdb_{media_type}_{tmdb_id}` |
| `tg` | BIGINT | 用户的 Telegram ID |
| `request_name` | VARCHAR(255) | 影片名称 |
| `cost` | VARCHAR(255) | 消耗积分（求片为 "0"） |
| `detail` | TEXT | 详情，包含链接和类型 |
| `download_state` | VARCHAR(50) | 状态：pending/completed/failed |
| `create_at` | DATETIME | 创建时间 |
| `update_at` | DATETIME | 更新时间 |

## 常见问题

### Q1: 链接解析失败怎么办？

**A**: 确保链接格式正确：
- ✅ `https://www.themoviedb.org/movie/12345`
- ✅ `https://www.themoviedb.org/tv/67890-series-name`
- ❌ `https://themoviedb.org/movie/12345` (缺少 www)
- ❌ `www.themoviedb.org/movie/12345` (缺少协议)

### Q2: 为什么 Emby 库中明明有，却提示未找到？

**A**: 可能的原因：
1. **片名不匹配** - TMDB 链接中的片名与 Emby 中的不一致
2. **搜索算法** - 当前使用模糊搜索，可能无法精确匹配所有情况
3. **解决方法** - 手动在 Emby 中搜索确认，或联系管理员

### Q3: 求片后多久能添加到库中？

**A**: 取决于：
1. 管理员的处理速度
2. 资源的可用性
3. 服务器的存储空间

建议耐心等待，管理员会尽快处理。

### Q4: 可以求 Emby 库中已有的影片吗？

**A**: 可以，但系统会提示"Emby 库中已存在相关资源"。如果你确认库中确实没有，可能是检索问题，请联系管理员。

### Q5: 求片记录可以删除吗？

**A**: 目前不支持用户自行删除，如需删除请联系管理员。

管理员可通过以下方式删除：

```sql
DELETE FROM request_records WHERE download_id = 'tmdb_movie_27205';
```

## 技术细节

### 工作流程

```
用户点击"链接求片"
    ↓
发送 TMDB 链接
    ↓
系统解析链接 (tmdb_utils.py)
    ↓
查询 Emby 库 (emby.get_movies)
    ↓
是否存在？
    ├─ 存在 → 提示用户并结束
    └─ 不存在 → 记录到数据库 (request_records)
              ↓
          通知管理员群组
              ↓
          回复用户成功提示
```

### 核心文件

| 文件路径 | 功能 |
|---------|------|
| `bot/func_helper/tmdb_utils.py` | TMDB 链接解析工具 |
| `bot/sql_helper/sql_request_record.py` | 数据库操作函数 |
| `bot/modules/panel/request_movie_panel.py` | 用户端求片功能 |
| `bot/modules/commands/movie_request.py` | 管理员端查看/导出功能 |
| `bot/schemas/schemas.py` | 配置模型 |

### 依赖项

无需额外安装依赖，使用项目现有的：
- `pyrogram` - Telegram Bot 框架
- `sqlalchemy` - 数据库 ORM
- `csv` - CSV 文件生成（Python 标准库）

## 更新日志

### v1.0.0 (2025-01-22)

#### 新增功能
- ✅ 用户可通过 TMDB 链接求片
- ✅ 自动查询 Emby 库并提示是否已存在
- ✅ 管理员查看待处理求片列表（支持分页）
- ✅ 管理员导出求片记录为 CSV
- ✅ 求片通知发送到指定群组

#### 技术实现
- 新增 `tmdb_utils.py` 工具模块
- 扩展 `request_records` 数据库表
- 新增配置项 `movie_request_chatid`
- 支持电影和剧集两种媒体类型

## 反馈与建议

如果你在使用过程中遇到问题或有改进建议，请：

1. 联系管理员
2. 提交 Issue 到项目仓库
3. 在群组中反馈

感谢使用！
