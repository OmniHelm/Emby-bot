#!/usr/bin/env python3
"""
【已废弃】多服务器数据迁移脚本（旧方案）

本脚本基于“向 emby 表添加 server_id 列”的旧设计，已不再适用。
新版本已采用绑定表 emby_server_bindings 表达“用户-服务器”关系。

请改用新的绑定迁移脚本：
    python3 scripts/migrate_bindings.py --server-id main
或（如历史上 emby 表存在 server_id 列）：
    python3 scripts/migrate_bindings.py --use-emby-server-id
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from datetime import datetime

from bot import config
from bot.sql_helper import Session, engine
from bot.sql_helper.sql_emby import Emby
from sqlalchemy import text, func


def backup_database():
    """备份数据库（提示用户手动备份）"""
    logger.info("=" * 60)
    logger.warning("⚠️  请确保已手动备份数据库！")
    logger.warning("建议执行: mysqldump -u root -p embybot > backup_$(date +%Y%m%d).sql")
    logger.info("=" * 60)

    response = input("\n已完成数据库备份？(y/n): ").strip().lower()
    if response != 'y':
        logger.error("❌ 用户取消迁移，请先完成数据库备份")
        return False

    return True


def check_server_id_column():
    """检查 server_id 列是否存在"""
    logger.info("检查数据库表结构...")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE emby"))
            columns = [row[0] for row in result]

            if 'server_id' in columns:
                logger.info("✅ server_id 列已存在")
                return True
            else:
                logger.warning("❌ server_id 列不存在，需要先执行 SQL 迁移")
                return False

    except Exception as e:
        logger.error(f"检查表结构失败: {e}")
        return False


def add_server_id_column():
    """添加 server_id 列"""
    logger.info("添加 server_id 列...")

    try:
        with engine.connect() as conn:
            # 添加 server_id 列
            conn.execute(text("""
                ALTER TABLE emby
                ADD COLUMN server_id VARCHAR(50) NOT NULL DEFAULT 'main'
                COMMENT '关联的 Emby 服务器 ID'
                AFTER tg
            """))
            conn.commit()
            logger.info("✅ server_id 列添加成功")

            # 创建索引
            try:
                conn.execute(text("CREATE INDEX idx_server_id ON emby(server_id)"))
                conn.commit()
                logger.info("✅ 索引 idx_server_id 创建成功")
            except Exception:
                logger.warning("⚠️  索引 idx_server_id 可能已存在，跳过")

            try:
                conn.execute(text("CREATE INDEX idx_server_embyid ON emby(server_id, embyid)"))
                conn.commit()
                logger.info("✅ 索引 idx_server_embyid 创建成功")
            except Exception:
                logger.warning("⚠️  索引 idx_server_embyid 可能已存在，跳过")

            try:
                conn.execute(text("CREATE INDEX idx_server_lv ON emby(server_id, lv)"))
                conn.commit()
                logger.info("✅ 索引 idx_server_lv 创建成功")
            except Exception:
                logger.warning("⚠️  索引 idx_server_lv 可能已存在，跳过")

            try:
                conn.execute(text("CREATE INDEX idx_server_ex ON emby(server_id, ex)"))
                conn.commit()
                logger.info("✅ 索引 idx_server_ex 创建成功")
            except Exception:
                logger.warning("⚠️  索引 idx_server_ex 可能已存在，跳过")

            return True

    except Exception as e:
        if "Duplicate column name" in str(e):
            logger.info("✅ server_id 列已存在，跳过添加")
            return True
        logger.error(f"添加 server_id 列失败: {e}")
        return False


def migrate_existing_users(target_server_id: str = None):
    """
    将现有用户迁移到指定服务器
    """
    logger.info("开始迁移用户数据...")

    # 确定目标服务器
    if target_server_id is None:
        enabled_servers = config.get_enabled_servers()
        if not enabled_servers:
            logger.error("❌ 未找到可用的服务器配置，终止迁移")
            return False
        target_server_id = enabled_servers[0].id

    target_server = config.get_server_by_id(target_server_id)
    if not target_server:
        logger.error(f"❌ 目标服务器不存在或未启用: {target_server_id}")
        return False

    logger.info(f"目标服务器: {target_server.name} ({target_server.id})")

    with Session() as session:
        try:
            # 查询所有 server_id 为空或默认值 'main' 的用户
            users = session.query(Emby).filter(
                (Emby.server_id == None) |
                (Emby.server_id == '') |
                (Emby.server_id == 'main')
            ).all()

            if not users:
                logger.info("✅ 没有需要迁移的用户")
                return True

            logger.info(f"找到 {len(users)} 个需要迁移的用户")

            # 批量更新
            migrated_count = 0
            failed_count = 0

            for user in users:
                try:
                    user.server_id = target_server.id
                    session.add(user)
                    migrated_count += 1

                    if migrated_count % 100 == 0:
                        session.commit()
                        logger.info(f"已迁移 {migrated_count} 个用户...")

                except Exception as e:
                    logger.error(f"迁移用户失败 tg={user.tg}: {e}")
                    failed_count += 1

            # 提交剩余的
            session.commit()

            logger.success(
                f"用户迁移完成: "
                f"成功 {migrated_count} 个，失败 {failed_count} 个"
            )

            return failed_count == 0

        except Exception as e:
            session.rollback()
            logger.error(f"迁移过程失败: {e}")
            return False


def verify_migration():
    """验证迁移结果"""
    logger.info("验证迁移结果...")

    with Session() as session:
        try:
            # 统计各服务器的用户数
            stats = session.query(
                Emby.server_id,
                func.count(Emby.tg)
            ).group_by(Emby.server_id).all()

            logger.info("服务器用户分布:")
            for server_id, count in stats:
                server_name = "未知"
                server_config = config.get_server_by_id(server_id) if server_id else None
                if server_config:
                    server_name = server_config.name
                logger.info(f"  {server_id} ({server_name}): {count} 个用户")

            # 检查是否有空 server_id
            null_count = session.query(Emby).filter(
                (Emby.server_id == None) | (Emby.server_id == '')
            ).count()

            if null_count > 0:
                logger.warning(f"⚠️  仍有 {null_count} 个用户的 server_id 为空")
                return False
            else:
                logger.success("✅ 所有用户都已分配 server_id")
                return True

        except Exception as e:
            logger.error(f"验证失败: {e}")
            return False


def check_emby2_table():
    """检查 emby2 表是否需要迁移"""
    logger.info("检查 emby2 表...")

    try:
        with engine.connect() as conn:
            # 检查 emby2 表是否存在
            result = conn.execute(text("SHOW TABLES LIKE 'emby2'"))
            if not result.fetchone():
                logger.info("emby2 表不存在，跳过")
                return True

            # 检查是否有 server_id 列
            result = conn.execute(text("DESCRIBE emby2"))
            columns = [row[0] for row in result]

            if 'server_id' not in columns:
                logger.info("为 emby2 表添加 server_id 列...")
                conn.execute(text("""
                    ALTER TABLE emby2
                    ADD COLUMN server_id VARCHAR(50) NOT NULL DEFAULT 'main'
                    COMMENT '关联的 Emby 服务器 ID'
                    AFTER tg
                """))
                conn.commit()
                logger.info("✅ emby2 表 server_id 列添加成功")
            else:
                logger.info("✅ emby2 表已有 server_id 列")

            return True

    except Exception as e:
        if "Duplicate column name" in str(e):
            return True
        logger.error(f"检查 emby2 表失败: {e}")
        return False


def check_favorites_table():
    """检查 favorites 表是否需要迁移"""
    logger.info("检查 favorites 表...")

    try:
        with engine.connect() as conn:
            # 检查 favorites 表是否存在
            result = conn.execute(text("SHOW TABLES LIKE 'favorites'"))
            if not result.fetchone():
                logger.info("favorites 表不存在，跳过")
                return True

            # 检查是否有 server_id 列
            result = conn.execute(text("DESCRIBE favorites"))
            columns = [row[0] for row in result]

            if 'server_id' not in columns:
                logger.info("为 favorites 表添加 server_id 列...")
                conn.execute(text("""
                    ALTER TABLE favorites
                    ADD COLUMN server_id VARCHAR(50) NOT NULL DEFAULT 'main'
                    COMMENT '关联的 Emby 服务器 ID'
                """))
                conn.commit()
                logger.info("✅ favorites 表 server_id 列添加成功")
            else:
                logger.info("✅ favorites 表已有 server_id 列")

            return True

    except Exception as e:
        if "Duplicate column name" in str(e):
            return True
        logger.error(f"检查 favorites 表失败: {e}")
        return False


def main():
    """主函数"""
    logger.error("=" * 60)
    logger.error("⚠️  本迁移脚本已废弃：不再向 emby 表添加 server_id 字段")
    logger.error("➡️  请使用新的绑定迁移脚本：scripts/migrate_bindings.py")
    logger.error("   示例：python3 scripts/migrate_bindings.py --server-id main")
    logger.error("=" * 60)
    return 1

    # 以下为旧逻辑，已不再执行
    logger.info("=" * 60)
    logger.info("EmbyBot 多服务器数据迁移工具")
    logger.info("=" * 60)

    # 步骤0: 确认备份
    logger.info("\n步骤 0/6: 确认数据备份")
    if not backup_database():
        return 1

    # 步骤1: 检查配置
    logger.info("\n步骤 1/6: 检查配置")
    enabled_servers = config.get_enabled_servers()
    if not enabled_servers:
        logger.error("❌ 配置文件中没有启用的服务器，请先配置 emby_servers")
        return 1
    logger.info(f"✅ 找到 {len(enabled_servers)} 个启用的服务器: {[s.id for s in enabled_servers]}")

    # 步骤2: 检查/添加 server_id 列
    logger.info("\n步骤 2/6: 检查数据库表结构")
    if not check_server_id_column():
        logger.info("尝试添加 server_id 列...")
        if not add_server_id_column():
            logger.error("❌ 添加 server_id 列失败，终止迁移")
            return 1

    # 步骤3: 检查其他表
    logger.info("\n步骤 3/6: 检查关联表")
    check_emby2_table()
    check_favorites_table()

    # 步骤4: 选择目标服务器
    logger.info("\n步骤 4/6: 选择目标服务器")
    print("\n可用的服务器列表:")
    for i, server in enumerate(enabled_servers):
        print(f"  [{i}] {server.name} (ID: {server.id})")

    try:
        choice = input(f"\n请选择目标服务器编号 [默认: 0]: ").strip()
        if choice == '':
            choice = 0
        else:
            choice = int(choice)

        if choice < 0 or choice >= len(enabled_servers):
            logger.error("❌ 无效的选择")
            return 1

        target_server_id = enabled_servers[choice].id
        logger.info(f"选择目标服务器: {enabled_servers[choice].name} ({target_server_id})")

    except ValueError:
        logger.error("❌ 无效的输入")
        return 1

    # 步骤5: 迁移用户数据
    logger.info("\n步骤 5/6: 迁移用户数据")
    if not migrate_existing_users(target_server_id):
        logger.error("❌ 用户数据迁移失败")
        return 1

    # 步骤6: 验证迁移结果
    logger.info("\n步骤 6/6: 验证迁移结果")
    if not verify_migration():
        logger.error("❌ 迁移验证失败")
        return 1

    logger.success("\n" + "=" * 60)
    logger.success("✅ 数据迁移完成！")
    logger.success("=" * 60)
    logger.info("\n下一步:")
    logger.info("1. 重启 Bot 服务: python3 main.py")
    logger.info("2. 测试核心功能: /kk, /myinfo 等")
    logger.info("3. 查看日志确认无错误")

    return 0


if __name__ == '__main__':
    sys.exit(main())
