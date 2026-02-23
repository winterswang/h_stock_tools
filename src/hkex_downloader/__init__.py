#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所上市公司信息查询和下载工具

HKEx Downloader - A tool for querying and downloading Hong Kong Stock
Exchange listed company information.
"""

__version__ = "1.0.0"
__author__ = "HKEx Downloader Team"
__email__ = "admin@example.com"
__description__ = "港交所上市公司信息查询和下载工具"

from .api.client import HKExClient
from .models.company import Company, Document
from .models.financial import (
    FinancialData,
    FinancialDataCollection,
    FinancialDataRequest,
    FinancialDataResponse,
    ReportType,
    ReportPeriod,
)
from .services.downloader import DocumentDownloader
from .services.financial_downloader import FinancialDataDownloader
from .services.financial_service import FinancialDataService
from .services.searcher import DocumentSearcher
from .utils.financial_formatter import FinancialDataFormatter

__all__ = [
    "HKExClient",
    "Company",
    "Document",
    "DocumentDownloader",
    "DocumentSearcher",
    "FinancialData",
    "FinancialDataCollection",
    "FinancialDataRequest",
    "FinancialDataResponse",
    "FinancialDataDownloader",
    "FinancialDataService",
    "FinancialDataFormatter",
    "ReportType",
    "ReportPeriod",
]
