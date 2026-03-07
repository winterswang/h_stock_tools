from typing import List, Dict, Optional
import aiohttp
import asyncio
from hkex_downloader.services.downloader import DocumentDownloader, DownloadResult
from hkex_downloader.models.company import Document

# 单例模式
_downloader = DocumentDownloader()

def download_filing(url: str, save_path: str, chunk_size: int = 8192) -> bool:
    """
    下载单个文件 (同步)
    
    Args:
        url: 文件链接
        save_path: 保存路径
        chunk_size: 下载块大小
        
    Returns:
        是否成功
    """
    import requests
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

async def _async_download_batch(urls: List[str], save_paths: List[str]) -> List[bool]:
    """
    批量异步下载
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url, path in zip(urls, save_paths):
            tasks.append(_download_one(session, url, path))
        return await asyncio.gather(*tasks)

async def _download_one(session, url, path):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                with open(path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                return True
    except Exception as e:
        print(f"Async download failed: {e}")
        return False
    return False

def batch_download_filings(urls: List[str], save_paths: List[str]) -> List[bool]:
    """
    批量下载多个文件 (异步并发)
    """
    return asyncio.run(_async_download_batch(urls, save_paths))
