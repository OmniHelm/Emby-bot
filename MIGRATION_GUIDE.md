# 迁移指南 (Migration Guide)

## 📋 适用场景

如果你正在从旧版本（重构前）迁移到新版本（重构后），请按照本指南操作。

---

## ⚠️ 重要提示

✅ **数据库完全兼容** - 无需任何数据库迁移操作  
✅ **功能完全兼容** - 所有功能保持不变  
⚠️ **配置文件需要更新** - 必须修改配置文件字段名

---

## 🚀 迁移步骤

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

#### Docker 模式
```bash
cd /path/to/EmbyBot
docker-compose down
```

#### Systemd 模式
```bash
sudo systemctl stop embyboss
# 或
sudo systemctl stop embybot
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

### 步骤 5: 更新 Docker 配置（仅 Docker 模式）

**修改 `docker-compose.yml`**:

容器服务名已从 `embyboss` 改为 `embybot`：

```yaml
# 修改前
services:
  embyboss:
    container_name: embyboss

# 修改后
services:
  embybot:
    container_name: embybot
```

**如果使用自定义的 docker-compose.yml**，请更新服务名。

### 步骤 6: 启动新服务

#### Docker 模式
```bash
# 拉取新镜像
docker pull ghcr.io/omnihelm/emby-bot:latest

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f embybot
```

#### Systemd 模式

**如果 service 文件名改变了**：

```bash
# 1. 停止旧服务
sudo systemctl stop embyboss

# 2. 禁用旧服务
sudo systemctl disable embyboss

# 3. 重命名或创建新服务文件
sudo mv /etc/systemd/system/embyboss.service /etc/systemd/system/embybot.service

# 4. 编辑服务文件（如果路径改变）
sudo vi /etc/systemd/system/embybot.service
# 更新 WorkingDirectory 和 ExecStart 路径

# 5. 重新加载 systemd
sudo systemctl daemon-reload

# 6. 启动新服务
sudo systemctl start embybot
sudo systemctl enable embybot

# 7. 查看状态
sudo systemctl status embybot
```

### 步骤 7: 验证运行

```bash
# 1. 检查服务状态
docker-compose ps  # Docker 模式
# 或
sudo systemctl status embybot  # Systemd 模式

# 2. 查看日志
docker-compose logs -f embybot  # Docker 模式
# 或
journalctl -u embybot -f  # Systemd 模式

# 3. 测试 Bot 功能
# 在 Telegram 中发送 /start 命令测试
```

---

## 🔍 常见问题

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
# Docker 模式
docker exec -it mysql mysql -u root -p -e "USE embyboss; SELECT COUNT(*) FROM emby;"

# 直接模式
mysql -u root -p -e "USE embyboss; SELECT COUNT(*) FROM emby;"
```

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

### Q5: Systemd 服务找不到

**现象**:
```
Unit embyboss.service not found
```

**解决**:
```bash
# 查找实际的服务文件位置
sudo find /etc/systemd -name "*emby*"

# 如果服务文件名是 embybot.service
sudo systemctl status embybot
```

---

## 📊 迁移验证清单

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

## 🆘 回滚方案

如果迁移遇到问题需要回滚：

```bash
# 1. 停止新服务
docker-compose down  # 或 systemctl stop embybot

# 2. 恢复旧配置
cp config.json.backup config.json

# 3. 恢复旧代码（如果有备份）
# ... 根据你的备份方式恢复

# 4. 重启旧服务
docker-compose up -d  # 或 systemctl start embyboss
```

---

## 📞 需要帮助？

如果遇到问题：

1. 查看日志：`docker-compose logs -f` 或 `journalctl -u embybot -f`
2. 检查配置：确保 `config.json` 字段名正确
3. 提交 Issue：https://github.com/OmniHelm/Emby-bot/issues

---

**祝迁移顺利！** 🎉
