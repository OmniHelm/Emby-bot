#!/usr/bin/env python3
"""
多服务器配置测试脚本
验证配置加载、向后兼容和辅助方法
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_emby_server_config():
    """测试 EmbyServerConfig 类"""
    print("\n🧪 测试 EmbyServerConfig 类...")

    try:
        # 直接导入 schemas 模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "schemas",
            "bot/schemas/schemas.py"
        )
        schemas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schemas)

        EmbyServerConfig = schemas.EmbyServerConfig

        # 测试正常创建
        server = EmbyServerConfig(
            id="test_server",
            name="测试服务器",
            api_key="test_api_key",
            url="http://emby.example.com:8096",
            line="emby.example.com"
        )

        assert server.id == "test_server"
        assert server.url == "http://emby.example.com:8096"  # 不应该有尾部斜杠
        assert server.enabled == True  # 默认值

        print("✅ EmbyServerConfig 创建成功")

        # 测试 URL 验证
        try:
            invalid_server = EmbyServerConfig(
                id="test",
                name="测试",
                api_key="key",
                url="invalid_url",  # 无效 URL
                line="test"
            )
            print("❌ URL 验证失败 - 应该抛出异常")
            return False
        except ValueError as e:
            print(f"✅ URL 验证正常: {e}")

        # 测试 ID 验证
        try:
            invalid_id = EmbyServerConfig(
                id="test server!",  # 无效 ID（包含空格和特殊字符）
                name="测试",
                api_key="key",
                url="http://test.com",
                line="test"
            )
            print("❌ ID 验证失败 - 应该抛出异常")
            return False
        except ValueError as e:
            print(f"✅ ID 验证正常: {e}")

        return True

    except Exception as e:
        print(f"❌ EmbyServerConfig 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_legacy_config_conversion():
    """测试旧配置自动转换"""
    print("\n🧪 测试旧配置自动转换...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "schemas",
            "bot/schemas/schemas.py"
        )
        schemas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schemas)

        Config = schemas.Config
        Open = schemas.Open
        Ranks = schemas.Ranks
        Schedall = schemas.Schedall

        # 模拟旧配置数据
        legacy_data = {
            "bot_name": "TestBot",
            "bot_token": "test_token",
            "owner_api": 123456,
            "owner_hash": "test_hash",
            "owner": 123,
            "group": [456],
            "main_group": "test_group",
            "chanel": "test_channel",
            "bot_photo": "test.jpg",
            "open": {
                "stat": True,
                "all_user": 100,
                "checkin": True,
                "exchange": True,
                "whitelist": True,
                "invite": True
            },
            "credits_name": "积分",

            # 旧的单服务器配置
            "emby_api": "old_api_key",
            "emby_url": "http://old.server.com:8096",
            "emby_line": "old.server.com",
            "emby_whitelist_line": "vip.old.server.com",

            "db_host": "localhost",
            "db_user": "root",
            "db_pwd": "password",
            "db_name": "test",
            "ranks": {},
            "schedall": {}
        }

        # 创建配置对象（应该自动转换）
        config = Config(**legacy_data)

        # 验证是否正确转换
        assert config.emby_servers is not None, "emby_servers 应该被创建"
        assert len(config.emby_servers) == 1, "应该有 1 个服务器"

        server = config.emby_servers[0]
        assert server.id == "main", f"服务器 ID 应该是 'main'，但是 '{server.id}'"
        assert server.name == "主服务器"
        assert server.api_key == "old_api_key"
        assert server.url == "http://old.server.com:8096"
        assert server.line == "old.server.com"
        assert server.whitelist_line == "vip.old.server.com"
        assert server.enabled == True

        print("✅ 旧配置自动转换成功")
        print(f"   - 服务器 ID: {server.id}")
        print(f"   - 服务器名称: {server.name}")
        print(f"   - API Key: {server.api_key}")
        print(f"   - URL: {server.url}")

        return True

    except Exception as e:
        print(f"❌ 旧配置转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_new_multi_server_config():
    """测试新的多服务器配置"""
    print("\n🧪 测试新的多服务器配置...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "schemas",
            "bot/schemas/schemas.py"
        )
        schemas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schemas)

        Config = schemas.Config
        Open = schemas.Open
        Ranks = schemas.Ranks
        Schedall = schemas.Schedall

        # 新的多服务器配置
        multi_server_data = {
            "bot_name": "TestBot",
            "bot_token": "test_token",
            "owner_api": 123456,
            "owner_hash": "test_hash",
            "owner": 123,
            "group": [456],
            "main_group": "test_group",
            "chanel": "test_channel",
            "bot_photo": "test.jpg",
            "open": {
                "stat": True,
                "all_user": 100,
                "checkin": True,
                "exchange": True,
                "whitelist": True,
                "invite": True
            },
            "credits_name": "积分",

            # 新的多服务器配置（内容分类）
            "emby_servers": [
                {
                    "id": "anime",
                    "name": "动漫服务器",
                    "api_key": "anime_api_key",
                    "url": "http://anime.server.com:8096",
                    "line": "anime.server.com",
                    "whitelist_line": "vip.anime.server.com",
                    "enabled": True
                },
                {
                    "id": "movie",
                    "name": "电影服务器",
                    "api_key": "movie_api_key",
                    "url": "http://movie.server.com:8096",
                    "line": "movie.server.com",
                    "enabled": True
                },
                {
                    "id": "series",
                    "name": "剧集服务器",
                    "api_key": "series_api_key",
                    "url": "http://series.server.com:8096",
                    "line": "series.server.com",
                    "enabled": True
                }
            ],

            "db_host": "localhost",
            "db_user": "root",
            "db_pwd": "password",
            "db_name": "test",
            "ranks": {},
            "schedall": {}
        }

        # 创建配置对象
        config = Config(**multi_server_data)

        # 验证多服务器配置
        assert config.emby_servers is not None
        assert len(config.emby_servers) == 3, f"应该有 3 个服务器，但有 {len(config.emby_servers)}"

        # 测试辅助方法
        server_by_id = config.get_server_by_id("anime")
        assert server_by_id is not None
        assert server_by_id.name == "动漫服务器"

        movie_server = config.get_server_by_id("movie")
        assert movie_server is not None
        assert movie_server.name == "电影服务器"

        enabled_servers = config.get_enabled_servers()
        assert len(enabled_servers) == 3

        server_ids = config.list_server_ids()
        assert "anime" in server_ids
        assert "movie" in server_ids
        assert "series" in server_ids

        print("✅ 多服务器配置测试通过")
        print(f"   - 服务器数量: {len(config.emby_servers)}")
        print(f"   - 服务器列表: {', '.join([s.name for s in enabled_servers])}")
        print(f"   - 服务器 ID: {server_ids}")

        return True

    except Exception as e:
        print(f"❌ 多服务器配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_rules():
    """测试验证规则"""
    print("\n🧪 测试验证规则...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "schemas",
            "bot/schemas/schemas.py"
        )
        schemas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schemas)

        Config = schemas.Config
        Open = schemas.Open
        Ranks = schemas.Ranks
        Schedall = schemas.Schedall

        base_data = {
            "bot_name": "TestBot",
            "bot_token": "test_token",
            "owner_api": 123456,
            "owner_hash": "test_hash",
            "owner": 123,
            "group": [456],
            "main_group": "test_group",
            "chanel": "test_channel",
            "bot_photo": "test.jpg",
            "open": {
                "stat": True,
                "all_user": 100,
                "checkin": True,
                "exchange": True,
                "whitelist": True,
                "invite": True
            },
            "credits_name": "积分",
            "db_host": "localhost",
            "db_user": "root",
            "db_pwd": "password",
            "db_name": "test",
            "ranks": {},
            "schedall": {}
        }

        # 测试：没有配置任何服务器
        try:
            invalid_data = base_data.copy()
            invalid_data["emby_servers"] = []  # 空服务器列表
            config = Config(**invalid_data)
            print("❌ 应该抛出'必须配置至少一个 Emby 服务器'异常")
            return False
        except ValueError as e:
            print(f"✅ 服务器列表非空验证正常: {e}")

        # 测试：服务器 ID 重复
        try:
            invalid_data = base_data.copy()
            invalid_data["emby_servers"] = [
                {
                    "id": "same_id",
                    "name": "服务器1",
                    "api_key": "key1",
                    "url": "http://server1.com",
                    "line": "server1.com",
                    "enabled": True
                },
                {
                    "id": "same_id",  # 重复的 ID
                    "name": "服务器2",
                    "api_key": "key2",
                    "url": "http://server2.com",
                    "line": "server2.com",
                    "enabled": True
                }
            ]
            config = Config(**invalid_data)
            print("❌ 应该抛出'服务器 ID 必须唯一'异常")
            return False
        except ValueError as e:
            print(f"✅ ID 唯一性验证正常: {e}")

        return True

    except Exception as e:
        print(f"❌ 验证规则测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 70)
    print("多服务器配置测试")
    print("=" * 70)

    results = []

    results.append(("EmbyServerConfig 类", test_emby_server_config()))
    results.append(("旧配置自动转换", test_legacy_config_conversion()))
    results.append(("新多服务器配置", test_new_multi_server_config()))
    results.append(("验证规则", test_validation_rules()))

    # 输出测试结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print("\n" + "-" * 70)
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print("=" * 70)

    if failed > 0:
        print("\n⚠️  部分测试失败")
        return 1
    else:
        print("\n🎉 所有测试通过！配置结构重构成功！")
        return 0


if __name__ == '__main__':
    sys.exit(main())
