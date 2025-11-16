from fastapi import APIRouter

from ..services import system_service

router = APIRouter()


@router.get("/info")
async def get_system_info():
    """Get system information including GPU status and recommended model."""
    return await system_service.get_system_info()

