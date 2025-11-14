from collections.abc import Sequence


def generate_response(prompt: str, context: Sequence[str] | None = None) -> str:
    """Placeholder LLM call."""
    context_text = "\n".join(context or [])
    return f"Echoing prompt: {prompt}\nContext: {context_text}"
