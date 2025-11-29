"""
Vector Store service using ChromaDB for semantic search.
Uses Ollama for generating embeddings.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional

import chromadb
import httpx
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings

logger = logging.getLogger(__name__)

# Singleton instance
_vector_store: Optional["VectorStore"] = None


class VectorStore:
    """
    Vector store using ChromaDB for document storage and semantic search.
    Uses Ollama embeddings for vector generation.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize the vector store.
        
        Args:
            persist_dir: Directory for ChromaDB persistence. If None, uses config default.
        """
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.embedding_model = settings.embedding_model
        self.ollama_url = settings.ollama_base_url
        
        # Ensure persist directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        
        # Get or create the documents collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        logger.info(f"Vector store initialized with {self.collection.count()} documents")

    def _get_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Truncate very long texts (embedding models have limits)
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text},
                )
                response.raise_for_status()
                result = response.json()
                return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")

    def _chunk_text(
        self, 
        text: str, 
        chunk_size: int = 500, 
        overlap: int = 50
    ) -> list[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target words per chunk
            overlap: Words to overlap between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                chunks.append(chunk_text)
            
            # Move forward, keeping overlap
            start = end - overlap if end < len(words) else len(words)
        
        return chunks

    def _generate_id(self, text: str, source: str, chunk_idx: int = 0) -> str:
        """Generate a unique ID for a chunk."""
        content = f"{source}:{chunk_idx}:{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()

    def add_document(
        self,
        text: str,
        source_name: str,
        source_type: str = "document",
        document_id: Optional[int] = None,
        chunk_size: int = 500,
    ) -> dict:
        """
        Add a document to the vector store.
        
        Args:
            text: Document text content
            source_name: Name/identifier of the source
            source_type: Type of source ('document', 'url', 'file')
            document_id: Optional database document ID
            chunk_size: Words per chunk for splitting
            
        Returns:
            Dictionary with indexing results
        """
        if not text or not text.strip():
            return {"success": False, "error": "Empty text provided"}
        
        # Chunk the document
        chunks = self._chunk_text(text, chunk_size=chunk_size)
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = self._generate_id(chunk, source_name, idx)
            
            try:
                embedding = self._get_embedding(chunk)
            except Exception as e:
                logger.warning(f"Failed to embed chunk {idx} of {source_name}: {e}")
                continue
            
            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk)
            metadatas.append({
                "source_name": source_name,
                "source_type": source_type,
                "document_id": str(document_id) if document_id else "",
                "chunk_index": idx,
                "total_chunks": len(chunks),
            })
        
        if not ids:
            return {"success": False, "error": "No chunks could be embedded"}
        
        # Add to ChromaDB (upsert to handle re-indexing)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        logger.info(f"Indexed {len(ids)} chunks from {source_name}")
        
        return {
            "success": True,
            "source_name": source_name,
            "chunks_indexed": len(ids),
            "total_chunks": len(chunks),
        }

    def search(
        self,
        query: str,
        n_results: int = 5,
        source_type: Optional[str] = None,
        document_id: Optional[int] = None,
    ) -> list[dict]:
        """
        Search for relevant chunks using semantic similarity.
        
        Args:
            query: Search query
            n_results: Maximum number of results
            source_type: Optional filter by source type
            document_id: Optional filter by document ID
            
        Returns:
            List of matching chunks with metadata and scores
        """
        try:
            query_embedding = self._get_embedding(query)
        except Exception as e:
            logger.error(f"Search failed - couldn't embed query: {e}")
            return []
        
        # Build where filter
        where_filter = None
        if source_type or document_id:
            conditions = []
            if source_type:
                conditions.append({"source_type": source_type})
            if document_id:
                conditions.append({"document_id": str(document_id)})
            
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distance, convert to similarity score
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance  # Cosine distance to similarity
                
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "similarity": round(similarity, 4),
                })
        
        return formatted

    def delete_by_source(self, source_name: str) -> dict:
        """
        Delete all chunks from a specific source.
        
        Args:
            source_name: Name of the source to delete
            
        Returns:
            Dictionary with deletion results
        """
        try:
            # Get IDs to delete
            results = self.collection.get(
                where={"source_name": source_name},
                include=[],
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                return {
                    "success": True,
                    "deleted_chunks": len(results["ids"]),
                    "source_name": source_name,
                }
            
            return {"success": True, "deleted_chunks": 0, "source_name": source_name}
            
        except Exception as e:
            logger.error(f"Delete failed for {source_name}: {e}")
            return {"success": False, "error": str(e)}

    def delete_by_document_id(self, document_id: int) -> dict:
        """
        Delete all chunks for a document by its database ID.
        
        Args:
            document_id: Database document ID
            
        Returns:
            Dictionary with deletion results
        """
        try:
            results = self.collection.get(
                where={"document_id": str(document_id)},
                include=[],
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                return {
                    "success": True,
                    "deleted_chunks": len(results["ids"]),
                    "document_id": document_id,
                }
            
            return {"success": True, "deleted_chunks": 0, "document_id": document_id}
            
        except Exception as e:
            logger.error(f"Delete failed for document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        count = self.collection.count()
        
        # Get unique sources
        sources = set()
        if count > 0:
            try:
                results = self.collection.get(include=["metadatas"])
                for meta in results["metadatas"]:
                    if meta and "source_name" in meta:
                        sources.add(meta["source_name"])
            except Exception:
                pass
        
        return {
            "total_chunks": count,
            "unique_sources": len(sources),
            "sources": list(sources)[:20],  # Limit to first 20
            "embedding_model": self.embedding_model,
            "persist_dir": self.persist_dir,
        }

    def clear(self) -> dict:
        """Clear all documents from the vector store."""
        try:
            # Delete and recreate the collection
            self.client.delete_collection("documents")
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"},
            )
            return {"success": True, "message": "Vector store cleared"}
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return {"success": False, "error": str(e)}


def get_vector_store() -> VectorStore:
    """Return singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
