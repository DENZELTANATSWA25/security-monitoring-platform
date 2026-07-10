from fastapi import APIRouter

router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)