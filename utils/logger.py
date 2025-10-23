"""
日志系统
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import LOGGING


def setup_logger(name: str = "quant_trading") -> logging.Logger:
    """
    设置日志器

    Args:
        name: 日志器名称

    Returns:
        logging.Logger: 配置好的日志器
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOGGING["level"]))

    # 确保日志目录存在
    log_dir = os.path.dirname(LOGGING["file"])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 文件处理器（自动轮转）
    file_handler = RotatingFileHandler(
        LOGGING["file"],
        maxBytes=LOGGING["max_bytes"],
        backupCount=LOGGING["backup_count"],
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式化器
    formatter = logging.Formatter(LOGGING["format"])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# 创建默认日志器
logger = setup_logger()


# 便捷函数
def log_trade(action: str, symbol: str, price: float, amount: float, **kwargs):
    """记录交易日志"""
    logger.info(
        f"TRADE | {action} | {symbol} | Price: {price} | Amount: {amount} | {kwargs}"
    )


def log_signal(strategy: str, symbol: str, signal: str, **kwargs):
    """记录信号日志"""
    logger.info(
        f"SIGNAL | {strategy} | {symbol} | {signal} | {kwargs}"
    )


def log_risk(event: str, level: str, message: str, **kwargs):
    """记录风控日志"""
    log_func = getattr(logger, level.lower(), logger.warning)
    log_func(
        f"RISK | {event} | {message} | {kwargs}"
    )


def log_error(module: str, error: Exception, **kwargs):
    """记录错误日志"""
    logger.error(
        f"ERROR | {module} | {type(error).__name__}: {str(error)} | {kwargs}",
        exc_info=True
    )
