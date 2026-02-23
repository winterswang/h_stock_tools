#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据下载器

提供财务数据下载和格式化功能
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame

from ..models.financial import (
    FinancialData,
    FinancialDataCollection,
    FinancialDataRequest,
    FinancialDataResponse,
    ReportType,
    ReportPeriod,
)
from ..utils.logger import get_logger
from .financial_service import FinancialDataService


class FinancialDownloadResult:
    """
    财务数据下载结果
    """

    def __init__(
        self,
        stock_code: str,
        report_type: ReportType,
        success: bool,
        file_path: Optional[str] = None,
        error: Optional[str] = None,
        record_count: int = 0,
    ):
        self.stock_code = stock_code
        self.report_type = report_type
        self.success = success
        self.file_path = file_path
        self.error = error
        self.record_count = record_count
        self.download_time = datetime.now()

    def __repr__(self):
        status = "成功" if self.success else "失败"
        return f"FinancialDownloadResult({self.stock_code}-{self.report_type}, {status}, {self.record_count}条记录)"


class FinancialDataDownloader:
    """
    财务数据下载器
    
    提供财务数据下载和格式化功能，包括：
    - CSV格式保存
    - 数据格式化
    - 英文字段映射
    - 批量下载
    """

    def __init__(
        self,
        financial_service: Optional[FinancialDataService] = None,
        download_dir: str = "./data/financial",
        logger: Optional[logging.Logger] = None,
    ):
        """
        初始化财务数据下载器
        
        Args:
            financial_service: 财务数据服务
            download_dir: 下载目录
            logger: 日志记录器
        """
        self.financial_service = financial_service or FinancialDataService()
        self.download_dir = Path(download_dir)
        self.logger = logger or get_logger(__name__)
        
        # 确保下载目录存在
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 输出格式映射
        self._output_formats = {
            "csv": self._save_as_csv,
            "excel": self._save_as_excel,
            "json": self._save_as_json,
            "pivot-csv": self._save_as_pivot_csv,
            "pivot-excel": self._save_as_pivot_excel,
        }
    
    def generate_filename(
        self, 
        stock_code: str, 
        report_type: ReportType, 
        format_type: str = "csv",
        include_timestamp: bool = True
    ) -> str:
        """
        生成文件名
        
        Args:
            stock_code: 股票代码
            report_type: 报表类型
            format_type: 文件格式
            include_timestamp: 是否包含时间戳
            
        Returns:
            文件名
        """
        # 报表类型映射
        type_mapping = {
            ReportType.BALANCE_SHEET: "balance_sheet",
            ReportType.INCOME_STATEMENT: "income_statement", 
            ReportType.CASH_FLOW: "cash_flow",
            ReportType.FINANCIAL_INDICATORS: "financial_indicators"
        }
        
        type_name = type_mapping.get(report_type, report_type.value if hasattr(report_type, 'value') else str(report_type))
        
        # 格式类型映射到正确的文件扩展名
        extension_mapping = {
            "csv": "csv",
            "excel": "xlsx",
            "json": "json",
            "pivot-csv": "csv",
            "pivot-excel": "xlsx"
        }
        
        file_extension = extension_mapping.get(format_type, format_type)
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_{type_name}_{timestamp}.{file_extension}"
        else:
            filename = f"{stock_code}_{type_name}.{file_extension}"
        
        return filename
    
    def _prepare_dataframe(self, financial_data_list: List[FinancialData], use_english_fields: bool = True) -> DataFrame:
        """
        准备DataFrame数据
        
        Args:
            financial_data_list: 财务数据列表
            use_english_fields: 是否使用英文字段名
            
        Returns:
            DataFrame
        """
        if not financial_data_list:
            return pd.DataFrame()
        
        # 收集所有数据
        records = []
        for data in financial_data_list:
            record = {
                "股票代码": data.stock_code,
                "股票名称": data.stock_name or "",
                "报告期": data.report_date,
                "报表类型": data.report_type.value if hasattr(data.report_type, 'value') else str(data.report_type),
            "报告期类型": data.report_period.value if hasattr(data.report_period, 'value') else str(data.report_period),
                "货币单位": data.currency,
            }
            
            # 添加财务数据
            record.update(data.data)
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # 如果使用英文字段名，进行映射
        if use_english_fields:
            df = self._apply_english_field_mapping(df)
        
        return df
    
    def _apply_english_field_mapping(self, df: DataFrame, use_english_fields: bool = True) -> DataFrame:
        """
        应用英文字段映射
        
        Args:
            df: 原始DataFrame
            use_english_fields: 是否使用英文字段名
            
        Returns:
            映射后的DataFrame
        """
        # 基础字段映射（仅在use_english_fields=True时应用）
        basic_field_mapping = {
            "股票代码": "stock_code",
            "股票名称": "stock_name", 
            "报告期": "report_date",
            "报表类型": "report_type",
            "报告期类型": "report_period",
            "货币单位": "currency",
        }
        
        # akshare原始字段映射（总是应用）
        akshare_field_mapping = {
            "SECUCODE": "security_code",
            "SECURITY_CODE": "stock_code_raw",
            "SECURITY_NAME_ABBR": "stock_name",
            "ORG_CODE": "org_code",
            "REPORT_DATE": "report_date",
            "DATE_TYPE_CODE": "date_type_code",
            "FISCAL_YEAR": "fiscal_year",
            "STD_ITEM_CODE": "item_code",
            "STD_ITEM_NAME": "item_name",
            "AMOUNT": "amount",
            "STD_REPORT_DATE": "std_report_date",
            "START_DATE": "start_date",
        }
        
        # 财务科目中英文映射（仅在use_english_fields=True时应用）
        financial_item_mapping = {
            "中长期存款": "long_term_deposits",
            "储备": "reserves",
            "其他应付款及应计费用": "other_payables_and_accruals",
            "其他非流动负债": "other_non_current_liabilities",
            "净流动资产": "net_current_assets",
            "净资产": "net_assets",
            "合同负债": "contract_liabilities",
            "存货": "inventory",
            "少数股东权益": "minority_interests",
            "应付帐款": "accounts_payable",
            "应付税项": "tax_payable",
            "应收帐款": "accounts_receivable",
            "总权益": "total_equity",
            "总权益及总负债": "total_equity_and_liabilities",
            "总权益及非流动负债": "total_equity_and_non_current_liabilities",
            "总负债": "total_liabilities",
            "总资产": "total_assets",
            "总资产减流动负债": "total_assets_less_current_liabilities",
            "指定以公允价值记账之金融资产": "financial_assets_at_fair_value",
            "指定以公允价值记账之金融资产(流动)": "current_financial_assets_at_fair_value",
            "无形资产": "intangible_assets",
            "流动负债合计": "current_liabilities",
            "流动资产合计": "current_assets",
            "物业厂房及设备": "property_plant_equipment",
            "现金及等价物": "cash_and_equivalents",
            "短期贷款": "short_term_loans",
            "联营公司权益": "interests_in_associates",
            "股东权益": "shareholders_equity",
            "股本": "share_capital",
            "融资租赁负债(流动)": "current_lease_liabilities",
            "融资租赁负债(非流动)": "non_current_lease_liabilities",
            "递延收入(非流动)": "non_current_deferred_income",
            "递延税项负债": "deferred_tax_liabilities",
            "递延税项资产": "deferred_tax_assets",
            "长期应付款": "long_term_payables",
            "非流动负债其他项目": "other_non_current_liabilities_items",
            "非流动负债合计": "non_current_liabilities",
            "非流动资产其他项目": "other_non_current_assets_items",
            "非流动资产合计": "non_current_assets",
            "预付款按金及其他应收款": "prepayments_deposits_and_other_receivables",
            "投资物业": "investment_properties",
            "受限制存款及现金": "restricted_cash_and_deposits",
        }
        
        # 构建最终的字段映射
        field_mapping = {}
        
        # 总是应用akshare字段映射
        field_mapping.update(akshare_field_mapping)
        
        # 根据use_english_fields参数决定是否应用其他映射
        if use_english_fields:
            field_mapping.update(basic_field_mapping)
            field_mapping.update(financial_item_mapping)
        
        # 应用基础映射
        df_mapped = df.rename(columns=field_mapping)
        
        # 获取财务服务的字段映射
        field_mappings = self.financial_service._field_mappings
        
        # 应用所有财务字段映射
        for report_type, mapping in field_mappings.items():
            df_mapped = df_mapped.rename(columns=mapping)
        
        return df_mapped
    
    def _filter_by_year_range(self, df: DataFrame, start_year: Optional[int] = None, end_year: Optional[int] = None) -> DataFrame:
        """
        根据年份范围筛选数据
        
        Args:
            df: 原始DataFrame
            start_year: 开始年份
            end_year: 结束年份
            
        Returns:
            筛选后的DataFrame
        """
        if df.empty:
            return df
            
        # 尝试从不同的日期字段中提取年份
        date_columns = ['report_date', 'REPORT_DATE', 'std_report_date', 'STD_REPORT_DATE']
        year_column = None
        
        for col in date_columns:
            if col in df.columns:
                year_column = col
                break
                
        if year_column is None:
            self.logger.warning("未找到日期字段，无法进行年份筛选")
            return df
            
        try:
            # 提取年份
            df_filtered = df.copy()
            df_filtered['year'] = pd.to_datetime(df_filtered[year_column]).dt.year
            
            # 应用年份筛选
            if start_year is not None:
                df_filtered = df_filtered[df_filtered['year'] >= start_year]
            if end_year is not None:
                df_filtered = df_filtered[df_filtered['year'] <= end_year]
                
            # 删除临时年份列
            df_filtered = df_filtered.drop('year', axis=1)
            
            self.logger.info(f"年份筛选: {len(df)} -> {len(df_filtered)} 条记录")
            return df_filtered
            
        except Exception as e:
            self.logger.error(f"年份筛选失败: {e}")
            return df
    
    def _pivot_financial_data(self, df: DataFrame, use_english_fields: bool = True) -> DataFrame:
        """
        将财务数据从纵向格式转换为横向透视格式
        
        Args:
            df: 原始DataFrame（纵向格式）
            use_english_fields: 是否使用英文字段名
            
        Returns:
            透视后的DataFrame（横向格式）
        """
        if df.empty:
            return df
            
        try:
            # 动态确定关键字段（支持中英文字段名）
            date_col = None
            item_col = None
            amount_col = None
            
            # 查找日期字段
            for col in ['report_date', 'REPORT_DATE', '报告期']:
                if col in df.columns:
                    date_col = col
                    break
                    
            # 查找科目名称字段
            for col in ['item_name', 'STD_ITEM_NAME', '科目名称']:
                if col in df.columns:
                    item_col = col
                    break
                    
            # 查找金额字段
            for col in ['amount', 'AMOUNT', '金额']:
                if col in df.columns:
                    amount_col = col
                    break
                    
            self.logger.info(f"透视转换字段识别: 日期={date_col}, 科目={item_col}, 金额={amount_col}")
            
            # 检查必要字段是否存在
            if not all([date_col, item_col, amount_col]):
                missing = []
                if not date_col: missing.append('日期字段')
                if not item_col: missing.append('科目名称字段')
                if not amount_col: missing.append('金额字段')
                self.logger.warning(f"缺少必要字段进行透视转换: {missing}")
                return df
                
            # 获取元数据字段（除了item_name、amount和date_col之外的字段）
            meta_cols = [col for col in df.columns if col not in [item_col, amount_col, 'item_code', date_col]]
            
            self.logger.info(f"元数据字段: {meta_cols}")
            
            # 按日期分组，获取每个日期的元数据
            try:
                if meta_cols:
                    date_groups = df.groupby(date_col).first()[meta_cols].reset_index()
                    date_groups[date_col] = df.groupby(date_col).first().index
                else:
                    # 如果没有元数据字段，只保留日期
                    date_groups = df[[date_col]].drop_duplicates().reset_index(drop=True)
            except Exception as e:
                self.logger.error(f"按日期分组失败: {e}")
                return df
            
            # 执行透视转换
            pivot_df = df.pivot_table(
                index=date_col,
                columns=item_col,
                values=amount_col,
                aggfunc='first'  # 如果有重复值，取第一个
            )
            
            # 重置索引并清理列名
            pivot_df = pivot_df.reset_index()
            pivot_df.columns.name = None  # 清除列名的名称
            
            # 合并元数据
            result_df = date_groups.merge(pivot_df, on=date_col, how='left')
            
            # 重新排列列顺序：元数据字段在前，财务科目在后
            meta_columns = [col for col in meta_cols if col in result_df.columns]
            item_columns = [col for col in result_df.columns if col not in meta_columns]
            result_df = result_df[meta_columns + sorted(item_columns)]
            
            # 填充空值
            result_df = result_df.fillna('')
            
            # 应用英文字段映射
            result_df = self._apply_english_field_mapping(result_df, use_english_fields)
            
            self.logger.info(f"数据透视转换完成: {len(df)} 行 -> {len(result_df)} 行, {len(df.columns)} 列 -> {len(result_df.columns)} 列")
            return result_df
            
        except Exception as e:
            self.logger.error(f"数据透视转换失败: {e}")
            return df
    
    def _save_as_csv(
        self, 
        df: DataFrame, 
        file_path: Path, 
        encoding: str = "utf-8-sig"
    ) -> bool:
        """
        保存为CSV格式
        
        Args:
            df: 数据框
            file_path: 文件路径
            encoding: 编码格式
            
        Returns:
            是否成功
        """
        try:
            df.to_csv(file_path, index=False, encoding=encoding)
            return True
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")
            return False
    
    def _save_as_excel(self, df: DataFrame, file_path: Path) -> bool:
        """
        保存为Excel格式
        
        Args:
            df: 数据框
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='财务数据')
            return True
        except Exception as e:
            self.logger.error(f"保存Excel文件失败: {e}")
            return False
    
    def _save_as_json(self, df: DataFrame, file_path: Path) -> bool:
        """
        保存为JSON格式
        
        Args:
            df: 数据框
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            df.to_json(file_path, orient='records', force_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存JSON文件失败: {e}")
            return False
    
    def _save_as_pivot_csv(self, df: DataFrame, file_path: Path, use_english_fields: bool = True) -> bool:
        """
        保存为透视CSV格式
        
        Args:
            df: 数据框
            file_path: 文件路径
            use_english_fields: 是否使用英文字段名
            
        Returns:
            是否成功
        """
        try:
            # 先进行透视转换
            pivot_df = self._pivot_financial_data(df, use_english_fields)
            # 保存为CSV
            pivot_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            return True
        except Exception as e:
            self.logger.error(f"保存透视CSV文件失败: {e}")
            return False
    
    def _save_as_pivot_excel(self, df: DataFrame, file_path: Path, use_english_fields: bool = True) -> bool:
        """
        保存为透视Excel格式
        
        Args:
            df: 数据框
            file_path: 文件路径
            use_english_fields: 是否使用英文字段名
            
        Returns:
            是否成功
        """
        try:
            # 先进行透视转换
            pivot_df = self._pivot_financial_data(df, use_english_fields)
            # 保存为Excel
            pivot_df.to_excel(file_path, index=False, engine='openpyxl')
            return True
        except Exception as e:
            self.logger.error(f"保存透视Excel文件失败: {e}")
            return False
    
    def download_financial_data(
        self,
        request: FinancialDataRequest,
        format_type: str = "csv",
        use_english_fields: bool = True,
        custom_filename: Optional[str] = None,
        subfolder: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> FinancialDownloadResult:
        """
        下载财务数据
        
        Args:
            request: 财务数据请求
            format_type: 输出格式 (csv, excel, json)
            use_english_fields: 是否使用英文字段名
            custom_filename: 自定义文件名
            subfolder: 子文件夹
            
        Returns:
            下载结果
        """
        try:
            self.logger.info(f"开始下载财务数据: {request.stock_code} - {request.report_type}")
            
            # 获取财务数据
            response = self.financial_service.get_financial_report(request)
            
            if not response.success or not response.data:
                return FinancialDownloadResult(
                    stock_code=request.stock_code,
                    report_type=request.report_type,
                    success=False,
                    error=response.message or "未获取到数据"
                )
            
            # 优先使用原始DataFrame，保留所有字段包括STD_ITEM_NAME
            if hasattr(response.data, 'raw_dataframe') and response.data.raw_dataframe is not None:
                df = response.data.raw_dataframe.copy()
                # 应用英文字段映射
                df = self._apply_english_field_mapping(df, use_english_fields)
            elif response.data.data_list:
                # 备选方案：使用转换后的数据
                df = self._prepare_dataframe(response.data.data_list, use_english_fields)
            else:
                return FinancialDownloadResult(
                    stock_code=request.stock_code,
                    report_type=request.report_type,
                    success=False,
                    error="未获取到数据"
                )
            
            if df.empty:
                return FinancialDownloadResult(
                    stock_code=request.stock_code,
                    report_type=request.report_type,
                    success=False,
                    error="没有可用的数据"
                )
            
            # 应用年份筛选
            if start_year is not None or end_year is not None:
                df = self._filter_by_year_range(df, start_year, end_year)
                if df.empty:
                    return FinancialDownloadResult(
                        stock_code=request.stock_code,
                        report_type=request.report_type,
                        success=False,
                        error=f"在指定年份范围 ({start_year}-{end_year}) 内没有找到数据"
                    )
            
            # 确定保存路径
            save_dir = self.download_dir
            if subfolder:
                save_dir = save_dir / subfolder
                save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if custom_filename:
                filename = custom_filename
                if not filename.endswith(f".{format_type}"):
                    filename += f".{format_type}"
            else:
                filename = self.generate_filename(
                    request.stock_code, 
                    request.report_type, 
                    format_type
                )
            
            file_path = save_dir / filename
            
            # 保存文件
            save_func = self._output_formats.get(format_type, self._save_as_csv)
            if format_type in ['pivot-csv', 'pivot-excel']:
                success = save_func(df, file_path, use_english_fields)
            else:
                success = save_func(df, file_path)
            
            if success:
                self.logger.info(f"财务数据下载成功: {file_path}")
                return FinancialDownloadResult(
                    stock_code=request.stock_code,
                    report_type=request.report_type,
                    success=True,
                    file_path=str(file_path),
                    record_count=len(df)
                )
            else:
                return FinancialDownloadResult(
                    stock_code=request.stock_code,
                    report_type=request.report_type,
                    success=False,
                    error="文件保存失败"
                )
            
        except Exception as e:
            error_msg = f"下载财务数据失败: {str(e)}"
            self.logger.error(error_msg)
            return FinancialDownloadResult(
                stock_code=request.stock_code,
                report_type=request.report_type,
                success=False,
                error=error_msg
            )
    
    def download_all_financial_data(
        self,
        stock_code: str,
        format_type: str = "csv",
        use_english_fields: bool = True,
        subfolder: Optional[str] = None,
        limit: Optional[int] = None,
        period: Optional[ReportPeriod] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[FinancialDownloadResult]:
        """
        下载所有类型的财务数据
        
        Args:
            stock_code: 股票代码
            format_type: 输出格式
            use_english_fields: 是否使用英文字段名
            subfolder: 子文件夹
            limit: 每种类型的数据条数限制
            
        Returns:
            下载结果列表
        """
        results = []
        
        # 下载各种类型的财务数据
        for report_type in [ReportType.BALANCE_SHEET, ReportType.INCOME_STATEMENT, 
                          ReportType.CASH_FLOW, ReportType.FINANCIAL_INDICATORS]:
            request = FinancialDataRequest(
                stock_code=stock_code,
                report_type=report_type,
                report_period=period,
                limit=limit
            )
            
            result = self.download_financial_data(
                request=request,
                format_type=format_type,
                use_english_fields=use_english_fields,
                subfolder=subfolder or stock_code,
                start_year=start_year,
                end_year=end_year
            )
            
            results.append(result)
        
        return results
    
    def download_batch_financial_data(
        self,
        stock_codes: List[str],
        report_types: Optional[List[ReportType]] = None,
        format_type: str = "csv",
        use_english_fields: bool = True,
        organize_by_stock: bool = True,
        limit: Optional[int] = None,
    ) -> Dict[str, List[FinancialDownloadResult]]:
        """
        批量下载财务数据
        
        Args:
            stock_codes: 股票代码列表
            report_types: 报表类型列表
            format_type: 输出格式
            use_english_fields: 是否使用英文字段名
            organize_by_stock: 是否按股票组织文件夹
            limit: 每种类型的数据条数限制
            
        Returns:
            下载结果字典
        """
        if report_types is None:
            report_types = [ReportType.BALANCE_SHEET, ReportType.INCOME_STATEMENT, 
                          ReportType.CASH_FLOW, ReportType.FINANCIAL_INDICATORS]
        
        all_results = {}
        
        for stock_code in stock_codes:
            self.logger.info(f"开始下载股票 {stock_code} 的财务数据")
            
            stock_results = []
            subfolder = stock_code if organize_by_stock else None
            
            for report_type in report_types:
                request = FinancialDataRequest(
                    stock_code=stock_code,
                    report_type=report_type,
                    limit=limit
                )
                
                result = self.download_financial_data(
                    request=request,
                    format_type=format_type,
                    use_english_fields=use_english_fields,
                    subfolder=subfolder
                )
                
                stock_results.append(result)
            
            all_results[stock_code] = stock_results
        
        return all_results
    
    def get_download_statistics(self, results: List[FinancialDownloadResult]) -> Dict[str, Union[int, float]]:
        """
        获取下载统计信息
        
        Args:
            results: 下载结果列表
            
        Returns:
            统计信息字典
        """
        if not results:
            return {}
        
        total_count = len(results)
        success_count = sum(1 for r in results if r.success)
        failed_count = total_count - success_count
        total_records = sum(r.record_count for r in results if r.success)
        
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        # 按报表类型统计
        type_stats = {}
        for result in results:
            report_type = result.report_type.value if hasattr(result.report_type, 'value') else str(result.report_type)
            if report_type not in type_stats:
                type_stats[report_type] = {"total": 0, "success": 0, "records": 0}
            
            type_stats[report_type]["total"] += 1
            if result.success:
                type_stats[report_type]["success"] += 1
                type_stats[report_type]["records"] += result.record_count
        
        return {
            "总下载任务数": total_count,
            "成功任务数": success_count,
            "失败任务数": failed_count,
            "成功率": round(success_rate, 2),
            "总记录数": total_records,
            "按类型统计": type_stats,
        }
    
    def cleanup_failed_downloads(self, results: List[FinancialDownloadResult]):
        """
        清理失败的下载文件
        
        Args:
            results: 下载结果列表
        """
        for result in results:
            if not result.success and result.file_path and os.path.exists(result.file_path):
                try:
                    os.remove(result.file_path)
                    self.logger.info(f"已清理失败的下载文件: {result.file_path}")
                except Exception as e:
                    self.logger.error(f"清理文件失败: {result.file_path}, 错误: {e}")