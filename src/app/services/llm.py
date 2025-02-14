from groq import Groq
from app.core.config import settings
from app.services.document import DocumentService
import aiofiles


class LLMService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.document_service = DocumentService()

    async def get_answer(self, document_id: str, question: str) -> str:
        """Get an answer from the LLM based on the document content."""
        # Get document content
        doc_path = await self.document_service.get_document_path(document_id)
        async with aiofiles.open(doc_path, 'r') as f:
            content = await f.read()

        # Prepare prompt
        prompt = self._create_prompt(content, question)

        # Get response from Groq
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided document content. Keep your answers concise and relevant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    def _create_prompt(self, content: str, question: str) -> str:
        """Create a prompt for the LLM."""
        return f"""
        Here is the document content:
        ---
        {content}
        ---
        
        Please answer the following question about the document:
        {question}
        """ 