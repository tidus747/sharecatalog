from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from sharecatalog.services.preferences import Preferences
from sharecatalog.ui.document_table import DocumentTableModel
from sharecatalog.ui.main_window import MainWindow, SearchWorker
from sharecatalog.ui.mapping_dialog import MappingDialog, MappingTestDialog


def test_table_editability_and_keyboard(app, project):
    model = DocumentTableModel(project.documents)
    for column in (1, 2, 5, 6, 7):
        assert not model.flags(model.index(0, column)) & Qt.ItemFlag.ItemIsEditable
        assert not model.setData(model.index(0, column), "Forbidden")
    assert model.setData(model.index(0, 3), "Edited")
    assert project.documents[0].title == "Edited"
    assert model.setData(model.index(0, 0), Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
    assert not project.documents[0].included


def test_window_and_rich_clipboard(app, project, tmp_path):
    window = MainWindow(Preferences(), tmp_path / "preferences.json")
    window.project = project
    window.model.replace(project.documents)
    window.show()
    app.processEvents()
    assert window.isVisible()
    window.table.setFocus()
    window.table.setCurrentIndex(window.proxy.index(0, 3))
    QTest.keyClick(window.table, Qt.Key.Key_F2)
    QTest.keyClicks(window.table.focusWidget(), "Edited via keyboard")
    QTest.keyClick(window.table.focusWidget(), Qt.Key.Key_Return)
    app.processEvents()
    assert project.documents[0].title == "Edited via keyboard"
    window.copy_confluence()
    mime = app.clipboard().mimeData()
    assert mime.hasHtml() and mime.hasText()
    assert '<a href="https://' in mime.html()
    assert window.dirty
    window.dirty = False
    window.close()
    assert (tmp_path / "preferences.json").exists()


def test_mapping_sample_requires_browser_open(app, mapping):
    dialog = MappingTestDialog(mapping)
    assert not dialog.confirm_button.isEnabled()
    assert not dialog.open_button.isEnabled()
    editor = MappingDialog([mapping])
    editor.list.setCurrentRow(0)
    assert editor.root.text() == mapping.local_root


def test_unsaved_cancel_and_worker(app, tmp_path, monkeypatch):
    window = MainWindow(Preferences(), tmp_path / "preferences.json")
    window.modified()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Cancel)
    assert not window.may_discard()

    class Adapter:
        def probe(self):
            pass

    worker = SearchWorker(Adapter())
    received = []
    worker.result.connect(received.append)
    worker.start()
    assert worker.wait(2000)
    app.processEvents()
    assert received == [None]
    window.dirty = False
    window.close()


def test_save_commits_active_editor(app, project, tmp_path):
    from sharecatalog.services.project_store import load_project

    window = MainWindow(Preferences(), tmp_path / "preferences.json")
    window.project = project
    window.project_path = tmp_path / "catalog.sharecatalog.json"
    window.model.replace(project.documents)
    window.show()
    window.table.setFocus()
    window.table.setCurrentIndex(window.proxy.index(0, 3))
    QTest.keyClick(window.table, Qt.Key.Key_F2)
    QTest.keyClicks(window.table.focusWidget(), "Saved while editing")
    assert window.save()
    assert load_project(window.project_path).documents[0].title == "Saved while editing"
    window.close()


def test_detection_prefills_without_applying_or_confirming(app, mapping, monkeypatch):
    from sharecatalog.models.library import LibraryMapping
    from sharecatalog.services.sharepoint import mapping_confirmed

    candidate = LibraryMapping(mapping.local_root, mapping.library_url)
    calls = []

    def detect(directory):
        calls.append(directory)
        return candidate

    monkeypatch.setattr("sharecatalog.ui.mapping_dialog.discover_mapping", detect)
    dialog = MappingDialog([], search_directory=r"C:\Catalog\Nested")
    dialog.detect()
    assert calls == [r"C:\Catalog\Nested"]
    assert dialog.root.text() == candidate.local_root
    assert dialog.url.text() == candidate.library_url
    assert dialog.mappings == []
    assert dialog.apply()
    assert len(dialog.mappings) == 1
    assert not mapping_confirmed(dialog.mappings[0])


def test_sample_path_uses_text_dialog_instead_of_file_picker(app, mapping, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QInputDialog

    def forbidden(*args, **kwargs):
        raise AssertionError("Native file selection is forbidden in sample validation")

    monkeypatch.setattr(QFileDialog, "getOpenFileName", forbidden)
    monkeypatch.setattr(
        QInputDialog, "getText", lambda *args, **kwargs: (r"C:\Catalog\Guide.pdf", True)
    )
    monkeypatch.setattr("sharecatalog.ui.mapping_dialog.Path.is_file", lambda path: True)
    dialog = MappingTestDialog(mapping)
    dialog.choose()
    assert dialog.url.text().endswith("/Guide.pdf")
    assert dialog.open_button.isEnabled()
    assert not dialog.confirm_button.isEnabled()
