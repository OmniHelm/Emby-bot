# EmbyBot 多服务器改造实施清单

> 快速实施指南 - 方案A

## 📋 前期准备

### 1. 环境检查
```bash
# 检查 Python 版本
python3 --version  # 需要 3.9+

# 检查数据库连接
mysql -u root -p embybot -e "SELECT COUNT(*) FROM emby;"

# 检查当前用户数
mysql -u root -p embybot -e "SELECT COUNT(*) as total, lv, COUNT(*) as count FROM emby GROUP BY lv;"
```

### 2. 数据备份
```bash
# 备份数据库
mysqldump -u root -p embybot > backup_$(date +%Y%m%d).sql

# 备份配置文件
cp config.json config.json.backup

# 备份代码（如果不是 Git 管理）
tar -czf embybot_backup_$(date +%Y%m%d).tar.gz .
```

---

## 🔧 实施步骤

### 阶段一：配置与数据库 (预计 2-3 小时)

#### ✅ 步骤 1: 更新配置文件
- [ ] 编辑 `config.json`
- [ ] 将单服务器配置转换为 `emby_servers` 数组
- [ ] 至少配置一个服务器，设置 `is_default: true`
- [ ] 验证 JSON 格式正确

**示例**:
```json
{
  "emby_servers": [
    {
      "id": "main",
      "name": "主服务器",
      "api_key": "你的API密钥",
      "url": "http://emby.example.com:8096",
      "line": "emby.example.com",
      "whitelist_line": null,
      "is_default": true,
      "max_users": 500,
      "priority": 1,
      "enabled": true
    }
  ]
}
```

#### ✅ 步骤 2: 更新配置模型
- [ ] 编辑 `bot/schemas/schemas.py`
- [ ] 添加 `EmbyServerConfig` 类
- [ ] 修改 `Config` 类，添加 `emby_servers` 字段
- [ ] 添加辅助方法: `get_default_server()`, `get_server_by_id()` 等

#### ✅ 步骤 3: 数据库表结构升级
```bash
# 创建迁移 SQL 文件
mkdir -p migrations
nano migrations/add_server_id.sql
```

**执行 SQL**:
```sql
-- 1. 添加 server_id 列
ALTER TABLE emby ADD COLUMN server_id VARCHAR(50) NOT NULL DEFAULT 'main' AFTER tg;

-- 2. 创建索引
CREATE INDEX idx_server_id ON emby(server_id);
CREATE INDEX idx_server_embyid ON emby(server_id, embyid);

-- 3. 验证
DESCRIBE emby;
SELECT COUNT(*), server_id FROM emby GROUP BY server_id;
```

```bash
# 执行迁移
mysql -u root -p embybot < migrations/add_server_id.sql
```

#### ✅ 步骤 4: 更新数据库模型
- [ ] 编辑 `bot/sql_helper/sql_emby.py`
- [ ] 在 `Emby` 类中添加 `server_id` 字段
- [ ] 添加联合索引定义
- [ ] 更新/添加查询函数（见完整文档）

---

### 阶段二：服务层改造 (预计 3-4 小时)

#### ✅ 步骤 5: 创建服务器管理器
```bash
# 创建新文件
nano bot/func_helper/emby_manager.py
```

- [ ] 实现 `EmbyServerManager` 类
- [ ] 实现 `register_server()` 方法
- [ ] 实现 `get_server()` 方法
- [ ] 创建全局单例 `emby_manager`

#### ✅ 步骤 6: 修改 Embyservice
- [ ] 编辑 `bot/func_helper/emby.py`
- [ ] 移除 `Embyservice` 的 `metaclass=Singleton`
- [ ] 删除全局实例 `emby = Embyservice(...)` 的创建

#### ✅ 步骤 7: 更新 Bot 初始化
- [ ] 编辑 `bot/__init__.py`
- [ ] 导入 `emby_manager` 替代 `emby`
- [ ] 初始化所有服务器: 遍历 `config.emby_servers` 并注册
- [ ] 更新 `__all__` 导出列表

