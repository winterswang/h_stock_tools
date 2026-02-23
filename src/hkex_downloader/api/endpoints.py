#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所API端点配置
"""

from typing import Any, Dict


class HKExEndpoints:
    """
    港交所API端点配置类
    """

    # 基础URL
    BASE_URL = "https://www1.hkexnews.hk"

    # API端点
    STOCK_SEARCH = "/search/prefix.do"  # 股票代码搜索
    DOCUMENT_SEARCH = "/search/titleSearchServlet.do"  # 文档搜索

    # 文档下载基础URL
    DOCUMENT_BASE_URL = "https://www1.hkexnews.hk"

    @classmethod
    def get_stock_search_url(cls) -> str:
        """
        获取股票搜索URL
        """
        return f"{cls.BASE_URL}{cls.STOCK_SEARCH}"

    @classmethod
    def get_document_search_url(cls) -> str:
        """
        获取文档搜索URL
        """
        return f"{cls.BASE_URL}{cls.DOCUMENT_SEARCH}"

    @classmethod
    def get_document_download_url(cls, file_path: str) -> str:
        """
        获取文档下载URL

        Args:
            file_path: 文档路径，如
                '/listedco/listconews/sehk/2024/1230/2024121201396_c.htm'

        Returns:
            完整的下载URL
        """
        if file_path.startswith("http"):
            return file_path

        if not file_path.startswith("/"):
            file_path = "/" + file_path

        return f"{cls.DOCUMENT_BASE_URL}{file_path}"


class DocumentTypes:
    """
    文档类型配置
    """

    # IPO相关文档
    IPO_PROSPECTUS = {
        "t1code": "91000",  # 申請版本、整體協調人公告及聆訊後資料集
        "t2Gcode": "-2",
        "t2code": "91200",  # 申請版本或相關材料
        "name": "IPO招股书",
        "description": "申请版本或相关材料",
    }

    # 业绩公告
    ANNUAL_RESULTS = {
        "t1code": "10000",  # 公告及通告
        "t2Gcode": "3",  # 财务业绩相关
        "t2code": "13300",  # 末期业绩
        "name": "年度业绩公告",
        "description": "末期业绩公告",
    }

    INTERIM_RESULTS = {
        "t1code": "10000",  # 公告及通告
        "t2Gcode": "3",  # 财务业绩相关
        "t2code": "13400",  # 中期业绩
        "name": "中期业绩公告",
        "description": "中期业绩公告",
    }

    # 其他常用文档类型
    QUARTERLY_RESULTS = {
        "t1code": "10000",
        "t2Gcode": "3",
        "t2code": "13600",  # 季度业绩
        "name": "季度业绩公告",
        "description": "季度业绩公告",
    }

    DIVIDEND_ANNOUNCEMENT = {
        "t1code": "10000",
        "t2Gcode": "3",
        "t2code": "13250",  # 股息或分派
        "name": "股息公告",
        "description": "股息或分派公告",
    }

    CONNECTED_TRANSACTIONS = {
        "t1code": "10000",
        "t2Gcode": "1",
        "t2code": "11200",  # 关连交易
        "name": "关连交易",
        "description": "关连交易公告",
    }

    DISCLOSEABLE_TRANSACTIONS = {
        "t1code": "10000",
        "t2Gcode": "6",
        "t2code": "16200",  # 须予披露的交易
        "name": "须予披露交易",
        "description": "须予披露的交易公告",
    }

    @classmethod
    def get_all_types(cls) -> Dict[str, Dict[str, Any]]:
        """
        获取所有文档类型
        """
        return {
            "ipo_prospectus": cls.IPO_PROSPECTUS,
            "annual_results": cls.ANNUAL_RESULTS,
            "interim_results": cls.INTERIM_RESULTS,
            "quarterly_results": cls.QUARTERLY_RESULTS,
            "dividend_announcement": cls.DIVIDEND_ANNOUNCEMENT,
            "connected_transactions": cls.CONNECTED_TRANSACTIONS,
            "discloseable_transactions": cls.DISCLOSEABLE_TRANSACTIONS,
        }

    @classmethod
    def get_type_by_name(cls, name: str) -> Dict[str, Any]:
        """
        根据名称获取文档类型配置

        Args:
            name: 文档类型名称，如 'ipo_prospectus', 'annual_results' 等

        Returns:
            文档类型配置字典

        Raises:
            ValueError: 如果文档类型不存在
        """
        all_types = cls.get_all_types()
        if name not in all_types:
            available_types = ", ".join(all_types.keys())
            raise ValueError(f"未知的文档类型: {name}. 可用类型: {available_types}")

        return all_types[name]


class SearchDefaults:
    """
    搜索默认参数配置
    """

    # 默认搜索参数
    DEFAULT_PARAMS = {
        "sortDir": "0",  # 降序
        "sortByOptions": "DateTime",  # 按时间排序
        "category": "0",
        "market": "SEHK",  # 港交所主板
        "stockId": "-1",  # 所有股票
        "documentType": "-1",  # 所有文档类型
        "title": "",  # 无标题过滤
        "searchType": "1",
        "rowRange": "200",  # 每页200条记录
        "lang": "zh",  # 中文
    }

    # 股票搜索默认参数
    STOCK_SEARCH_PARAMS = {
        "callback": "callback",
        "lang": "ZH",
        "type": "A",
        "market": "SEHK",
    }

    @classmethod
    def get_document_search_params(cls, **overrides: Any) -> Dict[str, str]:
        """
        获取文档搜索参数，支持覆盖默认值

        Args:
            **overrides: 要覆盖的参数

        Returns:
            合并后的参数字典
        """
        params = cls.DEFAULT_PARAMS.copy()
        params.update(overrides)
        return params

    @classmethod
    def get_stock_search_params(cls, **overrides: Any) -> Dict[str, str]:
        """
        获取股票搜索参数，支持覆盖默认值

        Args:
            **overrides: 要覆盖的参数

        Returns:
            合并后的参数字典
        """
        params = cls.STOCK_SEARCH_PARAMS.copy()
        params.update(overrides)
        return params
