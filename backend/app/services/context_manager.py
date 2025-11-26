"""
Context Manager for handling content extraction, chunking, and token management.
Manages context from URLs and files, formats it for LLM prompts, and handles token limits.
"""
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context extraction, chunking, and formatting for LLM prompts."""
    
    def __init__(self, max_tokens: int = 4000, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize the ContextManager.
        
        Args:
            max_tokens: Maximum tokens to include in context (approximate)
            chunk_size: Size of text chunks for splitting large documents
            overlap: Overlap between chunks to maintain context
        """
        self.max_tokens = max_tokens
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.sources: List[Dict[str, str]] = []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text using word count.
        More accurate: 1 token ≈ 0.75 words (or use word count directly as approximation).
        """
        # Use word count as a better approximation for tokens
        words = text.split()
        return len(words)
    
    def chunk_text(self, text: str, source_name: str) -> List[Dict[str, str]]:
        """
        Split text into chunks if it's too large.
        For most web content, we keep it as a single chunk to preserve context.
        
        Args:
            text: Text to chunk
            source_name: Name/identifier of the source
            
        Returns:
            List of chunk dictionaries with 'text' and 'source' keys
        """
        # For web content under 4000 tokens (~4000 words), keep as single chunk
        # This preserves context better than fragmenting
        words = text.split()
        estimated_tokens = len(words)
        
        # If text is reasonable size (under 4000 tokens), return as single chunk
        if estimated_tokens <= 4000:
            return [{"text": text, "source": source_name}]
        
        # Only chunk very large documents
        chunk_size_words = 2000  # ~2000 tokens per chunk
        overlap_words = 100  # Small overlap for continuity
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + chunk_size_words, len(words))
            
            # Try to break at sentence boundaries (look back up to 100 words)
            if end < len(words):
                for i in range(end - 1, max(start, end - 100), -1):
                    word = words[i]
                    if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                        end = i + 1
                        break
            
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "source": source_name,
                    "chunk_index": len(chunks) + 1
                })
            
            # Move to next chunk position (with minimal overlap to avoid tiny fragments)
            start = end - overlap_words if end < len(words) else len(words)
        
        return chunks
    
    def add_source(self, content: str, source_type: str, source_name: str) -> None:
        """
        Add a source to the context manager.
        
        Args:
            content: Extracted text content
            source_type: Type of source ('url', 'file', 'document')
            source_name: Name/identifier of the source
        """
        if not content or not content.strip():
            logger.warning(f"Empty content from {source_type}: {source_name}")
            return
        
        # Clean up content with aggressive filtering
        # Note: If content comes from Jina Reader API, it's already clean, but we still filter
        content = self._clean_text(content)
        
        # For URLs, apply limits to reduce false positives
        # Jina Reader content is already clean, so we can be more generous
        if source_type == 'url':
            words = content.split()
            # Allow up to 2000 words (Jina Reader content is pre-cleaned)
            if len(words) > 2000:
                content = ' '.join(words[:2000]) + '\n\n[Content truncated for brevity]'
                logger.info(f"Truncated URL content from {source_name} to 2000 words")
        
        # Calculate tokens (word count)
        tokens = self.estimate_tokens(content)
        
        # Chunk if necessary
        chunks = self.chunk_text(content, source_name)
        
        for chunk in chunks:
            chunk_tokens = self.estimate_tokens(chunk["text"])
            self.sources.append({
                "type": source_type,
                "name": source_name,
                "content": chunk["text"],
                "tokens": chunk_tokens,
                "chunk_index": chunk.get("chunk_index", 1),
                "total_chunks": len(chunks) if len(chunks) > 1 else None
            })
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content with aggressive filtering.
        Removes potentially problematic content that might trigger safety filters.
        """
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        
        # Aggressive line filtering - remove lines that might trigger safety filters
        lines = []
        skip_patterns = [
            'cookie', 'javascript', 'subscribe', 'sign in', 'log in', 'login',
            'sign up', 'register', 'newsletter', 'advertisement', 'advert',
            'click here', 'buy now', 'shop now', 'add to cart'
        ]
        
        for line in text.splitlines():
            line = line.strip()
            # Skip very short lines (often navigation/UI elements)
            if len(line) < 10:
                continue
            # Skip lines with suspicious patterns (case-insensitive)
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in skip_patterns):
                continue
            lines.append(line)
        
        text = '\n\n'.join(lines)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def format_context(self, max_context_tokens: Optional[int] = None) -> Tuple[str, Dict]:
        """
        Format all sources into a context string for the LLM prompt.
        
        Args:
            max_context_tokens: Maximum tokens to include (defaults to self.max_tokens)
            
        Returns:
            Tuple of (formatted_context_string, metadata_dict)
        """
        max_tokens = max_context_tokens or self.max_tokens
        
        # Calculate total tokens (use stored token count if available)
        total_tokens = sum(src.get("tokens", self.estimate_tokens(src["content"])) for src in self.sources)
        
        # If we're under the limit, include everything
        if total_tokens <= max_tokens:
            context_parts = []
            for src in self.sources:
                source_label = f"[Source: {src['name']}]"
                if src.get("chunk_index") and src.get("total_chunks"):
                    source_label += f" (Part {src['chunk_index']}/{src['total_chunks']})"
                
                context_parts.append(f"{source_label}\n{src['content']}")
            
            context_text = "\n\n".join(context_parts)
            
            return context_text, {
                "total_sources": len(set(s["name"] for s in self.sources)),
                "total_chunks": len(self.sources),
                "estimated_tokens": total_tokens,
                "truncated": False
            }
        
        # Need to prioritize/truncate
        # Strategy: Include sources in order, but truncate if needed
        context_parts = []
        current_tokens = 0
        included_sources = set()
        truncated = False
        
        for src in self.sources:
            src_tokens = src.get("tokens", self.estimate_tokens(src["content"]))
            
            if current_tokens + src_tokens <= max_tokens:
                source_label = f"[Source: {src['name']}]"
                if src.get("chunk_index") and src.get("total_chunks"):
                    source_label += f" (Part {src['chunk_index']}/{src['total_chunks']})"
                
                context_parts.append(f"{source_label}\n{src['content']}")
                current_tokens += src_tokens
                included_sources.add(src["name"])
            else:
                # Try to include partial content
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 50:  # Only if we have meaningful space
                    # Truncate by words, not characters
                    words = src["content"].split()
                    remaining_words = words[:remaining_tokens]
                    truncated_content = ' '.join(remaining_words) + "\n[...content truncated...]"
                    source_label = f"[Source: {src['name']}]"
                    if src.get("chunk_index") and src.get("total_chunks"):
                        source_label += f" (Part {src['chunk_index']}/{src['total_chunks']})"
                    source_label += " (Truncated)"
                    context_parts.append(f"{source_label}\n{truncated_content}\n")
                    truncated = True
                break
        
        context_text = "\n\n".join(context_parts)
        
        return context_text, {
            "total_sources": len(set(s["name"] for s in self.sources)),
            "included_sources": len(included_sources),
            "total_chunks": len(self.sources),
            "included_chunks": len(context_parts),
            "estimated_tokens": current_tokens,
            "truncated": truncated
        }
    
    def get_prompt_template(self, user_question: str, context_text: str) -> str:
        """
        Format the complete prompt with context and user question.
        Uses neutral framing that's less likely to trigger safety filters.
        
        Args:
            user_question: The user's question
            context_text: Formatted context from format_context()
            
        Returns:
            Complete formatted prompt
        """
        if context_text:
            # Use a more neutral framing that's less likely to trigger filters
            prompt = f"""Below is reference material from trusted sources that you should use to answer the question.

<context>
{context_text}
</context>

Question: {user_question}

Instructions: Provide a helpful answer based on the reference material above. Focus on being accurate and informative."""
        else:
            prompt = user_question
        
        return prompt
    
    def clear(self) -> None:
        """Clear all sources."""
        self.sources = []
    
    def get_source_summary(self) -> List[Dict[str, str]]:
        """Get a summary of all sources without full content."""
        summary = []
        seen = set()
        
        for src in self.sources:
            key = (src["type"], src["name"])
            if key not in seen:
                seen.add(key)
                summary.append({
                    "type": src["type"],
                    "name": src["name"],
                    "chunks": sum(1 for s in self.sources if s["name"] == src["name"])
                })
        
        return summary