**关键代码**:
```python
from bot.func_helper.emby_manager import emby_manager

# 初始化所有 Emby 服务器
for server_config in config.emby_servers:
    if server_config.enabled:
        emby_manager.register_server(server_config)
```

---

### 阶段三：业务层适配 (预计 4-6 小时)

#### ✅ 步骤 8: 创建辅助工具
```bash
nano bot/func_helper/emby_utils.py
```

- [ ] 实现 `get_user_emby_service(tg)` - 根据用户获取服务实例
- [ ] 实现 `get_emby_line(server_id, is_whitelist)` - 获取线路地址
- [ ] 实现 `select_available_server()` - 智能选择服务器
- [ ] 实现 `format_server_list_text()` - 格式化服务器列表

#### ✅ 步骤 9: 修改核心命令
需要修改的文件（按优先级）:

**P0 - 必须修改**:
- [ ] `bot/modules/panel/kk.py` - 用户信息查询
- [ ] `bot/modules/commands/user.py` - 用户创建/管理
- [ ] `bot/modules/commands/admin.py` - 管理员命令

**修改模式**:
```python
# 原代码
from bot.func_helper.emby import emby
result = await emby.user(emby_id=embyid)

# 新代码
from bot.func_helper.emby_utils import get_user_emby_service
emby_service, server_config, user = get_user_emby_service(tg)
if emby_service:
    result = await emby_service.user(emby_id=user.embyid)
```

**P1 - 建议修改**:
- [ ] `bot/modules/callback/*.py` - 回调处理器
- [ ] `bot/modules/extra/*.py` - 额外功能

#### ✅ 步骤 10: 修改定时任务
- [ ] `bot/scheduler/check_ex.py` - 到期检查
- [ ] `bot/scheduler/ranks_task.py` - 榜单生成
- [ ] `bot/scheduler/backup_db.py` - 数据库备份

**修改要点**: 遍历所有服务器，分别处理

---

### 阶段四：数据迁移 (预计 1 小时)

#### ✅ 步骤 11: 创建迁移脚本
```bash
mkdir -p scripts
nano scripts/migrate_to_multi_server.py
```

- [ ] 复制完整文档中的迁移脚本
- [ ] 赋予执行权限: `chmod +x scripts/migrate_to_multi_server.py`

#### ✅ 步骤 12: 执行数据迁移
```bash
# 停止服务
pkill -f main.py
# 或 docker-compose down

# 执行迁移
python3 scripts/migrate_to_multi_server.py

# 验证结果
mysql -u root -p embybot -e "
  SELECT server_id, COUNT(*) as user_count
  FROM emby
  GROUP BY server_id;
"
```

---

### 阶段五：测试验证 (预计 2-3 小时)

#### ✅ 步骤 13: 单元测试
```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 创建测试文件
mkdir -p tests
nano tests/test_multi_server.py

# 运行测试
pytest tests/test_multi_server.py -v
```

#### ✅ 步骤 14: 功能测试清单
- [ ] 配置加载正常
- [ ] 服务器注册成功
- [ ] 用户信息查询正常（`/kk`）
- [ ] 创建新用户成功
- [ ] 续期功能正常（`/renew`）
- [ ] 定时任务运行正常
- [ ] 日志输出正常

#### ✅ 步骤 15: 健康检查
```python
# 测试脚本
python3 -c "
import asyncio
from bot import emby_manager

async def test():
    results = await emby_manager.health_check()
    print('健康检查结果:', results)

asyncio.run(test())
"
```

---

### 阶段六：新增功能 (可选，预计 2-3 小时)

#### ✅ 步骤 16: 添加服务器管理命令
```bash
nano bot/modules/commands/servers.py
```

- [ ] 实现 `/servers` - 列出服务器
- [ ] 实现 `/serverinfo <id>` - 服务器详情
- [ ] 在 `bot/__init__.py` 注册命令

#### ✅ 步骤 17: 添加健康检查任务
```bash
nano bot/scheduler/health_check.py
```

- [ ] 实现 `health_check_task()`
- [ ] 在 `bot/func_helper/scheduler.py` 注册定时任务

---

## 🚀 部署上线

### 生产环境部署

