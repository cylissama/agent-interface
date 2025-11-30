import httpx
from collections.abc import Sequence

from ..config import get_settings


async def generate_response(
    prompt: str,
    context: Sequence[str] | None = None,
    conversation_history: Sequence[dict[str, str]] | None = None,
    model_name: str | None = None,
) -> str:
    """Generate a response using Ollama."""
    settings = get_settings()
    # model = model_name or settings.ollama_model
    model = "llama3.2:latest"  # Use latest 3.2B model for better quality
    
    # Build context if provided
    context_text = ""
    if context:
        context_text = "\n\n=== DOCUMENT CONTENT (ALREADY EXTRACTED AND PROVIDED BELOW) ===\n"
        context_text += "\n\n".join(context)
        context_text += "\n\n=== END OF DOCUMENT CONTENT ===\n"
    
    # Build messages for chat API
    messages = []
    
    # Add system message with context if available
    if context_text:
        system_content = f"""You are a helpful assistant with access to the following content that was just retrieved for this conversation:

{context_text}

IMPORTANT INSTRUCTIONS:
- Answer directly using the content above. Do NOT say you don't have access to real-time data - you DO have it above.
- Be concise and direct. Skip unnecessary preamble or disclaimers.
- If the content contains the answer, state it confidently without caveats.
- Only mention limitations if the content truly doesn't contain what's needed."""
    else:
        system_content = "You are a helpful assistant. Be concise and direct in your responses."
    
    messages.append({"role": "system", "content": system_content})
    
    # Add conversation history
    if conversation_history:
        if context:
            # Limit history when context is provided
            recent_history = list(conversation_history[-3:]) if len(conversation_history) > 3 else conversation_history
            messages.extend(recent_history)
        else:
            messages.extend(conversation_history)
    
    # Add the current user prompt
    messages.append({"role": "user", "content": prompt})
    
    # Call Ollama API with optimized settings
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_ctx": 4096,  # Limit context window for faster processing
                    "num_predict": 512,  # Limit response length for faster generation
                },
            },
        )
        
        if response.status_code != 200:
            return f"Ollama API error (status {response.status_code}). Make sure Ollama is running."
        
        result = response.json()
        
        if "error" in result:
            return f"Ollama error: {result['error']}"
        
        return result.get("message", {}).get("content", "No response generated.")
