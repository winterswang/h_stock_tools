#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票解析服务

提供股票代码到股票ID的转换功能
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..api.client import HKExClient
from ..models.company import Company

# from ..models.search import StockSearchRequest  # 暂时注释掉未使用的导入


class StockResolver:
    """
    股票解析服务

    提供股票代码到股票ID的转换功能，支持缓存机制
    """

    def __init__(
        self,
        client: Optional[HKExClient] = None,
        cache_dir: Optional[str] = None,
        cache_ttl_hours: int = 24,
    ):
        """
        初始化股票解析服务

        Args:
            client: HKEx API客户端，如果为None则创建新实例
            cache_dir: 缓存目录，如果为None则不使用缓存
            cache_ttl_hours: 缓存有效期（小时）
        """
        self.client = client or HKExClient()
        self.cache_dir = cache_dir
        self.cache_ttl_hours = cache_ttl_hours
        self._cache: Dict[str, Dict[str, Any]] = {}

        # 如果指定了缓存目录，确保目录存在
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            self._load_cache()

    def _get_cache_file_path(self) -> str:
        """
        获取缓存文件路径
        """
        if not self.cache_dir:
            raise ValueError("缓存目录未设置")
        return os.path.join(self.cache_dir, "stock_cache.json")

    def _load_cache(self):
        """
        从文件加载缓存
        """
        if not self.cache_dir:
            return

        cache_file = self._get_cache_file_path()
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载缓存失败: {e}")
                self._cache = {}

    def _save_cache(self):
        """
        保存缓存到文件
        """
        if not self.cache_dir:
            return

        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存缓存失败: {e}")

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """
        检查缓存条目是否有效

        Args:
            cache_entry: 缓存条目

        Returns:
            缓存是否有效
        """
        if "timestamp" not in cache_entry:
            return False

        cache_time = datetime.fromisoformat(cache_entry["timestamp"])
        expiry_time = cache_time + timedelta(hours=self.cache_ttl_hours)

        return datetime.now() < expiry_time

    def _get_from_cache(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取股票信息

        Args:
            stock_code: 股票代码

        Returns:
            缓存的股票信息，如果不存在或已过期则返回None
        """
        if stock_code not in self._cache:
            return None

        cache_entry = self._cache[stock_code]
        if not self._is_cache_valid(cache_entry):
            # 删除过期缓存
            del self._cache[stock_code]
            return None

        return cache_entry.get("data")

    def _save_to_cache(self, stock_code: str, data: Dict[str, Any]):
        """
        保存股票信息到缓存

        Args:
            stock_code: 股票代码
            data: 股票信息
        """
        self._cache[stock_code] = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        # 保存到文件
        self._save_cache()

    def resolve_stock_id(self, stock_code: str) -> Optional[str]:
        """
        根据股票代码获取股票ID

        Args:
            stock_code: 股票代码，如 '00700'

        Returns:
            股票ID，如果未找到则返回None
        """
        # 标准化股票代码
        stock_code = self._normalize_stock_code(stock_code)

        # 先尝试从缓存获取
        cached_data = self._get_from_cache(stock_code)
        if cached_data:
            return cached_data.get("stock_id")

        # 从API获取
        try:
            response = self.client.search_stock(stock_code)
            stock_id = response.get_stock_id(stock_code)

            # 保存到缓存
            if stock_id:
                cache_data = {
                    "stock_id": stock_id,
                    "stock_code": stock_code,
                    "companies": response.companies,
                }
                self._save_to_cache(stock_code, cache_data)

            return stock_id

        except Exception as e:
            print(f"解析股票ID失败: {e}")
            return None

    def resolve_company_info(self, stock_code: str) -> Optional[Company]:
        """
        根据股票代码获取公司信息

        Args:
            stock_code: 股票代码，如 '00700'

        Returns:
            公司信息对象，如果未找到则返回None
        """
        # 标准化股票代码
        stock_code = self._normalize_stock_code(stock_code)

        # 先尝试从缓存获取
        cached_data = self._get_from_cache(stock_code)
        if cached_data:
            return self._create_company_from_cache(cached_data)

        # 从API获取
        try:
            response = self.client.search_stock(stock_code)

            # 查找匹配的公司
            for company_data in response.companies:
                if company_data.get("code") == stock_code:
                    stock_id = company_data.get("id")
                    stock_name = company_data.get("name", "")

                    # 创建Company对象
                    company = Company(
                        stock_code=stock_code,
                        stock_id=stock_id,
                        stock_name=stock_name,
                    )

                    # 保存到缓存
                    cache_data = {
                        "stock_id": stock_id,
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "companies": response.companies,
                    }
                    self._save_to_cache(stock_code, cache_data)

                    return company

            return None

        except Exception as e:
            print(f"解析公司信息失败: {e}")
            return None

    def _create_company_from_cache(
        self, cached_data: Dict[str, Any]
    ) -> Company:
        """
        从缓存数据创建Company对象

        Args:
            cached_data: 缓存数据

        Returns:
            公司信息对象
        """
        return Company(
            stock_code=cached_data["stock_code"],
            stock_id=cached_data.get("stock_id"),
            stock_name=cached_data.get("stock_name", ""),
        )

    def _normalize_stock_code(self, stock_code: str) -> str:
        """
        标准化股票代码

        Args:
            stock_code: 原始股票代码

        Returns:
            标准化后的股票代码（5位数字）
        """
        # 移除空格和特殊字符
        code = "".join(c for c in stock_code if c.isdigit())

        # 补齐到5位
        return code.zfill(5)

    def batch_resolve(
        self, stock_codes: List[str]
    ) -> Dict[str, Optional[Company]]:
        """
        批量解析股票信息

        Args:
            stock_codes: 股票代码列表

        Returns:
            股票代码到公司信息的映射
        """
        results = {}

        for stock_code in stock_codes:
            try:
                company = self.resolve_company_info(stock_code)
                results[stock_code] = company
            except Exception as e:
                print(f"解析股票 {stock_code} 失败: {e}")
                results[stock_code] = None

        return results

    def search_companies(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据关键词搜索公司

        Args:
            keyword: 搜索关键词（可以是股票代码或公司名称）

        Returns:
            匹配的公司列表
        """
        try:
            response = self.client.search_stock(keyword)
            return response.companies
        except Exception as e:
            print(f"搜索公司失败: {e}")
            return []

    def clear_cache(self):
        """
        清空缓存
        """
        self._cache.clear()

        if self.cache_dir:
            cache_file = self._get_cache_file_path()
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except OSError as e:
                    print(f"删除缓存文件失败: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        total_entries = len(self._cache)
        valid_entries = 0
        expired_entries = 0

        for entry in self._cache.values():
            if self._is_cache_valid(entry):
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_dir": self.cache_dir,
            "cache_ttl_hours": self.cache_ttl_hours,
        }
