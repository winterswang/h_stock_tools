#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索请求和响应数据模型
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from ..utils.logger import get_logger
from .company import Document

logger = get_logger("hkex_downloader.models.search")


class SearchRequest(BaseModel):
    """
    搜索请求参数模型
    """

    # 基本搜索参数
    from_date: date = Field(..., description="开始日期")
    to_date: date = Field(..., description="结束日期")
    stock_id: Optional[str] = Field(default="-1", description="股票ID，-1表示所有")
    market: str = Field(default="SEHK", description="市场代码")

    # 文档分类参数
    t1_code: str = Field(..., description="一级分类代码")
    t2_gcode: str = Field(..., description="二级分组代码")
    t2_code: str = Field(..., description="二级分类代码")

    # 搜索选项
    title: str = Field(default="", description="标题关键词")
    search_type: str = Field(default="1", description="搜索类型")
    category: str = Field(default="0", description="分类")
    document_type: str = Field(default="-1", description="文档类型")

    # 排序和分页
    sort_dir: str = Field(default="0", description="排序方向，0=降序，1=升序")
    sort_by_options: str = Field(default="DateTime", description="排序字段")
    row_range: int = Field(default=200, description="返回记录数")
    lang: str = Field(default="zh", description="语言")

    @validator("from_date", "to_date")
    def validate_dates(cls, v: Union[date, str]) -> date:
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y%m%d").date()
            except ValueError:
                raise ValueError("日期格式必须是 YYYYMMDD")
        return v

    @validator("to_date")
    def validate_date_range(cls, v: date, values: Dict[str, Any]) -> date:
        if "from_date" in values and v < values["from_date"]:
            raise ValueError("结束日期不能早于开始日期")
        return v

    def to_query_params(self) -> Dict[str, str]:
        """
        转换为查询参数字典
        """
        return {
            "sortDir": self.sort_dir,
            "sortByOptions": self.sort_by_options,
            "category": self.category,
            "market": self.market,
            "stockId": self.stock_id or "-1",
            "documentType": self.document_type,
            "fromDate": self.from_date.strftime("%Y%m%d"),
            "toDate": self.to_date.strftime("%Y%m%d"),
            "title": self.title,
            "searchType": self.search_type,
            "t1code": self.t1_code,
            "t2Gcode": self.t2_gcode,
            "t2code": self.t2_code,
            "rowRange": str(self.row_range),
            "lang": self.lang,
        }


class SearchResponse(BaseModel):
    """
    搜索响应数据模型
    """

    documents: List[Document] = Field(default_factory=list, description="文档列表")
    has_next_row: bool = Field(default=False, description="是否有下一页")
    loaded_record: int = Field(default=0, description="已加载记录数")
    record_cnt: int = Field(default=0, description="总记录数")
    row_range: int = Field(default=200, description="每页记录数")
    lang: str = Field(default="C", description="语言")
    sort_list: Optional[str] = Field(None, description="排序列表")

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "SearchResponse":
        """
        从API响应数据创建SearchResponse对象
        """
        documents = []

        # 解析文档列表
        result_data = data.get("result")
        if result_data:
            # 如果result是字符串，需要再次解析JSON
            if isinstance(result_data, str):
                try:
                    import json

                    result_data = json.loads(result_data)
                except json.JSONDecodeError:
                    logger.error(f"无法解析result字符串: {result_data[:100]}...")
                    result_data = []

            # 现在result_data应该是一个列表
            if isinstance(result_data, list):
                for item in result_data:
                    try:
                        doc = Document(
                            news_id=item.get("NEWS_ID", ""),
                            stock_code=item.get("STOCK_CODE", ""),
                            stock_name=item.get("STOCK_NAME", ""),
                            title=item.get("TITLE", ""),
                            file_type=item.get("FILE_TYPE", ""),
                            file_info=item.get("FILE_INFO", ""),
                            file_link=item.get("FILE_LINK", ""),
                            date_time=item.get("DATE_TIME", ""),
                            short_text=item.get("SHORT_TEXT", ""),
                            long_text=item.get("LONG_TEXT", ""),
                            total_count=item.get("TOTAL_COUNT", ""),
                            t1_code=item.get("T1_CODE"),
                            t2_code=item.get("T2_CODE"),
                            t2_gcode=item.get("T2_GCODE"),
                        )
                        documents.append(doc)
                    except Exception as e:
                        # 记录解析错误但继续处理其他文档
                        logger.error(f"解析文档时出错: {e}, 数据: {item}")
                        continue

        return cls(
            documents=documents,
            has_next_row=data.get("hasNextRow", False),
            loaded_record=data.get("loadedRecord", 0),
            record_cnt=data.get("recordCnt", 0),
            row_range=data.get("rowRange", 200),
            lang=data.get("lang", "C"),
            sort_list=data.get("sortList"),
        )

    @property
    def pdf_documents(self) -> List[Document]:
        """
        获取所有PDF文档
        """
        return [doc for doc in self.documents if doc.is_pdf]

    @property
    def unique_companies(self) -> List[str]:
        """
        获取所有唯一的公司代码
        """
        return list(set(doc.stock_code for doc in self.documents))

    def filter_by_company(self, stock_code: str) -> List[Document]:
        """
        按公司代码过滤文档
        """
        return [doc for doc in self.documents if doc.stock_code == stock_code]

    def filter_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Document]:
        """
        按日期范围过滤文档
        """
        filtered = []
        for doc in self.documents:
            parsed_date = doc.parsed_datetime
            if parsed_date:
                doc_date = parsed_date.date()
                if start_date <= doc_date <= end_date:
                    filtered.append(doc)
        return filtered


class StockSearchRequest(BaseModel):
    """
    股票代码搜索请求模型
    """

    name: str = Field(..., description="股票代码或名称")
    lang: str = Field(default="ZH", description="语言")
    type: str = Field(default="A", description="搜索类型")
    market: str = Field(default="SEHK", description="市场代码")

    def to_query_params(self) -> Dict[str, str]:
        """
        转换为查询参数字典
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        return {
            "callback": "callback",
            "lang": self.lang,
            "type": self.type,
            "name": self.name,
            "market": self.market,
            "_": timestamp,
        }


class StockSearchResponse(BaseModel):
    """
    股票搜索响应模型
    """

    companies: List[Dict[str, Any]] = Field(
        default_factory=list, description="公司列表"
    )

    @classmethod
    def from_jsonp_response(cls, jsonp_text: str) -> "StockSearchResponse":
        """
        从JSONP响应文本创建StockSearchResponse对象
        """
        import json
        import re

        # 提取JSON部分
        match = re.search(r"callback\((.*)\)", jsonp_text)
        if not match:
            return cls()

        try:
            data = json.loads(match.group(1))
            # API返回格式:
            # {"more":"1","stockInfo":[{"stockId":7609,"code":"00700","name":"騰訊控股"}]}
            if isinstance(data, dict) and "stockInfo" in data:
                companies = data["stockInfo"]
                # 转换字段名以匹配我们的期望格式
                formatted_companies = []
                for company in companies:
                    formatted_companies.append(
                        {
                            "id": str(company.get("stockId", "")),
                            "code": company.get("code", ""),
                            "name": company.get("name", ""),
                        }
                    )
                return cls(companies=formatted_companies)
            elif isinstance(data, list):
                return cls(companies=data)
            else:
                return cls()
        except json.JSONDecodeError:
            return cls()

    def get_stock_id(self, stock_code: str) -> Optional[str]:
        """
        根据股票代码获取股票ID
        """
        for company in self.companies:
            if company.get("code") == stock_code:
                return company.get("id")
        return None
