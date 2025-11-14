from fastapi import APIRouter

router = APIRouter()


@router.post("/process")
def process_batch() -> dict[str, str]:
    """Kick off a batch processing job."""
    # Placeholder implementation
    return {"status": "queued"}
