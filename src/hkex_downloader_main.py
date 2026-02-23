#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所文档下载工具 - 主入口点
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from hkex_downloader.cli.main import main

if __name__ == '__main__':
    main()