from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from sharecatalog.models.library import LibraryMapping
from sharecatalog.services.sharepoint import (
    MappingResolver,
    confirm_mapping,
    mapped_url,
    mapping_confirmed,
    validate_mapping,
)


class MappingDialog(QDialog):
    def __init__(self, mappings: list[LibraryMapping], parent=None):
        super().__init__(parent)
        self.setWindowTitle("SharePoint library mappings")
        self.resize(820, 470)
        self.mappings = deepcopy(mappings)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Add each synced library explicitly. OneDrive shortcuts and junctions may need "
            "their own mapping. Use the library URL, not a sharing link or AllItems.aspx page. "
            "Changes reset sample confirmation."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.root, self.url = QLineEdit(), QLineEdit()
        self.root.setPlaceholderText(r"C:\Users\Example\Contoso\Engineering - Documents")
        self.url.setPlaceholderText(
            "https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents"
        )
        form = QFormLayout()
        root_row = QHBoxLayout()
        root_row.addWidget(self.root)
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.browse)
        root_row.addWidget(browse)
        form.addRow("Local root", root_row)
        form.addRow("SharePoint library root", self.url)
        layout.addLayout(form)
        actions = QHBoxLayout()
        for label, handler in (
            ("New", self.new),
            ("Apply mapping", self.apply),
            ("Remove", self.remove),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status = QLabel()
        layout.addWidget(self.status)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.finish)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.list.currentRowChanged.connect(self.select)
        self.redraw()

    def redraw(self, selected=-1):
        self.list.blockSignals(True)
        self.list.clear()
        self.list.addItems([m.local_root for m in self.mappings])
        self.list.blockSignals(False)
        self.list.setCurrentRow(selected)
        self.select(selected)

    def select(self, row):
        mapping = self.mappings[row] if 0 <= row < len(self.mappings) else None
        self.root.setText(mapping.local_root if mapping else "")
        self.url.setText(mapping.library_url if mapping else "")
        self.status.setText(
            "Sample manually confirmed"
            if mapping and mapping_confirmed(mapping)
            else "Sample confirmation required before export"
        )

    def new(self):
        self.list.setCurrentRow(-1)
        self.select(-1)
        self.root.setFocus()

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "Choose synchronized library root")
        if path:
            self.root.setText(path)

    def apply(self):
        try:
            row = self.list.currentRow()
            mapping = LibraryMapping(self.root.text().strip(), self.url.text().strip())
            validate_mapping(mapping)
            candidate = list(self.mappings)
            if row >= 0:
                previous = candidate[row]
                mapping.id = previous.id
                if (previous.local_root, previous.library_url) == (
                    mapping.local_root,
                    mapping.library_url,
                ):
                    mapping = previous
                candidate[row] = mapping
            else:
                candidate.append(mapping)
                row = len(candidate) - 1
            MappingResolver(candidate)
            self.mappings = candidate
            self.redraw(row)
            return True
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid mapping", str(exc))
            return False

    def remove(self):
        row = self.list.currentRow()
        if row >= 0:
            del self.mappings[row]
            self.redraw()

    def finish(self):
        if self.root.text() or self.url.text():
            if not self.apply():
                return
        self.accept()


class MappingTestDialog(QDialog):
    def __init__(self, mapping: LibraryMapping, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test library mapping")
        self.resize(760, 280)
        self.mapping = mapping
        self.sample = ""
        self.opened_url = ""
        layout = QVBoxLayout(self)
        explanation = QLabel(
            "Choose an existing sample file, open the generated URL, then confirm only if "
            "the correct document opens. This does not independently verify other documents."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.path = QLabel("No sample selected")
        self.path.setWordWrap(True)
        layout.addWidget(self.path)
        choose = QPushButton("Choose sample file...")
        choose.clicked.connect(self.choose)
        layout.addWidget(choose)
        self.url = QLineEdit()
        self.url.setReadOnly(True)
        layout.addWidget(self.url)
        self.open_button = QPushButton("Open in Browser")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open)
        layout.addWidget(self.open_button)
        self.confirm_button = QPushButton("I confirm the correct document opened")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.confirm)
        layout.addWidget(self.confirm_button)
        cancel = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        cancel.rejected.connect(self.reject)
        layout.addWidget(cancel)

    def choose(self):
        sample, _ = QFileDialog.getOpenFileName(
            self, "Choose sample inside this library", self.mapping.local_root
        )
        if not sample:
            return
        self.confirm_button.setEnabled(False)
        self.opened_url = ""
        try:
            url = mapped_url(self.mapping, sample)
            if not url or not Path(sample).is_file():
                raise ValueError("Choose an existing file inside this library's local root.")
        except ValueError as exc:
            self.sample = ""
            self.url.clear()
            self.open_button.setEnabled(False)
            QMessageBox.warning(self, "Invalid sample", str(exc))
            return
        self.sample = sample
        self.path.setText(sample)
        self.url.setText(url)
        self.open_button.setEnabled(True)

    def open(self):
        if QDesktopServices.openUrl(QUrl(self.url.text())):
            self.opened_url = self.url.text()
            self.confirm_button.setEnabled(True)
        else:
            QMessageBox.warning(
                self, "Browser unavailable", "Could not open the browser. Copy and inspect the URL."
            )

    def confirm(self):
        if self.sample and self.opened_url:
            confirm_mapping(self.mapping, self.sample, self.opened_url)
            self.accept()
