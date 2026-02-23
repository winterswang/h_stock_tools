#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公司和文档数据模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class Company(BaseModel):
    """
    港交所上市公司信息模型
    """

    stock_code: str = Field(..., description="股票代码，如 '00700'")
    stock_id: Optional[str] = Field(None, description="港交所内部股票ID")
    stock_name: str = Field(..., description="公司名称")
    market: str = Field(default="SEHK", description="市场代码")

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        if not v or len(v) != 5:
            raise ValueError('股票代码必须是5位数字，如 "00700"')
        if not v.isdigit():
            raise ValueError("股票代码必须是数字")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Document(BaseModel):
    """
    港交所文档信息模型
    """

    news_id: str = Field(..., description="新闻ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="公司名称")
    title: str = Field(..., description="文档标题")
    file_type: Optional[str] = Field(None, description="文件类型，如 'PDF'")
    file_info: Optional[str] = Field(None, description="文件信息，如文件大小")
    file_link: str = Field(..., description="文件下载链接")
    date_time: str = Field(..., description="发布时间")
    short_text: Optional[str] = Field(None, description="简短描述")
    long_text: Optional[str] = Field(None, description="详细描述")
    total_count: Optional[str] = Field(None, description="总记录数")

    # 文档分类相关
    t1_code: Optional[str] = Field(None, description="一级分类代码")
    t2_code: Optional[str] = Field(None, description="二级分类代码")
    t2_gcode: Optional[str] = Field(None, description="二级分组代码")

    @property
    def full_file_url(self) -> str:
        """
        获取完整的文件下载URL
        """
        if self.file_link.startswith("http"):
            return self.file_link
        return f"https://www1.hkexnews.hk{self.file_link}"

    @property
    def is_pdf(self) -> bool:
        """
        判断是否为PDF文件 - 只检查文件链接后缀
        """
        # 只有.pdf后缀的文件才是PDF
        if self.file_link and self.file_link.lower().endswith(".pdf"):
            return True
        return False

    @property
    def parsed_datetime(self) -> Optional[datetime]:
        """
        解析发布时间为datetime对象
        """
        try:
            # 港交所时间格式: "12/12/2024 22:29"
            return datetime.strptime(self.date_time, "%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return None

    @property
    def file_size_mb(self) -> Optional[float]:
        """
        解析文件大小（MB）
        """
        if not self.file_info:
            return None

        try:
            # 解析如 "10MB", "多檔案" 等格式
            if "MB" in self.file_info:
                size_str = self.file_info.replace("MB", "").strip()
                return float(size_str)
        except (ValueError, TypeError):
            pass

        return None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DocumentType:
    """
    文档类型常量
    """

    # IPO相关
    IPO_PROSPECTUS = "91200"  # 申请版本或相关材料

    # 业绩公告
    ANNUAL_RESULTS = "13300"  # 末期业绩
    INTERIM_RESULTS = "13400"  # 中期业绩

    # 其他常用类型
    ANNOUNCEMENTS = "10000"  # 公告及通告
    CIRCULARS = "20000"  # 通函
    LISTING_DOCUMENTS = "30000"  # 上市文件
    FINANCIAL_STATEMENTS = "40000"  # 財務報表/環境、社會及管治資料


class DocumentCategory:
    """
    文档分类常量
    """

    # t1code 一级分类
    ANNOUNCEMENTS_AND_NOTICES = "10000"  # 公告及通告
    CIRCULARS = "20000"  # 通函
    LISTING_DOCUMENTS = "30000"  # 上市文件
    FINANCIAL_REPORTS = "40000"  # 財務報表/環境、社會及管治資料
    IPO_DOCUMENTS = "91000"  # 申請版本、整體協調人公告及聆訊後資料集

    # t2Gcode 二级分组
    FINANCIAL_RESULTS = "3"  # 财务业绩相关
    IPO_RELATED = "-2"  # IPO相关
