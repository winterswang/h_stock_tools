#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据模型

定义港股财务报表相关的数据模型
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ReportType(str, Enum):
    """财务报表类型"""
    BALANCE_SHEET = "balance_sheet"  # 资产负债表
    INCOME_STATEMENT = "income_statement"  # 利润表
    CASH_FLOW = "cash_flow"  # 现金流量表
    FINANCIAL_INDICATORS = "financial_indicators"  # 财务指标


class ReportPeriod(str, Enum):
    """报告期类型"""
    ANNUAL = "annual"  # 年报
    INTERIM = "interim"  # 中报
    QUARTERLY = "quarterly"  # 季报


class FinancialData(BaseModel):
    """财务数据基础模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    report_date: str = Field(..., description="报告期")
    report_type: ReportType = Field(..., description="报表类型")
    report_period: ReportPeriod = Field(..., description="报告期类型")
    currency: str = Field(default="HKD", description="货币单位")
    data: Dict[str, Union[float, str, None]] = Field(..., description="财务数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    model_config = ConfigDict(use_enum_values=True)


class BalanceSheetData(FinancialData):
    """资产负债表数据模型"""
    report_type: ReportType = Field(default=ReportType.BALANCE_SHEET, description="报表类型")
    
    # 常用字段映射
    @property
    def total_assets(self) -> Optional[float]:
        """总资产"""
        return self.data.get('总资产') or self.data.get('total_assets')
    
    @property
    def total_liabilities(self) -> Optional[float]:
        """总负债"""
        return self.data.get('总负债') or self.data.get('total_liabilities')
    
    @property
    def total_equity(self) -> Optional[float]:
        """股东权益合计"""
        return self.data.get('股东权益合计') or self.data.get('total_equity')
    
    @property
    def current_assets(self) -> Optional[float]:
        """流动资产合计"""
        return self.data.get('流动资产合计') or self.data.get('current_assets')
    
    @property
    def current_liabilities(self) -> Optional[float]:
        """流动负债合计"""
        return self.data.get('流动负债合计') or self.data.get('current_liabilities')


class IncomeStatementData(FinancialData):
    """利润表数据模型"""
    report_type: ReportType = Field(default=ReportType.INCOME_STATEMENT, description="报表类型")
    
    # 常用字段映射
    @property
    def total_revenue(self) -> Optional[float]:
        """营业总收入"""
        return self.data.get('营业总收入') or self.data.get('total_revenue')
    
    @property
    def net_profit(self) -> Optional[float]:
        """净利润"""
        return self.data.get('净利润') or self.data.get('net_profit')
    
    @property
    def gross_profit(self) -> Optional[float]:
        """毛利润"""
        return self.data.get('毛利润') or self.data.get('gross_profit')
    
    @property
    def operating_profit(self) -> Optional[float]:
        """营业利润"""
        return self.data.get('营业利润') or self.data.get('operating_profit')
    
    @property
    def total_profit(self) -> Optional[float]:
        """利润总额"""
        return self.data.get('利润总额') or self.data.get('total_profit')


class CashFlowData(FinancialData):
    """现金流量表数据模型"""
    report_type: ReportType = Field(default=ReportType.CASH_FLOW, description="报表类型")
    
    # 常用字段映射
    @property
    def operating_cash_flow(self) -> Optional[float]:
        """经营活动现金流量净额"""
        return self.data.get('经营活动现金流量净额') or self.data.get('operating_cash_flow')
    
    @property
    def investing_cash_flow(self) -> Optional[float]:
        """投资活动现金流量净额"""
        return self.data.get('投资活动现金流量净额') or self.data.get('investing_cash_flow')
    
    @property
    def financing_cash_flow(self) -> Optional[float]:
        """筹资活动现金流量净额"""
        return self.data.get('筹资活动现金流量净额') or self.data.get('financing_cash_flow')
    
    @property
    def net_cash_flow(self) -> Optional[float]:
        """现金及现金等价物净增加额"""
        return self.data.get('现金及现金等价物净增加额') or self.data.get('net_cash_flow')


class FinancialIndicatorsData(FinancialData):
    """财务指标数据模型"""
    report_type: ReportType = Field(default=ReportType.FINANCIAL_INDICATORS, description="报表类型")
    
    # 常用指标映射
    @property
    def roe(self) -> Optional[float]:
        """净资产收益率"""
        return self.data.get('净资产收益率') or self.data.get('roe')
    
    @property
    def roa(self) -> Optional[float]:
        """总资产收益率"""
        return self.data.get('总资产收益率') or self.data.get('roa')
    
    @property
    def current_ratio(self) -> Optional[float]:
        """流动比率"""
        return self.data.get('流动比率') or self.data.get('current_ratio')
    
    @property
    def debt_to_equity_ratio(self) -> Optional[float]:
        """资产负债率"""
        return self.data.get('资产负债率') or self.data.get('debt_to_equity_ratio')
    
    @property
    def eps(self) -> Optional[float]:
        """每股收益"""
        return self.data.get('每股收益') or self.data.get('eps')
    
    @property
    def pe_ratio(self) -> Optional[float]:
        """市盈率"""
        return self.data.get('市盈率') or self.data.get('pe_ratio')
    
    @property
    def pb_ratio(self) -> Optional[float]:
        """市净率"""
        return self.data.get('市净率') or self.data.get('pb_ratio')


class FinancialDataCollection(BaseModel):
    """财务数据集合"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    report_type: Optional[ReportType] = Field(None, description="报表类型")
    report_period: Optional[ReportPeriod] = Field(None, description="报告期类型")
    data_list: List[FinancialData] = Field(default_factory=list, description="财务数据列表")
    raw_dataframe: Optional[Any] = Field(None, description="原始DataFrame数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def add_data(self, data: FinancialData):
        """添加财务数据"""
        self.data_list.append(data)
    
    def get_data_by_type(self, report_type: ReportType) -> List[FinancialData]:
        """根据报表类型获取数据"""
        return [data for data in self.data_list if data.report_type == report_type]
    
    def get_data_by_period(self, report_period: ReportPeriod) -> List[FinancialData]:
        """根据报告期类型获取数据"""
        return [data for data in self.data_list if data.report_period == report_period]
    
    def get_latest_data(self, report_type: Optional[ReportType] = None) -> Optional[FinancialData]:
        """获取最新的财务数据"""
        filtered_data = self.data_list
        if report_type:
            filtered_data = self.get_data_by_type(report_type)
        
        if not filtered_data:
            return None
        
        return max(filtered_data, key=lambda x: x.report_date)


class FinancialDataRequest(BaseModel):
    """财务数据请求模型"""
    stock_code: str = Field(..., description="股票代码")
    report_type: ReportType = Field(..., description="报表类型")
    report_period: Optional[ReportPeriod] = Field(None, description="报告期类型")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    limit: Optional[int] = Field(default=10, description="返回数据条数限制")
    
    model_config = ConfigDict(use_enum_values=True)


class FinancialDataResponse(BaseModel):
    """财务数据响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="", description="响应消息")
    data: Optional[FinancialDataCollection] = Field(None, description="财务数据")
    total_count: int = Field(default=0, description="总数据条数")
    
    model_config = ConfigDict(use_enum_values=True)