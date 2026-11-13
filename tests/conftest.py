import gc
import os

import pytest

from sharecatalog.models.library import LibraryMapping
from sharecatalog.models.project import Project
from sharecatalog.services.sharepoint import confirm_mapping, mapped_url

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def mapping():
    return LibraryMapping(
        r"C:\Catalog", "https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents"
    )


@pytest.fixture
def project(mapping):
    sample = r"C:\Catalog\Guide.pdf"
    confirm_mapping(mapping, sample, mapped_url(mapping, sample))
    project = Project(search_directory=r"C:\Catalog", mappings=[mapping])
    project.refresh([sample])
    return project


@pytest.fixture(scope="session")
def app():
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    # Release Qt-owned MIME data while the application still exists.
    application.clipboard().clear()
    application.closeAllWindows()
    for widget in application.topLevelWidgets():
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    application.processEvents()
    gc.collect()
