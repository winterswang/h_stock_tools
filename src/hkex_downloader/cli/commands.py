#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行命令实现
"""

import json
from datetime import datetime
from pathlib import Path

import click

from ..api.client import HKExClient
from ..models.financial import FinancialDataRequest, ReportType, ReportPeriod
from ..models.search import SearchResponse
from ..services.downloader import DocumentDownloader
from ..services.financial_downloader import FinancialDataDownloader
from ..services.financial_service import FinancialDataService
from ..services.searcher import DocumentSearcher
from ..services.stock_resolver import StockResolver


def get_services(output_dir: str = "./downloads") -> tuple:
    """
    获取服务实例
    """
    client = HKExClient()
    cache_dir = str(Path(output_dir) / "cache")
    stock_resolver = StockResolver(client, cache_dir=cache_dir)
    searcher = DocumentSearcher(client, stock_resolver)
    downloader = DocumentDownloader(download_dir=output_dir)

    return client, stock_resolver, searcher, downloader


def format_date_range(from_date: datetime, to_date: datetime) -> str:
    """
    格式化日期范围显示
    """
    return f"{from_date.strftime('%Y-%m-%d')} 到 {to_date.strftime('%Y-%m-%d')}"


def display_search_results(response: SearchResponse, document_type: str) -> None:
    """
    显示搜索结果
    """
    if not response.documents:
        click.echo(f"未找到{document_type}文档")
        return

    click.echo(f"找到 {len(response.documents)} 个{document_type}文档:")
    click.echo()

    for i, doc in enumerate(response.documents[:10], 1):  # 只显示前10个
        click.echo(f"{i:2d}. {doc.stock_code} - {doc.stock_name}")
        click.echo(f"    标题: {doc.title}")
        click.echo(f"    时间: {doc.date_time}")
        click.echo(f"    类型: {doc.file_type or 'HTML'}")
        if doc.file_info:
            click.echo(f"    大小: {doc.file_info}")
        click.echo()

    if len(response.documents) > 10:
        click.echo(f"... 还有 {len(response.documents) - 10} 个文档")
        click.echo()


@click.command()
@click.option(
    "--from-date",
    "-f",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="开始日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    "-t",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="结束日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option("--stock-code", "-s", help="股票代码 (如: 00700)")
@click.option("--output", "-o", type=click.File("w"), help="输出到文件 (JSON格式)")
@click.option("--download", "-d", is_flag=True, help="直接下载找到的文档")
@click.option(
    "--download-dir", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option("--pdf-only/--no-pdf-only", default=True, help="只下载PDF文档")
@click.pass_context
def search_ipo(
    ctx, from_date, to_date, stock_code, output, download, download_dir, pdf_only
):
    """
    搜索IPO招股书文档
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("搜索IPO招股书")
        click.echo(f"日期范围: {format_date_range(from_date, to_date)}")
        if stock_code:
            click.echo(f"股票代码: {stock_code}")
        click.echo()

    try:
        _, stock_resolver, searcher, downloader = get_services(download_dir)

        # 搜索IPO文档
        response = searcher.search_ipo_prospectus(
            from_date=from_date.date(),
            to_date=to_date.date(),
            stock_code=stock_code,
        )

        # 显示结果
        display_search_results(response, "IPO招股书")

        # 输出到文件
        if output:
            data = {
                "search_type": "ipo_prospectus",
                "from_date": from_date.date().isoformat(),
                "to_date": to_date.date().isoformat(),
                "stock_code": stock_code,
                "total_documents": len(response.documents),
                "documents": [doc.dict() for doc in response.documents],
            }
            json.dump(data, output, ensure_ascii=False, indent=2)
            click.echo(f"搜索结果已保存到 {output.name}")

        # 下载文档
        if download and response.documents:
            results = downloader.download_search_results(
                response, subfolder="IPO招股书", pdf_only=pdf_only
            )
            
            success_count = sum(1 for r in results if r.success)
            click.echo(f"\n下载完成: {success_count}/{len(results)} 成功")

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        ctx.exit(1)


