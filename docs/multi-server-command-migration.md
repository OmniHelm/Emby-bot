# 多服务器架构下的命令交互设计与修改需求

**文档版本**: v2.0
**创建日期**: 2024-11-24
**更新日期**: 2025-11-25
**状态**: ✅ 迁移完成

---

## 📋 目录

1. [核心问题](#核心问题)
2. [交互设计方案](#交互设计方案)
3. [命令分类与影响分析](#命令分类与影响分析)
4. [需要修改的命令清单](#需要修改的命令清单)
5. [实施建议](#实施建议)
6. [测试检查清单](#测试检查清单)

---

## 核心问题

### 问题描述

在多服务器架构下（动漫服、电影服、剧集服等），TG Bot 与用户的交互命令需要适配新的架构设计：

1. **用户创建命令** - 需要指定目标服务器
2. **用户查询命令** - 需要根据用户所属服务器查询
3. **用户管理命令** - 需要操作用户所属的特定服务器
4. **批量操作命令** - 需要跨服务器批量执行

### 设计原则

- ✅ **透明性**: 普通用户无需关心服务器细节，体验无缝
- ✅ **明确性**: 管理员创建用户时明确指定服务器
- ✅ **一致性**: 用户始终在同一服务器上操作
- ✅ **可扩展性**: 支持后续新增服务器

---

## 交互设计方案

### 方案 1：手动指定服务器（已采用）

**适用场景**: 内容分类管理（动漫服、电影服、剧集服）

**特点**:
- 管理员创建用户时手动指定服务器 ID
- 用户绑定到特定服务器，后续操作自动定位
- 用户无需知道服务器概念，透明体验

**示例**:
```bash
# 管理员命令（需指定服务器）
/ucr testuser 30 anime        # 在动漫服创建用户
/ucr moviefan 30 movie        # 在电影服创建用户

# 用户命令（无需指定服务器，自动定位）
/myinfo                       # 查看个人信息（自动获取所属服务器）
/start                        # 启动面板（自动获取所属服务器）
```

---

## 命令分类与影响分析

### 分类标准

根据命令的服务器依赖程度，分为以下几类：

| 分类 | 说明 | 需要修改 | 修改方式 |
|------|------|----------|----------|
| **A 类** | 直接操作 Emby 服务器的命令 | ✅ 是 | 使用 `get_user_emby_service()` 或 `get_server_by_id_or_none()` |
| **B 类** | 查询用户数据的命令 | ⚠️ 可能 | 确保正确处理 `server_id` 字段 |
| **C 类** | 批量操作命令 | ✅ 是 | 遍历所有服务器或指定服务器 |
| **D 类** | 不涉及 Emby 的命令 | ❌ 否 | 无需修改 |

---

## 需要修改的命令清单

### ✅ 已完成修改

| 命令 | 文件 | 状态 | 说明 |
|------|------|------|------|
| `/ucr` | `bot/modules/extra/create.py` | ✅ 已完成 | 创建用户时必须指定服务器 ID |
| `/kk` | `bot/modules/panel/kk.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/user_devices` | `bot/modules/commands/view_user.py` | ✅ 已完成 | 汇总所有服务器数据 |
| `/uinfo` | `bot/modules/extra/create.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/userip` | `bot/modules/extra/create.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/udeviceid` | `bot/modules/extra/create.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| 续期命令 | `bot/modules/commands/exchange.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/rmemby` | `bot/modules/commands/rmemby.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/only_rm_emby` | `bot/modules/commands/rmemby.py` | ✅ 已完成 | 遍历所有服务器查找并删除 |
| `/syncgroupm` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/syncunbound` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 遍历所有服务器 |
| `/bindall_id` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 遍历所有服务器 |
| `/embyadmin` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/restore_from_db` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/unbanall` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 遍历所有服务器 |
| `/banall` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 遍历所有服务器 |
| `/paolu` | `bot/modules/commands/syncs.py` | ✅ 已完成 | 遍历所有服务器 |
| `/auditip` | `bot/modules/commands/audit.py` | ✅ 已完成 | 聚合所有服务器审计结果 |
| `/auditdevice` | `bot/modules/commands/audit.py` | ✅ 已完成 | 聚合所有服务器审计结果 |
| `/auditclient` | `bot/modules/commands/audit.py` | ✅ 已完成 | 聚合所有服务器审计结果 |
| `/embylibs_blockall` | `bot/modules/commands/emby_libs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/embylibs_unblockall` | `bot/modules/commands/emby_libs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/extraembylibs_blockall` | `bot/modules/commands/emby_libs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| `/extraembylibs_unblockall` | `bot/modules/commands/emby_libs.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| 离群删除 | `bot/modules/callback/leave_delemby.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |
| 内联搜索 | `bot/modules/callback/on_inline_query.py` | ✅ 已完成 | 只搜索用户所属服务器 |
| 收藏功能 | `bot/modules/callback/on_inline_query.py` | ✅ 已完成 | 使用 `get_user_emby_service()` |

---

### ✅ 无需修改

以下命令不涉及 Emby 服务器操作，无需修改：

| 命令 | 文件 | 说明 |
|------|------|------|
| `/help` | `bot/modules/commands/help.py` | 帮助文档 |
| `/faq` | `bot/modules/commands/help.py` | 常见问题 |
| `/guide` | `bot/modules/commands/help.py` | 使用指南 |
| `/score` | `bot/modules/commands/score_coins.py` | 积分管理 |
| `/coins` | `bot/modules/commands/score_coins.py` | 货币管理 |
| `/proadmin` | `bot/modules/commands/pro_rev.py` | 提升管理员 |
| `/revadmin` | `bot/modules/commands/pro_rev.py` | 撤销管理员 |
| `/prouser` | `bot/modules/commands/pro_rev.py` | 提升白名单 |
| `/revuser` | `bot/modules/commands/pro_rev.py` | 撤销白名单 |
| `/renewall` | `bot/modules/commands/renewall.py` | 批量续期（只改数据库） |
| `/coinsall` | `bot/modules/commands/renewall.py` | 批量发币 |
| `/coinsclear` | `bot/modules/commands/renewall.py` | 清空积分 |
| `/callall` | `bot/modules/commands/renewall.py` | 群发消息 |
| `/viewrequests` | `bot/modules/commands/movie_request.py` | 查看求片 |
| `/exportrequests` | `bot/modules/commands/movie_request.py` | 导出求片 |
| `/config` | `bot/modules/panel/config_panel.py` | 配置面板 |
| 定时任务命令 | `bot/modules/panel/sched_panel.py` | 任务管理 |
| 反频道命令 | `bot/modules/extra/antichanel.py` | 频道管理 |
| 红包命令 | `bot/modules/extra/red_envelope.py` | 红包系统 |
| `/checkin` | `bot/modules/callback/checkin.py` | 签到（只涉及数据库） |

---

## 实施建议

### 修改优先级

**所有命令已完成多服务器适配！**

| 优先级 | 模块 | 状态 |
|--------|------|------|
| P0 - 核心功能 | 用户创建、续期、删除、离群删除 | ✅ 已完成 |
| P1 - 批量操作 | 群组同步、媒体库管理 | ✅ 已完成 |
| P2 - 查询功能 | 审计命令、内联查询 | ✅ 已完成 |

### 通用修改模式

#### 模式 1: 单用户操作
```python
# 根据用户 TG ID 获取对应服务
emby_service, server_config, user = get_user_emby_service(tg)
if not emby_service:
    return await sendMessage(msg, '❌ 无法连接到服务器')

# 执行操作
result = await emby_service.some_operation(user.embyid)
```

#### 模式 2: 批量用户操作
```python
# 按用户所属服务器分组操作
success_count = 0
fail_count = 0

for user in users:
    emby_service, server_config, _ = get_user_emby_service(user.tg)
    if not emby_service:
        LOGGER.warning(f"跳过用户 {user.tg}: 无法定位服务器")
        fail_count += 1
        continue

    try:
        result = await emby_service.some_operation(user.embyid)
        if result:
            success_count += 1
        else:
            fail_count += 1
    except Exception as e:
        LOGGER.error(f"操作失败: {e}")
        fail_count += 1

# 返回统计结果
```

#### 模式 3: 全服务器查询
```python
# 汇总所有服务器的结果
all_results = []

for server_id, emby_service in emby_manager.get_all_servers().items():
    try:
        success, result = await emby_service.query_something()
        if success and result:
            # 添加服务器标识
            for item in result:
                item['server_id'] = server_id
                item['server_name'] = config.get_server_by_id(server_id).name
            all_results.extend(result)
    except Exception as e:
        LOGGER.warning(f"查询服务器 {server_id} 失败: {e}")

# 返回汇总结果
```

---

## 测试检查清单

### 功能测试

- [ ] **用户创建**
  - [ ] 在不同服务器创建用户
  - [ ] 验证用户被正确分配到指定服务器
  - [ ] 验证 `server_id` 字段正确写入数据库

- [ ] **用户续期**
  - [ ] 测试已过期账户续期
  - [ ] 测试未过期账户续期
  - [ ] 验证操作正确的服务器

- [ ] **用户删除**
  - [ ] 通过 TG ID 删除
  - [ ] 通过 Emby 用户名删除
  - [ ] 验证只删除指定服务器的账户

- [ ] **批量操作**
  - [ ] 群组同步（多服务器用户）
  - [ ] 批量媒体库操作
  - [ ] 验证所有服务器都被正确处理

- [ ] **查询功能**
  - [ ] IP 审计（多服务器汇总）
  - [ ] 设备审计（多服务器汇总）
  - [ ] 客户端审计（多服务器汇总）
  - [ ] 内联搜索（多服务器汇总或指定服务器）

- [ ] **用户体验**
  - [ ] `/start` - 个人面板显示正确
  - [ ] `/myinfo` - 显示所属服务器信息
  - [ ] `/count` - 显示正确的服务器统计

### 边界测试

- [ ] 用户在数据库但 `server_id` 为空（fallback 到 'main'）
- [ ] 用户的 `server_id` 对应服务器不存在或未启用
- [ ] 服务器连接失败的错误处理
- [ ] 并发操作的数据一致性

### 性能测试

- [ ] 批量操作大量用户的性能
- [ ] 跨服务器查询的响应时间
- [ ] 多服务器同时操作的并发性能

---

## 附录

### 已完成修改的文件清单

```
bot/modules/commands/exchange.py          # ✅ P0 - 续期
bot/modules/commands/rmemby.py            # ✅ P0 - 删除用户
bot/modules/callback/leave_delemby.py     # ✅ P0 - 离群删除
bot/modules/commands/syncs.py             # ✅ P1 - 批量操作
bot/modules/commands/emby_libs.py         # ✅ P1 - 媒体库管理
bot/modules/commands/audit.py             # ✅ P2 - 审计
bot/modules/callback/on_inline_query.py   # ✅ P2 - 内联查询
```

### 导入语句参考

所有需要修改的文件应添加以下导入：

```python
from bot.func_helper.emby_utils import get_user_emby_service, get_server_by_id_or_none
from bot.func_helper.emby_manager import emby_manager
from bot import config, LOGGER
```

移除旧的导入（如果存在）：
```python
# 删除这些
from bot.func_helper.emby import emby
from bot import emby
```

---

**文档维护**: 本文档应随着代码修改进度更新，标记已完成的项目。

**相关文档**:
- [多服务器快速开始指南](./multi-server-quickstart.md)
- [迁移完成报告](./MIGRATION_COMPLETED.md)
- [技术方案](./multi-server-migration-plan.md)
