from fastapi import APIRouter
from pydantic import BaseModel

from app.services.modules import MODULES

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleInfo(BaseModel):
    name: str
    description: str
    timeout: int


@router.get("", response_model=list[ModuleInfo])
def list_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(name=m.name, description=m.description, timeout=m.timeout)
        for m in MODULES
    ]
