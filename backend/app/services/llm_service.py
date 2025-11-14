import httpx
from collections.abc import Sequence

from ..config import get_settings


async def generate_response(
    prompt: str,
    context: Sequence[str] | None = None,
    conversation_history: Sequence[dict[str, str]] | None = None,
    personality_prompt: str | None = None,
    model_name: str | None = None,
) -> str:
    """Generate a response using Ollama."""
    settings = get_settings()
    # Use provided model or fall back to configured default
    model = model_name or settings.ollama_model
    
    # Build context if provided
    context_text = ""
    if context:
        context_text = "\n\nContext from documents:\n" + "\n".join(context)
    
    # Build messages for chat API
    messages = []
    
    # Add system message with personality prompt if available, otherwise use default
    system_content = ""
    if personality_prompt:
        system_content = personality_prompt
        if context_text:
            system_content += context_text
    elif context_text:
        system_content = f"You are a helpful assistant. {context_text}"
    
    if system_content:
        messages.append({"role": "system", "content": system_content})
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add the current user prompt
    messages.append({"role": "user", "content": prompt})
    
    # Call Ollama API
    async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for slower responses
        try:
            response = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                },
                headers={"Content-Type": "application/json"},
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_text = response.text
                return f"Ollama API error (status {response.status_code}): {error_text}. Make sure Ollama is running on {settings.ollama_base_url} and the model '{model}' is available."
            
            result = response.json()
            
            # Check for errors in response
            if "error" in result:
                return f"Ollama error: {result['error']}"
            
            # Extract message content
            message = result.get("message", {})
            content = message.get("content", "")
            
            if not content:
                return "No response generated from Ollama. The model may not have produced any output."
            
            return content
            
        except httpx.ConnectError as e:
            return f"Error connecting to Ollama: Cannot reach {settings.ollama_base_url}. Make sure Ollama is running."
        except httpx.TimeoutException as e:
            return f"Ollama request timed out. The model may be taking too long to respond. Try again or use a faster model."
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response else str(e)
            return f"Ollama HTTP error (status {e.response.status_code if e.response else 'unknown'}): {error_text}"
        except httpx.RequestError as e:
            return f"Error connecting to Ollama: {str(e)}. Make sure Ollama is running on {settings.ollama_base_url}"
        except Exception as e:
            import traceback
            error_details = str(e) if str(e) else type(e).__name__
            return f"Error generating response: {error_details}"
