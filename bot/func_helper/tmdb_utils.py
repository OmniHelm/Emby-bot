"""
TMDB 链接解析工具

支持解析 TMDB 电影/剧集链接，提取 ID 和媒体类型
"""

import re
from typing import Optional, Dict
from bot import LOGGER


def parse_tmdb_link(link: str) -> Optional[Dict[str, str]]:
    """
    解析 TMDB 链接

    :param link: TMDB 链接，例如：
                 https://www.themoviedb.org/movie/12345-inception
                 https://www.themoviedb.org/tv/67890-breaking-bad
    :return: 解析结果字典，包含 tmdb_id, media_type, title_slug；解析失败返回 None

    示例返回:
    {
        "tmdb_id": "12345",
        "media_type": "movie",  # 或 "tv"
        "title_slug": "inception"
    }
    """
    try:
        # 支持的链接格式:
        # https://www.themoviedb.org/movie/12345
        # https://www.themoviedb.org/movie/12345-movie-title
        # https://www.themoviedb.org/tv/67890-series-title

        # 正则匹配 /movie/ 或 /tv/ 后面的 ID 和可选的标题
        pattern = r'themoviedb\.org/(movie|tv)/(\d+)(?:-([a-z0-9-]+))?'
        match = re.search(pattern, link.lower())

        if not match:
            LOGGER.warning(f"无法解析 TMDB 链接: {link}")
            return None

        media_type = match.group(1)  # 'movie' or 'tv'
        tmdb_id = match.group(2)      # '12345'
        title_slug = match.group(3) if match.group(3) else ""  # 'inception' 或空字符串

        result = {
            "tmdb_id": tmdb_id,
            "media_type": media_type,
            "title_slug": title_slug
        }

        LOGGER.info(f"成功解析 TMDB 链接: {result}")
        return result

    except Exception as e:
        LOGGER.error(f"解析 TMDB 链接时出错: {str(e)}")
        return None


def get_media_type_cn(media_type: str) -> str:
    """
    获取媒体类型的中文名称

    :param media_type: 'movie' 或 'tv'
    :return: '电影' 或 '剧集'
    """
    mapping = {
        'movie': '电影',
        'tv': '剧集'
    }
    return mapping.get(media_type, '未知')


def format_title_slug(title_slug: str) -> str:
    """
    格式化标题 slug（将连字符替换为空格并首字母大写）

    :param title_slug: 'inception' 或 'breaking-bad'
    :return: 'Inception' 或 'Breaking Bad'
    """
    if not title_slug:
        return ""

    # 将连字符替换为空格
    words = title_slug.replace('-', ' ').split()
    # 首字母大写
    formatted = ' '.join(word.capitalize() for word in words)
    return formatted


def is_valid_tmdb_link(link: str) -> bool:
    """
    验证是否为有效的 TMDB 链接

    :param link: 待验证的链接
    :return: True 如果是有效的 TMDB 链接，否则 False
    """
    if not link or not isinstance(link, str):
        return False

    return parse_tmdb_link(link) is not None
