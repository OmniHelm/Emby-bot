"""
Emoji 使用规范
确保整个项目中 Emoji 使用的一致性
"""

class Emojis:
    """标准化的 Emoji 定义"""

    # ==================== 状态指示 ====================
    SUCCESS = "✅"           # 成功
    ERROR = "❌"             # 错误
    WARNING = "⚠️"          # 警告
    INFO = "ℹ️"             # 信息
    LOADING = "⏳"          # 加载中
    DONE = "✔️"             # 完成

    # ==================== 用户相关 ====================
    USER = "👤"              # 用户
    USERS = "👥"             # 多个用户
    ADMIN = "👑"             # 管理员
    VIP = "⭐"              # VIP/白名单
    ROBOT = "🤖"            # 机器人

    # ==================== 功能操作 ====================
    PLAY = "▶️"             # 播放
    PAUSE = "⏸️"            # 暂停
    STOP = "⏹️"             # 停止
    REFRESH = "🔄"          # 刷新
    SETTINGS = "⚙️"         # 设置
    SEARCH = "🔍"           # 搜索
    DELETE = "🗑️"          # 删除
    EDIT = "✏️"             # 编辑
    ADD = "➕"              # 添加
    REMOVE = "➖"           # 移除

    # ==================== 数据相关 ====================
    STATS = "📊"            # 统计
    CHART = "📈"            # 图表
    DOCUMENT = "📄"         # 文档
    FOLDER = "📁"           # 文件夹
    FILE = "📃"             # 文件
    LINK = "🔗"             # 链接

    # ==================== 时间相关 ====================
    CALENDAR = "📅"         # 日历
    CLOCK = "🕐"            # 时钟
    TIMER = "⏰"            # 定时器
    HOURGLASS = "⏳"        # 沙漏

    # ==================== 通知提醒 ====================
    BELL = "🔔"             # 通知
    ALERT = "🚨"            # 警报
    ANNOUNCEMENT = "📢"     # 公告
    MESSAGE = "💬"          # 消息
    MAIL = "📧"             # 邮件

    # ==================== 媒体相关 ====================
    MOVIE = "🎬"            # 电影
    TV = "📺"               # 电视
    MUSIC = "🎵"            # 音乐
    PHOTO = "🖼️"            # 图片
    VIDEO = "🎥"            # 视频

    # ==================== 财务相关 ====================
    COIN = "💰"             # 金币
    MONEY = "💵"            # 货币
    GIFT = "🎁"             # 礼物
    SHOP = "🏪"             # 商店
    TICKET = "🎟️"          # 票券

    # ==================== 安全相关 ====================
    KEY = "🔑"              # 密钥
    LOCK = "🔒"             # 锁定
    UNLOCK = "🔓"           # 解锁
    SHIELD = "🛡️"          # 防护
    BAN = "🚫"              # 禁止

    # ==================== 网络相关 ====================
    GLOBE = "🌐"            # 全球/网络
    SIGNAL = "📡"           # 信号
    WIFI = "📶"             # WiFi
    SERVER = "🖥️"          # 服务器
    DATABASE = "💾"         # 数据库

    # ==================== 方向导航 ====================
    HOME = "🏠"             # 主页
    BACK = "↩️"             # 返回
    FORWARD = "⏩"          # 前进
    UP = "⬆️"              # 向上
    DOWN = "⬇️"            # 向下
    LEFT = "⬅️"            # 向左
    RIGHT = "➡️"           # 向右

    # ==================== 情感表达 ====================
    CELEBRATE = "🎉"        # 庆祝
    PARTY = "🎊"            # 派对
    HEART = "❤️"            # 爱心
    STAR = "⭐"            # 星星
    SPARKLE = "✨"          # 闪光
    FIRE = "🔥"             # 火焰
    THUMBUP = "👍"          # 点赞
    THUMBDOWN = "👎"        # 点踩

    # ==================== 等级状态 ====================
    LEVEL_A = "🟢"          # 白名单（绿色）
    LEVEL_B = "🔵"          # 正常用户（蓝色）
    LEVEL_C = "🔴"          # 禁用（红色）
    LEVEL_D = "⚪"          # 未注册（白色）

    @staticmethod
    def get_status_emoji(level: str) -> str:
        """根据用户等级获取状态 Emoji"""
        status_map = {
            'a': Emojis.LEVEL_A,
            'b': Emojis.LEVEL_B,
            'c': Emojis.LEVEL_C,
            'd': Emojis.LEVEL_D,
        }
        return status_map.get(level, '❓')

    @staticmethod
    def get_level_text(level: str) -> str:
        """获取等级文本描述"""
        text_map = {
            'a': '白名单',
            'b': '正常用户',
            'c': '已禁用',
            'd': '未注册',
        }
        return text_map.get(level, '未知')


class ButtonEmojis:
    """按钮专用 Emoji"""

    # 主面板按钮
    CREATE_ACCOUNT = "🎨"    # 创建账户
    MY_INFO = "👤"           # 我的信息
    MY_FAVORITES = "💖"      # 我的收藏
    MY_DEVICES = "💠"        # 我的设备
    RESET_PASSWORD = "🔑"    # 重置密码
    DELETE_ACCOUNT = "🗑️"   # 删除账户
    STORE = "🏪"             # 商店
    HELP = "❓"              # 帮助

    # 管理面板按钮
    USER_LIST = "👥"         # 用户列表
    WHITELIST = "👑"         # 白名单
    CODE_MANAGE = "🎟️"      # 码管理
    STATS = "📊"             # 统计
    SETTINGS = "⚙️"          # 设置

    # 操作按钮
    CONFIRM = "✅"           # 确认
    CANCEL = "❌"            # 取消
    BACK = "↩️"             # 返回
    CLOSE = "🔒"             # 关闭
    REFRESH = "🔄"          # 刷新

    # 功能按钮
    SHOW_HIDE = "🎬"        # 显示/隐藏
    QUERY = "🔍"            # 查询
    EXPORT = "📤"           # 导出
    IMPORT = "📥"           # 导入
