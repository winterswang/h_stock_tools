import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from unittest.mock import MagicMock, patch
from datetime import date
from hkex_downloader.services.searcher import DocumentSearcher
from hkex_downloader.models.search import SearchResponse, Document

class TestDocumentSearcher(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_resolver = MagicMock()
        self.searcher = DocumentSearcher(client=self.mock_client, stock_resolver=self.mock_resolver)

    def test_search_ipo_prospectus(self):
        # Setup
        self.mock_resolver.resolve_stock_id.return_value = "12345"
        self.mock_client.search_documents.return_value = SearchResponse(sort_list="DESC")
        
        # Execute
        result = self.searcher.search_ipo_prospectus(
            from_date=date(2023, 1, 1),
            to_date=date(2023, 1, 31),
            stock_code="00700"
        )
        
        # Verify
        self.mock_resolver.resolve_stock_id.assert_called_with("00700")
        self.mock_client.search_documents.assert_called_once()
        self.assertIsInstance(result, SearchResponse)

    def test_search_ipo_prospectus_no_stock_id(self):
        # Setup
        self.mock_resolver.resolve_stock_id.return_value = None
        self.mock_client.search_documents.return_value = SearchResponse(sort_list="DESC")

        # Execute
        result = self.searcher.search_ipo_prospectus(
            from_date=date(2023, 1, 1),
            to_date=date(2023, 1, 31),
            stock_code="00000"
        )
        
        # Verify
        # Should log warning but continue
        self.mock_client.search_documents.assert_called_once()

if __name__ == '__main__':
    unittest.main()
