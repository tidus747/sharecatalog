# Third-party notices

The MIT license covers ShareCatalog source, not dependencies. Everything and ES
remain external and are not redistributed.

The documentation site adapts [Terminal Noir](https://github.com/nandomoreirame/terminalnoir-astro-theme)
by Fernando Moreira (MIT). Its original notice is preserved in
`licenses/Terminal-Noir-MIT.txt`. The Noir/Paper palette, global styles, typography
and section component were adapted from upstream commit
`f702aa1a2175f3e8ac4447e1d008c286728a1d0e`. Local font packages Inter, Newsreader
and JetBrains Mono use the SIL Open Font License; their package notices apply.
Astro, Tailwind CSS and their dependency licenses remain separate from the app.

The `licenses/` directory contains unmodified LGPLv3, GPLv3 and GPLv2 texts from
[Qt's official license directory](https://github.com/qt/qtbase/tree/dev/LICENSES).
They are copied into the packaged app alongside installed-package notices.

| Component | License/reference |
| --- | --- |
| Python | [PSF license](https://docs.python.org/3/license.html) |
| PySide6 / Shiboken6 / Qt | [Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html), LGPLv3/GPLv3/commercial depending on component |
| PyInstaller | [GPL with distribution exception](https://pyinstaller.org/en/stable/license.html) |
| Everything / ES | [Everything license](https://www.voidtools.com/License.txt), [ES MIT](https://github.com/voidtools/ES/blob/main/LICENSE) |
| pytest / Ruff | [pytest MIT](https://github.com/pytest-dev/pytest/blob/main/LICENSE), [Ruff MIT](https://github.com/astral-sh/ruff/blob/main/LICENSE) |

For binary redistribution, include this notice, ShareCatalog's MIT license, the
Python license and exact dependency license/copyright notices, including Qt's
third-party code. The build collects installed PySide6/Shiboken license directories
and Python's license when present. Inspect the artifact inventory and add omissions;
automatic collection is not a complete distribution license audit.

The one-directory build dynamically links replaceable Qt libraries. If relying on
LGPLv3, supply required notices and license texts, identify versions/modifications,
provide corresponding source or a compliant source offer for covered libraries,
and preserve users' rights to replace/debug LGPL components, including reverse
engineering for that purpose. Supply installation information where applicable.
Do not impose incompatible end-user restrictions. Modified LGPL components have
additional source obligations. Verify terms for every shipped component.

ShareCatalog uses Core, GUI and Widgets. The build excludes unused WebEngine, PDF,
Network, QML and other major modules where possible. Not every module in a full
PySide6 installation is available under LGPL. A commercial Qt license is another
option. Review upstream terms for your actual distribution before publication.
