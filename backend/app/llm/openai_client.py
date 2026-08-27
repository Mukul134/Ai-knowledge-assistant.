from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

class OpenAIClient:
    def __init__(self):
        """
        Initialize the AsyncOpenAI client as a singleton resource.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be configured in environment.")
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Fetch embeddings from OpenAI using the configured embedding model (text-embedding-3-small).
        Processes queries in batch to minimize network roundtrips.
        """
        if not texts:
            return []

        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=settings.OPENAI_EMBEDDING_MODEL,
                timeout=60.0
            )
            # OpenAI returns list of embeddings ordered identically to the inputs list
            return [data.embedding for data in response.data]
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding generation failed: {str(e)}")

# Initialize shared client helper
openai_helper = OpenAIClient()
