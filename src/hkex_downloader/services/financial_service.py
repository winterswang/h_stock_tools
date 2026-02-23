#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据服务

基于akshare提供港股财务数据获取功能
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import akshare as ak
import pandas as pd
from pandas import DataFrame

from ..models.financial import (
    BalanceSheetData,
    CashFlowData,
    FinancialData,
    FinancialDataCollection,
    FinancialDataRequest,
    FinancialDataResponse,
    FinancialIndicatorsData,
    IncomeStatementData,
    ReportPeriod,
    ReportType,
)
from ..utils.logger import get_logger


class FinancialDataService:
    """
    财务数据服务类
    
    提供港股财务数据获取功能，包括：
    - 资产负债表
    - 利润表
    - 现金流量表
    - 财务指标
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化财务数据服务
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger or get_logger(__name__)
        
        # 字段映射字典
        self._field_mappings = self._init_field_mappings()
    
    def _init_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        初始化字段映射字典
        
        Returns:
            字段映射字典
        """
        return {
            "balance_sheet": {
                "总资产": "total_assets",
                "总负债": "total_liabilities", 
                "股东权益合计": "total_equity",
                "流动资产合计": "current_assets",
                "流动负债合计": "current_liabilities",
                "非流动资产合计": "non_current_assets",
                "非流动负债合计": "non_current_liabilities",
                "货币资金": "cash_and_equivalents",
                "应收账款": "accounts_receivable",
                "存货": "inventory",
                "固定资产": "fixed_assets",
                "无形资产": "intangible_assets",
                "应付账款": "accounts_payable",
                "短期借款": "short_term_debt",
                "长期借款": "long_term_debt",
                "实收资本": "paid_in_capital",
                "未分配利润": "retained_earnings"
            },
            "income_statement": {
                "营业总收入": "total_revenue",
                "营业收入": "operating_revenue",
                "营业成本": "operating_costs",
                "毛利润": "gross_profit",
                "营业利润": "operating_profit",
                "利润总额": "total_profit",
                "净利润": "net_profit",
                "销售费用": "selling_expenses",
                "管理费用": "administrative_expenses",
                "财务费用": "financial_expenses",
                "研发费用": "rd_expenses",
                "所得税费用": "income_tax_expense",
                "基本每股收益": "basic_eps",
                "稀释每股收益": "diluted_eps"
            },
            "cash_flow": {
                "经营活动现金流量净额": "operating_cash_flow",
                "投资活动现金流量净额": "investing_cash_flow",
                "筹资活动现金流量净额": "financing_cash_flow",
                "现金及现金等价物净增加额": "net_cash_flow",
                "销售商品、提供劳务收到的现金": "cash_from_sales",
                "购买商品、接受劳务支付的现金": "cash_paid_for_goods",
                "支付给职工以及为职工支付的现金": "cash_paid_to_employees",
                "支付的各项税费": "taxes_paid",
                "收回投资收到的现金": "cash_from_investments",
                "取得投资收益收到的现金": "investment_income_received",
                "购建固定资产、无形资产和其他长期资产支付的现金": "capex_cash_paid",
                "吸收投资收到的现金": "cash_from_equity_financing",
                "取得借款收到的现金": "cash_from_borrowing",
                "偿还债务支付的现金": "debt_repayment",
                "分配股利、利润或偿付利息支付的现金": "dividends_and_interest_paid"
            },
            "financial_indicators": {
                "净资产收益率": "roe",
                "总资产收益率": "roa",
                "流动比率": "current_ratio",
                "速动比率": "quick_ratio",
                "资产负债率": "debt_to_equity_ratio",
                "每股收益": "eps",
                "每股净资产": "book_value_per_share",
                "市盈率": "pe_ratio",
                "市净率": "pb_ratio",
                "毛利率": "gross_margin",
                "净利率": "net_margin",
                "营业利润率": "operating_margin",
                "总资产周转率": "asset_turnover",
                "应收账款周转率": "receivables_turnover",
                "存货周转率": "inventory_turnover"
            }
        }
    
    def _convert_stock_code(self, stock_code: str) -> str:
        """
        转换股票代码格式
        
        Args:
            stock_code: 原始股票代码
            
        Returns:
            转换后的股票代码
        """
        # 根据调试结果，akshare港股接口需要标准的5位格式(如00700)
        # 确保股票代码是5位数，前面补0
        if len(stock_code) < 5:
            return stock_code.zfill(5)
        return stock_code
    
    def _normalize_dataframe(self, df: DataFrame, report_type: str) -> DataFrame:
        """
        标准化DataFrame数据
        
        Args:
            df: 原始数据
            report_type: 报表类型
            
        Returns:
            标准化后的数据
        """
        if df.empty:
            return df
        
        # 复制数据避免修改原始数据
        normalized_df = df.copy()
        
        # 获取字段映射
        field_mapping = self._field_mappings.get(report_type, {})
        
        # 重命名列
        for chinese_name, english_name in field_mapping.items():
            if chinese_name in normalized_df.columns:
                normalized_df[english_name] = normalized_df[chinese_name]
        
        # 处理数值列
        numeric_columns = normalized_df.select_dtypes(include=['object']).columns
        for col in numeric_columns:
            if col not in ['股票代码', 'stock_code', '股票名称', 'stock_name', '报告期', 'report_date']:
                normalized_df[col] = pd.to_numeric(normalized_df[col], errors='coerce')
        
        return normalized_df
    
    def _dataframe_to_financial_data(
        self, 
        df: DataFrame, 
        stock_code: str, 
        report_type: ReportType,
        report_period: ReportPeriod = ReportPeriod.ANNUAL
    ) -> List[FinancialData]:
        """
        将DataFrame转换为FinancialData列表
        
        Args:
            df: 数据框
            stock_code: 股票代码
            report_type: 报表类型
            report_period: 报告期类型
            
        Returns:
            FinancialData列表
        """
        if df.empty:
            return []
        
        financial_data_list = []
        
        for _, row in df.iterrows():
            # 构建数据字典
            data_dict = {}
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    data_dict[col] = value
            
            # 获取报告期
            report_date = str(row.get('报告期', row.get('report_date', datetime.now().strftime('%Y-%m-%d'))))
            
            # 获取股票名称
            stock_name = str(row.get('股票名称', row.get('stock_name', '')))
            
            # 根据报表类型创建相应的数据模型
            if report_type == ReportType.BALANCE_SHEET:
                financial_data = BalanceSheetData(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    report_date=report_date,
                    report_period=report_period,
                    data=data_dict
                )
            elif report_type == ReportType.INCOME_STATEMENT:
                financial_data = IncomeStatementData(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    report_date=report_date,
                    report_period=report_period,
                    data=data_dict
                )
            elif report_type == ReportType.CASH_FLOW:
                financial_data = CashFlowData(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    report_date=report_date,
                    report_period=report_period,
                    data=data_dict
                )
            elif report_type == ReportType.FINANCIAL_INDICATORS:
                financial_data = FinancialIndicatorsData(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    report_date=report_date,
                    report_period=report_period,
                    data=data_dict
                )
            else:
                financial_data = FinancialData(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    report_date=report_date,
                    report_type=report_type,
                    report_period=report_period,
                    data=data_dict
                )
            
            financial_data_list.append(financial_data)
        
        return financial_data_list
    
    def get_financial_report(self, request: FinancialDataRequest) -> FinancialDataResponse:
        """
        获取财务报表数据
        
        Args:
            request: 财务数据请求
            
        Returns:
            财务数据响应
        """
        try:
            self.logger.info(f"开始获取财务数据: {request.stock_code} - {request.report_type}")
            
            # 转换股票代码
            converted_code = self._convert_stock_code(request.stock_code)
            
            # 获取报告期参数
            report_period = request.report_period or ReportPeriod.ANNUAL
            
            # 根据报表类型调用不同的akshare接口
            if request.report_type == ReportType.BALANCE_SHEET:
                df = self._get_balance_sheet(converted_code, report_period)
            elif request.report_type == ReportType.INCOME_STATEMENT:
                df = self._get_income_statement(converted_code, report_period)
            elif request.report_type == ReportType.CASH_FLOW:
                df = self._get_cash_flow(converted_code, report_period)
            elif request.report_type == ReportType.FINANCIAL_INDICATORS:
                df = self._get_financial_indicators(converted_code)
            else:
                return FinancialDataResponse(
                    success=False,
                    message=f"不支持的报表类型: {request.report_type}"
                )
            
            if df.empty:
                return FinancialDataResponse(
                    success=False,
                    message=f"未找到股票 {request.stock_code} 的财务数据"
                )
            
            # 添加基础字段到DataFrame
            df['stock_code'] = request.stock_code
            df['report_type'] = request.report_type.value if hasattr(request.report_type, 'value') else str(request.report_type)
            df['report_period'] = (request.report_period or ReportPeriod.ANNUAL).value if hasattr((request.report_period or ReportPeriod.ANNUAL), 'value') else str(request.report_period or ReportPeriod.ANNUAL)
            
            # 应用限制
            if request.limit and len(df) > request.limit:
                df = df.head(request.limit)
            
            # 直接返回DataFrame而不是转换为FinancialData对象
            # 这样可以保留所有原始字段包括STD_ITEM_NAME
            collection = FinancialDataCollection(
                stock_code=request.stock_code,
                data_list=[],  # 暂时为空，后续会直接使用DataFrame
                raw_dataframe=df  # 添加原始DataFrame
            )
            
            self.logger.info(f"成功获取财务数据: {len(df)} 条记录")
            
            return FinancialDataResponse(
                success=True,
                message="获取财务数据成功",
                data=collection,
                total_count=len(df)
            )
            
        except Exception as e:
            error_msg = f"获取财务数据失败: {str(e)}"
            self.logger.error(error_msg)
            return FinancialDataResponse(
                success=False,
                message=error_msg
            )
    
    def _extract_balance_sheet_from_indicators(self, stock_code: str) -> DataFrame:
        """
        从财务指标中提取资产负债表相关数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            包含资产负债表数据的DataFrame
        """
        try:
            df = ak.stock_financial_hk_analysis_indicator_em(symbol=stock_code)
            if df.empty:
                return pd.DataFrame()
            
            # 从财务指标中提取资产负债表相关字段
            balance_sheet_data = []
            for _, row in df.iterrows():
                data = {
                    '报告期': row.get('REPORT_DATE', ''),
                    '股票代码': stock_code,
                    '股票名称': row.get('SECURITY_NAME_ABBR', ''),
                    '每股净资产': row.get('BPS', None),
                    '资产负债率': row.get('DEBT_ASSET_RATIO', None),
                    '流动比率': row.get('CURRENT_RATIO', None),
                    '货币单位': row.get('CURRENCY', 'HKD'),
                }
                balance_sheet_data.append(data)
            
            return pd.DataFrame(balance_sheet_data)
        except Exception as e:
            self.logger.error(f"从财务指标提取资产负债表数据失败: {e}")
            return pd.DataFrame()
    
    def _extract_income_statement_from_indicators(self, stock_code: str) -> DataFrame:
        """
        从财务指标中提取利润表相关数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            包含利润表数据的DataFrame
        """
        try:
            df = ak.stock_financial_hk_analysis_indicator_em(symbol=stock_code)
            if df.empty:
                return pd.DataFrame()
            
            # 从财务指标中提取利润表相关字段
            income_data = []
            for _, row in df.iterrows():
                data = {
                    '报告期': row.get('REPORT_DATE', ''),
                    '股票代码': stock_code,
                    '股票名称': row.get('SECURITY_NAME_ABBR', ''),
                    '营业收入': row.get('OPERATE_INCOME', None),
                    '毛利润': row.get('GROSS_PROFIT', None),
                    '净利润': row.get('HOLDER_PROFIT', None),
                    '基本每股收益': row.get('BASIC_EPS', None),
                    '稀释每股收益': row.get('DILUTED_EPS', None),
                    '毛利率': row.get('GROSS_PROFIT_RATIO', None),
                    '净利率': row.get('NET_PROFIT_RATIO', None),
                    '营业收入同比增长率': row.get('OPERATE_INCOME_YOY', None),
                    '净利润同比增长率': row.get('HOLDER_PROFIT_YOY', None),
                    '货币单位': row.get('CURRENCY', 'HKD'),
                }
                income_data.append(data)
            
            return pd.DataFrame(income_data)
        except Exception as e:
            self.logger.error(f"从财务指标提取利润表数据失败: {e}")
            return pd.DataFrame()
    
    def _extract_cash_flow_from_indicators(self, stock_code: str) -> DataFrame:
        """
        从财务指标中提取现金流量表相关数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            包含现金流量表数据的DataFrame
        """
        try:
            df = ak.stock_financial_hk_analysis_indicator_em(symbol=stock_code)
            if df.empty:
                return pd.DataFrame()
            
            # 从财务指标中提取现金流量表相关字段
            cash_flow_data = []
            for _, row in df.iterrows():
                data = {
                    '报告期': row.get('REPORT_DATE', ''),
                    '股票代码': stock_code,
                    '股票名称': row.get('SECURITY_NAME_ABBR', ''),
                    '每股经营现金流': row.get('PER_NETCASH_OPERATE', None),
                    '经营现金流/销售收入': row.get('OCF_SALES', None),
                    '货币单位': row.get('CURRENCY', 'HKD'),
                }
                cash_flow_data.append(data)
            
            return pd.DataFrame(cash_flow_data)
        except Exception as e:
            self.logger.error(f"从财务指标提取现金流量表数据失败: {e}")
            return pd.DataFrame()
    
    def _get_balance_sheet(self, stock_code: str, report_period: ReportPeriod = ReportPeriod.ANNUAL) -> DataFrame:
        """
        获取资产负债表数据
        
        Args:
            stock_code: 股票代码
            report_period: 报告期类型
            
        Returns:
            资产负债表数据
        """
        try:
            # 报告期类型映射
            indicator_mapping = {
                ReportPeriod.ANNUAL: "年度",
                ReportPeriod.INTERIM: "报告期"
            }
            indicator = indicator_mapping.get(report_period, "年度")
            
            # 使用正确的参数格式调用akshare接口
            df = ak.stock_financial_hk_report_em(
                stock=stock_code, 
                symbol="资产负债表", 
                indicator=indicator
            )
            if df.empty:
                self.logger.warning(f"资产负债表接口返回空数据，股票代码: {stock_code}, 报告期: {indicator}")
            return df
        except Exception as e:
            self.logger.error(f"获取资产负债表失败: {e}")
            return pd.DataFrame()
    
    def _get_income_statement(self, stock_code: str, report_period: ReportPeriod = ReportPeriod.ANNUAL) -> DataFrame:
        """
        获取利润表数据
        
        Args:
            stock_code: 股票代码
            report_period: 报告期类型
            
        Returns:
            利润表数据
        """
        try:
            # 报告期类型映射
            indicator_mapping = {
                ReportPeriod.ANNUAL: "年度",
                ReportPeriod.INTERIM: "报告期"
            }
            indicator = indicator_mapping.get(report_period, "年度")
            
            # 使用正确的参数格式调用akshare接口
            df = ak.stock_financial_hk_report_em(
                stock=stock_code, 
                symbol="利润表", 
                indicator=indicator
            )
            if df.empty:
                self.logger.warning(f"利润表接口返回空数据，股票代码: {stock_code}, 报告期: {indicator}")
            return df
        except Exception as e:
            self.logger.error(f"获取利润表失败: {e}")
            return pd.DataFrame()
    
    def _get_cash_flow(self, stock_code: str, report_period: ReportPeriod = ReportPeriod.ANNUAL) -> DataFrame:
        """
        获取现金流量表数据
        
        Args:
            stock_code: 股票代码
            report_period: 报告期类型
            
        Returns:
            现金流量表数据
        """
        try:
            # 报告期类型映射
            indicator_mapping = {
                ReportPeriod.ANNUAL: "年度",
                ReportPeriod.INTERIM: "报告期"
            }
            indicator = indicator_mapping.get(report_period, "年度")
            
            # 使用正确的参数格式调用akshare接口
            df = ak.stock_financial_hk_report_em(
                stock=stock_code, 
                symbol="现金流量表", 
                indicator=indicator
            )
            if df.empty:
                self.logger.warning(f"现金流量表接口返回空数据，股票代码: {stock_code}, 报告期: {indicator}")
            return df
        except Exception as e:
            self.logger.error(f"获取现金流量表失败: {e}")
            return pd.DataFrame()
    
    def _get_financial_indicators(self, stock_code: str) -> DataFrame:
        """
        获取财务指标数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            财务指标数据
        """
        try:
            # 使用akshare获取港股财务分析指标
            df = ak.stock_financial_hk_analysis_indicator_em(symbol=stock_code)
            return df
        except Exception as e:
            self.logger.error(f"获取财务指标失败: {e}")
            return pd.DataFrame()
    
    def get_all_financial_data(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse:
        """
        获取所有类型的财务数据
        
        Args:
            stock_code: 股票代码
            limit: 每种类型的数据条数限制
            
        Returns:
            财务数据响应
        """
        try:
            self.logger.info(f"开始获取股票 {stock_code} 的所有财务数据")
            
            all_data = []
            
            # 获取各种类型的财务数据
            for report_type in [ReportType.BALANCE_SHEET, ReportType.INCOME_STATEMENT, 
                              ReportType.CASH_FLOW, ReportType.FINANCIAL_INDICATORS]:
                request = FinancialDataRequest(
                    stock_code=stock_code,
                    report_type=report_type,
                    limit=limit
                )
                
                response = self.get_financial_report(request)
                if response.success and response.data:
                    if response.data.data_list:
                        all_data.extend(response.data.data_list)
                    # 如果有raw_dataframe，也可以处理，但这里主要用于兼容性
                    # 实际使用中建议直接调用单个报表类型的接口
            
            if not all_data:
                return FinancialDataResponse(
                    success=False,
                    message=f"未找到股票 {stock_code} 的任何财务数据"
                )
            
            # 创建数据集合
            collection = FinancialDataCollection(
                stock_code=stock_code,
                data_list=all_data
            )
            
            self.logger.info(f"成功获取所有财务数据: {len(all_data)} 条记录")
            
            return FinancialDataResponse(
                success=True,
                message="获取所有财务数据成功",
                data=collection,
                total_count=len(all_data)
            )
            
        except Exception as e:
            error_msg = f"获取所有财务数据失败: {str(e)}"
            self.logger.error(error_msg)
            return FinancialDataResponse(
                success=False,
                message=error_msg
            )