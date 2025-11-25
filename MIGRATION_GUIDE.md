# 迁移指南 (Migration Guide)

## 适用场景

如果你正在从旧版本（重构前）迁移到新版本（重构后），请按照本指南操作。

---

## 重要提示

✅ **数据库数据完全兼容** - 数据表结构和数据无需任何修改
✅ **功能完全兼容** - 所有功能保持不变
⚠️ **配置文件需要更新** - 必须修改配置文件字段名
⚠️ **数据库名称已变更** - 默认从 `embyboss` 改为 `embybot`（见下方说明）

---

## 迁移步骤

### 步骤 1: 备份现有配置和数据

```bash
# 1. 备份配置文件
cp config.json config.json.backup

# 2. 备份数据库（如果使用 Docker）
docker exec mysql mysqldump -u root -p embyboss > backup_$(date +%Y%m%d).sql

# 3. 备份整个项目（可选）
tar -czf embybot_backup_$(date +%Y%m%d).tar.gz /path/to/EmbyBot
```

### 步骤 2: 停止旧服务

```bash
cd /path/to/EmbyBot
docker-compose down
```

### 步骤 3: 更新配置文件

**必须修改 `config.json` 中的以下字段：**

```json
{
  // 修改前
  "money": "樱花币",
  "ranks": {
    "logo": "SAKURA"
  }

  // 修改后
  "credits_name": "积分",  // 字段名从 money 改为 credits_name
  "ranks": {
    "logo": "EmbyBot"     // 值从 SAKURA 改为 EmbyBot
  }
}
```

**快速修改命令**：
```bash
# 方法 1: 使用 sed 批量替换（谨慎使用，建议先备份）
sed -i 's/"money":/"credits_name":/g' config.json
sed -i 's/"SAKURA"/"EmbyBot"/g' config.json

# 方法 2: 手动编辑
vi config.json  # 或使用你喜欢的编辑器
```

### 步骤 4: 拉取新代码

```bash
cd /path/to/EmbyBot

# 如果是 git 仓库
git pull origin master

# 如果是全新克隆
cd ..
rm -rf EmbyBot_old
git clone https://github.com/OmniHelm/Emby-bot.git EmbyBot
cd EmbyBot
# 复制回配置文件
cp ../config.json.backup config.json
# 记得修改配置文件字段（见步骤 3）
```

### 步骤 5: 更新 Docker 配置

**修改 `docker-compose.yml`**:

容器服务名已从 `embyboss` 改为 `embybot`：

```yaml
# 修改前
services:
  embyboss:
    container_name: embyboss
    environment:
      MYSQL_DATABASE: embyboss

# 修改后
services:
  embybot:
    container_name: embybot
    environment:
      MYSQL_DATABASE: embybot  # 数据库名也改了
```

**⚠️ 重要：数据库名称变更处理**

新版本默认数据库名从 `embyboss` 改为 `embybot`。你有两个选择：

**方案 A：保持使用旧数据库名（推荐，无需迁移数据）**
```bash
# 在 config.json 中配置旧数据库名
{
  "db_name": "embyboss"  # 继续使用旧数据库名
}
```

**方案 B：重命名数据库（彻底去叉）**
```bash
# 进入 MySQL 容器
docker exec -it mysql mysql -u root -p

# 重命名数据库
CREATE DATABASE embybot CHARACTER SET utf8mb4;
RENAME TABLE embyboss.emby TO embybot.emby;
RENAME TABLE embyboss.Rcode TO embybot.Rcode;
RENAME TABLE embyboss.favorites TO embybot.favorites;
RENAME TABLE embyboss.request_record TO embybot.request_record;
# ... 重命名所有表

# 删除旧数据库
DROP DATABASE embyboss;

# 更新 config.json
{
  "db_name": "embybot"
}
```

**如果使用自定义的 docker-compose.yml**，请更新服务名和数据库名。

### 步骤 6: 启动新服务

```bash
# 拉取新镜像
docker pull ghcr.io/omnihelm/emby-bot:latest

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f embybot
```

### 步骤 7: 验证运行

```bash
# 1. 检查服务状态
docker-compose ps

# 2. 查看日志
docker-compose logs -f embybot

# 3. 测试 Bot 功能
# 在 Telegram 中发送 /start 命令测试
```

---

## 常见问题

### Q1: 配置文件字段名错误会怎样？

**现象**: Bot 启动失败，提示配置加载错误

**解决**:
```bash
# 检查配置文件
python3 -c "import json; json.load(open('config.json'))"

# 如果报错，说明 JSON 格式有问题
# 如果不报错，检查字段名是否正确
grep -E "money|credits_name" config.json
```

### Q2: Docker 容器名冲突

**现象**:
```
Error: Conflict. The container name "/embyboss" is already in use
```

**解决**:
```bash
# 停止并删除旧容器
docker stop embyboss
docker rm embyboss

# 重新启动
docker-compose up -d
```

### Q3: 数据会丢失吗？

**答案**: 不会！

数据库数据完全兼容，只要数据库挂载路径正确，数据不会丢失。

验证数据库数据：
```bash
# Docker 模式（使用你实际的数据库名）
docker exec -it mysql mysql -u root -p -e "USE embyboss; SELECT COUNT(*) FROM emby;"
# 或如果改了数据库名
docker exec -it mysql mysql -u root -p -e "USE embybot; SELECT COUNT(*) FROM emby;"
```

**重要**：如果你保持使用旧数据库名 `embyboss`，确保 `config.json` 中 `db_name` 仍然是 `"embyboss"`。

### Q4: 旧版本和新版本可以共存吗？

**答案**: 可以，但不推荐

如果你想同时运行旧版本测试：
```bash
# 复制一份项目
cp -r EmbyBot EmbyBot_new

# 在新目录使用不同的容器名和端口
cd EmbyBot_new
# 修改 docker-compose.yml 中的容器名和端口
# 修改 config.json 中的配置
docker-compose up -d
```

---

## 迁移验证清单

完成迁移后，请检查以下项目：

- [ ] Bot 服务正常运行
- [ ] Telegram Bot 可以响应 `/start` 命令
- [ ] 用户数据完整（数据库记录数量正确）
- [ ] 配置文件字段正确（`credits_name` 而非 `money`）
- [ ] 日志输出正常
- [ ] 定时任务正常运行
- [ ] Web API 正常（如果启用）
- [ ] Docker 容器名正确（`embybot` 而非 `embyboss`）

---

## 回滚方案

如果迁移遇到问题需要回滚：

```bash
# 1. 停止新服务
docker-compose down

# 2. 恢复旧配置
cp config.json.backup config.json

# 3. 恢复旧代码（如果有备份）
# ... 根据你的备份方式恢复

# 4. 重启旧服务
docker-compose up -d
```

---

## 需要帮助？

如果遇到问题：

1. 查看日志：`docker-compose logs -f`
2. 检查配置：确保 `config.json` 字段名正确
3. 提交 Issue：https://github.com/OmniHelm/Emby-bot/issues
