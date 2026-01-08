"""Chat service for natural language queries about memories using Gemini Flash."""

import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

from database import search_memories, get_memories
from models import FilterParams

# Load environment variables
load_dotenv()

# Configure Gemini
_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
_model: Optional[genai.GenerativeModel] = None


def get_model() -> Optional[genai.GenerativeModel]:
    """Get or initialize the Gemini model."""
    global _model
    if _model is None and _api_key:
        genai.configure(api_key=_api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash-exp")
    return _model


def is_available() -> bool:
    """Check if the chat service is available."""
    return _api_key is not None


async def ask_about_memories(
    db_path: str,
    question: str,
    max_memories: int = 10,
) -> dict:
    """Ask a natural language question about memories.

    Args:
        db_path: Path to the database file
        question: The user's question
        max_memories: Maximum memories to include in context

    Returns:
        Dict with answer and sources
    """
    if not is_available():
        return {
            "answer": "Chat is not available. Please configure GEMINI_API_KEY or GOOGLE_API_KEY environment variable.",
            "sources": [],
            "error": "api_key_missing",
        }

    model = get_model()
    if not model:
        return {
            "answer": "Failed to initialize Gemini model.",
            "sources": [],
            "error": "model_init_failed",
        }

    # Search for relevant memories
    memories = search_memories(db_path, question, limit=max_memories)

    # If no memories found via search, get recent ones
    if not memories:
        filters = FilterParams(
            sort_by="last_accessed",
            sort_order="desc",
            limit=max_memories,
            offset=0,
        )
        memories = get_memories(db_path, filters)

    if not memories:
        return {
            "answer": "No memories found in the database to answer your question.",
            "sources": [],
            "error": None,
        }

    # Build context from memories
    memory_context = []
    sources = []
    for i, mem in enumerate(memories, 1):
        memory_context.append(f"""
Memory {i}:
- Type: {mem.memory_type}
- Content: {mem.content}
- Context: {mem.context or 'N/A'}
- Tags: {', '.join(mem.tags) if mem.tags else 'N/A'}
- Status: {mem.status}
- Importance: {mem.importance_score}/100
""")
        sources.append({
            "id": mem.id,
            "type": mem.memory_type,
            "content_preview": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
            "tags": mem.tags,
        })

    context_str = "\n---\n".join(memory_context)

    # Create prompt
    prompt = f"""You are a helpful assistant that answers questions about stored memories and knowledge.

The user has a collection of memories that capture decisions, solutions, insights, errors, preferences, and other learnings from their work.

Here are the relevant memories:

{context_str}

User question: {question}

Instructions:
1. Answer the question based on the memories provided
2. If the memories don't contain relevant information, say so
3. Reference specific memories when appropriate (e.g., "According to memory 1...")
4. Be concise but thorough
5. If the question is asking for a recommendation or decision, synthesize from multiple memories if possible

Answer:"""

    try:
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        return {
            "answer": f"Failed to generate response: {str(e)}",
            "sources": sources,
            "error": "generation_failed",
        }

    return {
        "answer": answer,
        "sources": sources,
        "error": None,
    }