@click.command()
@click.argument("stock_code")
@click.option(
    "--report-type",
    "-t",
    type=click.Choice(["balance_sheet", "income_statement", "cash_flow", "financial_indicators", "all"]),
    default="all",
    help="报表类型"
)
@click.option(
    "--period",
    "-p",
    type=click.Choice(["annual", "interim"]),
    default="annual",
    help="报告期类型: annual=年度, interim=报告期"
)
@click.option(
    "--start-year",
    type=int,
    help="开始年份 (默认为当前年份-10年)"
)
@click.option(
    "--end-year",
    type=int,
    help="结束年份 (默认为当前年份)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "excel", "json", "pivot-csv", "pivot-excel"]),
    default="csv",
    help="输出格式: csv=纵向格式, pivot-csv=横向透视格式"
)
@click.option(
    "--download-dir",
    "-d",
    type=click.Path(),
    default="./data/financial",
    help="下载目录"
)
@click.option(
    "--english-fields/--chinese-fields",
    default=True,
    help="使用英文字段名"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="数据条数限制"
)
@click.option(
    "--organize-by-stock",
    is_flag=True,
    default=True,
    help="按股票代码组织文件夹"
)
@click.pass_context
def download_financial(ctx, stock_code, report_type, period, start_year, end_year, format, download_dir, english_fields, limit, organize_by_stock):
    """
    下载财务数据
    
    STOCK_CODE: 股票代码 (如: 00700)
    """
    try:
        # 设置默认年份范围（最近十年）
        current_year = datetime.now().year
        if start_year is None:
            start_year = current_year - 10
        if end_year is None:
            end_year = current_year
            
        # 验证年份范围
        if start_year > end_year:
            click.echo(f"错误: 开始年份 ({start_year}) 不能大于结束年份 ({end_year})")
            return
            
        click.echo(f"开始下载股票 {stock_code} 的财务数据...")
        click.echo(f"报告期类型: {'年度' if period == 'annual' else '报告期'}")
        click.echo(f"年份范围: {start_year} - {end_year}")
        
        # 创建财务数据下载器
        financial_downloader = FinancialDataDownloader(
            download_dir=download_dir
        )
        
        # 报告期类型映射
        period_mapping = {
            "annual": ReportPeriod.ANNUAL,
            "interim": ReportPeriod.INTERIM
        }
        
        if report_type == "all":
            # 下载所有类型的财务数据
            results = financial_downloader.download_all_financial_data(
                stock_code=stock_code,
                format_type=format,
                use_english_fields=english_fields,
                subfolder=stock_code if organize_by_stock else None,
                limit=limit,
                period=period_mapping[period],
                start_year=start_year,
                end_year=end_year
            )
        else:
            # 下载指定类型的财务数据
            report_type_mapping = {
                "balance_sheet": ReportType.BALANCE_SHEET,
                "income_statement": ReportType.INCOME_STATEMENT,
                "cash_flow": ReportType.CASH_FLOW,
                "financial_indicators": ReportType.FINANCIAL_INDICATORS
            }
            
            request = FinancialDataRequest(
                stock_code=stock_code,
                report_type=report_type_mapping[report_type],
                report_period=period_mapping[period],
                limit=limit
            )
            
            result = financial_downloader.download_financial_data(
                request=request,
                format_type=format,
                use_english_fields=english_fields,
                subfolder=stock_code if organize_by_stock else None,
                start_year=start_year,
                end_year=end_year
            )
            
            results = [result]
        
        # 显示结果
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        click.echo(f"\n下载完成: {success_count}/{total_count} 成功")
        
        for result in results:
            report_type_name = result.report_type.value if hasattr(result.report_type, 'value') else str(result.report_type)
            if result.success:
                click.echo(f"✓ {report_type_name}: {result.file_path} ({result.record_count}条记录)")
            else:
                click.echo(f"✗ {report_type_name}: {result.error}")
        
        # 显示统计信息
        if results:
            stats = financial_downloader.get_download_statistics(results)
            click.echo(f"\n统计信息:")
            click.echo(f"  总记录数: {stats.get('总记录数', 0)}")
            click.echo(f"  成功率: {stats.get('成功率', 0)}%")
        
    except Exception as e:
        click.echo(f"下载失败: {e}", err=True)
        ctx.exit(1)


