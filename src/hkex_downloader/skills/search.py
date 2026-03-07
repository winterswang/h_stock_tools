from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from hkex_downloader.services.searcher import DocumentSearcher
from hkex_downloader.services.stock_resolver import StockResolver
from hkex_downloader.models.company import Document

# 单例模式
_searcher = DocumentSearcher()
_resolver = StockResolver(_searcher.client)

def search_filings(
    ticker: str,
    doc_type: str = "annual_results",
    days: int = 365,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    搜索港股公告
    
    Args:
        ticker: 股票代码 (如 00700)
        doc_type: 文档类型 (annual_results, interim_results, ipo_prospectus)
        days: 搜索最近多少天 (如果未指定start_date)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数量限制
        
    Returns:
        文档列表 (字典格式)
    """
    # 1. 处理日期
    if end_date:
        to_d = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        to_d = date.today()
        
    if start_date:
        from_d = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        from_d = to_d - timedelta(days=days)
        
    # 2. 搜索
    try:
        response = _searcher.search_by_document_type(
            from_date=from_d,
            to_date=to_d,
            document_type=doc_type,
            stock_code=ticker
        )
        
        # 3. 转换结果
        docs = []
        for doc in response.documents[:limit]:
            docs.append({
                "title": doc.title,
                "stock_code": doc.stock_code,
                "stock_name": doc.stock_name,
                "file_link": doc.full_file_url,
                "file_type": doc.file_type,
                "date_time": doc.date_time,
                "file_size": doc.file_info,
                "release_time": doc.parsed_datetime.isoformat() if doc.parsed_datetime else None
            })
            
        return docs
    except Exception as e:
        print(f"Search failed: {e}")
        return []
