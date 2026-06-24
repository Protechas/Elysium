"""QML list models for Elysium UI."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot

from elysium.core.models import AppDefinition
from elysium.ui.icon_utils import to_icon_url
from elysium.ui.theme import status_colors


class AppListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    IconPathRole = Qt.UserRole + 4
    StatusRole = Qt.UserRole + 5
    TagsRole = Qt.UserRole + 6
    StatusBgRole = Qt.UserRole + 7
    StatusFgRole = Qt.UserRole + 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[dict] = []
        self._filter = ""

    def roleNames(self):
        return {
            self.IdRole: b"appId",
            self.NameRole: b"name",
            self.DescriptionRole: b"description",
            self.IconPathRole: b"iconPath",
            self.StatusRole: b"status",
            self.TagsRole: b"tags",
            self.StatusBgRole: b"statusBg",
            self.StatusFgRole: b"statusFg",
        }

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._visible_items())

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._visible_items()[index.row()]
        if role == self.IdRole:
            return item["id"]
        if role == self.NameRole:
            return item["name"]
        if role == self.DescriptionRole:
            return item["description"]
        if role == self.IconPathRole:
            return item["iconPath"]
        if role == self.StatusRole:
            return item["status"]
        if role == self.TagsRole:
            return item["tags"]
        if role == self.StatusBgRole:
            return item["statusBg"]
        if role == self.StatusFgRole:
            return item["statusFg"]
        return None

    def _visible_items(self) -> list[dict]:
        if not self._filter:
            return self._items
        q = self._filter.lower()
        return [
            item
            for item in self._items
            if q in item["name"].lower()
            or q in item["description"].lower()
            or q in item["tags"].lower()
            or q in item["status"].lower()
        ]

    @Slot(str)
    def setFilterText(self, text: str) -> None:
        self.beginResetModel()
        self._filter = (text or "").strip()
        self.endResetModel()

    def set_items(self, items: list[dict]) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def update_status(self, app_id: str, status: str) -> None:
        for idx, item in enumerate(self._items):
            if item["id"] == app_id:
                bg, fg = status_colors(status)
                item["status"] = status
                item["statusBg"] = bg
                item["statusFg"] = fg
                model_index = self.index(idx)
                for role in (
                    self.StatusRole,
                    self.StatusBgRole,
                    self.StatusFgRole,
                ):
                    self.dataChanged.emit(model_index, model_index, [role])
                break

    def update_icon(self, app_id: str, icon_path: str) -> None:
        icon_url = to_icon_url(icon_path) if icon_path and not icon_path.startswith("file:") else icon_path
        for idx, item in enumerate(self._items):
            if item["id"] == app_id:
                item["iconPath"] = icon_url
                model_index = self.index(idx)
                self.dataChanged.emit(model_index, model_index, [self.IconPathRole])
                break

    def count_by_status(self, status: str) -> int:
        return sum(1 for item in self._items if item["status"] == status)

    def total_count(self) -> int:
        return len(self._items)

    @staticmethod
    def item_from_app(
        app: AppDefinition,
        *,
        icon_path: str,
        status: str,
    ) -> dict:
        bg, fg = status_colors(status)
        return {
            "id": app.id,
            "name": app.name,
            "description": app.description or "",
            "iconPath": to_icon_url(icon_path),
            "status": status,
            "tags": ", ".join(app.tags),
            "statusBg": bg,
            "statusFg": fg,
        }
