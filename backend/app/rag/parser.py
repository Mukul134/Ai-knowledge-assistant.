import io
from typing import List, Dict, Any
import pdfplumber

class PDFParser:
    @staticmethod
    def extract_text_by_page(file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Parses PDF binary stream page by page.
        Returns a list of dictionaries mapping page number to raw text content.
        Raises ValueError if text cannot be parsed or document is empty/malformed.
        """
        pages_content = []
        
        try:
            # pdfplumber accepts a file-like object (BytesIO) for in-memory streams
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                if not pdf.pages:
                    raise ValueError("The uploaded PDF contains no pages.")
                
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    page_number = idx + 1
                    
                    # Clean/strip text if it exists, otherwise store as empty
                    clean_text = text.strip() if text else ""
                    
                    pages_content.append({
                        "page_number": page_number,
                        "text": clean_text
                    })
                    
        except Exception as e:
            # Intercept any parsing failures (malformed headers, encryption, etc.)
            raise ValueError(f"Failed to parse PDF document: {str(e)}")
            
        # Verify that we extracted *some* readable text.
        # If all pages are completely empty (e.g. image-only scans without OCR), raise a warning/error.
        total_text_length = sum(len(page["text"]) for page in pages_content)
        if total_text_length == 0:
            raise ValueError(
                "No readable text was extracted from this PDF. "
                "This document may be a scanned image. Please run OCR on the file before uploading."
            )
            
        return pages_content
