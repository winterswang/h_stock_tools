#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所文档下载工具 - 命令行主入口
"""
from datetime import datetime
from pathlib import Path

import click

from .commands import (
    search_ipo,
    search_annual,
    search_interim,
    search_quarterly,
    download_documents,
    search_stock,
    download_financial,
    batch_download_financial,
    show_financial,
)


@click.group()
@click.version_option(version="1.0.0")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
@click.option("--config", "-c", type=click.Path(), help="配置文件路径")
@click.pass_context
def main(ctx, verbose, config):
    """
    港交所上市公司信息查询和下载工具

    支持查询和下载IPO招股书、年度业绩公告、中期业绩公告等文档。
    """
    # 确保上下文对象存在
    ctx.ensure_object(dict)

    # 设置全局配置
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config

    if verbose:
        click.echo("港交所文档下载工具 v1.0.0")
        click.echo("=" * 40)


# 注册子命令
main.add_command(search_ipo)
main.add_command(search_annual)
main.add_command(search_interim)
main.add_command(search_quarterly)
main.add_command(download_documents)
main.add_command(search_stock)

# 财务数据相关命令
main.add_command(download_financial)
main.add_command(batch_download_financial)
main.add_command(show_financial)


@main.command()
@click.option(
    "--from-date",
    "-f",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    default=datetime.now().replace(day=1).strftime("%Y%m%d"),
    help="开始日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    "-t",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    default=datetime.now().strftime("%Y%m%d"),
    help="结束日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option("--stock-code", "-s", help="股票代码 (如: 00700)")
@click.option(
    "--output-dir", "-o", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option("--pdf-only/--no-pdf-only", default=True, help="只下载PDF文档")
@click.option("--async-download", is_flag=True, default=True, help="使用异步下载")
@click.pass_context
def quick_download(
    ctx, from_date, to_date, stock_code, output_dir, pdf_only, async_download
):
    """
    快速下载 - 一键下载IPO招股书和业绩公告
    """
    from ..api.client import HKExClient
    from ..services.downloader import DocumentDownloader
    from ..services.searcher import DocumentSearcher
    from ..services.stock_resolver import StockResolver

    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"搜索日期范围: {from_date.date()} 到 {to_date.date()}")
        if stock_code:
            click.echo(f"指定股票代码: {stock_code}")
        click.echo(f"下载目录: {output_dir}")
        click.echo()

    try:
        # 初始化服务
        client = HKExClient()
        stock_resolver = StockResolver(
            client, cache_dir=str(Path(output_dir) / "cache")
        )
        searcher = DocumentSearcher(client, stock_resolver)
        downloader = DocumentDownloader(download_dir=output_dir)

        # 搜索文档类型
        document_types = [
            ("IPO招股书", "ipo_prospectus"),
            ("年度业绩公告", "annual_results"),
            ("中期业绩公告", "interim_results"),
            ("季度业绩公告", "quarterly_results"),
        ]

        all_results = []

        for type_name, type_key in document_types:
            click.echo(f"正在搜索{type_name}...")

            try:
                if type_key == "ipo_prospectus":
                    response = searcher.search_ipo_prospectus(
                        from_date=from_date.date(),
                        to_date=to_date.date(),
                        stock_code=stock_code,
                    )
                elif type_key == "annual_results":
                    response = searcher.search_annual_results(
                        from_date=from_date.date(),
                        to_date=to_date.date(),
                        stock_code=stock_code,
                    )
                elif type_key == "interim_results":
                    response = searcher.search_interim_results(
                        from_date=from_date.date(),
                        to_date=to_date.date(),
                        stock_code=stock_code,
                    )
                elif type_key == "quarterly_results":
                    response = searcher.search_quarterly_results(
                        from_date=from_date.date(),
                        to_date=to_date.date(),
                        stock_code=stock_code,
                    )

                if response.documents:
                    click.echo(f"找到 {len(response.documents)} 个{type_name}文档")

                    # 下载文档
                    results = downloader.download_search_results(
                        search_response=response,
                        subfolder=type_name,
                        pdf_only=pdf_only,
                        use_async=async_download,
                    )

                    all_results.extend(results)

                    success_count = sum(1 for r in results if r.success)
                    click.echo(
                        f"{type_name}: 成功下载 {success_count}/{len(results)} 个文档"
                    )
                else:
                    click.echo(f"未找到{type_name}文档")

            except Exception as e:
                click.echo(f"搜索{type_name}时出错: {e}", err=True)

            click.echo()

        # 显示总体统计
        if all_results:
            stats = downloader.get_download_statistics(all_results)
            click.echo("下载完成!")
            click.echo(
                f"总计: {stats['successful_downloads']}/"
                f"{stats['total_downloads']} 个文档下载成功"
            )
            click.echo(f"成功率: {stats['success_rate']:.1%}")
            click.echo(f"总大小: {stats['total_size_mb']:.1f} MB")
            click.echo(f"保存位置: {stats['download_dir']}")
        else:
            click.echo("未下载任何文档")

    except Exception as e:
        click.echo(f"执行失败: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument("stock_codes", nargs=-1, required=True)
@click.option(
    "--from-date",
    "-f",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    default=datetime.now().replace(day=1).strftime("%Y%m%d"),
    help="开始日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    "-t",
    type=click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    default=datetime.now().strftime("%Y%m%d"),
    help="结束日期 (YYYYMMDD 或 YYYY-MM-DD)",
)
@click.option(
    "--output-dir", "-o", type=click.Path(), default="./downloads", help="下载目录"
)
@click.option(
    "--organize-by-company", is_flag=True, default=True, help="按公司组织文件夹"
)
@click.pass_context
def batch_download(
    ctx, stock_codes, from_date, to_date, output_dir, organize_by_company
):
    """
    批量下载 - 为多个股票代码批量下载文档

    STOCK_CODES: 股票代码列表，如: 00700 00981 01024
    """
    from ..api.client import HKExClient
    from ..services.downloader import DocumentDownloader
    from ..services.searcher import DocumentSearcher
    from ..services.stock_resolver import StockResolver

    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"批量下载 {len(stock_codes)} 个股票的文档")
        click.echo(f"股票代码: {', '.join(stock_codes)}")
        click.echo(f"日期范围: {from_date.date()} 到 {to_date.date()}")
        click.echo()

    try:
        # 初始化服务
        client = HKExClient()
        stock_resolver = StockResolver(
            client, cache_dir=str(Path(output_dir) / "cache")
        )
        searcher = DocumentSearcher(client, stock_resolver)
        downloader = DocumentDownloader(download_dir=output_dir)

        all_results = []

        for stock_code in stock_codes:
            click.echo(f"处理股票 {stock_code}...")

            try:
                # 搜索该股票的所有文档
                company_docs = searcher.search_company_documents(
                    stock_code=stock_code,
                    from_date=from_date.date(),
                    to_date=to_date.date(),
                )

                # 合并所有文档
                all_docs = []
                for doc_type, response in company_docs.items():
                    all_docs.extend(response.documents)

                if all_docs:
                    click.echo(f"  找到 {len(all_docs)} 个文档")

                    # 下载文档
                    if organize_by_company:
                        # 获取公司信息
                        company = stock_resolver.resolve_company_info(
                            stock_code
                        )
                        company_name = (
                            company.stock_name if company else stock_code
                        )
                        subfolder = f"{stock_code}_{company_name}"
                    else:
                        subfolder = None

                    from ..models.search import SearchResponse

                    mock_response = SearchResponse(documents=all_docs, sort_list=None)

                    results = downloader.download_search_results(
                        search_response=mock_response,
                        subfolder=subfolder,
                        pdf_only=True,
                        use_async=True,
                    )

                    all_results.extend(results)

                    success_count = sum(1 for r in results if r.success)
                    click.echo(f"  成功下载 {success_count}/{len(results)} 个文档")
                else:
                    click.echo("  未找到文档")

            except Exception as e:
                click.echo(f"  处理股票 {stock_code} 时出错: {e}", err=True)

            click.echo()

        # 显示总体统计
        if all_results:
            stats = downloader.get_download_statistics(all_results)
            click.echo("批量下载完成!")
            click.echo(
                f"总计: {stats['successful_downloads']}/"
                f"{stats['total_downloads']} 个文档下载成功"
            )
            click.echo(f"成功率: {stats['success_rate']:.1%}")
            click.echo(f"总大小: {stats['total_size_mb']:.1f} MB")
            click.echo(f"保存位置: {stats['download_dir']}")
        else:
            click.echo("未下载任何文档")

    except Exception as e:
        click.echo(f"批量下载失败: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
