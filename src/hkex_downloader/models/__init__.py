#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块
"""

from .company import Company, Document
from .search import SearchRequest, SearchResponse

__all__ = [
    "Company",
    "Document",
    "SearchRequest",
    "SearchResponse",
]