@click.command()
@click.argument("stock_codes", nargs=-1, required=True)
@click.option(
    "--report-types",
    "-t",
    multiple=True,
    type=click.Choice(["balance_sheet", "income_statement", "cash_flow", "financial_indicators"]),
    help="报表类型 (可多选)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "excel", "json", "pivot-csv", "pivot-excel"]),
    default="csv",
    help="输出格式: csv=纵向格式, pivot-csv=横向透视格式"
)
@click.option(
    "--download-dir",
    "-d",
    type=click.Path(),
    default="./data/financial",
    help="下载目录"
)
@click.option(
    "--english-fields/--chinese-fields",
    default=True,
    help="使用英文字段名"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="每种类型的数据条数限制"
)
@click.option(
    "--organize-by-stock",
    is_flag=True,
    default=True,
    help="按股票代码组织文件夹"
)
@click.pass_context
def batch_download_financial(ctx, stock_codes, report_types, format, download_dir, english_fields, limit, organize_by_stock):
    """
    批量下载财务数据
    
    STOCK_CODES: 股票代码列表 (如: 00700 00981 01810)
    """
    try:
        if not stock_codes:
            click.echo("请提供至少一个股票代码", err=True)
            ctx.exit(1)
        
        # 如果没有指定报表类型，下载所有类型
        if not report_types:
            report_types_enum = [ReportType.BALANCE_SHEET, ReportType.INCOME_STATEMENT, 
                               ReportType.CASH_FLOW, ReportType.FINANCIAL_INDICATORS]
        else:
            report_type_mapping = {
                "balance_sheet": ReportType.BALANCE_SHEET,
                "income_statement": ReportType.INCOME_STATEMENT,
                "cash_flow": ReportType.CASH_FLOW,
                "financial_indicators": ReportType.FINANCIAL_INDICATORS
            }
            report_types_enum = [report_type_mapping[rt] for rt in report_types]
        
        click.echo(f"开始批量下载 {len(stock_codes)} 只股票的财务数据...")
        
        # 创建财务数据下载器
        financial_downloader = FinancialDataDownloader(
            download_dir=download_dir
        )
        
        # 批量下载
        all_results = financial_downloader.download_batch_financial_data(
            stock_codes=list(stock_codes),
            report_types=report_types_enum,
            format_type=format,
            use_english_fields=english_fields,
            organize_by_stock=organize_by_stock,
            limit=limit
        )
        
        # 显示结果
        total_tasks = 0
        total_success = 0
        
        click.echo("\n下载结果:")
        for stock_code, results in all_results.items():
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)
            total_tasks += total_count
            total_success += success_count
            
            click.echo(f"\n{stock_code}: {success_count}/{total_count} 成功")
            for result in results:
                 report_type_name = result.report_type.value if hasattr(result.report_type, 'value') else str(result.report_type)
                 if result.success:
                     click.echo(f"  ✓ {report_type_name}: {result.record_count}条记录")
                 else:
                     click.echo(f"  ✗ {report_type_name}: {result.error}")
        
        # 显示总体统计
        click.echo(f"\n总体统计:")
        click.echo(f"  总任务数: {total_tasks}")
        click.echo(f"  成功任务数: {total_success}")
        click.echo(f"  成功率: {(total_success/total_tasks*100):.1f}%" if total_tasks > 0 else "  成功率: 0%")
        
    except Exception as e:
        click.echo(f"批量下载失败: {e}", err=True)
        ctx.exit(1)


