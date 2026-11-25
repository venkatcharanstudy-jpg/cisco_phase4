from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_menu_repository
from app.models.user import User
from app.repositories.menu_repository import MenuRepository
from app.schemas import LoginOut, MenuItemOut

router = APIRouter(prefix="/api")


@router.get("/auth/me", response_model=LoginOut)
def me(user: User = Depends(get_current_user)) -> LoginOut:
    return LoginOut(username=user.username, role=user.role)


@router.get("/menu", response_model=list[MenuItemOut])
def list_menu(
    _user: User = Depends(get_current_user),
    menu: MenuRepository = Depends(get_menu_repository),
) -> list[MenuItemOut]:
    return [MenuItemOut.model_validate(item) for item in menu.list_active()]
