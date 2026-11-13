from pathlib import Path

from PySide6.QtCore import QMimeData, QSortFilterProxyModel, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from sharecatalog.models.document import LinkStatus
from sharecatalog.models.project import Project
from sharecatalog.services import exporter
from sharecatalog.services.everything import EverythingAdapter
from sharecatalog.services.preferences import Preferences
from sharecatalog.services.project_store import atomic_write, load_project, save_project
from sharecatalog.services.sharepoint import mapping_confirmed
from sharecatalog.ui.document_table import DocumentTableModel
from sharecatalog.ui.mapping_dialog import MappingDialog, MappingTestDialog
from sharecatalog.ui.settings_dialog import SettingsDialog


class SearchWorker(QThread):
    result = Signal(object)
    failed = Signal(str)

    def __init__(self, adapter, arguments=None, parent=None):
        super().__init__(parent)
        self.adapter, self.arguments = adapter, arguments

    def run(self):
        try:
            if self.arguments is None:
                self.adapter.probe()
                self.result.emit(None)
            else:
                self.result.emit(self.adapter.search(*self.arguments))
        except (RuntimeError, ValueError) as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, preferences: Preferences, preferences_path: Path):
        super().__init__()
        self.preferences = preferences
        self.preferences_path = preferences_path
        self.project = Project()
        self.project_path = None
        self.dirty = False
        self.worker = None
        self.resize(preferences.width, preferences.height)
        toolbar = QToolBar("Project", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addWidget(QLabel("  ShareCatalog  "))
        self.project_actions = []
        for label, handler, shortcut in (
            ("Open Project", self.open_project, QKeySequence.StandardKey.Open),
            ("Save Project", self.save, QKeySequence.StandardKey.Save),
            ("Settings", self.settings, None),
        ):
            action = QAction(label, self)
            action.triggered.connect(handler)
            if shortcut:
                action.setShortcut(shortcut)
            toolbar.addAction(action)
            self.project_actions.append(action)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        search_box = QGroupBox("Search indexed documents")
        form = QFormLayout(search_box)
        self.directory = QLineEdit()
        self.directory.setPlaceholderText("Choose a local OneDrive synchronized directory")
        row = QHBoxLayout()
        row.addWidget(self.directory)
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        form.addRow("Local directory", row)
        self.filename = QLineEdit()
        self.filename.setPlaceholderText("Optional literal filename text")
        form.addRow("Filename contains", self.filename)
        self.extensions = QLineEdit(self.project.extensions)
        self.extensions.setPlaceholderText("pdf,docx,xlsx or * for all file types")
        form.addRow("Extensions", self.extensions)
        row = QHBoxLayout()
        self.search_button = QPushButton("Search Everything")
        self.search_button.setDefault(True)
        self.search_button.clicked.connect(self.search)
        self.retry = QPushButton("Retry connection")
        self.retry.clicked.connect(self.probe)
        row.addWidget(self.search_button)
        row.addWidget(self.retry)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        row.addWidget(self.progress)
        row.addStretch()
        form.addRow(row)
        layout.addWidget(search_box)
        mappings = QGroupBox("SharePoint library mapping")
        row = QHBoxLayout(mappings)
        self.mapping_combo = QComboBox()
        self.mapping_combo.setMinimumWidth(230)
        self.mapping_combo.currentIndexChanged.connect(self.mapping_status)
        self.mapping_label = QLabel()
        self.mapping_label.setWordWrap(True)
        self.configure_button = QPushButton("Configure mappings")
        self.configure_button.clicked.connect(self.configure_mappings)
        self.test_button = QPushButton("Test Mapping")
        self.test_button.clicked.connect(self.test_mapping)
        for widget in (
            self.mapping_combo,
            self.mapping_label,
            self.configure_button,
            self.test_button,
        ):
            row.addWidget(widget)
        layout.addWidget(mappings)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(
            "Filter catalog rows by filename, title, description, extension, or status"
        )
        layout.addWidget(self.filter)
        self.model = DocumentTableModel(self.project.documents, self)
        self.model.changed.connect(self.modified)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter.textChanged.connect(self.proxy.setFilterFixedString)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setWordWrap(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        self.table.clicked.connect(self.table_click)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate((65, 160, 65, 160, 180, 180, 220, 110)):
            self.table.setColumnWidth(column, width)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.count = QLabel("No documents yet. Choose a directory and search Everything.")
        layout.addWidget(self.count)
        row = QHBoxLayout()
        for label, handler in (
            ("Select All", lambda: self.select_all(True)),
            ("Select None", lambda: self.select_all(False)),
            ("Open selected link", self.open_link),
            ("Copy for Confluence", self.copy_confluence),
            ("Export CSV", lambda: self.export("csv")),
            ("Export HTML", lambda: self.export("html")),
            ("Save Project", self.save),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            row.addWidget(button)
        layout.addLayout(row)
        self.statusBar().showMessage(
            "Ready. Configure Everything in Settings if es.exe is not on PATH."
        )
        for edit in (self.directory, self.filename, self.extensions):
            edit.textChanged.connect(self.modified)
            edit.returnPressed.connect(self.search)
        self.update_mappings()
        self.update_title()

    def update_title(self):
        name = self.project_path.name if self.project_path else "Untitled catalog"
        self.setWindowTitle(f"{'*' if self.dirty else ''}{name} | ShareCatalog")

    def modified(self, *_):
        self.dirty = True
        self.update_title()

    def sync_fields(self):
        self.project.search_directory = self.directory.text().strip()
        self.project.filename_filter = self.filename.text()
        self.project.extensions = self.extensions.text()

    def browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "Choose synchronized directory", self.directory.text()
        )
        if path:
            self.directory.setText(path)

    def settings(self):
        dialog = SettingsDialog(self.preferences, self)
        if dialog.exec():
            self.preferences.executable = dialog.executable.text().strip()
            self.preferences.result_limit = dialog.limit.value()
            self.save_preferences()
            self.probe()

    def set_busy(self, busy):
        for widget in (
            self.search_button,
            self.retry,
            self.configure_button,
            self.test_button,
            self.directory,
            self.filename,
            self.extensions,
        ):
            widget.setEnabled(not busy)
        for action in self.project_actions:
            action.setEnabled(not busy)
        self.progress.setVisible(busy)

    def start_worker(self, arguments=None):
        if self.worker and self.worker.isRunning():
            return
        self.set_busy(True)
        self.statusBar().showMessage(
            "Searching Everything..." if arguments else "Checking Everything connection..."
        )
        self.worker = SearchWorker(EverythingAdapter(self.preferences.executable), arguments, self)
        self.worker.result.connect(self.search_done)
        self.worker.failed.connect(self.search_failed)
        self.worker.finished.connect(lambda: self.set_busy(False))
        self.worker.start()

    def probe(self):
        self.start_worker()

    def search(self):
        if not Path(self.directory.text()).is_dir():
            QMessageBox.warning(
                self, "Directory required", "Choose an existing local synchronized directory."
            )
            return
        self.sync_fields()
        self.start_worker(
            (
                self.project.search_directory,
                self.project.extensions,
                self.project.filename_filter,
                self.preferences.result_limit,
            )
        )

    def search_done(self, result):
        if result is None:
            self.statusBar().showMessage("Everything connection is available.")
            return
        added = self.project.refresh(result.paths)
        self.model.replace(self.project.documents)
        self.modified()
        suffix = (
            " Limit reached; narrow your filters or increase the limit."
            if result.limit_reached
            else ""
        )
        self.count.setText(
            f"{len(result.paths)} matching files returned, {added} new. "
            f"{len(self.project.documents)} catalog entries (previous entries retained).{suffix}"
        )
        self.statusBar().showMessage(
            "No matching files. Try other filters. Previous catalog entries retained."
            if not result.paths
            else "Search complete. Edit titles and descriptions in the table."
        )

    def search_failed(self, message):
        self.statusBar().showMessage(message)
        QMessageBox.warning(self, "Everything search", message)

    def update_mappings(self):
        self.mapping_combo.clear()
        self.mapping_combo.addItems([m.local_root for m in self.project.mappings])
        self.mapping_status()

    def mapping_status(self, *_):
        row = self.mapping_combo.currentIndex()
        if row < 0:
            self.mapping_label.setText(
                "No mappings configured. Export requires a confirmed sample."
            )
        else:
            confirmed = mapping_confirmed(self.project.mappings[row])
            self.mapping_label.setText(
                "Sample manually confirmed. Other links remain unreviewed."
                if confirmed
                else "Sample confirmation required before export."
            )

    def configure_mappings(self):
        dialog = MappingDialog(self.project.mappings, self)
        if dialog.exec():
            self.project.mappings = dialog.mappings
            self.project.refresh([])
            self.model.replace(self.project.documents)
            self.update_mappings()
            self.modified()

    def test_mapping(self):
        row = self.mapping_combo.currentIndex()
        if row < 0:
            self.configure_mappings()
            return
        if MappingTestDialog(self.project.mappings[row], self).exec():
            self.mapping_status()
            self.modified()

    def current_document(self):
        index = self.table.currentIndex()
        return (
            self.project.documents[self.proxy.mapToSource(index).row()] if index.isValid() else None
        )

    def table_click(self, index):
        if index.column() == 7:
            self.open_link()

    def open_link(self):
        document = self.current_document()
        if document and document.sharepoint_url:
            if not QDesktopServices.openUrl(QUrl(document.sharepoint_url)):
                QMessageBox.warning(self, "Browser unavailable", "Could not open the browser.")

    def context_menu(self, position):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        self.table.setCurrentIndex(index)
        document = self.current_document()
        menu = QMenu(self)
        open_action = menu.addAction("Open SharePoint link", self.open_link)
        copy_action = menu.addAction(
            "Copy SharePoint URL", lambda: QApplication.clipboard().setText(document.sharepoint_url)
        )
        review_action = menu.addAction("Mark link as manually reviewed", self.mark_reviewed)
        for action in (open_action, copy_action, review_action):
            action.setEnabled(bool(document.sharepoint_url))
        menu.addAction(
            "Exclude document" if document.included else "Include document", self.toggle_include
        )
        menu.exec(self.table.viewport().mapToGlobal(position))

    def mark_reviewed(self):
        document = self.current_document()
        if (
            document
            and document.sharepoint_url
            and QMessageBox.question(
                self,
                "Confirm individual review",
                "Have you opened this link and confirmed the correct document?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            document.link_status = LinkStatus.REVIEWED
            self.model.replace(self.project.documents)
            self.modified()

    def toggle_include(self):
        document = self.current_document()
        if document:
            document.included = not document.included
            self.model.replace(self.project.documents)
            self.modified()

    def select_all(self, included):
        # Inclusion applies to visible rows; export always uses all included catalog entries.
        for row in range(self.proxy.rowCount()):
            source = self.proxy.mapToSource(self.proxy.index(row, 0))
            self.project.documents[source.row()].included = included
        self.model.replace(self.project.documents)
        self.modified()
        self.statusBar().showMessage(
            "Updated visible rows. Exports include all checked catalog entries, even hidden rows."
        )

    def copy_confluence(self):
        self.commit_editor()
        try:
            mime = QMimeData()
            mime.setHtml(exporter.html_table(self.project))
            mime.setText(exporter.plain_text(self.project))
            QApplication.clipboard().setMimeData(mime)
            self.statusBar().showMessage(
                "HTML table and plain text copied. Paste into a Confluence rich-text editor."
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot export", str(exc))

    def export(self, kind):
        self.commit_editor()
        try:
            text = (
                exporter.csv_text(self.project)
                if kind == "csv"
                else exporter.html_document(self.project)
            )
            path, _ = QFileDialog.getSaveFileName(
                self, "Export selected documents", f"catalog.{kind}", f"{kind.upper()} (*.{kind})"
            )
            if path:
                atomic_write(Path(path), text, "utf-8-sig" if kind == "csv" else "utf-8")
                self.statusBar().showMessage("Selected documents exported.")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def save(self):
        self.commit_editor()
        self.sync_fields()
        path = self.project_path
        if path is None:
            value, _ = QFileDialog.getSaveFileName(
                self,
                "Save catalog project",
                "catalog.sharecatalog.json",
                "ShareCatalog (*.sharecatalog.json)",
            )
            if not value:
                return False
            path = Path(value)
        try:
            save_project(path, self.project)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Save failed", str(exc))
            return False
        self.project_path = path
        self.dirty = False
        self.update_title()
        self.statusBar().showMessage("Project saved.")
        return True

    def commit_editor(self):
        focus = self.table.focusWidget()
        if focus is not None and self.table.isAncestorOf(focus):
            self.table.commitData(focus)
            self.table.closeEditor(focus, QAbstractItemDelegate.EndEditHint.NoHint)

    def may_discard(self):
        if not self.dirty:
            return True
        answer = QMessageBox.warning(
            self,
            "Unsaved changes",
            "Save your changes before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        return answer == QMessageBox.StandardButton.Discard or (
            answer == QMessageBox.StandardButton.Save and self.save()
        )

    def open_project(self):
        if not self.may_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open catalog project", "", "ShareCatalog (*.sharecatalog.json);;JSON (*.json)"
        )
        if not path:
            return
        try:
            project = load_project(Path(path))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Open failed", str(exc))
            return
        self.project, self.project_path = project, Path(path)
        self.directory.setText(project.search_directory)
        self.extensions.setText(project.extensions)
        self.filename.setText(project.filename_filter)
        self.model.replace(project.documents)
        self.update_mappings()
        self.count.setText(
            f"{len(project.documents)} catalog entries loaded. Review links before relying on them."
        )
        self.dirty = False
        self.update_title()

    def save_preferences(self):
        try:
            self.preferences.save(self.preferences_path)
        except OSError:
            QMessageBox.warning(
                self,
                "Preferences",
                "Could not save preferences to your application configuration directory.",
            )

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(
                self,
                "Search running",
                "Wait for the current operation to finish before closing (up to 30 seconds).",
            )
            event.ignore()
            return
        if not self.may_discard():
            event.ignore()
            return
        self.preferences.width, self.preferences.height = self.width(), self.height()
        self.save_preferences()
        event.accept()
