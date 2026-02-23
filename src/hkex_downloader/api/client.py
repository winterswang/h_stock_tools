#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所API客户端
"""

import json
from datetime import datetime
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.company import Document
from ..models.financial import (
    FinancialDataRequest,
    FinancialDataResponse,
    ReportType,
)
from ..models.search import (
    SearchRequest,
    SearchResponse,
    StockSearchRequest,
    StockSearchResponse,
)
from .endpoints import DocumentTypes, HKExEndpoints


class HKExClient:
    """
    港交所API客户端

    提供与港交所网站API交互的功能，包括：
    - 股票代码搜索
    - 文档搜索
    - 文档下载
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        user_agent: Optional[str] = None,
    ):
        """
        初始化API客户端

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            backoff_factor: 重试间隔因子
            user_agent: 自定义User-Agent
        """
        self.timeout = timeout
        self.session = requests.Session()

        # 设置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置请求头
        default_user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )

        self.session.headers.update(
            {
                "User-Agent": user_agent or default_user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
            }
        )

    def search_stock(self, stock_code: str) -> StockSearchResponse:
        """
        搜索股票信息

        Args:
            stock_code: 股票代码，如 '00700'

        Returns:
            股票搜索响应

        Raises:
            requests.RequestException: 请求异常
        """
        request = StockSearchRequest(name=stock_code)
        url = HKExEndpoints.get_stock_search_url()
        params = request.to_query_params()

        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout
            )
            response.raise_for_status()

            # 解析JSONP响应
            return StockSearchResponse.from_jsonp_response(response.text)

        except requests.RequestException as e:
            raise requests.RequestException(f"股票搜索失败: {e}")

    def get_stock_id(self, stock_code: str) -> Optional[str]:
        """
        根据股票代码获取股票ID

        Args:
            stock_code: 股票代码，如 '00700'

        Returns:
            股票ID，如果未找到则返回None
        """
        try:
            response = self.search_stock(stock_code)
            return response.get_stock_id(stock_code)
        except Exception:
            return None

    def search_documents(self, request: SearchRequest) -> SearchResponse:
        """
        搜索文档

        Args:
            request: 搜索请求参数

        Returns:
            搜索响应

        Raises:
            requests.RequestException: 请求异常
        """
        url = HKExEndpoints.get_document_search_url()
        params = request.to_query_params()

        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout
            )
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()
            return SearchResponse.from_api_response(data)

        except requests.RequestException as e:
            raise requests.RequestException(f"文档搜索失败: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"响应解析失败: {e}")

    def search_ipo_documents(
        self, from_date: str, to_date: str, stock_id: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索IPO招股书文档

        Args:
            from_date: 开始日期，格式 'YYYYMMDD'
            to_date: 结束日期，格式 'YYYYMMDD'
            stock_id: 股票ID，可选

        Returns:
            搜索响应
        """
        doc_type = DocumentTypes.IPO_PROSPECTUS

        request = SearchRequest(
            from_date=datetime.strptime(from_date, "%Y%m%d").date(),
            to_date=datetime.strptime(to_date, "%Y%m%d").date(),
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.search_documents(request)

    def search_annual_results(
        self, from_date: str, to_date: str, stock_id: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索年度业绩公告

        Args:
            from_date: 开始日期，格式 'YYYYMMDD'
            to_date: 结束日期，格式 'YYYYMMDD'
            stock_id: 股票ID，可选

        Returns:
            搜索响应
        """
        doc_type = DocumentTypes.ANNUAL_RESULTS

        request = SearchRequest(
            from_date=datetime.strptime(from_date, "%Y%m%d").date(),
            to_date=datetime.strptime(to_date, "%Y%m%d").date(),
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.search_documents(request)

    def search_interim_results(
        self, from_date: str, to_date: str, stock_id: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索中期业绩公告

        Args:
            from_date: 开始日期，格式 'YYYYMMDD'
            to_date: 结束日期，格式 'YYYYMMDD'
            stock_id: 股票ID，可选

        Returns:
            搜索响应
        """
        doc_type = DocumentTypes.INTERIM_RESULTS

        request = SearchRequest(
            from_date=datetime.strptime(from_date, "%Y%m%d").date(),
            to_date=datetime.strptime(to_date, "%Y%m%d").date(),
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.search_documents(request)

    def search_quarterly_results(
        self, from_date: str, to_date: str, stock_id: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索季度业绩公告

        Args:
            from_date: 开始日期，格式 'YYYYMMDD'
            to_date: 结束日期，格式 'YYYYMMDD'
            stock_id: 股票ID，可选

        Returns:
            搜索响应
        """
        doc_type = DocumentTypes.QUARTERLY_RESULTS

        request = SearchRequest(
            from_date=datetime.strptime(from_date, "%Y%m%d").date(),
            to_date=datetime.strptime(to_date, "%Y%m%d").date(),
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.search_documents(request)

    def download_document(
        self, document: Document, save_path: str, chunk_size: int = 8192
    ) -> bool:
        """
        下载文档

        Args:
            document: 文档对象
            save_path: 保存路径
            chunk_size: 下载块大小

        Returns:
            下载是否成功

        Raises:
            requests.RequestException: 下载异常
        """
        url = document.full_file_url

        try:
            with self.session.get(
                url, stream=True, timeout=self.timeout
            ) as response:
                response.raise_for_status()

                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

                return True

        except requests.RequestException as e:
            raise requests.RequestException(f"文档下载失败: {e}")
        except IOError as e:
            raise IOError(f"文件保存失败: {e}")

    def get_document_content(self, document: Document) -> bytes:
        """
        获取文档内容（不保存到文件）

        Args:
            document: 文档对象

        Returns:
            文档内容字节

        Raises:
            requests.RequestException: 请求异常
        """
        url = document.full_file_url

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content

        except requests.RequestException as e:
            raise requests.RequestException(f"获取文档内容失败: {e}")

    def get_financial_data(self, request: FinancialDataRequest) -> FinancialDataResponse:
        """
        获取财务数据
        
        Args:
            request: 财务数据请求
            
        Returns:
            财务数据响应
        """
        from ..services.financial_service import FinancialDataService
        
        financial_service = FinancialDataService()
        return financial_service.get_financial_report(request)
    
    def get_balance_sheet(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse:
        """
        获取资产负债表数据
        
        Args:
            stock_code: 股票代码
            limit: 数据条数限制
            
        Returns:
            财务数据响应
        """
        request = FinancialDataRequest(
            stock_code=stock_code,
            report_type=ReportType.BALANCE_SHEET,
            limit=limit
        )
        return self.get_financial_data(request)
    
    def get_income_statement(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse:
        """
        获取利润表数据
        
        Args:
            stock_code: 股票代码
            limit: 数据条数限制
            
        Returns:
            财务数据响应
        """
        request = FinancialDataRequest(
            stock_code=stock_code,
            report_type=ReportType.INCOME_STATEMENT,
            limit=limit
        )
        return self.get_financial_data(request)
    
    def get_cash_flow(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse:
        """
        获取现金流量表数据
        
        Args:
            stock_code: 股票代码
            limit: 数据条数限制
            
        Returns:
            财务数据响应
        """
        request = FinancialDataRequest(
            stock_code=stock_code,
            report_type=ReportType.CASH_FLOW,
            limit=limit
        )
        return self.get_financial_data(request)
    
    def get_financial_indicators(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse:
        """
        获取财务指标数据
        
        Args:
            stock_code: 股票代码
            limit: 数据条数限制
            
        Returns:
            财务数据响应
        """
        request = FinancialDataRequest(
            stock_code=stock_code,
            report_type=ReportType.FINANCIAL_INDICATORS,
            limit=limit
        )
        return self.get_financial_data(request)
    
    def get_all_financial_data(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse:
        """
        获取所有类型的财务数据
        
        Args:
            stock_code: 股票代码
            limit: 每种类型的数据条数限制
            
        Returns:
            财务数据响应
        """
        from ..services.financial_service import FinancialDataService
        
        financial_service = FinancialDataService()
        return financial_service.get_all_financial_data(stock_code, limit)

    def close(self):
        """
        关闭会话
        """
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
