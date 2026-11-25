from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem


class MenuRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_active(self) -> list[MenuItem]:
        stmt = select(MenuItem).where(MenuItem.active.is_(True)).order_by(MenuItem.category, MenuItem.id)
        return list(self._session.scalars(stmt))

    def get(self, item_id: int) -> MenuItem | None:
        return self._session.get(MenuItem, item_id)

    def get_for_update(self, item_ids: list[int]) -> dict[int, MenuItem]:
        """Lock rows in ascending id order so concurrent orders cannot deadlock."""
        if not item_ids:
            return {}
        stmt = (
            select(MenuItem)
            .where(MenuItem.id.in_(sorted(set(item_ids))))
            .order_by(MenuItem.id)
            .with_for_update()
        )
        return {item.id: item for item in self._session.scalars(stmt)}

    def add(self, item: MenuItem) -> MenuItem:
        self._session.add(item)
        self._session.flush()
        return item
