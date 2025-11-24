"""
按钮配置规范
统一管理所有按钮的文本和样式
"""

from bot.constants.emojis import ButtonEmojis as E


class ButtonConfig:
    """按钮配置类"""

    # ==================== 用户主面板 ====================

    USER_PANEL = {
        'create_account': f'{E.CREATE_ACCOUNT} 创建账户',
        'my_info': f'{E.MY_INFO} 我的信息',
        'my_favorites': f'{E.MY_FAVORITES} 我的收藏',
        'my_devices': f'{E.MY_DEVICES} 我的设备',
        'reset_password': f'{E.RESET_PASSWORD} 重置密码',
        'delete_account': f'{E.DELETE_ACCOUNT} 删除账户',
        'store': f'{E.STORE} 兑换商店',
        'help': f'{E.HELP} 帮助',
        'show_hide': f'{E.SHOW_HIDE} 显示/隐藏',
    }

    # ==================== 管理员面板 ====================

    ADMIN_PANEL = {
        'user_list': f'{E.USER_LIST} 用户列表',
        'whitelist': f'👑 白名单',
        'normal_users': f'{E.USER_LIST} 普通用户',
        'code_manage': f'{E.CODE_MANAGE} 注册/续期码',
        'device_list': f'{E.MY_DEVICES} 设备列表',
        'stats': f'{E.STATS} 统计数据',
        'settings': f'{E.SETTINGS} 系统设置',
        'register_status': f'⭕ 注册状态',
        'query_register': f'{E.QUERY} 查询注册',
        'redeem_settings': f'🏬 兑换设置',
    }

    # ==================== 通用操作按钮 ====================

    COMMON = {
        'confirm': f'{E.CONFIRM} 确认',
        'cancel': f'{E.CANCEL} 取消',
        'back': f'{E.BACK} 返回',
        'close': f'{E.CLOSE} 关闭',
        'refresh': f'{E.REFRESH} 刷新',
        'home': f'🏠 返回主页',
    }

    # ==================== 功能操作按钮 ====================

    OPERATIONS = {
        'renew': '⏰ 续期',
        'ban': '🚫 封禁',
        'unban': '✅ 解封',
        'promote': '⬆️ 提升',
        'demote': '⬇️ 降级',
        'query': f'{E.QUERY} 查询',
        'edit': '✏️ 编辑',
        'delete': f'{E.DELETE_ACCOUNT} 删除',
    }

    # ==================== 分页按钮 ====================

    PAGINATION = {
        'previous': '◀️ 上一页',
        'next': '▶️ 下一页',
        'first': '⏮️ 首页',
        'last': '⏭️ 末页',
    }

    @staticmethod
    def get_button_text(category: str, key: str, default: str = None) -> str:
        """获取按钮文本"""
        config_map = {
            'user': ButtonConfig.USER_PANEL,
            'admin': ButtonConfig.ADMIN_PANEL,
            'common': ButtonConfig.COMMON,
            'operation': ButtonConfig.OPERATIONS,
            'page': ButtonConfig.PAGINATION,
        }
        return config_map.get(category, {}).get(key, default or key)


class ButtonLayouts:
    """按钮布局模板"""

    @staticmethod
    def user_main_panel():
        """用户主面板布局"""
        from bot.func_helper.fix_bottons import ikb
        bc = ButtonConfig

        return ikb([
            # 第一行：核心功能
            [(bc.USER_PANEL['my_info'], 'me'),
             (bc.USER_PANEL['my_favorites'], 'my_favorites')],

            # 第二行：账户操作
            [(bc.USER_PANEL['reset_password'], 'reset'),
             (bc.USER_PANEL['my_devices'], 'my_devices')],

            # 第三行：其他功能
            [(bc.USER_PANEL['store'], 'storeall'),
             (bc.USER_PANEL['show_hide'], 'embyblock')],

            # 第四行：危险操作
            [(bc.USER_PANEL['delete_account'], 'delme')],
        ])

    @staticmethod
    def admin_main_panel():
        """管理员主面板布局"""
        from bot.func_helper.fix_bottons import ikb
        bc = ButtonConfig

        return ikb([
            # 第一行：注册管理
            [(bc.ADMIN_PANEL['register_status'], 'open-menu'),
             (bc.ADMIN_PANEL['code_manage'], 'cr_link')],

            # 第二行：查询功能
            [(bc.ADMIN_PANEL['query_register'], 'ch_link'),
             (bc.ADMIN_PANEL['redeem_settings'], 'set_renew')],

            # 第三行：用户管理
            [(bc.ADMIN_PANEL['normal_users'], 'normaluser'),
             (bc.ADMIN_PANEL['whitelist'], 'whitelist')],

            # 第四行：设备统计
            [(bc.ADMIN_PANEL['device_list'], 'user_devices')],

            # 第五行：返回
            [(bc.COMMON['back'], 'start_over')],
        ])

    @staticmethod
    def confirm_cancel(confirm_callback: str, cancel_callback: str = 'cancel'):
        """确认/取消按钮布局"""
        from bot.func_helper.fix_bottons import ikb
        bc = ButtonConfig

        return ikb([
            [(bc.COMMON['confirm'], confirm_callback),
             (bc.COMMON['cancel'], cancel_callback)],
        ])
