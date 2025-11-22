import httpx
import logging

from ..config import get_settings

logger = logging.getLogger(__name__)


async def generate_personality_prompt(character: str) -> str:
    """Generate a personality prompt using GROQ Minstrel API based on character name."""
    settings = get_settings()
    
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY not configured. Please set it in your .env file.")
    
    # GROQ Minstrel API endpoint
    # Groq uses OpenAI-compatible API structure: /openai/v1/chat/completions
    # According to Groq docs: https://console.groq.com/docs/api-reference
    base_url = settings.groq_base_url or "https://api.groq.com"
    # Remove any trailing slashes and ensure we use the correct OpenAI-compatible path
    base_url = base_url.rstrip('/')
    # The correct endpoint is: https://api.groq.com/openai/v1/chat/completions
    endpoint = f"{base_url}/openai/v1/chat/completions"
    model = settings.groq_model or "mixtral-8x7b-32768"
    
    logger.info(f"GROQ API endpoint: {endpoint}")
    
    # Prompt for Minstrel to generate personality description
    minstrel_prompt = f"""Create a detailed personality prompt for an AI assistant that should adopt the persona of "{character}" from a show, movie, game, or other media.

The prompt should:
1. Describe the character's personality traits, speech patterns, and mannerisms in detail
2. Include their typical responses, catchphrases, or vocal tics
3. Specify their attitude, tone, and communication style
4. Include any relevant background or context about the character
5. Be formatted as a system prompt that can be used to instruct an LLM to respond as this character

Make it detailed and specific. The prompt should be ready to use as a system message for an LLM to roleplay as this character.

Character: {character}

Generate the personality prompt now:"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Call GROQ Minstrel API
            # Using Groq's OpenAI-compatible chat completions format
            logger.info(f"Calling GROQ API at endpoint: {endpoint}")
            response = await client.post(
                endpoint,
                json={
                    "model": model,  # Use configured model (default: mixtral-8x7b-32768)
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are Minstrel, an expert at creating detailed character personality prompts for roleplay scenarios."
                        },
                        {
                            "role": "user",
                            "content": minstrel_prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.groq_api_key}",
                },
            )
            
            # Check for errors in response
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"GROQ Minstrel API returned status {response.status_code}: {error_text}")
            
            result = response.json()
            
            # Extract the generated text from GROQ response
            # Adjust based on actual GROQ API response format
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                if content:
                    return content.strip()
            
            # Alternative response format check
            if "content" in result:
                return result["content"].strip()
            
            # If no content found, check for errors
            if "error" in result:
                raise Exception(f"GROQ Minstrel API error: {result['error']}")
            
            raise ValueError(f"Unexpected response format from GROQ Minstrel API: {result}")
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response else str(e)
            raise Exception(f"HTTP error from GROQ Minstrel API (status {e.response.status_code if e.response else 'unknown'}): {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error connecting to GROQ Minstrel API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating personality prompt: {str(e)}")

