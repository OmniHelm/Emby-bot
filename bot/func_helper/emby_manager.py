"""
Emby 服务器管理器
管理多个 Emby 服务器实例
"""

from typing import Dict, Optional
from loguru import logger

from bot.func_helper.emby import Embyservice
from bot.schemas.schemas import EmbyServerConfig


class EmbyServerManager:
    """
    Emby 服务器管理器（单例模式）
    负责管理多个 Emby 服务器实例
    """

    _instance: Optional['EmbyServerManager'] = None
    _initialized: bool = False

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化管理器"""
        if not self._initialized:
            self._servers: Dict[str, Embyservice] = {}
            self._configs: Dict[str, EmbyServerConfig] = {}
            self._initialized = True
            logger.info("EmbyServerManager 初始化完成")

    def register_server(self, server_config: EmbyServerConfig) -> bool:
        """
        注册一个 Emby 服务器实例

        Args:
            server_config: 服务器配置对象

        Returns:
            是否注册成功
        """
        try:
            server_id = server_config.id

            if server_id in self._servers:
                logger.warning(f"服务器 {server_id} 已存在，跳过注册")
                return True

            # 创建独立的 Embyservice 实例（不使用单例）
            instance = Embyservice.__new__(Embyservice)
            instance.__init__(
                url=server_config.url,
                api_key=server_config.api_key,
                timeout=10,
                max_retries=1
            )

            self._servers[server_id] = instance
            self._configs[server_id] = server_config

            logger.success(
                f"注册 Emby 服务器成功: {server_config.name} "
                f"({server_id}) - {server_config.url}"
            )
            return True

        except Exception as e:
            logger.error(f"注册服务器失败 {server_config.id}: {e}")
            return False

    def get_server(self, server_id: str) -> Optional[Embyservice]:
        """
        获取指定服务器实例

        Args:
            server_id: 服务器 ID

        Returns:
            Embyservice 实例或 None
        """
        return self._servers.get(server_id)

    def get_config(self, server_id: str) -> Optional[EmbyServerConfig]:
        """
        获取指定服务器配置

        Args:
            server_id: 服务器 ID

        Returns:
            EmbyServerConfig 对象或 None
        """
        return self._configs.get(server_id)

    def get_all_servers(self) -> Dict[str, Embyservice]:
        """
        获取所有服务器实例

        Returns:
            字典，格式: {server_id: Embyservice}
        """
        return self._servers.copy()

    def list_server_ids(self):
        """
        列出所有服务器 ID

        Returns:
            服务器 ID 列表
        """
        return list(self._servers.keys())

    def has_server(self, server_id: str) -> bool:
        """
        检查服务器是否存在

        Args:
            server_id: 服务器 ID

        Returns:
            是否存在
        """
        return server_id in self._servers

    def get_server_count(self) -> int:
        """
        获取服务器数量

        Returns:
            服务器数量
        """
        return len(self._servers)

    async def close_all(self) -> None:
        """
        关闭所有服务器连接
        用于程序退出时清理资源
        """
        logger.info("开始关闭所有 Emby 服务器连接...")

        for server_id, server in self._servers.items():
            try:
                await server.close()
                logger.info(f"关闭服务器连接成功: {server_id}")
            except Exception as e:
                logger.error(f"关闭服务器连接失败 {server_id}: {e}")

        logger.success("所有 Emby 服务器连接已关闭")

    def __repr__(self):
        """字符串表示"""
        return (
            f"<EmbyServerManager(servers={self.get_server_count()}, "
            f"ids={self.list_server_ids()})>"
        )


# 创建全局单例
emby_manager = EmbyServerManager()