```bash
# 1. 最终验证
python3 -c "from bot import config; print(f'服务器数: {len(config.emby_servers)}')"
python3 -c "from bot import emby_manager; print(f'已注册: {emby_manager.list_server_ids()}')"

# 2. 启动服务
python3 main.py

# 或使用 Docker
docker-compose up -d

# 3. 查看日志
tail -f logs/embybot.log

# 4. 监控运行状态
watch -n 5 'docker logs embybot --tail 20'
```

---

## ⚠️ 回滚方案

如果出现问题，执行以下步骤回滚：

```bash
# 1. 停止服务
pkill -f main.py

# 2. 恢复数据库
mysql -u root -p embybot < backup_YYYYMMDD.sql

# 3. 恢复配置
cp config.json.backup config.json

# 4. 回滚代码（如果使用 Git）
git checkout HEAD~1

# 5. 重启服务
python3 main.py
```

---

## 📊 验证清单

### 最终验证项目

#### 配置层
- [ ] `config.json` 格式正确
- [ ] 至少有一个默认服务器
- [ ] 所有服务器 ID 唯一

#### 数据库层
- [ ] `server_id` 字段存在
- [ ] 所有用户都有 `server_id`
- [ ] 索引创建成功

#### 服务层
- [ ] `emby_manager` 初始化成功
- [ ] 所有服务器已注册
- [ ] 健康检查通过

#### 业务层
- [ ] 核心命令正常工作
- [ ] 用户查询/创建正常
- [ ] 定时任务运行正常

#### 新功能
- [ ] `/servers` 命令可用
- [ ] 服务器统计正确
- [ ] 健康检查定时执行

---

## 📝 关键文件清单

### 需要修改的文件

```
✏️ 配置文件
├── config.json                          # 配置结构调整

✏️ 数据模型
├── bot/schemas/schemas.py               # 添加 EmbyServerConfig
├── bot/sql_helper/sql_emby.py           # 添加 server_id 字段

✏️ 服务层
├── bot/func_helper/emby.py              # 移除单例模式
├── bot/func_helper/emby_manager.py      # 新建: 服务器管理器
├── bot/func_helper/emby_utils.py        # 新建: 辅助工具
├── bot/__init__.py                      # 初始化 emby_manager

✏️ 业务层
├── bot/modules/panel/kk.py              # 修改用户查询逻辑
├── bot/modules/commands/*.py            # 修改命令处理器
├── bot/modules/callback/*.py            # 修改回调处理器

✏️ 定时任务
├── bot/scheduler/check_ex.py            # 支持多服务器
├── bot/scheduler/ranks_task.py          # 支持多服务器
├── bot/scheduler/health_check.py        # 新建: 健康检查

✏️ 脚本工具
├── scripts/migrate_to_multi_server.py   # 新建: 数据迁移
├── migrations/add_server_id.sql         # 新建: 表结构迁移
```

### 需要创建的文件

```
📁 docs/
├── multi-server-migration-plan.md       # 详细方案文档
└── multi-server-checklist.md            # 本清单

📁 migrations/
└── add_server_id.sql                    # 数据库迁移 SQL

📁 scripts/
├── migrate_to_multi_server.py           # 数据迁移脚本
└── test_integration.sh                  # 集成测试脚本

📁 tests/
└── test_multi_server.py                 # 单元测试
```

---

## 🔍 常见问题快速参考

| 问题 | 解决方案 |
|------|---------|
| 配置加载失败 | 检查 `config.json` 格式，验证 `emby_servers` 字段 |
| 服务器注册失败 | 检查 URL 和 API 密钥是否正确 |
| 用户查询失败 | 确认 `server_id` 字段存在且有值 |
| 定时任务报错 | 更新定时任务代码以支持多服务器 |
| 健康检查异常 | 检查网络连接和服务器状态 |

---

## 📞 支持与反馈

遇到问题？
1. 查看详细文档: `docs/multi-server-migration-plan.md`
2. 检查日志文件: `logs/embybot.log`
3. 运行诊断脚本: `python3 scripts/diagnose.py`

---

**实施清单版本**: v1.0
**最后更新**: 2025-11-24
