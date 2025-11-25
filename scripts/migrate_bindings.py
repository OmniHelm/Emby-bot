#!/usr/bin/env python3
"""
将单服务器时代 emby 表中的用户生成到多服务器绑定表 emby_server_bindings。

使用方式：
  1) 指定统一服务器ID（推荐用于无 emby.server_id 列的数据库）
     python3 scripts/migrate_bindings.py --server-id main

  2) 如果历史上 emby 表存在 server_id 列（不推荐保留），可按该列自动分配：
     python3 scripts/migrate_bindings.py --use-emby-server-id

选项：
  --dry-run           仅统计将要写入的数量，不实际写库
  --server-id         目标服务器ID（默认读取 config 的第一个启用服务器）
  --use-emby-server-id  尝试从 emby 表的 server_id 列读取归属（如存在）
"""
import argparse
from typing import Optional
from loguru import logger

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from bot import config
from bot.sql_helper import Session, engine
from bot.sql_helper.sql_emby import Emby
from bot.sql_helper.sql_server_bindings import add_binding, get_binding, get_primary_binding


def detect_emby_server_id_column() -> bool:
    """检测 emby 表是否存在 server_id 列"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE emby"))
            cols = [row[0] for row in result]
            return "server_id" in cols
    except Exception as e:
        logger.error(f"检测 emby 表结构失败: {e}")
        return False


def choose_default_server_id(cli_server_id: Optional[str]) -> Optional[str]:
    """选择默认 server_id：优先 CLI -> 配置文件第一个启用服务器"""
    if cli_server_id:
        if config.get_server_by_id(cli_server_id):
            return cli_server_id
        logger.error(f"命令行指定的服务器无效：{cli_server_id}")
        return None
    enabled = config.get_enabled_servers()
    if not enabled:
        logger.error("配置中无启用的服务器")
        return None
    return enabled[0].id


def main():
    parser = argparse.ArgumentParser(description="迁移 emby 表用户到 emby_server_bindings")
    parser.add_argument("--server-id", type=str, default=None, help="统一目标服务器ID（默认取配置首个启用服务器）")
    parser.add_argument("--use-emby-server-id", action="store_true", help="如 emby 表存在 server_id 列，从该列读取服务器归属")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    args = parser.parse_args()

    # 选择 server_id 来源
    has_emby_server_col = detect_emby_server_id_column()
    if args.use_emby_server_id and not has_emby_server_col:
        logger.warning("指定了 --use-emby-server-id，但 emby 表不存在 server_id 列，回退为统一 server-id")
        args.use_ember_server_id = False  # noqa

    default_server_id = choose_default_server_id(args.server_id)
    if not default_server_id and not args.use_emby_server_id:
        return 1
    logger.info(f"默认 server_id: {default_server_id or '（按 emby.server_id 列）'}")

    total = added = skipped = failed = 0

    with Session() as session:
        try:
            users = session.query(Emby).filter(Emby.embyid.isnot(None)).all()
        except Exception as e:
            logger.error(f"读取用户失败: {e}")
            return 1

        logger.info(f"待处理用户数：{len(users)}")

        for u in users:
            total += 1
            # 计算 server_id
            target_sid = default_server_id
            if args.use_emby_server_id and has_emby_server_col:
                try:
                    target_sid = getattr(u, "server_id", None) or default_server_id
                except Exception:
                    target_sid = default_server_id

            if not target_sid or not config.get_server_by_id(target_sid):
                logger.warning(f"跳过（无效服务器）: tg={u.tg}, embyid={u.embyid}, server_id={target_sid}")
                skipped += 1
                continue

            # 已存在绑定则跳过
            try:
                if get_binding(u.tg, target_sid):
                    skipped += 1
                    continue
            except Exception as e:
                logger.warning(f"检查绑定失败 tg={u.tg}, server={target_sid}: {e}")

            if args.dry_run:
                added += 1
                continue

            try:
                # 若用户尚无主绑定，则将首条设置为主服务器
                is_primary = get_primary_binding(u.tg) is None
                if add_binding(u.tg, target_sid, u.embyid, is_primary=is_primary):
                    added += 1
                else:
                    failed += 1
            except IntegrityError:
                logger.debug(f"绑定已存在 tg={u.tg}, server={target_sid}")
                skipped += 1
            except Exception as e:
                logger.error(f"添加绑定失败 tg={u.tg}, server={target_sid}: {e}")
                failed += 1

    logger.success(f"迁移完成：total={total}, added={added}, skipped={skipped}, failed={failed}")
    if args.dry_run:
        logger.info("（dry-run）未进行任何写入")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
