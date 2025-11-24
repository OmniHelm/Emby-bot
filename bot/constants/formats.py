"""
格式规范
定义统一的文本格式和样式
"""


class TextFormats:
    """文本格式规范"""

    # ==================== Markdown 格式 ====================

    @staticmethod
    def bold(text: str) -> str:
        """粗体"""
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """斜体"""
        return f"__{text}__"

    @staticmethod
    def code(text: str) -> str:
        """行内代码"""
        return f"`{text}`"

    @staticmethod
    def code_block(text: str, language: str = "") -> str:
        """代码块"""
        return f"```{language}\n{text}\n```"

    @staticmethod
    def link(text: str, url: str) -> str:
        """链接"""
        return f"[{text}]({url})"

    @staticmethod
    def user_link(user_id: int, name: str = None) -> str:
        """用户链接"""
        display_name = name or str(user_id)
        return f"[{display_name}](tg://user?id={user_id})"

    # ==================== 分隔符 ====================

    SEPARATOR_THIN = "─" * 20          # 细分隔线
    SEPARATOR_THICK = "━" * 20         # 粗分隔线
    SEPARATOR_DOTTED = "· " * 10       # 点分隔线

    # ==================== 卡片边框 ====================

    CARD_TOP = "╭─────────────────╮"
    CARD_BOTTOM = "╰─────────────────╯"
    CARD_SIDE = "│"

    @staticmethod
    def card(title: str, content: str) -> str:
        """卡片格式"""
        return f"""
{TextFormats.CARD_TOP}
│  {title}
{TextFormats.CARD_BOTTOM}

{content}
"""

    # ==================== 列表格式 ====================

    @staticmethod
    def numbered_list(items: list) -> str:
        """编号列表"""
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

    @staticmethod
    def bullet_list(items: list) -> str:
        """项目符号列表"""
        return "\n".join(f"• {item}" for item in items)

    @staticmethod
    def checkbox_list(items: list, checked: list = None) -> str:
        """复选框列表"""
        checked = checked or []
        return "\n".join(
            f"{'✅' if i in checked else '☐'} {item}"
            for i, item in enumerate(items)
        )

    # ==================== 进度条 ====================

    @staticmethod
    def progress_bar(current: int, total: int, length: int = 10) -> str:
        """进度条"""
        if total == 0:
            percent = 0
        else:
            percent = current / total

        filled_length = int(length * percent)
        bar = "█" * filled_length + "░" * (length - filled_length)
        percentage = f"{percent * 100:.1f}%"

        return f"{bar} {percentage}"

    # ==================== 表格格式 ====================

    @staticmethod
    def simple_table(headers: list, rows: list) -> str:
        """简单表格"""
        # 计算每列的最大宽度
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # 生成表格
        lines = []

        # 表头
        header_line = " | ".join(
            h.ljust(col_widths[i]) for i, h in enumerate(headers)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # 数据行
        for row in rows:
            row_line = " | ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            lines.append(row_line)

        return "\n".join(lines)

    # ==================== 键值对格式 ====================

    @staticmethod
    def key_value_pair(key: str, value: str, separator: str = "：") -> str:
        """键值对"""
        return f"**{key}**{separator}{value}"

    @staticmethod
    def key_value_list(pairs: dict) -> str:
        """键值对列表"""
        return "\n".join(
            f"• **{key}**：{value}" for key, value in pairs.items()
        )


class TimeFormats:
    """时间格式规范"""

    # 时间格式字符串
    DATETIME_FULL = "%Y-%m-%d %H:%M:%S"      # 2024-11-24 15:30:45
    DATETIME_SHORT = "%m-%d %H:%M"           # 11-24 15:30
    DATE_ONLY = "%Y-%m-%d"                   # 2024-11-24
    TIME_ONLY = "%H:%M:%S"                   # 15:30:45
    YEAR_MONTH = "%Y-%m"                     # 2024-11
    MONTH_DAY = "%m-%d"                      # 11-24

    @staticmethod
    def format_datetime(dt, format_str: str = None) -> str:
        """格式化日期时间"""
        from datetime import datetime

        if dt is None:
            return "未知"

        if isinstance(dt, str):
            return dt

        format_str = format_str or TimeFormats.DATETIME_FULL
        return dt.strftime(format_str)

    @staticmethod
    def format_duration(seconds: int) -> str:
        """格式化时长"""
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if secs > 0 or not parts:
            parts.append(f"{secs}秒")

        return " ".join(parts)

    @staticmethod
    def format_relative_time(dt) -> str:
        """格式化相对时间"""
        from datetime import datetime

        if dt is None:
            return "未知"

        now = datetime.now()
        delta = now - dt

        if delta.days > 365:
            years = delta.days // 365
            return f"{years}年前"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months}个月前"
        elif delta.days > 0:
            return f"{delta.days}天前"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours}小时前"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"


class NumberFormats:
    """数字格式规范"""

    @staticmethod
    def format_number(num: int, separator: str = ",") -> str:
        """格式化数字（千位分隔）"""
        return f"{num:,}".replace(",", separator)

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def format_percentage(value: float, total: float) -> str:
        """格式化百分比"""
        if total == 0:
            return "0%"
        percent = (value / total) * 100
        return f"{percent:.1f}%"

    @staticmethod
    def format_currency(amount: float, currency: str = "¥") -> str:
        """格式化货币"""
        return f"{currency}{amount:.2f}"


class StatusFormats:
    """状态格式规范"""

    # 状态徽章
    BADGE_SUCCESS = "🟢"
    BADGE_WARNING = "🟡"
    BADGE_ERROR = "🔴"
    BADGE_INFO = "🔵"
    BADGE_DISABLED = "⚪"

    @staticmethod
    def status_badge(status: str, text: str = None) -> str:
        """状态徽章"""
        badges = {
            'success': StatusFormats.BADGE_SUCCESS,
            'warning': StatusFormats.BADGE_WARNING,
            'error': StatusFormats.BADGE_ERROR,
            'info': StatusFormats.BADGE_INFO,
            'disabled': StatusFormats.BADGE_DISABLED,
        }
        badge = badges.get(status, '⚪')
        return f"{badge} {text}" if text else badge

    @staticmethod
    def online_status(is_online: bool) -> str:
        """在线状态"""
        return "🟢 在线" if is_online else "⚪ 离线"

    @staticmethod
    def enabled_status(is_enabled: bool) -> str:
        """启用状态"""
        return "✅ 已启用" if is_enabled else "❌ 已禁用"
