from typing import List, Dict, Any, Optional
from supabase import Client
from app.llm.openai_client import openai_helper

class DocumentRetriever:
    @staticmethod
    async def retrieve_relevant_chunks(
        query: str,
        user_id: str,
        supabase_user_client: Client,
        document_id: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most semantically relevant document chunks matching a query.
        1. Generates embedding vector for the search query using OpenAI.
        2. Executes database similarity search RPC matching the user's RLS context.
        """
        if not query.strip():
            return []

        # 1. Generate Query Embedding
        try:
            embeddings = await openai_helper.get_embeddings([query])
            if not embeddings:
                return []
            query_vector = embeddings[0]
        except Exception as e:
            # Propagate the embedding failure details
            raise RuntimeError(f"Retriever failed to generate query embedding: {str(e)}")

        # 2. Query Postgres pgvector via Supabase RPC function
        try:
            rpc_params = {
                "query_embedding": query_vector,
                "match_threshold": similarity_threshold,
                "match_count": top_k,
                "filter_user_id": str(user_id),
                "filter_document_id": str(document_id) if document_id else None
            }
            
            # Execute database search
            response = supabase_user_client.rpc(
                "match_document_chunks", 
                rpc_params
            ).execute()
            
            return response.data or []
            
        except Exception as e:
            raise RuntimeError(f"Database vector similarity search execution failed: {str(e)}")
