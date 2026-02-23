#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名
        max_length: 最大长度

    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, "_", filename)

    # 移除控制字符
    filename = "".join(char for char in filename if ord(char) >= 32)

    # 移除开头和结尾的空格和点
    filename = filename.strip(" .")

    # 限制长度
    if len(filename) > max_length:
        # 保留文件扩展名
        path = Path(filename)
        stem = path.stem
        suffix = path.suffix

        max_stem_length = max_length - len(suffix)
        if max_stem_length > 0:
            filename = stem[:max_stem_length] + suffix
        else:
            filename = filename[:max_length]

    # 确保文件名不为空
    if not filename:
        filename = "unnamed_file"

    return filename


def parse_date_string(date_str: str) -> Optional[date]:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串，支持多种格式

    Returns:
        解析后的日期对象，失败返回None
    """
    if not date_str:
        return None

    # 支持的日期格式
    date_formats = [
        "%Y%m%d",  # 20240101
        "%Y-%m-%d",  # 2024-01-01
        "%d/%m/%Y",  # 01/01/2024
        "%d/%m/%Y %H:%M",  # 01/01/2024 12:30
        "%Y/%m/%d",  # 2024/01/01
        "%m/%d/%Y",  # 01/01/2024
    ]

    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), fmt)
            return parsed_date.date()
        except ValueError:
            continue

    return None


def validate_stock_code(stock_code: str) -> bool:
    """
    验证股票代码格式

    Args:
        stock_code: 股票代码

    Returns:
        是否为有效的股票代码
    """
    if not stock_code:
        return False

    # 移除空格
    stock_code = stock_code.strip()

    # 港股代码通常是5位数字
    if len(stock_code) == 5 and stock_code.isdigit():
        return True

    # 也支持4位数字（会自动补零）
    if len(stock_code) == 4 and stock_code.isdigit():
        return True

    # 支持带前缀的格式，如 "HK.00700"
    if stock_code.startswith("HK.") and len(stock_code) == 8:
        code_part = stock_code[3:]
        return code_part.isdigit()

    return False


def normalize_stock_code(stock_code: str) -> str:
    """
    标准化股票代码

    Args:
        stock_code: 原始股票代码

    Returns:
        标准化后的5位股票代码
    """
    if not stock_code:
        return ""

    # 移除空格和特殊字符
    stock_code = stock_code.strip().upper()

    # 处理带前缀的格式
    if stock_code.startswith("HK."):
        stock_code = stock_code[3:]

    # 只保留数字
    code = "".join(c for c in stock_code if c.isdigit())

    # 补齐到5位
    return code.zfill(5) if code else ""


def extract_company_name_from_title(title: str) -> str:
    """
    从文档标题中提取公司名称

    Args:
        title: 文档标题

    Returns:
        提取的公司名称
    """
    if not title:
        return ""

    # 常见的标题模式
    patterns = [
        r"^([^-]+)\s*-",  # "公司名称 - 其他信息"
        r"^([^（]+)（",  # "公司名称（其他信息）"
        r"^([^(]+)\(",  # "公司名称(其他信息)"
    ]

    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(1).strip()

    # 如果没有匹配到模式，返回前30个字符
    return title[:30].strip()


def is_pdf_url(url: str) -> bool:
    """
    判断URL是否指向PDF文件

    Args:
        url: 文件URL

    Returns:
        是否为PDF文件
    """
    if not url:
        return False

    return url.lower().endswith(".pdf")


def get_file_extension_from_url(url: str) -> str:
    """
    从URL中获取文件扩展名

    Args:
        url: 文件URL

    Returns:
        文件扩展名（包含点号）
    """
    if not url:
        return ""

    path = Path(url)
    return path.suffix.lower()


def format_datetime_chinese(dt: datetime) -> str:
    """
    格式化日期时间为中文格式

    Args:
        dt: 日期时间对象

    Returns:
        中文格式的日期时间字符串
    """
    return dt.strftime("%Y年%m月%d日 %H:%M")


def format_date_chinese(d: date) -> str:
    """
    格式化日期为中文格式

    Args:
        d: 日期对象

    Returns:
        中文格式的日期字符串
    """
    return d.strftime("%Y年%m月%d日")


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def parse_file_size(size_str: str) -> Optional[int]:
    """
    解析文件大小字符串

    Args:
        size_str: 文件大小字符串，如 "10MB", "1.5GB"

    Returns:
        文件大小（字节），解析失败返回None
    """
    if not size_str:
        return None

    # 移除空格并转换为大写
    size_str = size_str.strip().upper()

    # 定义单位转换
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    # 使用正则表达式解析
    pattern = r"^([0-9.]+)\s*([A-Z]+)$"
    match = re.match(pattern, size_str)

    if not match:
        return None

    try:
        size_value = float(match.group(1))
        size_unit = match.group(2)

        if size_unit in units:
            return int(size_value * units[size_unit])
    except (ValueError, OverflowError):
        pass

    return None


def create_safe_directory(path: Union[str, Path]) -> Path:
    """
    安全创建目录

    Args:
        path: 目录路径

    Returns:
        创建的目录路径对象

    Raises:
        OSError: 如果创建目录失败
    """
    path = Path(path)

    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise OSError(f"无法创建目录 {path}: {e}")


def is_valid_date_range(from_date: date, to_date: date) -> bool:
    """
    验证日期范围是否有效

    Args:
        from_date: 开始日期
        to_date: 结束日期

    Returns:
        日期范围是否有效
    """
    if not from_date or not to_date:
        return False

    # 结束日期不能早于开始日期
    if to_date < from_date:
        return False

    # 日期范围不能超过10年
    max_days = 365 * 10
    if (to_date - from_date).days > max_days:
        return False

    return True
