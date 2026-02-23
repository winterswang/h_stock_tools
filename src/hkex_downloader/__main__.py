#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所文档下载工具 - 主入口模块

支持通过 python -m hkex_downloader 命令运行
"""

from .cli.main import main

if __name__ == "__main__":
    main()