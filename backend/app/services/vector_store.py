from collections.abc import Iterable
from typing import Any


class VectorStore:
    """Simplified vector store abstraction."""

    def __init__(self) -> None:
        self._store: list[tuple[list[float], Any]] = []

    def add(self, vector: list[float], metadata: Any) -> None:
        self._store.append((vector, metadata))

    def query(self, vector: list[float], k: int = 5) -> Iterable[Any]:
        # Placeholder similarity search
        return [metadata for _, metadata in self._store][:k]


def get_vector_store() -> VectorStore:
    """Return a singleton vector store instance."""
    # TODO: replace with persistent vector store
    return VectorStore()
