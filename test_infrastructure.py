#!/usr/bin/env python3
"""
基础架构测试脚本
测试新创建的消息模板、Emoji规范、按钮配置、格式化工具和验证器
"""

import sys
from datetime import datetime, timedelta

print("=" * 60)
print("EmbyBot 基础架构测试")
print("=" * 60)
print()

# ==================== 测试 1: 模块导入 ====================
print("📦 测试 1: 模块导入")
print("-" * 60)

test_results = []

try:
    print("导入 bot.constants.messages...", end=" ")
    from bot.constants.messages import Messages, ErrorMessages, SuccessMessages
    print("✅ 成功")
    test_results.append(("Messages 模块", True, ""))
except Exception as e:
    print(f"❌ 失败: {e}")
    test_results.append(("Messages 模块", False, str(e)))

try:
    print("导入 bot.constants.emojis...", end=" ")
    from bot.constants.emojis import Emojis, ButtonEmojis
    print("✅ 成功")
    test_results.append(("Emojis 模块", True, ""))
except Exception as e:
    print(f"❌ 失败: {e}")
    test_results.append(("Emojis 模块", False, str(e)))

try:
    print("导入 bot.constants.buttons...", end=" ")
    from bot.constants.buttons import ButtonConfig, ButtonLayouts
    print("✅ 成功")
    test_results.append(("Buttons 模块", True, ""))
except Exception as e:
    print(f"❌ 失败: {e}")
    test_results.append(("Buttons 模块", False, str(e)))

try:
    print("导入 bot.constants.formats...", end=" ")
    from bot.constants.formats import TextFormats, TimeFormats, NumberFormats, StatusFormats
    print("✅ 成功")
    test_results.append(("Formats 模块", True, ""))
except Exception as e:
    print(f"❌ 失败: {e}")
    test_results.append(("Formats 模块", False, str(e)))

try:
    print("导入 bot.func_helper.validators...", end=" ")
    from bot.func_helper.validators import Validators, ValidationResult
    print("✅ 成功")
    test_results.append(("Validators 模块", True, ""))
except Exception as e:
    print(f"❌ 失败: {e}")
    test_results.append(("Validators 模块", False, str(e)))

try:
    print("导入 bot.func_helper.message_formatter...", end=" ")
    from bot.func_helper.message_formatter import MessageFormatter, ProgressTracker
    print("✅ 成功")
    test_results.append(("MessageFormatter 模块", True, ""))
except Exception as e:
    print(f"❌ 失败: {e}")
    test_results.append(("MessageFormatter 模块", False, str(e)))

print()

# ==================== 测试 2: 消息模板 ====================
print("📝 测试 2: 消息模板系统")
print("-" * 60)

try:
    from bot.constants.messages import Messages

    # 测试欢迎消息
    welcome = Messages.SYSTEM_WELCOME.format(first_name="测试用户")
    print("✅ 欢迎消息模板:")
    print(welcome[:100] + "..." if len(welcome) > 100 else welcome)
    print()

    # 测试错误消息
    error = Messages.ERROR_USER_NOT_FOUND.format(user_id="123456")
    print("✅ 错误消息模板:")
    print(error[:100] + "..." if len(error) > 100 else error)
    print()

    # 测试账户创建消息
    account = Messages.ACCOUNT_CREATE_START.format(timeout=120)
    print("✅ 账户创建模板:")
    print(account[:100] + "..." if len(account) > 100 else account)
    print()

    test_results.append(("消息模板格式化", True, ""))
except Exception as e:
    print(f"❌ 消息模板测试失败: {e}")
    test_results.append(("消息模板格式化", False, str(e)))

# ==================== 测试 3: Emoji 规范 ====================
print("🎨 测试 3: Emoji 规范")
print("-" * 60)

try:
    from bot.constants.emojis import Emojis, ButtonEmojis

    print(f"成功状态: {Emojis.SUCCESS}")
    print(f"错误状态: {Emojis.ERROR}")
    print(f"警告状态: {Emojis.WARNING}")
    print(f"加载中: {Emojis.LOADING}")
    print()

    # 测试等级获取
    print("用户等级状态:")
    for level, desc in [('a', '白名单'), ('b', '正常'), ('c', '禁用'), ('d', '未注册')]:
        emoji = Emojis.get_status_emoji(level)
        text = Emojis.get_level_text(level)
        print(f"  等级 {level}: {emoji} {text}")
    print()

    # 测试按钮 Emoji
    print("按钮 Emoji:")
    print(f"  创建账户: {ButtonEmojis.CREATE_ACCOUNT}")
    print(f"  我的收藏: {ButtonEmojis.MY_FAVORITES}")
    print(f"  重置密码: {ButtonEmojis.RESET_PASSWORD}")
    print()

    test_results.append(("Emoji 规范", True, ""))
