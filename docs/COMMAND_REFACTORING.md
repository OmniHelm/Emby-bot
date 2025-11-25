# 命令命名重构方案

## 重构状态

**已完成** - 2025-11-25

---

## 重构原则

1. **统一使用下划线分隔**：`action_target` 格式
2. **动词开头**：明确操作类型
3. **避免拼音**：使用英文命名
4. **避免过度缩写**：保持可读性
5. **功能组前缀统一**：相关命令使用相同前缀

---

## 命令分组前缀规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `user_` | 用户管理操作 | `user_info`, `user_create` |
| `check_` | 检查/检测操作 | `check_expiry`, `check_activity` |
| `purge_` | 清理/删除批量操作 | `purge_left`, `purge_orphan` |
| `audit_` | 审计操作 | `audit_ip`, `audit_device` |
| `admin_` | 管理员操作 | `admin_add`, `admin_remove` |
| `vip_` | 白名单操作 | `vip_add`, `vip_remove` |
| `emby_` | Emby 相关操作 | `emby_grant_admin` |
| `sync_` | 同步操作 | `sync_ids`, `sync_favorites` |
| `lib_` | 媒体库操作 | `lib_hide_all`, `lib_show_all` |
| `ranks_` | 榜单操作 | `ranks_daily`, `ranks_weekly` |
| `del_` | 删除操作 | `del_emby`, `del_record` |
| `coins_` | 币币操作 | `coins_all`, `coins_clear` |

---

## 文件重命名

| 原文件名 | 新文件名 | 位置 | 说明 |
|---------|---------|------|------|
| `kk.py` | `user_manage.py` | `bot/modules/panel/` | 用户管理面板 |
| `rmemby.py` | `user_remove.py` | `bot/modules/commands/` | 用户删除相关 |
| `pro_rev.py` | `permissions.py` | `bot/modules/commands/` | 权限管理 |
| `renewall.py` | `batch_operations.py` | `bot/modules/commands/` | 批量操作 |
| `create.py` | `user_query.py` | `bot/modules/extra/` | 非TG用户查询 |

---

## 命令重命名清单

### 用户管理命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/kk` | `/user` | 用户管理面板 | `bot/modules/panel/user_manage.py` |
| `/ucr` | `/user_create` | 创建非TG用户 | `bot/modules/extra/user_query.py` |
| `/urm` | `/user_delete` | 删除指定用户 | `bot/modules/extra/user_query.py` |
| `/uinfo` | `/user_info` | 查询用户信息 | `bot/modules/extra/user_query.py` |
| `/userip` | `/user_ip` | 查询用户IP | `bot/modules/extra/user_query.py` |
| `/udeviceid` | `/user_device` | 查询用户设备 | `bot/modules/extra/user_query.py` |
| `/rmemby` | `/user_remove` | 删除用户(含TG) | `bot/modules/commands/user_remove.py` |
| `/only_rm_emby` | `/del_emby` | 仅删Emby账户 | `bot/modules/commands/user_remove.py` |
| `/only_rm_record` | `/del_record` | 仅删数据库记录 | `bot/modules/commands/user_remove.py` |

### 白名单/管理员命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/prouser` | `/vip_add` | 添加白名单 | `bot/modules/commands/permissions.py` |
| `/revuser` | `/vip_remove` | 移除白名单 | `bot/modules/commands/permissions.py` |
| `/proadmin` | `/admin_add` | 添加管理员 | `bot/modules/commands/permissions.py` |
| `/revadmin` | `/admin_remove` | 移除管理员 | `bot/modules/commands/permissions.py` |
| `/embyadmin` | `/emby_grant_admin` | 授权Emby管理 | `bot/modules/commands/syncs.py` |

### 清理/同步命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/syncgroupm` | `/purge_left` | 清理已退群用户 | `bot/modules/commands/syncs.py` |
| `/syncunbound` | `/purge_orphan` | 清理孤立账户 | `bot/modules/commands/syncs.py` |
| `/deleted` | `/purge_dead` | 清理死号 | `bot/modules/commands/syncs.py` |
| `/kick_not_emby` | `/kick_nonemby` | 踢出无号用户 | `bot/modules/commands/syncs.py` |
| `/bindall_id` | `/sync_ids` | 同步EmbyID | `bot/modules/commands/syncs.py` |
| `/scan_embyname` | `/scan_duplicate` | 扫描重复记录 | `bot/modules/commands/syncs.py` |

