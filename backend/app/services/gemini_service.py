import httpx

from ..config import get_settings


async def generate_personality_prompt(character: str) -> str:
    """Generate a personality prompt using Google Gemini API."""
    settings = get_settings()
    
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY not configured. Please set it in your .env file.")
    
    # Prompt for Gemini to generate personality description
    gemini_prompt = f"""Create a detailed personality prompt for an AI assistant that should adopt the persona of "{character}" from a show, movie, or game.

The prompt should:
1. Describe the character's personality traits, speech patterns, and mannerisms
2. Include their typical responses, catchphrases, or vocal tics
3. Specify their attitude, tone, and communication style
4. Include any relevant background or context about the character
5. Be formatted as a system prompt that can be used to instruct an LLM to respond as this character

Make it detailed and specific. The prompt should be ready to use as a system message for an LLM.

Character: {character}

Generate the personality prompt now:"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Use the correct Gemini API endpoint
            # Use gemini-2.0-flash which is available and supports generateContent
            model_name = "gemini-2.0-flash"
            # Use v1 API
            url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={settings.gemini_api_key}"
            
            response = await client.post(
                url,
                json={
                    "contents": [{
                        "parts": [{
                            "text": gemini_prompt
                        }]
                    }]
                },
                headers={"Content-Type": "application/json"},
            )
            
            # Check for errors in response
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"Gemini API returned status {response.status_code}: {error_text}")
            
            result = response.json()
            
            # Extract the generated text from Gemini response
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0].get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
            
            # If no candidates, check for errors
            if "error" in result:
                raise Exception(f"Gemini API error: {result['error']}")
            
            raise ValueError(f"Unexpected response format from Gemini API: {result}")
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if e.response else str(e)
            raise Exception(f"HTTP error from Gemini API (status {e.response.status_code if e.response else 'unknown'}): {error_text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error connecting to Gemini API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating personality prompt: {str(e)}")


async def generate_character_image(character: str) -> str | None:
    """Generate a character image using Google Gemini API."""
    settings = get_settings()
    
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY not configured. Please set it in your .env file.")
    
    # Try to use Gemini 2.5 image generation model first
    # If not available, fall back to generating a visual description
    image_prompt = f"Generate a profile picture or avatar of {character} from a show, movie, or game. Show their distinctive appearance, clothing, and features in a simple, clear style suitable for a profile picture."

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # First, try the image generation model (gemini-2.5-flash-image)
            # This requires Blaze plan, so we'll fall back if it fails
            image_model = "gemini-2.5-flash-image"
            url = f"https://generativelanguage.googleapis.com/v1/models/{image_model}:generateContent?key={settings.gemini_api_key}"
            
            try:
                response = await client.post(
                    url,
                    json={
                        "contents": [{
                            "parts": [{
                                "text": image_prompt
                            }]
                        }]
                    },
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"DEBUG: Image generation response: {result}")  # Debug logging
                    
                    # Check for generated_images field (newer API format)
                    if "generated_images" in result and len(result["generated_images"]) > 0:
                        image_data = result["generated_images"][0].get("bytes_base64_encoded")
                        if image_data:
                            return f"data:image/png;base64,{image_data}"
                    
                    # Check if response contains image data in candidates
                    if "candidates" in result and len(result["candidates"]) > 0:
                        content = result["candidates"][0].get("content", {})
                        parts = content.get("parts", [])
                        # Look for image data in response
                        for part in parts:
                            if "inlineData" in part:
                                # Return base64 image data
                                image_data = part["inlineData"].get("data")
                                mime_type = part["inlineData"].get("mimeType", "image/png")
                                if image_data:
                                    return f"data:{mime_type};base64,{image_data}"
                            elif "text" in part:
                                # If we get text, it might be an error message or description
                                text_content = part["text"]
                                # Don't return text if we're trying to get an image
                                print(f"DEBUG: Got text instead of image: {text_content[:100]}")
                                continue
                else:
                    # Log the error but continue to fallback
                    error_text = response.text
                    print(f"DEBUG: Image generation failed with status {response.status_code}: {error_text[:200]}")
            except Exception as e:
                # Image generation model not available, fall back to description
                print(f"DEBUG: Image generation exception: {e}")
                pass
            
            # Fallback: Use Imagen API for image generation (if available)
            # Try using the Imagen endpoint directly
            try:
                imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={settings.gemini_api_key}"
                imagen_response = await client.post(
                    imagen_url,
                    json={
                        "instances": [{
                            "prompt": image_prompt
                        }],
                        "parameters": {
                            "sampleCount": 1,
                            "aspectRatio": "1:1"
                        }
                    },
                    headers={"Content-Type": "application/json"},
                )
                
                if imagen_response.status_code == 200:
                    imagen_result = imagen_response.json()
                    print(f"DEBUG: Imagen response: {imagen_result}")
                    # Check for base64 image in predictions
                    if "predictions" in imagen_result and len(imagen_result["predictions"]) > 0:
                        image_b64 = imagen_result["predictions"][0].get("bytesBase64Encoded")
                        if image_b64:
                            return f"data:image/png;base64,{image_b64}"
            except Exception as e:
                print(f"DEBUG: Imagen API exception: {e}")
                pass
            
            # Final fallback: Create a simple terminal-style SVG avatar
            # This matches the terminal aesthetic better than generic avatars
            try:
                import hashlib
                import base64
                
                # Extract character name (first meaningful word)
                name_parts = character.split()
                skip_words = {"from", "in", "the", "a", "an", "of", "and", "or", "trevor", "philips"}
                name_words = [w for w in name_parts if w.lower() not in skip_words]
                char_name = name_words[0] if name_words else (name_parts[0] if name_parts else character[:1])
                char_initials = char_name[:2].upper() if len(char_name) >= 2 else char_name[0].upper() if char_name else "?"
                
                # Create a deterministic green color based on character name
                hash_obj = hashlib.md5(character.encode())
                hash_hex = hash_obj.hexdigest()
                # Use terminal green shades
                green_shade = int(hash_hex[0:2], 16) % 100 + 100  # 100-200 range
                green_color = f"00{green_shade:02x}00"
                
                # Create a simple SVG avatar with terminal style
                svg_content = f'''<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <rect width="128" height="128" fill="#000000" stroke="#00ff00" stroke-width="2"/>
  <text x="50%" y="50%" font-family="Courier New, monospace" font-size="48" font-weight="bold" 
        fill="#00ff00" text-anchor="middle" dominant-baseline="central">{char_initials}</text>
</svg>'''
                
                # Convert SVG to base64
                svg_bytes = svg_content.encode('utf-8')
                svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
                return f"data:image/svg+xml;base64,{svg_b64}"
            except Exception as e:
                print(f"DEBUG: SVG avatar fallback exception: {e}")
                import traceback
                traceback.print_exc()
                pass
            
            # If all else fails, return None (will show green dash in UI)
            return None
        except Exception as e:
            print(f"Error generating character image: {e}")
            import traceback
            traceback.print_exc()
            return None