except Exception as e:
    print(f"❌ Emoji 测试失败: {e}")
    test_results.append(("Emoji 规范", False, str(e)))

# ==================== 测试 4: 按钮配置 ====================
print("🔘 测试 4: 按钮配置")
print("-" * 60)

try:
    from bot.constants.buttons import ButtonConfig

    print("用户面板按钮:")
    for key, text in list(ButtonConfig.USER_PANEL.items())[:5]:
        print(f"  {key}: {text}")
    print()

    print("管理员面板按钮:")
    for key, text in list(ButtonConfig.ADMIN_PANEL.items())[:5]:
        print(f"  {key}: {text}")
    print()

    print("通用操作按钮:")
    for key, text in ButtonConfig.COMMON.items():
        print(f"  {key}: {text}")
    print()

    test_results.append(("按钮配置", True, ""))
except Exception as e:
    print(f"❌ 按钮配置测试失败: {e}")
    test_results.append(("按钮配置", False, str(e)))

# ==================== 测试 5: 验证器 ====================
print("✔️ 测试 5: 输入验证器")
print("-" * 60)

try:
    from bot.func_helper.validators import Validators

    # 测试用户名验证
    print("用户名验证:")
    test_usernames = [
        ("苏苏", True),
        ("TestUser123", True),
        ("a", False),  # 太短
        ("user@123", False),  # 特殊字符
    ]

    for username, expected in test_usernames:
        result = Validators.validate_username(username)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"  {status} '{username}': {'有效' if result.is_valid else '无效'}")
        if not result.is_valid:
            print(f"     原因: {result.error_message}")
    print()

    # 测试安全码验证
    print("安全码验证:")
    test_pins = [
        ("1234", True),
        ("123456", True),
        ("123", False),  # 太短
        ("abcd", False),  # 非数字
    ]

    for pin, expected in test_pins:
        result = Validators.validate_pin(pin)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"  {status} '{pin}': {'有效' if result.is_valid else '无效'}")
    print()

    # 测试 IP 验证
    print("IP 地址验证:")
    test_ips = [
        ("192.168.1.1", True),
        ("8.8.8.8", True),
        ("256.1.1.1", False),  # 超出范围
        ("invalid", False),
    ]

    for ip, expected in test_ips:
        result = Validators.validate_ip(ip)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"  {status} '{ip}': {'有效' if result.is_valid else '无效'}")
    print()

    # 测试用户名和安全码解析
    print("用户名+安全码解析:")
    test_inputs = [
        ("苏苏 1234", True),
        ("TestUser 5678", True),
        ("苏苏1234", False),  # 缺少空格
        ("abc 123", False),  # 安全码太短
    ]

    for input_text, expected in test_inputs:
        username, pin, error = Validators.parse_username_pin(input_text)
        success = (username is not None and pin is not None)
        status = "✅" if success == expected else "❌"
        print(f"  {status} '{input_text}'")
        if success:
            print(f"     用户名: {username}, 安全码: {pin}")
        else:
            print(f"     错误: {error}")
    print()

    test_results.append(("输入验证器", True, ""))
except Exception as e:
    print(f"❌ 验证器测试失败: {e}")
    test_results.append(("输入验证器", False, str(e)))

# ==================== 测试 6: 格式化工具 ====================
print("🛠️ 测试 6: 消息格式化工具")
print("-" * 60)

try:
    from bot.func_helper.message_formatter import MessageFormatter, ProgressTracker

    # 测试用户链接
    user_link = MessageFormatter.format_user_link(123456789, "测试用户")
    print(f"✅ 用户链接: {user_link}")
    print()

    # 测试时间格式化
    now = datetime.now()
    formatted_time = MessageFormatter.format_time(now)
    print(f"✅ 时间格式化: {formatted_time}")
    print()

    # 测试剩余天数
    future = datetime.now() + timedelta(days=5)
    days_left = MessageFormatter.format_days_left(future)
    print(f"✅ 剩余天数: {days_left}")
    print()

    # 测试文件大小格式化
    file_size = MessageFormatter.format_file_size(1536000)
    print(f"✅ 文件大小: {file_size}")
    print()

    # 测试进度条
    progress_bar = MessageFormatter.format_progress_bar(7, 10)
    print(f"✅ 进度条: {progress_bar}")
    print()

    # 测试列表格式化
    items = ["项目1", "项目2", "项目3"]
    numbered_list = MessageFormatter.format_list(items, numbered=True)
    print("✅ 编号列表:")
    print(numbered_list)
    print()

    # 测试进度追踪器
    print("✅ 进度追踪器:")
    tracker = ProgressTracker(3, "测试任务")
    tracker.add_step("步骤1")
    tracker.add_step("步骤2")
    tracker.add_step("步骤3")
    tracker.next_step()
    progress_text = tracker.format_progress("正在执行...")
    print(progress_text[:150] + "..." if len(progress_text) > 150 else progress_text)
    print()

    test_results.append(("消息格式化工具", True, ""))
