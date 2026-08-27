import re
from typing import List, Dict, Any

class CitationParser:
    # Regex to match citations formatted as: [File: filename.pdf | Page: X]
    CITATION_REGEX = re.compile(r"\[File:\s*([^|\]]+?)\s*\|\s*Page:\s*(\d+?)\s*\]")

    @classmethod
    def extract_citations(cls, text: str) -> List[Dict[str, Any]]:
        """
        Parses the generated assistant text and extracts source citations.
        Returns a list of unique citation dictionaries: [{"file_name": "...", "page_number": X}]
        """
        if not text:
            return []

        matches = cls.CITATION_REGEX.findall(text)
        citations = []
        seen = set()

        for file_name, page_str in matches:
            file_name = file_name.strip()
            try:
                page_number = int(page_str)
            except ValueError:
                continue

            # Ensure uniqueness
            key = (file_name, page_number)
            if key not in seen:
                seen.add(key)
                citations.append({
                    "file_name": file_name,
                    "page_number": page_number
                })

        return citations
