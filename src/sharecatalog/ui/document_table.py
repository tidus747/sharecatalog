from PySide6.QtCore import QAbstractTableModel, Qt, Signal

from sharecatalog.models.document import DocumentEntry


class DocumentTableModel(QAbstractTableModel):
    changed = Signal()
    headers = (
        "Include",
        "Original filename",
        "Extension",
        "Document title",
        "Description",
        "SharePoint URL",
        "Link status",
        "Open link",
    )
    attributes = (
        "included",
        "original_filename",
        "extension",
        "title",
        "description",
        "sharepoint_url",
        "link_status",
        "",
    )

    def __init__(self, documents: list[DocumentEntry], parent=None):
        super().__init__(parent)
        self.documents = documents

    def replace(self, documents: list[DocumentEntry]) -> None:
        self.beginResetModel()
        self.documents = documents
        self.endResetModel()

    def rowCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self.documents)

    def columnCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self.headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        document = self.documents[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.CheckStateRole and column == 0:
            return Qt.CheckState.Checked if document.included else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.ToolTipRole:
            return (
                document.local_path
                if column == 1
                else (
                    "Generated links are not remotely verified. "
                    "Open and review before relying on them."
                    if column == 6
                    else self.data(index)
                )
            )
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if column == 0:
                return ""
            if column == 7:
                return "Open in browser" if document.sharepoint_url else ""
            return str(getattr(document, self.attributes[column]))
        return None

    def flags(self, index):
        flags = super().flags(index)
        if index.column() in (3, 4):
            flags |= Qt.ItemFlag.ItemIsEditable
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        document = self.documents[index.row()]
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            document.included = value in (Qt.CheckState.Checked, Qt.CheckState.Checked.value)
        elif role == Qt.ItemDataRole.EditRole and index.column() in (3, 4):
            setattr(document, self.attributes[index.column()], str(value))
        else:
            return False
        self.dataChanged.emit(index, index, [role])
        self.changed.emit()
        return True
