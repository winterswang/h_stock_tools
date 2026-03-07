import fitz  # PyMuPDF
from typing import Dict, Any, List

class PDFParser:
    """
    基于 PyMuPDF 的 PDF 解析器 (复用 m_stock_tools 逻辑)
    """
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析 PDF 提取全文"""
        try:
            doc = fitz.open(file_path)
            text_content = []
            
            for page in doc:
                text_content.append(page.get_text())
                
            return {
                "text": "\n".join(text_content),
                "page_count": doc.page_count,
                "metadata": doc.metadata
            }
        except Exception as e:
            print(f"Parsing failed: {e}")
            return {"error": str(e)}

    def chunk_text(self, file_path: str, chunk_size: int = 2000, overlap: int = 200) -> List[Dict]:
        """按页和长度分块"""
        try:
            doc = fitz.open(file_path)
            chunks = []
            chunk_idx = 0
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                if len(text) > chunk_size:
                    start = 0
                    while start < len(text):
                        end = start + chunk_size
                        chunks.append({
                            "content": text[start:end],
                            "page": page_num,
                            "index": chunk_idx
                        })
                        start += (chunk_size - overlap)
                        chunk_idx += 1
                else:
                    chunks.append({
                        "content": text,
                        "page": page_num,
                        "index": chunk_idx
                    })
                    chunk_idx += 1
            return chunks
        except Exception as e:
            return [{"error": str(e)}]

_parser = PDFParser()

def parse_pdf_content(file_path: str) -> Dict[str, Any]:
    return _parser.parse(file_path)

def chunk_pdf_text(file_path: str, chunk_size: int = 2000) -> List[Dict]:
    return _parser.chunk_text(file_path, chunk_size)
