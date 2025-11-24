#!/usr/bin/env python3
"""
简化测试脚本 - 直接测试模块文件
不依赖 bot 包的初始化
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, '/home/jez/projects/EmbyBot')

print("=" * 60)
print("EmbyBot 基础架构简化测试")
print("=" * 60)
print()

test_results = []

# ==================== 测试 1: 直接导入验证器（无依赖） ====================
print("✔️ 测试 1: 验证器模块（无外部依赖）")
print("-" * 60)

try:
    sys.path.insert(0, '/home/jez/projects/EmbyBot/bot/func_helper')
    import validators
    from validators import Validators, ValidationResult

    print("✅ 验证器模块导入成功")

    # 测试用户名验证
    print("\n用户名验证测试:")
    tests = [
        ("苏苏", True, "有效中文用户名"),
        ("TestUser", True, "有效英文用户名"),
        ("a", False, "太短"),
        ("user@test", False, "包含特殊字符"),
    ]

    for username, expected, desc in tests:
        result = Validators.validate_username(username)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"  {status} '{username}' - {desc}")
        if not result.is_valid and result.error_message:
            print(f"      → {result.error_message.split(chr(10))[0]}")

    # 测试安全码验证
    print("\n安全码验证测试:")
    pin_tests = [
        ("1234", True, "4位数字"),
        ("123456", True, "6位数字"),
        ("123", False, "少于4位"),
        ("1234567", False, "超过6位"),
        ("abcd", False, "非数字"),
    ]

    for pin, expected, desc in pin_tests:
        result = Validators.validate_pin(pin)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"  {status} '{pin}' - {desc}")

    # 测试解析功能
    print("\n用户名+安全码解析测试:")
    parse_tests = [
        ("苏苏 1234", True),
        ("Test 5678", True),
        ("苏苏1234", False),
    ]

    for input_text, should_succeed in parse_tests:
        username, pin, error = Validators.parse_username_pin(input_text)
        success = (username is not None)
        status = "✅" if success == should_succeed else "❌"
        if success:
            print(f"  {status} '{input_text}' → 用户名: {username}, 安全码: {pin}")
        else:
            print(f"  {status} '{input_text}' → {error.split(chr(10))[0]}")

    test_results.append(("验证器模块", True))
    print()

except Exception as e:
    print(f"❌ 验证器测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("验证器模块", False))

# ==================== 测试 2: 检查模块文件语法 ====================
print("📝 测试 2: 检查所有新模块文件语法")
print("-" * 60)

files_to_check = [
    ('bot/constants/messages.py', '消息模板'),
    ('bot/constants/emojis.py', 'Emoji规范'),
    ('bot/constants/buttons.py', '按钮配置'),
    ('bot/constants/formats.py', '格式规范'),
    ('bot/func_helper/message_formatter.py', '消息格式化'),
    ('bot/func_helper/validators.py', '验证器'),
]

for filepath, name in files_to_check:
    full_path = f'/home/jez/projects/EmbyBot/{filepath}'
    try:
        # 尝试编译文件
        with open(full_path, 'r', encoding='utf-8') as f:
            code = f.read()
            compile(code, full_path, 'exec')
        print(f"✅ {name} - 语法正确")
        test_results.append((f"{name}语法", True))
    except SyntaxError as e:
        print(f"❌ {name} - 语法错误: {e}")
        test_results.append((f"{name}语法", False))
    except Exception as e:
        print(f"⚠️ {name} - 读取失败: {e}")
        test_results.append((f"{name}语法", False))

print()

# ==================== 测试 3: 检查文件结构 ====================
print("📁 测试 3: 检查文件结构和大小")
print("-" * 60)

import os

for filepath, name in files_to_check:
    full_path = f'/home/jez/projects/EmbyBot/{filepath}'
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        lines = 0
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
        print(f"✅ {name:20s} - {size:6d} bytes, {lines:4d} 行")
        test_results.append((f"{name}文件", True))
    else:
        print(f"❌ {name:20s} - 文件不存在")
        test_results.append((f"{name}文件", False))

print()

# ==================== 测试 4: 测试常量定义 ====================
print("🎨 测试 4: 测试常量和类定义")
print("-" * 60)

try:
    # 直接执行 messages.py 中的类定义
    with open('/home/jez/projects/EmbyBot/bot/constants/messages.py', 'r') as f:
        exec(f.read(), globals())

    print("✅ Messages 类定义成功")

    # 测试消息模板
    test_msg = Messages.SYSTEM_WELCOME.format(first_name="测试")
    print(f"✅ 消息模板格式化成功（长度: {len(test_msg)} 字符）")
    print(f"   预览: {test_msg[:80]}...")

    # 测试错误消息生成
    error = ErrorMessages.create_failed("username_exists")
    print(f"✅ 错误消息生成成功（长度: {len(error)} 字符）")

    test_results.append(("消息模板类", True))
    print()

except Exception as e:
    print(f"❌ Messages 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("消息模板类", False))

try:
    # 测试 Emojis
    with open('/home/jez/projects/EmbyBot/bot/constants/emojis.py', 'r') as f:
        exec(f.read(), globals())

    print("✅ Emojis 类定义成功")
    print(f"   SUCCESS: {Emojis.SUCCESS}")
    print(f"   ERROR: {Emojis.ERROR}")
    print(f"   用户: {Emojis.USER}")

    # 测试方法
    emoji = Emojis.get_status_emoji('a')
    text = Emojis.get_level_text('a')
    print(f"✅ 状态方法: {emoji} {text}")

    test_results.append(("Emoji规范类", True))
    print()

except Exception as e:
    print(f"❌ Emojis 测试失败: {e}")
    test_results.append(("Emoji规范类", False))

try:
    # 测试 Formats
    with open('/home/jez/projects/EmbyBot/bot/constants/formats.py', 'r') as f:
        exec(f.read(), globals())

    print("✅ Formats 类定义成功")

    # 测试格式化方法
    bold_text = TextFormats.bold("测试")
    print(f"   粗体: {bold_text}")

    code_text = TextFormats.code("code")
    print(f"   代码: {code_text}")

    file_size = NumberFormats.format_file_size(1024000)
    print(f"   文件大小: {file_size}")

    duration = TimeFormats.format_duration(3665)
    print(f"   时长: {duration}")

    test_results.append(("格式规范类", True))
    print()

except Exception as e:
    print(f"❌ Formats 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("格式规范类", False))

# ==================== 测试总结 ====================
print("=" * 60)
print("📊 测试总结")
print("=" * 60)

passed = sum(1 for _, success in test_results if success)
failed = sum(1 for _, success in test_results if not success)
total = len(test_results)

print(f"\n✅ 通过: {passed}/{total}")
print(f"❌ 失败: {failed}/{total}")
print(f"成功率: {(passed/total)*100:.1f}%\n")

if failed > 0:
    print("失败的测试:")
    for name, success in test_results:
        if not success:
            print(f"  ❌ {name}")
else:
    print("🎉 所有测试通过！")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
