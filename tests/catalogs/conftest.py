import importlib.util
import json
from typing import TYPE_CHECKING

import pytest

from design.catalogs.declaration import DEFAULT

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import ModuleType

SOURCE_LANGUAGE = DEFAULT.source.value


def header(language: str) -> str:
    return f'msgid ""\nmsgstr ""\n"Language: {language}\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n'


@pytest.fixture
def block() -> Callable[..., str]:
    """One catalog entry as gettext writes it; `context=None` leaves the msgctxt out."""

    def build(context: str | None, text: str, translation: str = "", *, fuzzy: bool = False) -> str:
        return (
            ("#, fuzzy\n" if fuzzy else "")
            + (f'msgctxt "{context}"\n' if context is not None else "")
            + f'msgid "{text}"\nmsgstr "{translation}"\n'
        )

    return build


@pytest.fixture
def catalog_text() -> Callable[..., str]:
    return lambda *blocks, language=SOURCE_LANGUAGE: "\n".join((header(language), *blocks))


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An app repository the command runs in."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def source_path(project: Path) -> Path:
    return project / DEFAULT.catalogs / f"{SOURCE_LANGUAGE}.po"


@pytest.fixture
def declare(project: Path) -> Callable[..., None]:
    """Writes the app's root pyproject.toml with a `[tool.design-catalogs]` table of the given keys."""

    def write(**table: str) -> None:
        lines = ["[tool.design-catalogs]", *(f"{key} = {json.dumps(value)}" for key, value in table.items())]
        (project / "pyproject.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return write


@pytest.fixture
def import_module() -> Callable[[Path], ModuleType]:
    """Imports a Python file the way an app does."""

    def load(path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load


@pytest.fixture
def write_catalog(project: Path) -> Callable[[str, str | bytes], Path]:
    """Writes the catalog file of one language, the source's or a translation's."""

    def write(language: str, content: str | bytes) -> Path:
        path = project / DEFAULT.catalogs / f"{language}.po"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    return write


@pytest.fixture
def write_source(write_catalog: Callable[[str, str | bytes], Path]) -> Callable[[str | bytes], Path]:
    return lambda content: write_catalog(SOURCE_LANGUAGE, content)


@pytest.fixture
def module_for(project: Path) -> Callable[[str], Path]:
    return lambda language: project / DEFAULT.typescript / f"{language}.ts"