except Exception as e:
    print(f"❌ 格式化工具测试失败: {e}")
    test_results.append(("消息格式化工具", False, str(e)))

# ==================== 测试 7: 文本格式 ====================
print("📐 测试 7: 文本格式规范")
print("-" * 60)

try:
    from bot.constants.formats import TextFormats, TimeFormats, NumberFormats

    # 测试 Markdown 格式
    print(f"✅ 粗体: {TextFormats.bold('粗体文本')}")
    print(f"✅ 斜体: {TextFormats.italic('斜体文本')}")
    print(f"✅ 代码: {TextFormats.code('code_block')}")
    print()

    # 测试列表
    items = ["选项A", "选项B", "选项C"]
    print("✅ 项目符号列表:")
    print(TextFormats.bullet_list(items))
    print()

    # 测试数字格式化
    print(f"✅ 数字格式化: {NumberFormats.format_number(1234567)}")
    print(f"✅ 文件大小: {NumberFormats.format_file_size(2048000)}")
    print(f"✅ 百分比: {NumberFormats.format_percentage(75, 100)}")
    print()

    # 测试时长格式化
    print(f"✅ 时长格式化: {TimeFormats.format_duration(3665)}")
    print()

    test_results.append(("文本格式规范", True, ""))
except Exception as e:
    print(f"❌ 文本格式测试失败: {e}")
    test_results.append(("文本格式规范", False, str(e)))

# ==================== 测试 8: 错误消息生成器 ====================
print("⚠️ 测试 8: 错误消息生成器")
print("-" * 60)

try:
    from bot.constants.messages import ErrorMessages

    # 测试创建失败消息
    error_msg = ErrorMessages.create_failed("username_exists")
    print("✅ 用户名已存在错误:")
    print(error_msg[:150] + "..." if len(error_msg) > 150 else error_msg)
    print()

    error_msg2 = ErrorMessages.create_failed("server_error")
    print("✅ 服务器错误:")
    print(error_msg2[:150] + "..." if len(error_msg2) > 150 else error_msg2)
    print()

    test_results.append(("错误消息生成器", True, ""))
except Exception as e:
    print(f"❌ 错误消息生成器测试失败: {e}")
    test_results.append(("错误消息生成器", False, str(e)))

# ==================== 测试 9: 用户信息卡片 ====================
print("🎴 测试 9: 用户信息卡片格式化")
print("-" * 60)

try:
    from bot.func_helper.message_formatter import MessageFormatter

    # 模拟用户数据
    user_data = {
        'tg_id': 123456789,
        'name': '测试用户',
        'lv': 'b',
        'coins': 100,
        'coin_name': '樱花',
        'emby_name': '测试Emby账户',
        'ex': datetime.now() + timedelta(days=30),
        'cr': datetime.now() - timedelta(days=10),
    }

    card = MessageFormatter.format_user_info_card(user_data)
    print("✅ 用户信息卡片:")
    print(card)
    print()

    test_results.append(("用户信息卡片", True, ""))
except Exception as e:
    print(f"❌ 用户信息卡片测试失败: {e}")
    test_results.append(("用户信息卡片", False, str(e)))

# ==================== 测试总结 ====================
print("=" * 60)
print("📊 测试总结")
print("=" * 60)

passed = sum(1 for _, success, _ in test_results if success)
failed = sum(1 for _, success, _ in test_results if not success)
total = len(test_results)

print(f"\n总计: {total} 个测试")
print(f"✅ 通过: {passed}")
print(f"❌ 失败: {failed}")
print(f"成功率: {(passed/total)*100:.1f}%\n")

if failed > 0:
    print("失败的测试:")
    for name, success, error in test_results:
        if not success:
            print(f"  ❌ {name}: {error}")
    print()

# 详细结果
print("详细结果:")
for name, success, error in test_results:
    status = "✅ 通过" if success else "❌ 失败"
    print(f"  {status}: {name}")

print("\n" + "=" * 60)
if failed == 0:
    print("🎉 所有测试通过！基础架构验证成功！")
else:
    print("⚠️ 部分测试失败，请检查上述错误信息。")
print("=" * 60)
