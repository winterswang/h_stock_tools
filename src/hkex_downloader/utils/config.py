#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


@dataclass
class APIConfig:
    """
    API配置
    """

    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.3
    user_agent: Optional[str] = None


@dataclass
class DownloadConfig:
    """
    下载配置
    """

    download_dir: str = "./downloads"
    max_concurrent: int = 5
    chunk_size: int = 8192
    timeout: int = 60
    pdf_only: bool = True
    organize_by_company: bool = True


@dataclass
class CacheConfig:
    """
    缓存配置
    """

    cache_dir: str = "./cache"
    cache_ttl_hours: int = 24
    enable_cache: bool = True


@dataclass
class LoggingConfig:
    """
    日志配置
    """

    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_file: str = "hkex_downloader.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    console_output: bool = True


@dataclass
class AppConfig:
    """
    应用配置
    """

    api: APIConfig
    download: DownloadConfig
    cache: CacheConfig
    logging: LoggingConfig

    @classmethod
    def default(cls) -> "AppConfig":
        """
        创建默认配置
        """
        return cls(
            api=APIConfig(),
            download=DownloadConfig(),
            cache=CacheConfig(),
            logging=LoggingConfig(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """
        从字典创建配置
        """
        api_data = data.get("api", {})
        download_data = data.get("download", {})
        cache_data = data.get("cache", {})
        logging_data = data.get("logging", {})

        return cls(
            api=APIConfig(**api_data),
            download=DownloadConfig(**download_data),
            cache=CacheConfig(**cache_data),
            logging=LoggingConfig(**logging_data),
        )


def load_config(config_path: Union[str, Path]) -> AppConfig:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        应用配置对象

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式错误
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")

        return AppConfig.from_dict(data)

    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ValueError(f"配置文件解析失败: {e}")
    except Exception as e:
        raise ValueError(f"加载配置文件失败: {e}")


def save_config(
    config: AppConfig, config_path: Union[str, Path], format: str = "yaml"
) -> None:
    """
    保存配置文件

    Args:
        config: 应用配置对象
        config_path: 配置文件路径
        format: 配置文件格式 ('yaml' 或 'json')

    Raises:
        ValueError: 不支持的格式
        IOError: 文件写入失败
    """
    config_path = Path(config_path)

    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = config.to_dict()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            if format.lower() == "yaml":
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
            elif format.lower() == "json":
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"不支持的格式: {format}")

    except Exception as e:
        raise IOError(f"保存配置文件失败: {e}")


def create_default_config(
    config_path: Union[str, Path], format: str = "yaml"
) -> AppConfig:
    """
    创建默认配置文件

    Args:
        config_path: 配置文件路径
        format: 配置文件格式

    Returns:
        默认配置对象
    """
    config = AppConfig.default()
    save_config(config, config_path, format)
    return config


def get_config_path() -> Path:
    """
    获取默认配置文件路径

    Returns:
        配置文件路径
    """
    # 优先级：当前目录 > 用户目录 > 系统目录
    possible_paths = [
        Path.cwd() / "config.yaml",
        Path.cwd() / "config" / "config.yaml",
        Path.home() / ".hkex_downloader" / "config.yaml",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # 如果都不存在，返回当前目录下的配置文件路径
    return possible_paths[0]


def load_or_create_config(
    config_path: Optional[Union[str, Path]] = None
) -> AppConfig:
    """
    加载配置文件，如果不存在则创建默认配置

    Args:
        config_path: 配置文件路径，如果为None则使用默认路径

    Returns:
        应用配置对象
    """
    if config_path is None:
        config_path = get_config_path()
    else:
        config_path = Path(config_path)

    try:
        return load_config(config_path)
    except FileNotFoundError:
        print(f"配置文件不存在，创建默认配置: {config_path}")
        return create_default_config(config_path)
    except Exception as e:
        print(f"加载配置失败，使用默认配置: {e}")
        return AppConfig.default()


def update_config(config: AppConfig, updates: Dict[str, Any]) -> AppConfig:
    """
    更新配置

    Args:
        config: 原始配置
        updates: 更新的配置项

    Returns:
        更新后的配置
    """
    config_dict = config.to_dict()

    def deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    deep_update(config_dict, updates)
    return AppConfig.from_dict(config_dict)


def validate_config(config: AppConfig) -> bool:
    """
    验证配置是否有效

    Args:
        config: 应用配置

    Returns:
        配置是否有效
    """
    try:
        # 验证API配置
        if config.api.timeout <= 0:
            print("错误: API超时时间必须大于0")
            return False

        if config.api.max_retries < 0:
            print("错误: 最大重试次数不能为负数")
            return False

        # 验证下载配置
        if config.download.max_concurrent <= 0:
            print("错误: 最大并发数必须大于0")
            return False

        if config.download.chunk_size <= 0:
            print("错误: 下载块大小必须大于0")
            return False

        # 验证缓存配置
        if config.cache.cache_ttl_hours <= 0:
            print("错误: 缓存有效期必须大于0")
            return False

        # 验证日志配置
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.logging.log_level.upper() not in valid_log_levels:
            print(f"错误: 无效的日志级别: {config.logging.log_level}")
            return False

        if config.logging.backup_count < 0:
            print("错误: 日志备份数量不能为负数")
            return False

        return True

    except Exception as e:
        print(f"配置验证失败: {e}")
        return False


def print_config(config: AppConfig) -> None:
    """
    打印配置信息

    Args:
        config: 应用配置
    """
    print("当前配置:")
    print("=" * 40)

    print("API配置:")
    print(f"  超时时间: {config.api.timeout}秒")
    print(f"  最大重试: {config.api.max_retries}次")
    print(f"  重试间隔因子: {config.api.backoff_factor}")
    print()

    print("下载配置:")
    print(f"  下载目录: {config.download.download_dir}")
    print(f"  最大并发: {config.download.max_concurrent}")
    print(f"  块大小: {config.download.chunk_size}字节")
    print(f"  超时时间: {config.download.timeout}秒")
    print(f"  仅PDF: {config.download.pdf_only}")
    print(f"  按公司组织: {config.download.organize_by_company}")
    print()

    print("缓存配置:")
    print(f"  缓存目录: {config.cache.cache_dir}")
    print(f"  有效期: {config.cache.cache_ttl_hours}小时")
    print(f"  启用缓存: {config.cache.enable_cache}")
    print()

    print("日志配置:")
    print(f"  日志级别: {config.logging.log_level}")
    print(f"  日志目录: {config.logging.log_dir}")
    print(f"  日志文件: {config.logging.log_file}")
    print(f"  最大文件大小: {config.logging.max_file_size}")
    print(f"  备份数量: {config.logging.backup_count}")
    print(f"  控制台输出: {config.logging.console_output}")
