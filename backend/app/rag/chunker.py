import uuid
from typing import List, Dict, Any
import tiktoken

class TokenChunker:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize the tokenizer using tiktoken.
        gpt-4o and gpt-4o-mini use the 'cl100k_base' or 'o200k_base' encodings.
        For continuity, cl100k_base is fully standard.
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a string."""
        return len(self.encoding.encode(text))

    def split_text_by_tokens(self, text: str, chunk_size: int = 512, chunk_overlap: int = 51) -> List[str]:
        """
        Splits a text string into overlapping fragments of a specified token length.
        Maintains syntactic alignment where possible.
        """
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= chunk_size:
            return [text]

        chunks = []
        start_idx = 0
        
        while start_idx < total_tokens:
            end_idx = min(start_idx + chunk_size, total_tokens)
            chunk_tokens = tokens[start_idx:end_idx]
            chunks.append(self.encoding.decode(chunk_tokens))
            
            # Slide the window forward
            start_idx += (chunk_size - chunk_overlap)
            
            # Safety checks to prevent infinite loops on malformed inputs
            if chunk_size <= chunk_overlap:
                break
                
        return chunks

    def chunk_page(
        self,
        page_text: str,
        page_number: int,
        file_name: str,
        document_id: str,
        user_id: str,
        chunk_size: int = 512,
        chunk_overlap: int = 51
    ) -> List[Dict[str, Any]]:
        """
        Split page content into semantic fragments and attach tracking metadata.
        Each chunk is mapped to the parent document, current user, and exact page number.
        """
        # Clean basic whitespace
        clean_text = " ".join(page_text.split())
        if not clean_text:
            return []

        text_chunks = self.split_text_by_tokens(clean_text, chunk_size, chunk_overlap)
        
        chunk_records = []
        for idx, text_content in enumerate(text_chunks):
            chunk_records.append({
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "user_id": user_id,
                "content": text_content,
                "page_number": page_number,
                "file_name": file_name,
                "metadata": {
                    "chunk_index": idx,
                    "token_count": self.count_tokens(text_content),
                    "total_page_chunks": len(text_chunks)
                }
            })
            
        return chunk_records
