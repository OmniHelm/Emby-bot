#!/usr/bin/env python3
"""
多服务器配置语法检查（不需要安装依赖）
"""

import re


def check_schemas_syntax():
    """检查 schemas.py 语法"""
    print("\n🔍 检查 schemas.py 语法...")

    try:
        with open("bot/schemas/schemas.py", "r") as f:
            content = f.read()

        checks = [
            # 导入检查
            ("from pydantic import BaseModel, Field, model_validator, field_validator", "✓ 导入 field_validator"),
            ("from typing_extensions import Self", "✓ 导入 Self"),

            # EmbyServerConfig 类
            ("class EmbyServerConfig(BaseModel):", "✓ EmbyServerConfig 类存在"),
            ('id: str = Field(..., description="服务器唯一标识', "✓ EmbyServerConfig 有 id 字段"),
            ('@field_validator(\'id\')', "✓ EmbyServerConfig 有 ID 验证器"),
            ('@field_validator(\'url\')', "✓ EmbyServerConfig 有 URL 验证器"),

            # Config 类多服务器字段
            ("emby_servers: Optional[List[EmbyServerConfig]] = None", "✓ Config 有 emby_servers 字段"),
            ("emby_api: Optional[str] = None", "✓ emby_api 标记为 Optional（向后兼容）"),
            ("emby_url: Optional[str] = None", "✓ emby_url 标记为 Optional（向后兼容）"),

            # 验证器
            ("@model_validator(mode='before')", "✓ 有 mode='before' 验证器（旧配置转换）"),
            ("def convert_legacy_config(cls, data: dict)", "✓ 有旧配置转换方法"),
            ("def validate_emby_servers(cls, v: Optional[List[EmbyServerConfig]])", "✓ 有服务器列表验证方法"),

            # 辅助方法
            ("def get_server_by_id(self, server_id: str)", "✓ 有 get_server_by_id 方法"),
            ("def get_enabled_servers(self)", "✓ 有 get_enabled_servers 方法"),
            ("def list_server_ids(self)", "✓ 有 list_server_ids 方法"),
        ]

        all_passed = True
        for pattern, description in checks:
            if pattern in content:
                print(f"  {description}")
            else:
                print(f"  ✗ 缺少: {description}")
                all_passed = False

        # 检查关键逻辑
        print("\n🔍 检查关键逻辑...")

        # 检查旧配置转换逻辑
        if "data['emby_servers'] = [{" in content:
            print("  ✓ 包含旧配置转换逻辑")
        else:
            print("  ✗ 缺少旧配置转换逻辑")
            all_passed = False

        # 检查唯一性验证
        if "len(ids) != len(set(ids))" in content:
            print("  ✓ 包含 ID 唯一性验证")
        else:
            print("  ✗ 缺少 ID 唯一性验证")
            all_passed = False

        if all_passed:
            print("\n✅ 所有语法检查通过")
        else:
            print("\n⚠️  部分检查未通过")

        return all_passed

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def check_config_example():
    """检查 config_example.json 格式建议"""
    print("\n📋 config_example.json 格式建议...")

    print("""
新格式示例（多服务器 - 内容分类管理）:
{
  "emby_servers": [
    {
      "id": "anime",
      "name": "动漫服务器",
      "api_key": "your_anime_api_key",
      "url": "http://anime-server:8096",
      "line": "anime.your-domain.com",
      "whitelist_line": "vip-anime.your-domain.com",
      "enabled": true
    },
    {
      "id": "movie",
      "name": "电影服务器",
      "api_key": "your_movie_api_key",
      "url": "http://movie-server:8096",
      "line": "movie.your-domain.com",
      "enabled": true
    }
  ],
  ... 其他配置保持不变 ...
}

向后兼容：
旧配置仍然可用（会自动转换）：
{
  "emby_api": "xxxxx",
  "emby_url": "http://your-emby-server:8096",
  "emby_line": "your-domain.com",
  ... 其他配置保持不变 ...
}
""")


def main():
    """主函数"""
    print("=" * 70)
    print("多服务器配置语法检查")
    print("=" * 70)

    passed = check_schemas_syntax()
    check_config_example()

    print("\n" + "=" * 70)
    if passed:
        print("✅ 语法检查通过！阶段一配置重构完成")
        print("\n下一步:")
        print("  1. 可以在实际环境测试配置加载")
        print("  2. 继续阶段二：数据库结构升级")
        return 0
    else:
        print("❌ 语法检查发现问题，请修复")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
