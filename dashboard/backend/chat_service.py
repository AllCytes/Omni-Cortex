"""Chat service for natural language queries about memories using Gemini Flash."""

import os
from typing import Optional, AsyncGenerator, Any

import google.generativeai as genai
from dotenv import load_dotenv

from database import search_memories, get_memories, create_memory
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
        _model = genai.GenerativeModel("gemini-3-flash-preview")
    return _model


def is_available() -> bool:
    """Check if the chat service is available."""
    return _api_key is not None


def _build_prompt(question: str, context_str: str) -> str:
    """Build the prompt for the AI model."""
    return f"""You are a helpful assistant that answers questions about stored memories and knowledge.

The user has a collection of memories that capture decisions, solutions, insights, errors, preferences, and other learnings from their work.

Here are the relevant memories:

{context_str}

User question: {question}

Instructions:
1. Answer the question based on the memories provided
2. If the memories don't contain relevant information, say so
3. Reference specific memories when appropriate using [[Memory N]] format (e.g., "According to [[Memory 1]]...")
4. Be concise but thorough
5. If the question is asking for a recommendation or decision, synthesize from multiple memories if possible

Answer:"""


def _get_memories_and_sources(db_path: str, question: str, max_memories: int) -> tuple[str, list[dict]]:
    """Get relevant memories and build context string and sources list."""
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
        return "", []

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
    return context_str, sources


async def stream_ask_about_memories(
    db_path: str,
    question: str,
    max_memories: int = 10,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream a response to a question about memories.

    Yields events with type 'sources', 'chunk', 'done', or 'error'.
    """
    if not is_available():
        yield {
            "type": "error",
            "data": "Chat is not available. Please configure GEMINI_API_KEY or GOOGLE_API_KEY environment variable.",
        }
        return

    model = get_model()
    if not model:
        yield {
            "type": "error",
            "data": "Failed to initialize Gemini model.",
        }
        return

    context_str, sources = _get_memories_and_sources(db_path, question, max_memories)

    if not sources:
        yield {
            "type": "sources",
            "data": [],
        }
        yield {
            "type": "chunk",
            "data": "No memories found in the database to answer your question.",
        }
        yield {
            "type": "done",
            "data": None,
        }
        return

    # Yield sources first
    yield {
        "type": "sources",
        "data": sources,
    }

    # Build and stream the response
    prompt = _build_prompt(question, context_str)

    try:
        response = model.generate_content(prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield {
                    "type": "chunk",
                    "data": chunk.text,
                }

        yield {
            "type": "done",
            "data": None,
        }
    except Exception as e:
        yield {
            "type": "error",
            "data": f"Failed to generate response: {str(e)}",
        }


async def save_conversation(
    db_path: str,
    messages: list[dict],
    referenced_memory_ids: list[str] | None = None,
    importance: int = 60,
) -> dict:
    """Save a chat conversation as a memory.

    Args:
        db_path: Path to the database file
        messages: List of message dicts with 'role', 'content', 'timestamp'
        referenced_memory_ids: IDs of memories referenced in the conversation
        importance: Importance score for the memory

    Returns:
        Dict with memory_id and summary
    """
    if not messages:
        raise ValueError("No messages to save")

    # Format conversation into markdown
    content_lines = ["## Chat Conversation\n"]
    for msg in messages:
        role = "**You**" if msg["role"] == "user" else "**Assistant**"
        content_lines.append(f"### {role}\n{msg['content']}\n")

    content = "\n".join(content_lines)

    # Generate summary using Gemini if available
    summary = "Chat conversation"
    model = get_model()
    if model:
        try:
            summary_prompt = f"""Summarize this conversation in one concise sentence (max 100 chars):

{content[:2000]}

Summary:"""
            response = model.generate_content(summary_prompt)
            summary = response.text.strip()[:100]
        except Exception:
            # Use fallback summary
            first_user_msg = next((m for m in messages if m["role"] == "user"), None)
            if first_user_msg:
                summary = f"Q: {first_user_msg['content'][:80]}..."

    # Extract topics from conversation for tags
    tags = ["chat", "conversation"]

    # Create memory
    memory_id = create_memory(
        db_path=db_path,
        content=content,
        memory_type="conversation",
        context=f"Chat conversation: {summary}",
        tags=tags,
        importance_score=importance,
        related_memory_ids=referenced_memory_ids,
    )

    return {
        "memory_id": memory_id,
        "summary": summary,
    }


async def ask_about_memories(
    db_path: str,
    question: str,
    max_memories: int = 10,
) -> dict:
    """Ask a natural language question about memories (non-streaming).

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

    context_str, sources = _get_memories_and_sources(db_path, question, max_memories)

    if not sources:
        return {
            "answer": "No memories found in the database to answer your question.",
            "sources": [],
            "error": None,
        }

    prompt = _build_prompt(question, context_str)

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
