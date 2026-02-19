from fastapi import APIRouter, Depends
from app.core.auth import verify_token

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "SynthTeam Backend Running"}

@router.get("/protected")
async def protected(user=Depends(verify_token)):
    return {"user": user}

