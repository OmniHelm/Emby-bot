"""
消息格式化工具
提供统一的消息格式化功能
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from bot.constants.emojis import Emojis
from bot.constants.formats import TextFormats, TimeFormats, NumberFormats


class MessageFormatter:
    """消息格式化工具类"""

    @staticmethod
    def format_user_link(user_id: int, name: Optional[str] = None) -> str:
        """
        格式化用户链接

        Args:
            user_id: 用户的 Telegram ID
            name: 显示名称，如果为 None 则使用 ID

        Returns:
            Markdown 格式的用户链接
        """
        return TextFormats.user_link(user_id, name)

    @staticmethod
    def format_time(
        dt: Union[datetime, str, None],
        format: str = None
    ) -> str:
        """
        格式化时间

        Args:
            dt: datetime 对象或时间字符串
            format: 时间格式

        Returns:
            格式化后的时间字符串
        """
        return TimeFormats.format_datetime(dt, format)

    @staticmethod
    def format_date(dt: Union[datetime, str, None]) -> str:
        """格式化日期（不含时间）"""
        return TimeFormats.format_datetime(dt, TimeFormats.DATE_ONLY)

    @staticmethod
    def format_datetime_short(dt: Union[datetime, str, None]) -> str:
        """格式化日期时间（短格式）"""
        return TimeFormats.format_datetime(dt, TimeFormats.DATETIME_SHORT)

    @staticmethod
    def format_status(level: str) -> str:
        """
        格式化用户状态

        Args:
            level: 用户等级 (a/b/c/d)

        Returns:
            带 Emoji 的状态文本
        """
        emoji = Emojis.get_status_emoji(level)
        text = Emojis.get_level_text(level)
        return f"{emoji} {text}"

    @staticmethod
    def format_code_block(text: str) -> str:
        """格式化为代码块"""
        return TextFormats.code(text)

    @staticmethod
    def format_bold(text: str) -> str:
        """格式化为粗体"""
        return TextFormats.bold(text)

    @staticmethod
    def format_italic(text: str) -> str:
        """格式化为斜体"""
        return TextFormats.italic(text)

    @staticmethod
    def format_link(text: str, url: str) -> str:
        """格式化为链接"""
        return TextFormats.link(text, url)

    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """
        截断长文本

        Args:
            text: 原文本
            max_length: 最大长度
            suffix: 后缀

        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小

        Args:
            size_bytes: 字节数

        Returns:
            人类可读的大小（如 1.5 MB）
        """
        return NumberFormats.format_file_size(size_bytes)

    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        格式化时长

        Args:
            seconds: 秒数

        Returns:
            格式化的时长
        """
        return TimeFormats.format_duration(seconds)

    @staticmethod
    def format_days_left(expiry_date: datetime) -> str:
        """
        格式化剩余天数

        Args:
            expiry_date: 到期日期

        Returns:
            剩余天数描述
        """
        now = datetime.now()
        delta = expiry_date - now

        if delta.days < 0:
            return f"{Emojis.ERROR} 已过期 {abs(delta.days)} 天"
        elif delta.days == 0:
            return f"{Emojis.WARNING} 今天到期"
        elif delta.days <= 3:
            return f"{Emojis.WARNING} 剩余 {delta.days} 天"
        elif delta.days <= 7:
            return f"{Emojis.INFO} 剩余 {delta.days} 天"
        else:
            return f"{Emojis.SUCCESS} 剩余 {delta.days} 天"

    @staticmethod
    def format_expiry_time(expiry_date: Union[datetime, str, None]) -> str:
        """
        格式化到期时间（包含倒计时）

        Args:
            expiry_date: 到期日期

        Returns:
            格式化的到期信息
        """
        if expiry_date is None:
            return "永久"

        if isinstance(expiry_date, str):
            # 尝试解析字符串
            try:
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            except:
                return expiry_date

        date_str = MessageFormatter.format_time(expiry_date)
        days_left = MessageFormatter.format_days_left(expiry_date)

        return f"{date_str}\n{days_left}"

    @staticmethod
    def format_list(items: list, numbered: bool = True) -> str:
        """
        格式化列表

        Args:
            items: 列表项
            numbered: 是否编号

        Returns:
            格式化的列表文本
        """
        if numbered:
            return TextFormats.numbered_list(items)
        else:
            return TextFormats.bullet_list(items)

    @staticmethod
    def format_table(headers: list, rows: list) -> str:
        """
        格式化简单表格

        Args:
            headers: 表头列表
            rows: 行数据列表（每行是一个列表）

        Returns:
            格式化的表格
        """
        return TextFormats.simple_table(headers, rows)

    @staticmethod
    def format_progress_bar(
        current: int,
        total: int,
        length: int = 10,
        filled: str = "█",
        empty: str = "░"
    ) -> str:
        """
        格式化进度条

        Args:
            current: 当前进度
            total: 总数
            length: 进度条长度
            filled: 已完成字符
            empty: 未完成字符

        Returns:
            进度条字符串
        """
        return TextFormats.progress_bar(current, total, length)

    @staticmethod
    def format_user_info_card(user_data: dict) -> str:
        """
        格式化用户信息卡片

        Args:
            user_data: 用户数据字典

        Returns:
            格式化的用户信息卡片
        """
        from bot.constants.messages import Messages

        return Messages.USER_INFO_CARD.format(
            tg_id=user_data.get('tg_id', '未知'),
            name=MessageFormatter.format_user_link(
                user_data.get('tg_id'),
                user_data.get('name')
            ),
            status_badge=Emojis.get_status_emoji(user_data.get('lv', 'd')),
            status=Emojis.get_level_text(user_data.get('lv', 'd')),
            coin_name=user_data.get('coin_name', '积分'),
            coins=user_data.get('coins', 0),
            emby_username=MessageFormatter.format_code_block(
                user_data.get('emby_name', '未创建')
            ),
            expiry=MessageFormatter.format_expiry_time(user_data.get('ex')),
            register_time=MessageFormatter.format_time(user_data.get('cr')),
        )


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total_steps: int, title: str = "处理中"):
        self.total_steps = total_steps
        self.current_step = 0
        self.title = title
        self.steps = []

    def add_step(self, description: str):
        """添加步骤描述"""
        self.steps.append(description)

    def next_step(self):
        """进入下一步"""
        self.current_step += 1

    def format_progress(self, message: str = "") -> str:
        """格式化当前进度"""
        from bot.constants.messages import Messages

        steps_text = []
        for i, step_desc in enumerate(self.steps, 1):
            if i < self.current_step:
                emoji = Emojis.DONE
            elif i == self.current_step:
                emoji = Emojis.LOADING
            else:
                emoji = "⏳"

            steps_text.append(f"{emoji} [{i}/{self.total_steps}] {step_desc}")

        return Messages.PROGRESS_TEMPLATE.format(
            icon=Emojis.LOADING,
            title=self.title,
            steps="\n".join(steps_text),
            message=message
        )
