"""
输入验证工具
提供统一的输入验证功能
"""

import re
from typing import Tuple, Optional


class ValidationResult:
    """验证结果类"""

    def __init__(self, is_valid: bool, error_message: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message

    def __bool__(self):
        return self.is_valid


class Validators:
    """输入验证器"""

    @staticmethod
    def validate_ip(ip_address: str) -> ValidationResult:
        """
        验证 IP 地址格式

        Args:
            ip_address: IP 地址字符串

        Returns:
            ValidationResult 对象
        """
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

        if re.match(pattern, ip_address):
            return ValidationResult(True)
        else:
            return ValidationResult(
                False,
                f"IP 地址格式错误：`{ip_address}`\n正确格式如：192.168.1.1"
            )

    @staticmethod
    def validate_username(username: str) -> ValidationResult:
        """
        验证用户名（允许中英文、数字、下划线、空格、Emoji）

        Args:
            username: 用户名

        Returns:
            ValidationResult 对象
        """
        # 长度检查
        if len(username) < 2:
            return ValidationResult(False, "用户名至少需要 2 个字符")

        if len(username) > 20:
            return ValidationResult(False, "用户名不能超过 20 个字符")

        # 字符检查（使用黑名单模式，排除特殊字符，允许 Emoji）
        # 禁止的特殊字符：@#$%^&*()[]{}|\\/<>"'+=
        forbidden_pattern = r'[@#$%^&*()\[\]{}|\\/<>"\'+=]'
        if re.search(forbidden_pattern, username):
            return ValidationResult(
                False,
                "用户名不支持特殊字符如：@#$%^&*()\n"
                "支持中英文、数字、下划线、空格和 Emoji"
            )

        # 不能全是空格
        if username.strip() == "":
            return ValidationResult(False, "用户名不能全是空格")

        return ValidationResult(True)

    @staticmethod
    def validate_pin(pin: str) -> ValidationResult:
        """
        验证安全码（4-6 位数字）

        Args:
            pin: 安全码

        Returns:
            ValidationResult 对象
        """
        if not pin.isdigit():
            return ValidationResult(False, "安全码必须是纯数字")

        if len(pin) < 4:
            return ValidationResult(False, "安全码至少需要 4 位数字")

        if len(pin) > 6:
            return ValidationResult(False, "安全码不能超过 6 位数字")

        return ValidationResult(True)

    @staticmethod
    def validate_emby_code(code: str) -> ValidationResult:
        """
        验证 Emby 注册码/续期码格式

        Args:
            code: 兑换码

        Returns:
            ValidationResult 对象
        """
        # 移除空格
        code = code.strip()

        if len(code) == 0:
            return ValidationResult(False, "兑换码不能为空")

        # 这里可以根据实际的兑换码规则进行验证
        # 示例：假设兑换码是 8-16 位字母数字组合
        if len(code) < 8:
            return ValidationResult(False, "兑换码至少需要 8 位字符")

        if len(code) > 16:
            return ValidationResult(False, "兑换码不能超过 16 位字符")

        return ValidationResult(True)

    @staticmethod
    def validate_days(days_str: str) -> ValidationResult:
        """
        验证天数输入（支持 +/- 前缀）

        Args:
            days_str: 天数字符串（如 "+30", "-7", "15"）

        Returns:
            ValidationResult 对象
        """
        # 移除空格
        days_str = days_str.strip()

        # 检查格式
        pattern = r'^[+-]?\d+$'
        if not re.match(pattern, days_str):
            return ValidationResult(
                False,
                "天数格式错误\n正确格式：+30（增加）、-7（减少）、15（设置）"
            )

        try:
            days = int(days_str)
            if abs(days) > 3650:  # 最多 10 年
                return ValidationResult(False, "天数不能超过 3650 天（10年）")

            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, "天数必须是有效的整数")

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        清理文本中的特殊字符

        Args:
            text: 原文本

        Returns:
            清理后的文本
        """
        # 移除特殊字符，只保留中英文、数字、常用标点
        return re.sub(r'[^\w\s\u4e00-\u9fa5\.,!?，。！？]', '', text)

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        转义 Telegram Markdown 特殊字符，防止解析错误

        Args:
            text: 原文本

        Returns:
            转义后的文本
        """
        # Telegram Markdown 特殊字符
        special_chars = ['\\', '`', '*', '_', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        result = text
        for char in special_chars:
            result = result.replace(char, '\\' + char)
        return result

    @staticmethod
    def parse_username_pin(input_text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        解析用户名和安全码输入

        Args:
            input_text: 用户输入（格式：用户名 安全码）

        Returns:
            (username, pin, error_message) 元组
        """
        # 移除首尾空格
        input_text = input_text.strip()

        # 按空格分割
        parts = input_text.split()

        if len(parts) < 2:
            return None, None, "请按格式输入：用户名 安全码\n示例：苏苏 1234"

        if len(parts) > 2:
            return None, None, "输入格式错误，用户名和安全码之间只能有一个空格"

        username, pin = parts

        # 验证用户名
        username_result = Validators.validate_username(username)
        if not username_result:
            return None, None, username_result.error_message

        # 验证安全码
        pin_result = Validators.validate_pin(pin)
        if not pin_result:
            return None, None, pin_result.error_message

        return username, pin, None

    @staticmethod
    def validate_telegram_id(tg_id: str) -> ValidationResult:
        """
        验证 Telegram ID

        Args:
            tg_id: Telegram ID

        Returns:
            ValidationResult 对象
        """
        try:
            tg_id_int = int(tg_id)
            if tg_id_int <= 0:
                return ValidationResult(False, "Telegram ID 必须是正整数")
            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, "Telegram ID 必须是数字")
