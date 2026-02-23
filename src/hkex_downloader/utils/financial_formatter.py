#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据格式化工具

提供财务数据的格式化、转换和标准化功能
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame

from ..models.financial import FinancialData, ReportType


class FinancialDataFormatter:
    """
    财务数据格式化器
    
    提供财务数据的格式化、转换和标准化功能，包括：
    - 字段名称标准化
    - 数值格式化
    - 单位转换
    - 数据类型转换
    - 英文字段映射
    """

    def __init__(self):
        """
        初始化财务数据格式化器
        """
        # 完整的中英文字段映射
        self._field_mappings = self._init_comprehensive_field_mappings()
        
        # 数值字段列表
        self._numeric_fields = self._init_numeric_fields()
        
        # 单位转换配置
        self._unit_conversions = {
            "万元": 10000,
            "千元": 1000,
            "百万元": 1000000,
            "亿元": 100000000,
            "万港元": 10000,
            "千港元": 1000,
            "百万港元": 1000000,
            "亿港元": 100000000,
        }
    
    def _init_comprehensive_field_mappings(self) -> Dict[str, str]:
        """
        初始化完整的中英文字段映射
        
        Returns:
            字段映射字典
        """
        return {
            # 基础信息字段
            "股票代码": "stock_code",
            "股票名称": "stock_name",
            "公司名称": "company_name",
            "报告期": "report_date",
            "报告期间": "report_period",
            "报表类型": "report_type",
            "货币单位": "currency",
            "审计意见": "audit_opinion",
            
            # 资产负债表字段
            "总资产": "total_assets",
            "总负债": "total_liabilities",
            "股东权益合计": "total_equity",
            "归属于母公司股东权益合计": "equity_attributable_to_parent",
            "少数股东权益": "minority_interests",
            "流动资产合计": "current_assets",
            "非流动资产合计": "non_current_assets",
            "流动负债合计": "current_liabilities",
            "非流动负债合计": "non_current_liabilities",
            
            # 流动资产明细
            "货币资金": "cash_and_equivalents",
            "交易性金融资产": "trading_financial_assets",
            "应收票据": "notes_receivable",
            "应收账款": "accounts_receivable",
            "应收款项融资": "receivables_financing",
            "预付款项": "prepayments",
            "其他应收款": "other_receivables",
            "存货": "inventory",
            "合同资产": "contract_assets",
            "持有待售资产": "assets_held_for_sale",
            "一年内到期的非流动资产": "non_current_assets_due_within_one_year",
            "其他流动资产": "other_current_assets",
            
            # 非流动资产明细
            "可供出售金融资产": "available_for_sale_financial_assets",
            "持有至到期投资": "held_to_maturity_investments",
            "长期应收款": "long_term_receivables",
            "长期股权投资": "long_term_equity_investments",
            "投资性房地产": "investment_property",
            "固定资产": "fixed_assets",
            "在建工程": "construction_in_progress",
            "生产性生物资产": "productive_biological_assets",
            "油气资产": "oil_and_gas_assets",
            "无形资产": "intangible_assets",
            "开发支出": "development_expenditure",
            "商誉": "goodwill",
            "长期待摊费用": "long_term_prepaid_expenses",
            "递延所得税资产": "deferred_tax_assets",
            "其他非流动资产": "other_non_current_assets",
            
            # 流动负债明细
            "短期借款": "short_term_debt",
            "交易性金融负债": "trading_financial_liabilities",
            "应付票据": "notes_payable",
            "应付账款": "accounts_payable",
            "预收款项": "advances_from_customers",
            "合同负债": "contract_liabilities",
            "应付职工薪酬": "employee_benefits_payable",
            "应交税费": "taxes_payable",
            "其他应付款": "other_payables",
            "持有待售负债": "liabilities_held_for_sale",
            "一年内到期的非流动负债": "non_current_liabilities_due_within_one_year",
            "其他流动负债": "other_current_liabilities",
            
            # 非流动负债明细
            "长期借款": "long_term_debt",
            "应付债券": "bonds_payable",
            "长期应付款": "long_term_payables",
            "长期应付职工薪酬": "long_term_employee_benefits_payable",
            "预计负债": "provisions",
            "递延收益": "deferred_revenue",
            "递延所得税负债": "deferred_tax_liabilities",
            "其他非流动负债": "other_non_current_liabilities",
            
            # 股东权益明细
            "实收资本": "paid_in_capital",
            "股本": "share_capital",
            "其他权益工具": "other_equity_instruments",
            "资本公积": "capital_surplus",
            "库存股": "treasury_shares",
            "其他综合收益": "other_comprehensive_income",
            "专项储备": "special_reserves",
            "盈余公积": "surplus_reserves",
            "未分配利润": "retained_earnings",
            
            # 利润表字段
            "营业总收入": "total_revenue",
            "营业收入": "operating_revenue",
            "利息收入": "interest_income",
            "已赚保费": "earned_premiums",
            "手续费及佣金收入": "fee_and_commission_income",
            "营业总成本": "total_operating_costs",
            "营业成本": "operating_costs",
            "利息支出": "interest_expense",
            "手续费及佣金支出": "fee_and_commission_expense",
            "退保金": "surrender_benefits",
            "赔付支出净额": "net_claims_expense",
            "提取保险合同准备金净额": "net_increase_in_insurance_contract_reserves",
            "保单红利支出": "policy_dividend_expense",
            "分保费用": "reinsurance_expense",
            "税金及附加": "taxes_and_surcharges",
            "销售费用": "selling_expenses",
            "管理费用": "administrative_expenses",
            "研发费用": "rd_expenses",
            "财务费用": "financial_expenses",
            "其他收益": "other_income",
            "投资收益": "investment_income",
            "净敞口套期收益": "net_exposure_hedging_gains",
            "公允价值变动收益": "fair_value_change_gains",
            "信用减值损失": "credit_impairment_losses",
            "资产减值损失": "asset_impairment_losses",
            "资产处置收益": "asset_disposal_gains",
            "营业利润": "operating_profit",
            "营业外收入": "non_operating_income",
            "营业外支出": "non_operating_expenses",
            "利润总额": "total_profit",
            "所得税费用": "income_tax_expense",
            "净利润": "net_profit",
            "持续经营净利润": "net_profit_from_continuing_operations",
            "终止经营净利润": "net_profit_from_discontinued_operations",
            "归属于母公司股东的净利润": "net_profit_attributable_to_parent",
            "少数股东损益": "minority_interests_in_profit",
            "其他综合收益的税后净额": "other_comprehensive_income_after_tax",
            "综合收益总额": "total_comprehensive_income",
            "归属于母公司股东的综合收益总额": "comprehensive_income_attributable_to_parent",
            "归属于少数股东的综合收益总额": "comprehensive_income_attributable_to_minority",
            "基本每股收益": "basic_eps",
            "稀释每股收益": "diluted_eps",
            
            # 现金流量表字段
            "经营活动现金流量": "operating_cash_flows",
            "销售商品、提供劳务收到的现金": "cash_from_sales",
            "客户存款和同业存放款项净增加额": "net_increase_in_customer_deposits",
            "向中央银行借款净增加额": "net_increase_in_borrowings_from_central_bank",
            "向其他金融机构拆入资金净增加额": "net_increase_in_borrowings_from_other_financial_institutions",
            "收到原保险合同保费取得的现金": "cash_from_original_insurance_premiums",
            "收到再保险业务现金净额": "net_cash_from_reinsurance",
            "保户储金及投资款净增加额": "net_increase_in_policyholder_deposits_and_investments",
            "处置交易性金融资产净增加额": "net_increase_in_disposal_of_trading_financial_assets",
            "收取利息、手续费及佣金的现金": "cash_from_interest_fees_and_commissions",
            "拆入资金净增加额": "net_increase_in_borrowed_funds",
            "回购业务资金净增加额": "net_increase_in_repurchase_funds",
            "收到的税费返还": "tax_refunds_received",
            "收到其他与经营活动有关的现金": "other_cash_from_operating_activities",
            "经营活动现金流入小计": "subtotal_cash_inflows_from_operating_activities",
            "购买商品、接受劳务支付的现金": "cash_paid_for_goods",
            "客户贷款及垫款净增加额": "net_increase_in_customer_loans_and_advances",
            "存放中央银行和同业款项净增加额": "net_increase_in_deposits_with_central_bank_and_other_banks",
            "支付原保险合同赔付款项的现金": "cash_paid_for_original_insurance_claims",
            "支付利息、手续费及佣金的现金": "cash_paid_for_interest_fees_and_commissions",
            "支付保单红利的现金": "cash_paid_for_policy_dividends",
            "支付给职工以及为职工支付的现金": "cash_paid_to_employees",
            "支付的各项税费": "taxes_paid",
            "支付其他与经营活动有关的现金": "other_cash_paid_for_operating_activities",
            "经营活动现金流出小计": "subtotal_cash_outflows_from_operating_activities",
            "经营活动产生的现金流量净额": "operating_cash_flow",
            
            "投资活动现金流量": "investing_cash_flows",
            "收回投资收到的现金": "cash_from_investments",
            "取得投资收益收到的现金": "investment_income_received",
            "处置固定资产、无形资产和其他长期资产收回的现金净额": "net_cash_from_disposal_of_fixed_assets",
            "处置子公司及其他营业单位收到的现金净额": "net_cash_from_disposal_of_subsidiaries",
            "收到其他与投资活动有关的现金": "other_cash_from_investing_activities",
            "投资活动现金流入小计": "subtotal_cash_inflows_from_investing_activities",
            "购建固定资产、无形资产和其他长期资产支付的现金": "capex_cash_paid",
            "投资支付的现金": "cash_paid_for_investments",
            "质押贷款净增加额": "net_increase_in_pledged_loans",
            "取得子公司及其他营业单位支付的现金净额": "net_cash_paid_for_acquisition_of_subsidiaries",
            "支付其他与投资活动有关的现金": "other_cash_paid_for_investing_activities",
            "投资活动现金流出小计": "subtotal_cash_outflows_from_investing_activities",
            "投资活动产生的现金流量净额": "investing_cash_flow",
            
            "筹资活动现金流量": "financing_cash_flows",
            "吸收投资收到的现金": "cash_from_equity_financing",
            "其中：子公司吸收少数股东投资收到的现金": "cash_from_minority_equity_financing",
            "取得借款收到的现金": "cash_from_borrowing",
            "发行债券收到的现金": "cash_from_bond_issuance",
            "收到其他与筹资活动有关的现金": "other_cash_from_financing_activities",
            "筹资活动现金流入小计": "subtotal_cash_inflows_from_financing_activities",
            "偿还债务支付的现金": "debt_repayment",
            "分配股利、利润或偿付利息支付的现金": "dividends_and_interest_paid",
            "其中：子公司支付给少数股东的股利、利润": "dividends_paid_to_minority_shareholders",
            "支付其他与筹资活动有关的现金": "other_cash_paid_for_financing_activities",
            "筹资活动现金流出小计": "subtotal_cash_outflows_from_financing_activities",
            "筹资活动产生的现金流量净额": "financing_cash_flow",
            
            "汇率变动对现金及现金等价物的影响": "effect_of_exchange_rate_changes",
            "现金及现金等价物净增加额": "net_cash_flow",
            "期初现金及现金等价物余额": "beginning_cash_and_equivalents",
            "期末现金及现金等价物余额": "ending_cash_and_equivalents",
            
            # 财务指标字段
            "净资产收益率": "roe",
            "总资产收益率": "roa",
            "销售净利率": "net_margin",
            "销售毛利率": "gross_margin",
            "资产负债率": "debt_to_equity_ratio",
            "流动比率": "current_ratio",
            "速动比率": "quick_ratio",
            "现金比率": "cash_ratio",
            "利息保障倍数": "interest_coverage_ratio",
            "应收账款周转率": "receivables_turnover",
            "存货周转率": "inventory_turnover",
            "总资产周转率": "asset_turnover",
            "固定资产周转率": "fixed_asset_turnover",
            "每股收益": "eps",
            "每股净资产": "book_value_per_share",
            "每股经营现金流": "operating_cash_flow_per_share",
            "市盈率": "pe_ratio",
            "市净率": "pb_ratio",
            "市销率": "ps_ratio",
            "企业价值倍数": "ev_multiple",
            "股息收益率": "dividend_yield",
            "股息支付率": "dividend_payout_ratio",
        }
    
    def _init_numeric_fields(self) -> List[str]:
        """
        初始化数值字段列表
        
        Returns:
            数值字段列表
        """
        # 所有财务数值字段
        numeric_fields = [
            # 资产负债表数值字段
            "total_assets", "total_liabilities", "total_equity", "current_assets", "current_liabilities",
            "cash_and_equivalents", "accounts_receivable", "inventory", "fixed_assets", "intangible_assets",
            "accounts_payable", "short_term_debt", "long_term_debt", "paid_in_capital", "retained_earnings",
            
            # 利润表数值字段
            "total_revenue", "operating_revenue", "operating_costs", "gross_profit", "operating_profit",
            "total_profit", "net_profit", "selling_expenses", "administrative_expenses", "financial_expenses",
            "rd_expenses", "income_tax_expense", "basic_eps", "diluted_eps",
            
            # 现金流量表数值字段
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_flow",
            "cash_from_sales", "cash_paid_for_goods", "cash_paid_to_employees", "taxes_paid",
            "cash_from_investments", "investment_income_received", "capex_cash_paid",
            "cash_from_equity_financing", "cash_from_borrowing", "debt_repayment", "dividends_and_interest_paid",
            
            # 财务指标数值字段
            "roe", "roa", "net_margin", "gross_margin", "debt_to_equity_ratio", "current_ratio",
            "quick_ratio", "cash_ratio", "interest_coverage_ratio", "receivables_turnover",
            "inventory_turnover", "asset_turnover", "eps", "book_value_per_share",
            "pe_ratio", "pb_ratio", "ps_ratio", "dividend_yield", "dividend_payout_ratio"
        ]
        
        return numeric_fields
    
    def format_field_name(self, field_name: str) -> str:
        """
        格式化字段名称
        
        Args:
            field_name: 原始字段名
            
        Returns:
            格式化后的字段名
        """
        # 移除特殊字符和空格
        cleaned_name = re.sub(r'[^\w\u4e00-\u9fff]', '', field_name)
        
        # 应用映射
        return self._field_mappings.get(cleaned_name, cleaned_name)
    
    def format_numeric_value(self, value: Any, field_name: str = "") -> Optional[float]:
        """
        格式化数值
        
        Args:
            value: 原始值
            field_name: 字段名（用于特殊处理）
            
        Returns:
            格式化后的数值
        """
        if pd.isna(value) or value is None:
            return None
        
        # 如果已经是数值类型
        if isinstance(value, (int, float)):
            return float(value)
        
        # 字符串处理
        if isinstance(value, str):
            # 移除逗号和空格
            cleaned_value = value.replace(',', '').replace(' ', '')
            
            # 处理单位转换
            for unit, multiplier in self._unit_conversions.items():
                if unit in cleaned_value:
                    cleaned_value = cleaned_value.replace(unit, '')
                    try:
                        return float(cleaned_value) * multiplier
                    except ValueError:
                        pass
            
            # 处理百分比
            if '%' in cleaned_value:
                cleaned_value = cleaned_value.replace('%', '')
                try:
                    return float(cleaned_value) / 100
                except ValueError:
                    pass
            
            # 处理负数
            if cleaned_value.startswith('-') or '负' in cleaned_value:
                cleaned_value = cleaned_value.replace('负', '').replace('-', '')
                try:
                    return -float(cleaned_value)
                except ValueError:
                    pass
            
            # 尝试直接转换
            try:
                return float(cleaned_value)
            except ValueError:
                pass
        
        return None
    
    def format_date(self, date_value: Any) -> str:
        """
        格式化日期
        
        Args:
            date_value: 原始日期值
            
        Returns:
            格式化后的日期字符串 (YYYY-MM-DD)
        """
        if pd.isna(date_value) or date_value is None:
            return ""
        
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        
        if isinstance(date_value, str):
            # 尝试解析各种日期格式
            date_patterns = [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
                r'(\d{4})(\d{2})(\d{2})',
                r'(\d{4})年(\d{1,2})月',
                r'(\d{4})-(\d{1,2})',
                r'(\d{4})年',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_value)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        year, month, day = groups
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif len(groups) == 2:
                        year, month = groups
                        return f"{year}-{month.zfill(2)}-01"
                    elif len(groups) == 1:
                        year = groups[0]
                        return f"{year}-01-01"
        
        return str(date_value)
    
    def format_financial_data(self, data: FinancialData, use_english_fields: bool = True) -> Dict[str, Any]:
        """
        格式化单个财务数据
        
        Args:
            data: 财务数据
            use_english_fields: 是否使用英文字段名
            
        Returns:
            格式化后的数据字典
        """
        formatted_data = {
            "stock_code": data.stock_code,
            "stock_name": data.stock_name or "",
            "report_date": self.format_date(data.report_date),
            "report_type": data.report_type.value,
            "report_period": data.report_period.value,
            "currency": data.currency,
        }
        
        # 格式化财务数据字段
        for key, value in data.data.items():
            # 格式化字段名
            field_name = self.format_field_name(key) if use_english_fields else key
            
            # 格式化数值
            if field_name in self._numeric_fields or self._is_numeric_field(key):
                formatted_value = self.format_numeric_value(value, field_name)
            else:
                formatted_value = value
            
            formatted_data[field_name] = formatted_value
        
        return formatted_data
    
    def format_dataframe(self, df: DataFrame, use_english_fields: bool = True) -> DataFrame:
        """
        格式化DataFrame
        
        Args:
            df: 原始DataFrame
            use_english_fields: 是否使用英文字段名
            
        Returns:
            格式化后的DataFrame
        """
        if df.empty:
            return df
        
        formatted_df = df.copy()
        
        # 格式化列名
        if use_english_fields:
            column_mapping = {}
            for col in formatted_df.columns:
                new_col = self.format_field_name(col)
                column_mapping[col] = new_col
            formatted_df = formatted_df.rename(columns=column_mapping)
        
        # 格式化数值列
        for col in formatted_df.columns:
            if col in self._numeric_fields or self._is_numeric_field(col):
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: self.format_numeric_value(x, col)
                )
        
        # 格式化日期列
        date_columns = ['report_date', '报告期', 'report_period']
        for col in date_columns:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(self.format_date)
        
        return formatted_df
    
    def _is_numeric_field(self, field_name: str) -> bool:
        """
        判断字段是否为数值字段
        
        Args:
            field_name: 字段名
            
        Returns:
            是否为数值字段
        """
        # 数值字段的关键词
        numeric_keywords = [
            '金额', '收入', '支出', '成本', '费用', '利润', '资产', '负债', '权益',
            '现金', '投资', '借款', '股本', '收益', '比率', '率', '倍数', '每股',
            'amount', 'income', 'expense', 'cost', 'profit', 'asset', 'liability',
            'equity', 'cash', 'investment', 'debt', 'capital', 'revenue', 'ratio',
            'rate', 'multiple', 'per_share', 'eps', 'roe', 'roa'
        ]
        
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in numeric_keywords)
    
    def standardize_report_structure(self, data_list: List[FinancialData]) -> Dict[str, List[Dict[str, Any]]]:
        """
        标准化报表结构
        
        Args:
            data_list: 财务数据列表
            
        Returns:
            按报表类型分组的标准化数据
        """
        structured_data = {
            ReportType.BALANCE_SHEET.value: [],
            ReportType.INCOME_STATEMENT.value: [],
            ReportType.CASH_FLOW.value: [],
            ReportType.FINANCIAL_INDICATORS.value: []
        }
        
        for data in data_list:
            formatted_data = self.format_financial_data(data, use_english_fields=True)
            report_type = data.report_type.value
            
            if report_type in structured_data:
                structured_data[report_type].append(formatted_data)
        
        return structured_data
    
    def create_summary_statistics(self, data_list: List[FinancialData]) -> Dict[str, Any]:
        """
        创建汇总统计信息
        
        Args:
            data_list: 财务数据列表
            
        Returns:
            汇总统计信息
        """
        if not data_list:
            return {}
        
        # 按报表类型分组
        type_counts = {}
        date_range = {"earliest": None, "latest": None}
        
        for data in data_list:
            report_type = data.report_type.value
            type_counts[report_type] = type_counts.get(report_type, 0) + 1
            
            # 更新日期范围
            report_date = self.format_date(data.report_date)
            if date_range["earliest"] is None or report_date < date_range["earliest"]:
                date_range["earliest"] = report_date
            if date_range["latest"] is None or report_date > date_range["latest"]:
                date_range["latest"] = report_date
        
        return {
            "total_records": len(data_list),
            "report_type_counts": type_counts,
            "date_range": date_range,
            "stock_codes": list(set(data.stock_code for data in data_list)),
            "currencies": list(set(data.currency for data in data_list)),
        }