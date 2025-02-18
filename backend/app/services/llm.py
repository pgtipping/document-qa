from groq import Groq
from app.core.config import settings
from app.services.document import DocumentService
import hashlib
from typing import Dict, Optional, Tuple, List
import time
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self) -> None:
        """Initialize the LLM service."""
        self.api_key = settings.GROQ_API_KEY
        self.client = Groq(
            api_key=self.api_key,
            default_headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.document_service = DocumentService()
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)
        self.max_chunk_size = 500  # Chunk size
        self.max_chunks = 8  # Increased for better coverage
        self.max_context_length = 4000  # Increased context length
        self.metadata_keywords = {
            'title', 'author', 'authors', 'written', 'published', 'publication',
            'copyright', 'version', 'edition', 'year'
        }

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into smaller, more focused chunks."""
        # Clean and normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Split by sentences for finer control
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            current_len = len(current_chunk) + len(sentence)
            if current_len < self.max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    def _get_relevant_chunks(
        self, 
        chunks: List[str], 
        question: str
    ) -> List[str]:
        """Get the most relevant chunks for the question.
        
        Uses semantic similarity and keyword matching to find best content.
        """
        # Extract keywords from the question
        stop_words = {
            'what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'the',
            'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
        question_words = re.findall(r'\w+', question.lower())
        keywords = set(question_words) - stop_words
        logger.debug(f"Extracted keywords: {keywords}")
        
        # Check if this is a metadata question
        is_metadata_question = any(
            word in self.metadata_keywords 
            for word in keywords
        )
        
        # Score chunks based on multiple factors
        chunk_scores = []
        for i, chunk in enumerate(chunks):
            # Calculate keyword density
            chunk_words = len(chunk.split())
            if chunk_words == 0:
                continue
                
            # Count exact keyword matches
            keyword_matches = sum(
                1 for keyword in keywords 
                if keyword in chunk.lower()
            )
            
            # Count partial matches (substrings)
            def is_partial_match(kw: str, w: str) -> bool:
                return (kw in w) or (w in kw)
                
            partial_matches = sum(
                1 for keyword in keywords
                for word in chunk.lower().split()
                if is_partial_match(keyword, word)
            )
            
            # Calculate base scores
            density = keyword_matches / chunk_words
            partial_score = partial_matches / chunk_words
            
            # Calculate context score based on surrounding chunks
            context_score = 0.0
            if i > 0:  # Check previous chunk
                prev_chunk = chunks[i-1].lower()
                context_score += sum(
                    1 for keyword in keywords 
                    if keyword in prev_chunk
                ) / len(prev_chunk.split())
            if i < len(chunks) - 1:  # Check next chunk
                next_chunk = chunks[i+1].lower()
                context_score += sum(
                    1 for keyword in keywords 
                    if keyword in next_chunk
                ) / len(next_chunk.split())
            context_score = context_score / 2  # Normalize to 0-1 range
            
            # Additional metadata score if relevant
            metadata_score = 0.0
            if is_metadata_question:
                metadata_matches = sum(
                    1 for word in self.metadata_keywords
                    if word in chunk.lower()
                )
                metadata_score = metadata_matches / chunk_words
            
            # Combine scores with weights
            final_score = (
                density * 0.4 +  # Exact keyword matches
                partial_score * 0.2 +  # Partial matches
                context_score * 0.2 +  # Surrounding context relevance
                metadata_score * 0.2  # Metadata terms if relevant
            )
            
            chunk_scores.append((final_score, i, chunk))
            logger.debug(f"Chunk {i} score: {final_score}")
        
        # Sort by score
        chunk_scores.sort(reverse=True)
        
        # Select chunks with context
        selected_indices = set()
        selected_chunks = []
        
        # Add highest scoring chunks and their context
        for score, idx, chunk in chunk_scores:
            if len(selected_chunks) >= self.max_chunks:
                break
                
            # If this chunk or its neighbors aren't already selected
            if idx not in selected_indices:
                # Add the chunk
                selected_indices.add(idx)
                selected_chunks.append(chunk)
                
                # Consider adding surrounding context
                if score > 0.1:  # Only add context for relevant chunks
                    # Add previous chunk if it exists and not already selected
                    if idx > 0 and (idx-1) not in selected_indices:
                        selected_indices.add(idx-1)
                        selected_chunks.append(chunks[idx-1])
                    
                    # Add next chunk if it exists and not already selected
                    if idx < len(chunks)-1 and (idx+1) not in selected_indices:
                        selected_indices.add(idx+1)
                        selected_chunks.append(chunks[idx+1])
        
        # Sort chunks by their original order to maintain document flow
        selected_chunks.sort(key=lambda x: chunks.index(x))
        
        # Truncate if total length exceeds max_context_length
        total_length = sum(len(chunk) for chunk in selected_chunks)
        if total_length > self.max_context_length:
            truncated = []
            current_length = 0
            for chunk in selected_chunks:
                if current_length + len(chunk) <= self.max_context_length:
                    truncated.append(chunk)
                    current_length += len(chunk)
                else:
                    remaining = self.max_context_length - current_length
                    if remaining > 100:  # Only add partial if substantial
                        truncated.append(chunk[:remaining])
                    break
            selected_chunks = truncated
        
        logger.debug(f"Selected {len(selected_chunks)} chunks")
        for i, chunk in enumerate(selected_chunks):
            logger.debug(f"Chunk {i} preview: {chunk[:100]}...")
        return selected_chunks

    def _create_prompt(self, content: str, question: str) -> str:
        """Create a detailed prompt for the LLM."""
        prompt = (
            "You are a helpful assistant that answers questions based on the "
            "provided document content. Your task is to:\n"
            "1. Read the following content carefully\n"
            "2. Answer the question accurately using ONLY the provided content\n"
            "3. If you cannot find the answer in the content, say so\n"
            "4. Do not make up or infer information not present in the "
            "content\n\n"
            "Important: For questions about title, author, or other metadata, "
            "look for explicit mentions in the text. Do not guess or infer.\n\n"
            f"Content:\n{content}\n\n"
            f"Question: {question}\n\n"
            "Answer: "
        )
        logger.debug(f"Created prompt with content length: {len(content)}")
        return prompt

    async def get_answer(self, document_id: str, question: str) -> str:
        """Get an answer from the LLM based on the document content."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in environment variables")
            
        # Generate cache key
        cache_key = self._generate_cache_key(document_id, question)
        
        # Check cache
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            logger.debug("Using cached response")
            return cached_response

        # Get document content
        content = await self.document_service.get_document_content(document_id)
        try:
            content_str = content.decode('utf-8')
            logger.debug(f"Decoded document content length: {len(content_str)}")
        except UnicodeDecodeError:
            content_str = content.decode('latin-1')
            logger.debug("Used latin-1 encoding for document content")

        # Split content and get relevant chunks
        chunks = self._split_into_chunks(content_str)
        relevant_chunks = self._get_relevant_chunks(chunks, question)
        relevant_content = " ".join(relevant_chunks)
        logger.debug(f"Total relevant content length: {len(relevant_content)}")

        # Create prompt
        prompt = self._create_prompt(relevant_content, question)

        try:
            # Get response from Groq with minimal system message
            logger.debug("Sending request to Groq")
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that provides accurate "
                            "answers based ONLY on the given content. Never make "
                            "up information or infer details not present in the "
                            "content."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150  # Reduced max tokens for response
            )
            
            answer = str(response.choices[0].message.content)
            logger.debug(f"Got response from Groq: {len(answer)} chars")
            
            # Cache the response
            self._add_to_cache(cache_key, answer)
            
            return answer
        except Exception as e:
            logger.error(f"Error getting response from Groq: {str(e)}")
            raise ValueError(f"Error getting response from Groq: {str(e)}")

    def _generate_cache_key(self, document_id: str, question: str) -> str:
        """Generate a unique cache key for a document-question pair."""
        combined = f"{document_id}:{question.lower().strip()}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
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

    async def test_connection(self) -> bool:
        """Test if the LLM service is accessible.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple test query that doesn't require a document
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "Test connection"}],
                model=settings.MODEL_NAME,
                max_tokens=10
            )
            return bool(response and response.choices)
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False 