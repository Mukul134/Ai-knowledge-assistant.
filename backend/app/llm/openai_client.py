from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

class OpenAIClient:
    def __init__(self):
        """Create the model client when credentials are available.

        The API health endpoint must remain available even when optional AI
        credentials have not been configured in a deployment.
        """
        self.client: AsyncOpenAI | None = None
        if settings.OPENAI_API_KEY:
            kwargs = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self.client = AsyncOpenAI(**kwargs)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Fetch embeddings from OpenAI using the configured embedding model (text-embedding-3-small).
        Processes queries in batch to minimize network roundtrips.
        """
        if not texts:
            return []
        if self.client is None:
            raise RuntimeError("AI embeddings are unavailable because OPENAI_API_KEY is not configured.")

        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=settings.OPENAI_EMBEDDING_MODEL,
                timeout=60.0,
                dimensions=1536
            )
            # OpenAI returns list of embeddings ordered identically to the inputs list
            return [data.embedding for data in response.data]
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding generation failed: {str(e)}")

# Initialize shared client helper
openai_helper = OpenAIClient()