@click.command()
@click.argument("stock_code")
@click.option(
    "--report-type",
    "-t",
    type=click.Choice(["balance_sheet", "income_statement", "cash_flow", "financial_indicators"]),
    required=True,
    help="报表类型"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=5,
    help="显示条数限制"
)
@click.pass_context
def show_financial(ctx, stock_code, report_type, limit):
    """
    查看财务数据 (不下载)
    
    STOCK_CODE: 股票代码 (如: 00700)
    """
    try:
        click.echo(f"正在获取股票 {stock_code} 的{report_type}数据...")
        
        # 创建财务数据服务
        financial_service = FinancialDataService()
        
        # 报表类型映射
        report_type_mapping = {
            "balance_sheet": ReportType.BALANCE_SHEET,
            "income_statement": ReportType.INCOME_STATEMENT,
            "cash_flow": ReportType.CASH_FLOW,
            "financial_indicators": ReportType.FINANCIAL_INDICATORS
        }
        
        request = FinancialDataRequest(
            stock_code=stock_code,
            report_type=report_type_mapping[report_type],
            limit=limit
        )
        
        response = financial_service.get_financial_report(request)
        
        if not response.success:
            click.echo(f"获取数据失败: {response.message}", err=True)
            ctx.exit(1)
        
        if not response.data or not response.data.data_list:
            click.echo("未找到财务数据")
            return
        
        # 显示数据
        click.echo(f"\n找到 {len(response.data.data_list)} 条记录:")
        click.echo("=" * 80)
        
        for i, data in enumerate(response.data.data_list[:limit], 1):
            click.echo(f"\n记录 {i}:")
            click.echo(f"  股票代码: {data.stock_code}")
            click.echo(f"  股票名称: {data.stock_name or 'N/A'}")
            click.echo(f"  报告期: {data.report_date}")
            click.echo(f"  报表类型: {data.report_type.value if hasattr(data.report_type, 'value') else str(data.report_type)}")
            click.echo(f"  货币单位: {data.currency}")
            
            # 显示主要财务指标
            if hasattr(data, 'total_assets') and data.total_assets:
                click.echo(f"  总资产: {data.total_assets:,.0f}")
            if hasattr(data, 'total_revenue') and data.total_revenue:
                click.echo(f"  营业总收入: {data.total_revenue:,.0f}")
            if hasattr(data, 'net_profit') and data.net_profit:
                click.echo(f"  净利润: {data.net_profit:,.0f}")
            if hasattr(data, 'operating_cash_flow') and data.operating_cash_flow:
                click.echo(f"  经营现金流: {data.operating_cash_flow:,.0f}")
            if hasattr(data, 'roe') and data.roe:
                click.echo(f"  净资产收益率: {data.roe:.2%}")
        
    except Exception as e:
        click.echo(f"查看数据失败: {e}", err=True)
        ctx.exit(1)

        # 下载文档
        if download and response.documents:
            click.echo("开始下载文档...")
            results = downloader.download_search_results(
                search_response=response,
                subfolder="IPO招股书",
                pdf_only=True,
                use_async=True,
            )

            stats = downloader.get_download_statistics(results)
            click.echo(
                f"下载完成: {stats['successful_downloads']}/"
                f"{stats['total_downloads']} 个文档"
            )

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        raise click.Abort()


