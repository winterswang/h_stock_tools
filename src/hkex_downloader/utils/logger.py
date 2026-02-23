#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .config import LoggingConfig


def parse_file_size(size_str: str) -> int:
    """
    解析文件大小字符串

    Args:
        size_str: 文件大小字符串，如 "10MB"

    Returns:
        文件大小（字节）
    """
    size_str = size_str.upper().strip()

    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
    }

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                size_value = float(size_str[: -len(unit)])
                return int(size_value * multiplier)
            except ValueError:
                break

    # 默认返回10MB
    return 10 * 1024 * 1024


def setup_logger(
    name: str = "hkex_downloader", config: Optional[LoggingConfig] = None
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        config: 日志配置

    Returns:
        配置好的日志记录器
    """
    if config is None:
        config = LoggingConfig()

    # 创建日志记录器
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 创建格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    if config.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if config.log_dir and config.log_file:
        # 确保日志目录存在
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file_path = log_dir / config.log_file

        # 解析最大文件大小
        max_bytes = parse_file_size(config.max_file_size)

        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=max_bytes,
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "hkex_downloader") -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    日志记录器混入类

    为类提供日志记录功能
    """

    @property
    def logger(self) -> logging.Logger:
        """
        获取日志记录器
        """
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

    def log_debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)

    def log_info(self, message: str, *args, **kwargs):
        """记录信息"""
        self.logger.info(message, *args, **kwargs)

    def log_warning(self, message: str, *args, **kwargs):
        """记录警告"""
        self.logger.warning(message, *args, **kwargs)

    def log_error(self, message: str, *args, **kwargs):
        """记录错误"""
        self.logger.error(message, *args, **kwargs)

    def log_critical(self, message: str, *args, **kwargs):
        """记录严重错误"""
        self.logger.critical(message, *args, **kwargs)

    def log_exception(self, message: str, *args, **kwargs):
        """记录异常"""
        self.logger.exception(message, *args, **kwargs)


def log_function_call(func):
    """
    函数调用日志装饰器

    Args:
        func: 被装饰的函数

    Returns:
        装饰后的函数
    """

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        # 记录函数调用
        logger.debug(f"调用函数: {func.__name__}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}")
            raise

    return wrapper


def log_method_call(method):
    """
    方法调用日志装饰器

    Args:
        method: 被装饰的方法

    Returns:
        装饰后的方法
    """

    def wrapper(self, *args, **kwargs):
        logger = get_logger(self.__class__.__name__)

        # 记录方法调用
        logger.debug(f"调用方法: {self.__class__.__name__}.{method.__name__}")

        try:
            result = method(self, *args, **kwargs)
            logger.debug(
                f"方法 {self.__class__.__name__}.{method.__name__} 执行成功"
            )
            return result
        except Exception as e:
            logger.error(
                f"方法 {self.__class__.__name__}.{method.__name__} 执行失败: {e}"
            )
            raise

    return wrapper


class ProgressLogger:
    """
    进度日志记录器

    用于记录长时间运行任务的进度
    """

    def __init__(
        self,
        logger: logging.Logger,
        total: int,
        task_name: str = "任务",
        log_interval: int = 10,
    ):
        """
        初始化进度日志记录器

        Args:
            logger: 日志记录器
            total: 总任务数
            task_name: 任务名称
            log_interval: 日志记录间隔（百分比）
        """
        self.logger = logger
        self.total = total
        self.task_name = task_name
        self.log_interval = log_interval
        self.current = 0
        self.last_logged_percent = 0

    def update(self, increment: int = 1):
        """
        更新进度

        Args:
            increment: 增量
        """
        self.current += increment

        if self.total > 0:
            percent = (self.current / self.total) * 100

            # 检查是否需要记录日志
            if percent - self.last_logged_percent >= self.log_interval:
                self.logger.info(
                    f"{self.task_name}进度: {self.current}/{self.total} "
                    f"({percent:.1f}%)"
                )
                self.last_logged_percent = percent

    def finish(self):
        """
        完成任务
        """
        self.logger.info(
            f"{self.task_name}完成: {self.current}/{self.total} (100%)"
        )


class TimedLogger:
    """
    计时日志记录器

    用于记录操作的执行时间
    """

    def __init__(self, logger: logging.Logger, operation_name: str):
        """
        初始化计时日志记录器

        Args:
            logger: 日志记录器
            operation_name: 操作名称
        """
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        self.logger.info(f"开始{self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        if self.start_time:
            elapsed_time = time.time() - self.start_time

            if exc_type is None:
                self.logger.info(
                    f"{self.operation_name}完成，耗时: {elapsed_time:.2f}秒"
                )
            else:
                self.logger.error(
                    f"{self.operation_name}失败，耗时: {elapsed_time:.2f}秒"
                )


def configure_third_party_loggers():
    """
    配置第三方库的日志级别
    """
    # 降低第三方库的日志级别，避免过多的调试信息
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def setup_application_logging(
    config: Optional[LoggingConfig] = None,
) -> logging.Logger:
    """
    设置应用程序日志

    Args:
        config: 日志配置

    Returns:
        主日志记录器
    """
    # 配置第三方库日志
    configure_third_party_loggers()

    # 设置主日志记录器
    main_logger = setup_logger("hkex_downloader", config)

    # 设置子模块日志记录器
    setup_logger("hkex_downloader.api", config)
    setup_logger("hkex_downloader.services", config)
    setup_logger("hkex_downloader.models", config)
    setup_logger("hkex_downloader.cli", config)

    return main_logger
