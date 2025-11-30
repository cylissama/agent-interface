import httpx
import subprocess

from ..config import get_settings


async def detect_gpu() -> bool:
    """Detect if GPU is available via nvidia-smi or Ollama."""
    # Try nvidia-smi first (most reliable)
    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            timeout=2,
            text=True
        )
        if result.returncode == 0 and "GPU" in result.stdout:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try checking Ollama's system info
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama reports GPU usage
            response = await client.get(f"{settings.ollama_base_url}/api/ps")
            if response.status_code == 200:
                data = response.json()
                # If models show size_vram > 0, GPU is likely being used
                if "models" in data and len(data["models"]) > 0:
                    for model in data["models"]:
                        if model.get("size_vram", 0) > 0:
                            return True
    except Exception:
        pass
    
    return False


def get_recommended_model(has_gpu: bool) -> str:
    """Get the recommended model based on GPU availability."""
    if has_gpu:
        # GPU can handle larger models efficiently
        return "llama3.2:latest"  # 3.2B model for better quality
    else:
        # CPU needs smaller models for speed
        return "llama3.2:latest"  # 1B model for faster CPU inference


async def get_system_info() -> dict:
    """Get system information including GPU status and recommended model."""
    has_gpu = await detect_gpu()
    recommended_model = get_recommended_model(has_gpu)
    
    return {
        "has_gpu": has_gpu,
        "recommended_model": recommended_model,
        "device": "GPU" if has_gpu else "CPU",
    }

