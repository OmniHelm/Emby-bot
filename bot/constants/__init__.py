"""
常量和配置模块
包含消息模板、Emoji 规范、按钮配置等
"""

from .messages import Messages, ErrorMessages, SuccessMessages
from .emojis import Emojis, ButtonEmojis
from .buttons import ButtonConfig, ButtonLayouts

__all__ = [
    'Messages',
    'ErrorMessages',
    'SuccessMessages',
    'Emojis',
    'ButtonEmojis',
    'ButtonConfig',
    'ButtonLayouts',
]