@click.command()
@click.option(
    "--from-date",
    "-f",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="开始日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    "-t",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="结束日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option("--stock-code", "-s", help="股票代码 (如: 00700)")
@click.option("--output", "-o", type=click.File("w"), help="输出到文件 (JSON格式)")
@click.option("--download", "-d", is_flag=True, help="直接下载找到的文档")
@click.option(
    "--download-dir", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option("--pdf-only/--no-pdf-only", default=True, help="只下载PDF文档")
@click.pass_context
def search_annual(
    ctx, from_date, to_date, stock_code, output, download, download_dir, pdf_only
):
    """
    搜索年度业绩公告
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("搜索年度业绩公告")
        click.echo(f"日期范围: {format_date_range(from_date, to_date)}")
        if stock_code:
            click.echo(f"股票代码: {stock_code}")
        click.echo()

    try:
        _, stock_resolver, searcher, downloader = get_services(download_dir)

        # 搜索年度业绩文档
        response = searcher.search_annual_results(
            from_date=from_date.date(),
            to_date=to_date.date(),
            stock_code=stock_code,
        )

        # 显示结果
        display_search_results(response, "年度业绩公告")

        # 输出到文件
        if output:
            data = {
                "search_type": "annual_results",
                "from_date": from_date.date().isoformat(),
                "to_date": to_date.date().isoformat(),
                "stock_code": stock_code,
                "total_documents": len(response.documents),
                "documents": [doc.dict() for doc in response.documents],
            }
            json.dump(data, output, ensure_ascii=False, indent=2)
            click.echo(f"搜索结果已保存到 {output.name}")

        # 下载文档
        if download and response.documents:
            click.echo("开始下载文档...")
            results = downloader.download_search_results(
                search_response=response,
                subfolder="年度业绩公告",
                pdf_only=pdf_only,
                use_async=True,
            )

            stats = downloader.get_download_statistics(results)
            click.echo(
                f"下载完成: {stats['successful_downloads']}/"
                f"{stats['total_downloads']} 个文档"
            )

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        raise click.Abort()


@click.command()
@click.option(
    "--from-date",
    "-f",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="开始日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    "-t",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="结束日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option("--stock-code", "-s", help="股票代码 (如: 00700)")
@click.option("--output", "-o", type=click.File("w"), help="输出到文件 (JSON格式)")
@click.option("--download", "-d", is_flag=True, help="直接下载找到的文档")
@click.option(
    "--download-dir", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option("--pdf-only/--no-pdf-only", default=True, help="只下载PDF文档")
@click.pass_context
def search_interim(
    ctx, from_date, to_date, stock_code, output, download, download_dir, pdf_only
):
    """
    搜索中期业绩公告
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("搜索中期业绩公告")
        click.echo(f"日期范围: {format_date_range(from_date, to_date)}")
        if stock_code:
            click.echo(f"股票代码: {stock_code}")
        click.echo()

    try:
        _, stock_resolver, searcher, downloader = get_services(download_dir)

        # 搜索中期业绩文档
        response = searcher.search_interim_results(
            from_date=from_date.date(),
            to_date=to_date.date(),
            stock_code=stock_code,
        )

        # 显示结果
        display_search_results(response, "中期业绩公告")

        # 输出到文件
        if output:
            data = {
                "search_type": "interim_results",
                "from_date": from_date.date().isoformat(),
                "to_date": to_date.date().isoformat(),
                "stock_code": stock_code,
                "total_documents": len(response.documents),
                "documents": [doc.dict() for doc in response.documents],
            }
            json.dump(data, output, ensure_ascii=False, indent=2)
            click.echo(f"搜索结果已保存到 {output.name}")

        # 下载文档
        if download and response.documents:
            click.echo("开始下载文档...")
            results = downloader.download_search_results(
                search_response=response,
                subfolder="中期业绩公告",
                pdf_only=pdf_only,
                use_async=True,
            )

            stats = downloader.get_download_statistics(results)
            click.echo(
                f"下载完成: {stats['successful_downloads']}/"
                f"{stats['total_downloads']} 个文档"
            )

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        raise click.Abort()


@click.command()
@click.option(
    "--from-date",
    "-f",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="开始日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    "-t",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    required=True,
    help="结束日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option("--stock-code", "-s", help="股票代码 (如: 00700)")
@click.option("--output", "-o", type=click.File("w"), help="输出到文件 (JSON格式)")
@click.option("--download", "-d", is_flag=True, help="直接下载找到的文档")
@click.option(
    "--download-dir", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option("--pdf-only/--no-pdf-only", default=True, help="只下载PDF文档")
@click.pass_context
def search_quarterly(
    ctx, from_date, to_date, stock_code, output, download, download_dir, pdf_only
):
    """
    搜索季度业绩公告
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("搜索季度业绩公告")
        click.echo(f"日期范围: {format_date_range(from_date, to_date)}")
        if stock_code:
            click.echo(f"股票代码: {stock_code}")
        click.echo()

    try:
        _, stock_resolver, searcher, downloader = get_services(download_dir)

        # 搜索季度业绩文档
        response = searcher.search_quarterly_results(
            from_date=from_date.date(),
            to_date=to_date.date(),
            stock_code=stock_code,
        )

        # 显示结果
        display_search_results(response, "季度业绩公告")

        # 输出到文件
        if output:
            data = {
                "search_type": "quarterly_results",
                "from_date": from_date.date().isoformat(),
                "to_date": to_date.date().isoformat(),
                "stock_code": stock_code,
                "total_documents": len(response.documents),
                "documents": [doc.dict() for doc in response.documents],
            }
            json.dump(data, output, ensure_ascii=False, indent=2)
            click.echo(f"搜索结果已保存到 {output.name}")

        # 下载文档
        if download and response.documents:
            click.echo("开始下载文档...")
            results = downloader.download_search_results(
                search_response=response,
                subfolder="季度业绩公告",
                pdf_only=pdf_only,
                use_async=True,
            )

            stats = downloader.get_download_statistics(results)
            click.echo(
                f"下载完成: {stats['successful_downloads']}/"
                f"{stats['total_downloads']} 个文档"
            )

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        raise click.Abort()


@click.command()
@click.argument("input_file", type=click.File("r"))
@click.option(
    "--download-dir", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option("--pdf-only/--no-pdf-only", default=True, help="只下载PDF文档")
@click.option(
    "--organize-by-company", is_flag=True, default=True, help="按公司组织文件夹"
)
@click.option("--max-concurrent", type=int, default=5, help="最大并发下载数")
@click.pass_context
def download_documents(
    ctx,
    input_file,
    download_dir,
    pdf_only,
    organize_by_company,
    max_concurrent,
):
    """
    从JSON文件下载文档

    INPUT_FILE: 包含搜索结果的JSON文件
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        # 读取搜索结果
        data = json.load(input_file)

        if "documents" not in data:
            click.echo("错误: JSON文件格式不正确，缺少 'documents' 字段", err=True)
            raise click.Abort()

        # 创建文档对象
        from ..models.company import Document

        documents = []

        for doc_data in data["documents"]:
            try:
                doc = Document(**doc_data)
                documents.append(doc)
            except Exception as e:
                if verbose:
                    click.echo(f"跳过无效文档: {e}", err=True)
                continue

        if not documents:
            click.echo("未找到有效的文档数据")
            return

        if verbose:
            click.echo(f"准备下载 {len(documents)} 个文档")
            click.echo(f"下载目录: {download_dir}")
            click.echo(f"PDF模式: {pdf_only}")
            click.echo(f"按公司组织: {organize_by_company}")
            click.echo()

        # 初始化下载器
        downloader = DocumentDownloader(
            download_dir=download_dir, max_concurrent=max_concurrent
        )

        # 创建搜索响应对象
        response = SearchResponse(documents=documents, sort_list=None)

        if organize_by_company:
            # 按公司组织下载
            results_by_company = downloader.organize_downloads_by_company(
                search_response=response, pdf_only=pdf_only, use_async=True
            )

            # 合并所有结果
            all_results = []
            for company_results in results_by_company.values():
                all_results.extend(company_results)
        else:
            # 统一下载
            all_results = downloader.download_search_results(
                search_response=response, pdf_only=pdf_only, use_async=True
            )

        # 显示统计信息
        stats = downloader.get_download_statistics(all_results)
        click.echo("下载完成!")
        click.echo(
            f"总计: {stats['successful_downloads']}/"
            f"{stats['total_downloads']} 个文档下载成功"
        )
        click.echo(f"成功率: {stats['success_rate']:.1%}")
        click.echo(f"总大小: {stats['total_size_mb']:.1f} MB")

        # 显示失败的下载
        failed_results = [r for r in all_results if not r.success]
        if failed_results and verbose:
            click.echo("\n失败的下载:")
            for result in failed_results[:5]:  # 只显示前5个
                click.echo(
                    f"  {result.document.stock_code} - "
                    f"{result.document.title[:30]}..."
                )
                click.echo(f"    错误: {result.error}")

            if len(failed_results) > 5:
                click.echo(f"  ... 还有 {len(failed_results) - 5} 个失败的下载")

    except json.JSONDecodeError as e:
        click.echo(f"JSON文件解析失败: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"下载失败: {e}", err=True)
        raise click.Abort()


@click.command()
@click.argument("keyword")
@click.option("--output", "-o", type=click.File("w"), help="输出到文件 (JSON格式)")
@click.pass_context
def search_stock(ctx, keyword, output):
    """
    搜索股票信息

    KEYWORD: 股票代码或公司名称关键词
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"搜索股票: {keyword}")
        click.echo()

    try:
        client, stock_resolver, _, _ = get_services()

        # 搜索股票
        companies = stock_resolver.search_companies(keyword)

        if not companies:
            click.echo(f"未找到匹配 '{keyword}' 的股票")
            return

        click.echo(f"找到 {len(companies)} 个匹配的股票:")
        click.echo()

        for i, company in enumerate(companies, 1):
            click.echo(
                f"{i:2d}. {company.get('code', 'N/A')} - "
                f"{company.get('name', 'N/A')}"
            )
            if company.get("id"):
                click.echo(f"    股票ID: {company['id']}")
            click.echo()

        # 输出到文件
        if output:
            data = {
                "keyword": keyword,
                "total_companies": len(companies),
                "companies": companies,
            }
            json.dump(data, output, ensure_ascii=False, indent=2)
            click.echo(f"搜索结果已保存到 {output.name}")

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        raise click.Abort()