### 检测命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/check_ex` | `/check_expiry` | 到期检测 | `bot/modules/panel/sched_panel.py` |
| `/low_activity` | `/check_activity` | 活跃检测 | `bot/modules/panel/sched_panel.py` |

### 榜单命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/uranks` | `/ranks_playtime` | 观影时长榜 | `bot/modules/panel/sched_panel.py` |
| `/days_ranks` | `/ranks_daily` | 日榜 | `bot/modules/panel/sched_panel.py` |
| `/week_ranks` | `/ranks_weekly` | 周榜 | `bot/modules/panel/sched_panel.py` |

### 批量操作命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/callall` | `/broadcast` | 群发消息 | `bot/modules/commands/batch_operations.py` |
| `/coinsclear` | `/coins_clear` | 清空币币 | `bot/modules/commands/batch_operations.py` |
| `/coinsall` | `/coins_all` | 批量发币 | `bot/modules/commands/batch_operations.py` |
| `/renewall` | `/renew_all` | 批量续期 | `bot/modules/commands/batch_operations.py` |

### 媒体库命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/embylibs_blockall` | `/lib_hide_all` | 隐藏所有媒体库 | `bot/modules/commands/emby_libs.py` |
| `/embylibs_unblockall` | `/lib_show_all` | 显示所有媒体库 | `bot/modules/commands/emby_libs.py` |
| `/extraembylibs_blockall` | `/lib_extra_hide` | 隐藏额外媒体库 | `bot/modules/commands/emby_libs.py` |
| `/extraembylibs_unblockall` | `/lib_extra_show` | 显示额外媒体库 | `bot/modules/commands/emby_libs.py` |

### 危险操作命令

| 旧命令 | 新命令 | 说明 | 文件位置 |
|--------|--------|------|----------|
| `/paolu` | `/nuke` | 跑路模式 | `bot/modules/commands/syncs.py` |
| `/banall` | `/ban_all` | 封禁所有 | `bot/modules/commands/syncs.py` |
| `/unbanall` | `/unban_all` | 解封所有 | `bot/modules/commands/syncs.py` |

### 保持不变的命令

以下命令命名良好，无需修改：

- `/start`, `/help`, `/faq`, `/guide`
- `/myinfo`, `/count`
- `/renew`, `/score`, `/coins`
- `/restart`, `/config`, `/update_bot`
- `/servers`, `/servercheck`
- `/auditip`, `/auditdevice`, `/auditclient`
- `/backup_db`, `/restore_from_db`
- `/sync_favorites`
- `/red`, `/srank`
- `/viewrequests`, `/exportrequests`
- `/white_channel`, `/rev_white_channel`, `/unban_channel`

---

## 修改位置汇总

### 命令定义文件

| 文件 | 修改命令数 |
|------|-----------|
| `bot/modules/panel/user_manage.py` | 1 |
| `bot/modules/extra/user_query.py` | 5 |
| `bot/modules/commands/user_remove.py` | 3 |
| `bot/modules/commands/permissions.py` | 4 |
| `bot/modules/commands/syncs.py` | 10 |
| `bot/modules/panel/sched_panel.py` | 5 |
| `bot/modules/commands/batch_operations.py` | 4 |
| `bot/modules/commands/emby_libs.py` | 4 |
| **总计** | **36** |

### 引用更新文件

| 文件 | 修改内容 |
|------|----------|
| `bot/__init__.py` | BotCommand 列表 |
| `bot/modules/panel/__init__.py` | 模块导入 |
| `bot/modules/commands/__init__.py` | 模块导入 |
| `bot/modules/extra/__init__.py` | 模块导入 |

---

## 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2025-11-25 | 1.0 | 初始方案制定 |
| 2025-11-25 | 2.0 | 完成所有命令重命名，移除旧命令别名 |
| 2025-11-25 | 2.1 | 完成文件重命名，更新模块引用 |

---

*文档版本: 2.1*
*最后更新: 2025-11-25*
