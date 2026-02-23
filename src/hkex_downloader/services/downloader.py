#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档下载服务

提供港交所文档下载功能
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import aiofiles
import aiohttp
from tqdm import tqdm

from ..api.client import HKExClient
from ..models.company import Document
from ..models.search import SearchResponse


class DownloadResult:
    """
    下载结果
    """

    def __init__(
        self,
        document: Document,
        success: bool,
        file_path: Optional[str] = None,
        error: Optional[str] = None,
        file_size: Optional[int] = None,
    ):
        self.document = document
        self.success = success
        self.file_path = file_path
        self.error = error
        self.file_size = file_size
        self.download_time = datetime.now()

    def __repr__(self):
        status = "成功" if self.success else "失败"
        return (
            f"DownloadResult({self.document.stock_code}-"
            f"{self.document.title[:20]}..., {status})"
        )


class DocumentDownloader:
    """
    文档下载服务

    支持单个和批量文档下载，提供进度显示和错误处理
    """

    def __init__(
        self,
        client: Optional[HKExClient] = None,
        download_dir: str = "./downloads",
        max_concurrent: int = 2,
        chunk_size: int = 8192,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        初始化文档下载服务

        Args:
            client: HKEx API客户端
            download_dir: 下载目录
            max_concurrent: 最大并发下载数
            chunk_size: 下载块大小
            timeout: 下载超时时间（秒）
            max_retries: 最大重试次数
        """
        self.client = client or HKExClient()
        self.download_dir = Path(download_dir)
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries

        # 确保下载目录存在
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, document: Document) -> str:
        """
        生成文件名

        Args:
            document: 文档对象

        Returns:
            文件名
        """
        import re

        # 清理股票代码中的HTML标签和特殊字符
        clean_stock_code = re.sub(
            r"<[^>]+>", "", document.stock_code
        )  # 移除HTML标签
        clean_stock_code = re.sub(r"[^\w]", "", clean_stock_code)  # 只保留字母数字
        clean_stock_code = clean_stock_code[:10]  # 限制长度

        # 清理标题中的HTML标签和非法字符
        clean_title = re.sub(r"<[^>]+>", "", document.title)  # 移除HTML标签
        clean_title = re.sub(
            r"[^\w\u4e00-\u9fff\s-]", "", clean_title
        )  # 保留中英文、数字、空格、连字符
        clean_title = re.sub(r"\s+", "_", clean_title.strip())  # 将空格替换为下划线
        clean_title = clean_title[:50]  # 限制长度

        # 获取文件扩展名
        if document.is_pdf:
            ext = ".pdf"
        else:
            # 从URL中提取扩展名
            parsed_url = urlparse(document.file_link)
            ext = Path(parsed_url.path).suffix or ".html"

        # 生成文件名: 股票代码_日期_标题.扩展名
        date_str = ""
        if document.parsed_datetime:
            date_str = document.parsed_datetime.strftime("%Y%m%d")

        filename = f"{clean_stock_code}_{date_str}_{clean_title}{ext}"

        # 确保文件名不重复
        counter = 1
        original_filename = filename
        while (self.download_dir / filename).exists():
            name_part = Path(original_filename).stem
            ext_part = Path(original_filename).suffix
            filename = f"{name_part}_{counter}{ext_part}"
            counter += 1

        return filename

    def download_document(
        self,
        document: Document,
        custom_filename: Optional[str] = None,
        subfolder: Optional[str] = None,
    ) -> DownloadResult:
        """
        下载单个文档

        Args:
            document: 文档对象
            custom_filename: 自定义文件名
            subfolder: 子文件夹名称

        Returns:
            下载结果
        """
        try:
            # 确定保存路径
            if subfolder:
                save_dir = self.download_dir / subfolder
                save_dir.mkdir(parents=True, exist_ok=True)
            else:
                save_dir = self.download_dir

            filename = custom_filename or self.generate_filename(document)
            file_path = save_dir / filename

            # 下载文档
            success = self.client.download_document(
                document=document,
                save_path=str(file_path),
                chunk_size=self.chunk_size,
            )

            if success:
                file_size = file_path.stat().st_size
                return DownloadResult(
                    document=document,
                    success=True,
                    file_path=str(file_path),
                    file_size=file_size,
                )
            else:
                return DownloadResult(
                    document=document, success=False, error="下载失败"
                )

        except Exception as e:
            return DownloadResult(
                document=document, success=False, error=str(e)
            )

    async def download_document_async(
        self,
        session: aiohttp.ClientSession,
        document: Document,
        custom_filename: Optional[str] = None,
        subfolder: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> DownloadResult:
        """
        异步下载单个文档（带重试机制）

        Args:
            session: aiohttp会话
            document: 文档对象
            custom_filename: 自定义文件名
            subfolder: 子文件夹名称
            progress_callback: 进度回调函数

        Returns:
            下载结果
        """
        # 确定保存路径
        if subfolder:
            save_dir = self.download_dir / subfolder
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.download_dir

        filename = custom_filename or self.generate_filename(document)
        file_path = save_dir / filename
        url = document.full_file_url

        # 带重试机制的下载逻辑
        last_error = None
        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(
                    total=self.timeout,
                    connect=30,
                    sock_read=self.timeout - 30
                )
                
                async with session.get(url, timeout=timeout) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded_size = 0

                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(
                            self.chunk_size
                        ):
                            await f.write(chunk)
                            downloaded_size += len(chunk)

                            if progress_callback:
                                progress_callback(downloaded_size, total_size)

                    file_size = file_path.stat().st_size
                    return DownloadResult(
                        document=document,
                        success=True,
                        file_path=str(file_path),
                        file_size=file_size,
                    )

            except asyncio.TimeoutError as e:
                last_error = f"下载超时 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 10))  # 指数退避，最大10秒
                    continue
            except aiohttp.ClientError as e:
                last_error = f"网络错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 5))  # 指数退避，最大5秒
                    continue
            except Exception as e:
                last_error = f"未知错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue

        # 清理失败的文件
        if file_path.exists():
            try:
                file_path.unlink()
            except:
                pass

        return DownloadResult(
            document=document, 
            success=False, 
            error=last_error or "下载失败"
        )

    def download_documents(
        self,
        documents: List[Document],
        subfolder: Optional[str] = None,
        show_progress: bool = True,
        filter_pdf_only: bool = False,
    ) -> List[DownloadResult]:
        """
        批量下载文档（同步版本）

        Args:
            documents: 文档列表
            subfolder: 子文件夹名称
            show_progress: 是否显示进度条
            filter_pdf_only: 是否只下载PDF文档

        Returns:
            下载结果列表
        """
        if filter_pdf_only:
            pdf_docs = [doc for doc in documents if doc.is_pdf]
            non_pdf_count = len(documents) - len(pdf_docs)
            if non_pdf_count > 0:
                print(f"跳过 {non_pdf_count} 个非PDF文件")
            documents = pdf_docs

        if not documents:
            print("没有找到可下载的文档")
            return []

        results = []

        if show_progress:
            documents = tqdm(documents, desc="下载文档")

        for document in documents:
            result = self.download_document(document, subfolder=subfolder)
            results.append(result)

            if show_progress and hasattr(documents, "set_postfix"):
                success_count = sum(1 for r in results if r.success)
                documents.set_postfix(
                    {"成功": success_count, "失败": len(results) - success_count}
                )

        return results

    async def download_documents_async(
        self,
        documents: List[Document],
        subfolder: Optional[str] = None,
        show_progress: bool = True,
        filter_pdf_only: bool = False,
    ) -> List[DownloadResult]:
        """
        批量下载文档（异步版本，优化版）

        Args:
            documents: 文档列表
            subfolder: 子文件夹名称
            show_progress: 是否显示进度条
            filter_pdf_only: 是否只下载PDF文档

        Returns:
            下载结果列表
        """
        if filter_pdf_only:
            pdf_docs = [doc for doc in documents if doc.is_pdf]
            non_pdf_count = len(documents) - len(pdf_docs)
            if non_pdf_count > 0:
                print(f"跳过 {non_pdf_count} 个非PDF文件")
            documents = pdf_docs

        if not documents:
            print("没有找到可下载的文档")
            return []

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 使用共享session提高效率
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            limit_per_host=self.max_concurrent,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=30,
            sock_read=60
        )

        async def download_with_semaphore(session, doc):
            async with semaphore:
                return await self.download_document_async(
                    session=session, document=doc, subfolder=subfolder
                )

        # 执行下载
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout
        ) as session:
            # 创建任务对象而不是协程
            tasks = [asyncio.create_task(download_with_semaphore(session, doc)) for doc in documents]

            if show_progress:
                results = []
                completed_count = 0
                
                with tqdm(total=len(tasks), desc="下载文档", unit="个") as pbar:
                    try:
                        # 简化的进度处理
                        for coro in asyncio.as_completed(tasks):
                            try:
                                result = await coro
                                results.append(result)
                            except Exception as e:
                                # 创建失败结果
                                doc_index = len(results)
                                if doc_index < len(documents):
                                    results.append(DownloadResult(
                                        document=documents[doc_index],
                                        success=False,
                                        error=f"任务异常: {str(e)}"
                                    ))
                            
                            success_count = sum(1 for r in results if r.success)
                            fail_count = len(results) - success_count
                            
                            pbar.set_postfix_str(
                                f"成功={success_count}, 失败={fail_count}"
                            )
                            pbar.update(1)
                                
                    except KeyboardInterrupt:
                        pbar.write("下载被用户中断")
                        # 取消剩余任务
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        raise

                return results
            else:
                return await asyncio.gather(*tasks)

    def download_search_results(
        self,
        search_response: SearchResponse,
        subfolder: Optional[str] = None,
        pdf_only: bool = True,
        use_async: bool = True,
    ) -> List[DownloadResult]:
        """
        下载搜索结果中的所有文档

        Args:
            search_response: 搜索响应
            subfolder: 子文件夹名称
            pdf_only: 是否只下载PDF文档
            use_async: 是否使用异步下载

        Returns:
            下载结果列表
        """
        documents = search_response.documents

        if use_async:
            return asyncio.run(
                self.download_documents_async(
                    documents=documents,
                    subfolder=subfolder,
                    filter_pdf_only=pdf_only,
                )
            )
        else:
            return self.download_documents(
                documents=documents,
                subfolder=subfolder,
                filter_pdf_only=pdf_only,
            )

    def organize_downloads_by_company(
        self,
        search_response: SearchResponse,
        pdf_only: bool = True,
        use_async: bool = True,
    ) -> Dict[str, List[DownloadResult]]:
        """
        按公司组织下载，每个公司创建单独的文件夹

        Args:
            search_response: 搜索响应
            pdf_only: 是否只下载PDF文档
            use_async: 是否使用异步下载

        Returns:
            公司代码到下载结果列表的映射
        """
        # 按公司分组文档
        company_docs = {}
        skipped_count = 0
        
        for doc in search_response.documents:
            if pdf_only and not doc.is_pdf:
                skipped_count += 1
                continue

            company_key = f"{doc.stock_code}_{doc.stock_name}"
            if company_key not in company_docs:
                company_docs[company_key] = []
            company_docs[company_key].append(doc)
        
        if pdf_only and skipped_count > 0:
            print(f"跳过 {skipped_count} 个非PDF文档")

        # 为每个公司下载文档
        all_results = {}

        for company_key, docs in company_docs.items():
            print(f"下载 {company_key} 的文档 ({len(docs)} 个)...")

            if use_async:
                results = asyncio.run(
                    self.download_documents_async(
                        documents=docs,
                        subfolder=company_key,
                        show_progress=True,
                    )
                )
            else:
                results = self.download_documents(
                    documents=docs, subfolder=company_key, show_progress=True
                )

            all_results[company_key] = results

        return all_results

    def get_download_statistics(
        self, results: List[DownloadResult]
    ) -> Dict[str, Any]:
        """
        获取下载统计信息

        Args:
            results: 下载结果列表

        Returns:
            统计信息
        """
        total_downloads = len(results)
        successful_downloads = sum(1 for r in results if r.success)
        failed_downloads = total_downloads - successful_downloads

        total_size = sum(
            r.file_size for r in results if r.success and r.file_size
        )

        # 按错误类型统计
        error_types = {}
        for result in results:
            if not result.success and result.error:
                error_types[result.error] = (
                    error_types.get(result.error, 0) + 1
                )

        # 按公司统计
        company_stats = {}
        for result in results:
            company = (
                f"{result.document.stock_code} - {result.document.stock_name}"
            )
            if company not in company_stats:
                company_stats[company] = {"total": 0, "success": 0}
            company_stats[company]["total"] += 1
            if result.success:
                company_stats[company]["success"] += 1

        return {
            "total_downloads": total_downloads,
            "successful_downloads": successful_downloads,
            "failed_downloads": failed_downloads,
            "success_rate": successful_downloads / total_downloads
            if total_downloads > 0
            else 0,
            "total_size_mb": total_size / (1024 * 1024) if total_size else 0,
            "error_types": error_types,
            "company_stats": company_stats,
            "download_dir": str(self.download_dir),
        }

    def cleanup_failed_downloads(self, results: List[DownloadResult]):
        """
        清理失败的下载文件

        Args:
            results: 下载结果列表
        """
        for result in results:
            if not result.success and result.file_path:
                try:
                    file_path = Path(result.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        print(f"已删除失败的下载文件: {result.file_path}")
                except Exception as e:
                    print(f"删除文件失败: {result.file_path}, 错误: {e}")
