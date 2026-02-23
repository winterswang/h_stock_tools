#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档搜索服务

提供港交所文档搜索功能
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ..api.client import HKExClient
from ..api.endpoints import DocumentTypes
from ..models.company import Document
from ..models.search import SearchRequest, SearchResponse
from ..utils.logger import LoggerMixin
from .stock_resolver import StockResolver


class DocumentSearcher(LoggerMixin):
    """
    文档搜索服务

    提供各种类型文档的搜索功能
    """

    def __init__(
        self,
        client: Optional[HKExClient] = None,
        stock_resolver: Optional[StockResolver] = None,
    ):
        """
        初始化文档搜索服务

        Args:
            client: HKEx API客户端
            stock_resolver: 股票解析服务
        """
        self.client = client or HKExClient()
        self.stock_resolver = stock_resolver or StockResolver(self.client)

    def search_ipo_prospectus(
        self, from_date: date, to_date: date, stock_code: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索IPO招股书

        Args:
            from_date: 开始日期
            to_date: 结束日期
            stock_code: 股票代码，可选

        Returns:
            搜索响应
        """
        stock_id = None
        if stock_code:
            stock_id = self.stock_resolver.resolve_stock_id(stock_code)
            if not stock_id:
                self.logger.warning(f"无法找到股票代码 {stock_code} 对应的股票ID")

        doc_type = DocumentTypes.IPO_PROSPECTUS

        request = SearchRequest(
            from_date=from_date,
            to_date=to_date,
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.client.search_documents(request)

    def search_annual_results(
        self, from_date: date, to_date: date, stock_code: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索年度业绩公告

        Args:
            from_date: 开始日期
            to_date: 结束日期
            stock_code: 股票代码，可选

        Returns:
            搜索响应
        """
        stock_id = None
        if stock_code:
            stock_id = self.stock_resolver.resolve_stock_id(stock_code)
            if not stock_id:
                self.logger.warning(f"无法找到股票代码 {stock_code} 对应的股票ID")

        doc_type = DocumentTypes.ANNUAL_RESULTS

        request = SearchRequest(
            from_date=from_date,
            to_date=to_date,
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.client.search_documents(request)

    def search_interim_results(
        self, from_date: date, to_date: date, stock_code: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索中期业绩公告

        Args:
            from_date: 开始日期
            to_date: 结束日期
            stock_code: 股票代码，可选

        Returns:
            搜索响应
        """
        stock_id = None
        if stock_code:
            stock_id = self.stock_resolver.resolve_stock_id(stock_code)
            if not stock_id:
                self.logger.warning(f"无法找到股票代码 {stock_code} 对应的股票ID")

        doc_type = DocumentTypes.INTERIM_RESULTS

        request = SearchRequest(
            from_date=from_date,
            to_date=to_date,
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.client.search_documents(request)

    def search_quarterly_results(
        self, from_date: date, to_date: date, stock_code: Optional[str] = None
    ) -> SearchResponse:
        """
        搜索季度业绩公告

        Args:
            from_date: 开始日期
            to_date: 结束日期
            stock_code: 股票代码，可选

        Returns:
            搜索响应
        """
        stock_id = None
        if stock_code:
            stock_id = self.stock_resolver.resolve_stock_id(stock_code)
            if not stock_id:
                self.logger.warning(f"无法找到股票代码 {stock_code} 对应的股票ID")

        doc_type = DocumentTypes.QUARTERLY_RESULTS

        request = SearchRequest(
            from_date=from_date,
            to_date=to_date,
            stock_id=stock_id or "-1",
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
        )

        return self.client.search_documents(request)

    def search_custom_documents(
        self,
        from_date: date,
        to_date: date,
        t1_code: str,
        t2_gcode: str,
        t2_code: str,
        stock_code: Optional[str] = None,
        title_keyword: Optional[str] = None,
    ) -> SearchResponse:
        """
        自定义文档搜索

        Args:
            from_date: 开始日期
            to_date: 结束日期
            t1_code: 一级分类代码
            t2_gcode: 二级分组代码
            t2_code: 二级分类代码
            stock_code: 股票代码，可选
            title_keyword: 标题关键词，可选

        Returns:
            搜索响应
        """
        stock_id = None
        if stock_code:
            stock_id = self.stock_resolver.resolve_stock_id(stock_code)
            if not stock_id:
                self.logger.warning(f"无法找到股票代码 {stock_code} 对应的股票ID")

        request = SearchRequest(
            from_date=from_date,
            to_date=to_date,
            stock_id=stock_id or "-1",
            t1_code=t1_code,
            t2_gcode=t2_gcode,
            t2_code=t2_code,
            title=title_keyword or "",
        )

        return self.client.search_documents(request)

    def search_by_document_type(
        self,
        from_date: date,
        to_date: date,
        document_type: str,
        stock_code: Optional[str] = None,
    ) -> SearchResponse:
        """
        根据文档类型搜索

        Args:
            from_date: 开始日期
            to_date: 结束日期
            document_type: 文档类型名称，如 'ipo_prospectus', 'annual_results' 等
            stock_code: 股票代码，可选

        Returns:
            搜索响应

        Raises:
            ValueError: 如果文档类型不支持
        """
        # 获取文档类型配置
        try:
            doc_type = DocumentTypes.get_type_by_name(document_type)
        except ValueError as e:
            raise ValueError(f"不支持的文档类型: {document_type}. {e}")

        return self.search_custom_documents(
            from_date=from_date,
            to_date=to_date,
            t1_code=doc_type["t1code"],
            t2_gcode=doc_type["t2Gcode"],
            t2_code=doc_type["t2code"],
            stock_code=stock_code,
        )

    def search_company_documents(
        self,
        stock_code: str,
        from_date: date,
        to_date: date,
        document_types: Optional[List[str]] = None,
    ) -> Dict[str, SearchResponse]:
        """
        搜索特定公司的所有文档

        Args:
            stock_code: 股票代码
            from_date: 开始日期
            to_date: 结束日期
            document_types: 文档类型列表，如果为None则搜索所有类型

        Returns:
            文档类型到搜索响应的映射
        """
        if document_types is None:
            document_types = [
                "ipo_prospectus",
                "annual_results",
                "interim_results",
            ]

        results = {}

        for doc_type in document_types:
            try:
                response = self.search_by_document_type(
                    from_date=from_date,
                    to_date=to_date,
                    document_type=doc_type,
                    stock_code=stock_code,
                )
                results[doc_type] = response
            except Exception as e:
                self.logger.error(f"搜索 {stock_code} 的 {doc_type} 文档失败: {e}")
                results[doc_type] = SearchResponse(sort_list=None)

        return results

    def get_recent_documents(
        self, document_type: str, days: int = 30, limit: int = 50
    ) -> SearchResponse:
        """
        获取最近的文档

        Args:
            document_type: 文档类型
            days: 最近天数
            limit: 限制数量

        Returns:
            搜索响应
        """
        to_date = date.today()
        from_date = date.today() - timedelta(days=days)

        response = self.search_by_document_type(
            from_date=from_date, to_date=to_date, document_type=document_type
        )

        # 限制返回数量
        if len(response.documents) > limit:
            response.documents = response.documents[:limit]
            response.loaded_record = min(response.loaded_record, limit)

        return response

    def filter_pdf_documents(self, response: SearchResponse) -> List[Document]:
        """
        过滤出PDF文档

        Args:
            response: 搜索响应

        Returns:
            PDF文档列表
        """
        return response.pdf_documents

    def group_documents_by_company(
        self, response: SearchResponse
    ) -> Dict[str, List[Document]]:
        """
        按公司分组文档

        Args:
            response: 搜索响应

        Returns:
            公司代码到文档列表的映射
        """
        grouped = {}

        for doc in response.documents:
            stock_code = doc.stock_code
            if stock_code not in grouped:
                grouped[stock_code] = []
            grouped[stock_code].append(doc)

        return grouped

    def get_document_statistics(
        self, response: SearchResponse
    ) -> Dict[str, Any]:
        """
        获取文档统计信息

        Args:
            response: 搜索响应

        Returns:
            统计信息
        """
        total_docs = len(response.documents)
        pdf_docs = len(response.pdf_documents)
        unique_companies = len(response.unique_companies)

        # 按文件类型统计
        file_types = {}
        for doc in response.documents:
            file_type = doc.file_type or "Unknown"
            file_types[file_type] = file_types.get(file_type, 0) + 1

        # 按公司统计
        company_stats = {}
        for doc in response.documents:
            company = f"{doc.stock_code} - {doc.stock_name}"
            company_stats[company] = company_stats.get(company, 0) + 1

        return {
            "total_documents": total_docs,
            "pdf_documents": pdf_docs,
            "unique_companies": unique_companies,
            "file_types": file_types,
            "top_companies": dict(
                sorted(
                    company_stats.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ),
            "date_range": {
                "earliest": min(
                    (
                        doc.parsed_datetime
                        for doc in response.documents
                        if doc.parsed_datetime
                    ),
                    default=None,
                ),
                "latest": max(
                    (
                        doc.parsed_datetime
                        for doc in response.documents
                        if doc.parsed_datetime
                    ),
                    default=None,
                ),
            },
        }
