from groq import Groq
from app.core.config import settings
from app.services.document import DocumentService
import aiofiles
import hashlib
from typing import Dict, Tuple
import time


class LLMService:
    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.document_service = DocumentService()
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)

    async def get_answer(self, document_id: str, question: str) -> str:
        """Get an answer from the LLM based on the document content."""
        # Generate cache key
        cache_key = self._generate_cache_key(document_id, question)
        
        # Check cache
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            return cached_response

        # Get document content
        doc_path = await self.document_service.get_document_path(document_id)
        async with aiofiles.open(doc_path, 'r') as f:
            content = await f.read()

        # Prepare prompt
        prompt = self._create_prompt(content, question)

        # Get response from Groq
        response = await self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that answers questions "
                        "based on the provided document content. Keep your "
                        "answers concise and relevant."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        answer = str(response.choices[0].message.content)
        
        # Cache the response
        self._add_to_cache(cache_key, answer)
        
        return answer

    def _generate_cache_key(self, document_id: str, question: str) -> str:
        """Generate a unique cache key for a document-question pair."""
        combined = f"{document_id}:{question.lower().strip()}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> str | None:
        """Get a response from cache if it exists and is not expired."""
        if cache_key in self.cache:
            answer, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return answer
            else:
                del self.cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, answer: str) -> None:
        """Add a response to the cache with current timestamp."""
        self.cache[cache_key] = (answer, time.time())

    def _create_prompt(self, content: str, question: str) -> str:
        """Create a prompt for the LLM."""
        return (
            f"\nHere is the document content:\n"
            f"---\n"
            f"{content}\n"
            f"---\n\n"
            f"Please answer the following question about the document:\n"
            f"{question}\n"
        ) 