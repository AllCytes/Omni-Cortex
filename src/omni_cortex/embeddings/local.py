"""Local embedding generation using sentence-transformers."""

import logging
import sqlite3
import struct
from typing import Optional

import numpy as np

from ..utils.ids import generate_embedding_id
from ..utils.timestamps import now_iso

logger = logging.getLogger(__name__)

# Model configuration
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

# Global model instance (lazy loaded)
_model = None
_model_name = None


def _get_model(model_name: str = DEFAULT_MODEL_NAME):
    """Get or load the sentence-transformers model.

    Args:
        model_name: Name of the model to load

    Returns:
        SentenceTransformer model instance
    """
    global _model, _model_name

    if _model is not None and _model_name == model_name:
        return _model

    try:
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        logger.info(f"Model loaded. Embedding dimension: {_model.get_sentence_embedding_dimension()}")
        return _model
    except ImportError:
        raise ImportError(
            "sentence-transformers is required for local embeddings. "
            "Install with: pip install sentence-transformers"
        )


def generate_embedding(
    text: str,
    model_name: str = DEFAULT_MODEL_NAME,
) -> np.ndarray:
    """Generate embedding for a text string.

    Args:
        text: Text to embed
        model_name: Name of the model to use

    Returns:
        Numpy array of embedding values (384 dimensions)
    """
    model = _get_model(model_name)

    # Generate embedding
    embedding = model.encode(text, convert_to_numpy=True)

    return embedding


def generate_embeddings_batch(
    texts: list[str],
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = 32,
) -> list[np.ndarray]:
    """Generate embeddings for multiple texts efficiently.

    Args:
        texts: List of texts to embed
        model_name: Name of the model to use
        batch_size: Batch size for processing

    Returns:
        List of embedding arrays
    """
    if not texts:
        return []

    model = _get_model(model_name)

    # Generate embeddings in batch
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
    )

    return list(embeddings)


def vector_to_blob(vector: np.ndarray) -> bytes:
    """Convert numpy array to SQLite BLOB.

    Args:
        vector: Numpy array of float32 values

    Returns:
        Bytes representation
    """
    # Ensure float32
    vector = vector.astype(np.float32)
    return vector.tobytes()


def blob_to_vector(blob: bytes) -> np.ndarray:
    """Convert SQLite BLOB to numpy array.

    Args:
        blob: Bytes from database

    Returns:
        Numpy array of float32 values
    """
    return np.frombuffer(blob, dtype=np.float32)


def store_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
    vector: np.ndarray,
    model_name: str = DEFAULT_MODEL_NAME,
) -> str:
    """Store an embedding in the database.

    Args:
        conn: Database connection
        memory_id: ID of the memory
        vector: Embedding vector
        model_name: Model used to generate the embedding

    Returns:
        Embedding ID
    """
    embedding_id = generate_embedding_id()
    blob = vector_to_blob(vector)

    cursor = conn.cursor()

    # Insert or replace embedding
    cursor.execute(
        """
        INSERT OR REPLACE INTO embeddings (id, memory_id, model_name, vector, dimensions, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (embedding_id, memory_id, model_name, blob, len(vector), now_iso()),
    )

    # Update memory's has_embedding flag
    cursor.execute(
        "UPDATE memories SET has_embedding = 1 WHERE id = ?",
        (memory_id,),
    )

    conn.commit()
    return embedding_id


def get_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
) -> Optional[np.ndarray]:
    """Get the embedding for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID

    Returns:
        Embedding vector or None if not found
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT vector FROM embeddings WHERE memory_id = ?",
        (memory_id,),
    )
    row = cursor.fetchone()

    if not row:
        return None

    return blob_to_vector(row["vector"])


def get_all_embeddings(
    conn: sqlite3.Connection,
) -> list[tuple[str, np.ndarray]]:
    """Get all embeddings from the database.

    Returns:
        List of (memory_id, vector) tuples
    """
    cursor = conn.cursor()
    cursor.execute("SELECT memory_id, vector FROM embeddings")

    results = []
    for row in cursor.fetchall():
        vector = blob_to_vector(row["vector"])
        results.append((row["memory_id"], vector))

    return results


def delete_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
) -> bool:
    """Delete embedding for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID

    Returns:
        True if deleted
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM embeddings WHERE memory_id = ?", (memory_id,))

    if cursor.rowcount > 0:
        cursor.execute(
            "UPDATE memories SET has_embedding = 0 WHERE id = ?",
            (memory_id,),
        )
        conn.commit()
        return True

    return False


def generate_and_store_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
    content: str,
    context: Optional[str] = None,
    model_name: str = DEFAULT_MODEL_NAME,
) -> Optional[str]:
    """Generate and store embedding for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID
        content: Memory content
        context: Optional context
        model_name: Model to use

    Returns:
        Embedding ID or None if failed
    """
    try:
        # Combine content and context for embedding
        text = content
        if context:
            text = f"{content}\n\nContext: {context}"

        vector = generate_embedding(text, model_name)
        embedding_id = store_embedding(conn, memory_id, vector, model_name)

        logger.debug(f"Generated embedding for memory {memory_id}")
        return embedding_id

    except Exception as e:
        logger.error(f"Failed to generate embedding for {memory_id}: {e}")
        return None


def get_memories_without_embeddings(
    conn: sqlite3.Connection,
    limit: int = 100,
) -> list[tuple[str, str, Optional[str]]]:
    """Get memories that don't have embeddings.

    Args:
        conn: Database connection
        limit: Maximum number to return

    Returns:
        List of (memory_id, content, context) tuples
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, content, context
        FROM memories
        WHERE has_embedding = 0
        LIMIT ?
        """,
        (limit,),
    )

    return [(row["id"], row["content"], row["context"]) for row in cursor.fetchall()]


def backfill_embeddings(
    conn: sqlite3.Connection,
    batch_size: int = 32,
    model_name: str = DEFAULT_MODEL_NAME,
) -> int:
    """Generate embeddings for all memories that don't have them.

    Args:
        conn: Database connection
        batch_size: Processing batch size
        model_name: Model to use

    Returns:
        Number of embeddings generated
    """
    total_generated = 0

    while True:
        # Get batch of memories without embeddings
        memories = get_memories_without_embeddings(conn, limit=batch_size)

        if not memories:
            break

        # Prepare texts
        texts = []
        for _, content, context in memories:
            text = content
            if context:
                text = f"{content}\n\nContext: {context}"
            texts.append(text)

        # Generate embeddings in batch
        vectors = generate_embeddings_batch(texts, model_name)

        # Store each embedding
        for (memory_id, _, _), vector in zip(memories, vectors):
            store_embedding(conn, memory_id, vector, model_name)
            total_generated += 1

        logger.info(f"Generated {len(memories)} embeddings (total: {total_generated})")

    return total_generated


def is_model_available() -> bool:
    """Check if sentence-transformers is available.

    Returns:
        True if available
    """
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False
