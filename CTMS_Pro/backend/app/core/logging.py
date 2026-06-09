<<<<<<< HEAD
"""
日志配置 - 使用 Loguru
"""
from loguru import logger
import sys


def setup_logging():
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # 文件输出（按天滚动，保留 30 天）
    logger.add(
        "logs/ctms_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        level="INFO",
        encoding="utf-8",
    )

    # 错误日志单独文件
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        level="ERROR",
        encoding="utf-8",
    )
=======
"""
日志配置 - 使用 Loguru
"""
from loguru import logger
import sys


def setup_logging():
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # 文件输出（按天滚动，保留 30 天）
    logger.add(
        "logs/ctms_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        level="INFO",
        encoding="utf-8",
    )

    # 错误日志单独文件
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        level="ERROR",
        encoding="utf-8",
    )
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
