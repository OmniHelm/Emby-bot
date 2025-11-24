"""
logger_config - 

Author:susu
Date:2023/12/12
"""
import datetime
import pytz
from loguru import logger

# 转换为亚洲上海时区
shanghai_tz = pytz.timezone("Asia/Shanghai")
Now = datetime.datetime.now(shanghai_tz)
log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS ZZ} | {name} | {level} | {message}"
# 动态文件名，跨天时 loguru 会自动按日期切换
log_config = {
    "sink": "log/log_{time:YYYYMMDD}.txt",
    "format": log_format,  # 显示时区信息
    "level": "INFO",
    "rotation": "00:00",  # rotation：一种条件，指示何时应关闭当前记录的文件并开始新的文件。
    "retention": "30 days",  # retention ：过滤旧文件的指令，在循环或程序结束期间会删除旧文件。
    "enqueue": True,
}
logger.add(**log_config)


def logu(name):
    """返回一个绑定名称的日志实例"""
    return logger.bind(name=name)
