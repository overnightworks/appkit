import importlib.util
import json
import subprocess
from typing import TYPE_CHECKING

import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog, TranslationCatalog
from design.catalogs.declaration import DEFAULT
from design.catalogs.po_file import plural_rule
from design.catalogs.python_module import render

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import ModuleType

SOURCE_LANGUAGE = DEFAULT.source.value


def header(language: str) -> str:
    return f'msgid ""\nmsgstr ""\n"Language: {language}\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n'


@pytest.fixture
def catalog():
    """A catalog of the given kind, from a language and its `surface_name: text` pairs."""

    def build(kind, language, texts):
        return kind(
            language=LanguageTag(language),
            entries=tuple(Entry(key=Key(key.replace("_", ".")), text=text) for key, text in texts.items()),
        )

    return build


@pytest.fixture
def module_text(catalog):
    """The module of a source and its translations, each given as a language and its `surface_name: text` pairs."""

    def build(source, *translations):
        return render(
            catalog(SourceCatalog, *source),
            tuple(catalog(TranslationCatalog, *translation) for translation in translations),
            plural_rule,
        )

    return build


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


@pytest.fixture
def evaluate(tmp_path: Path) -> Callable[[dict[str, str], str], object]:
    """Writes generated modules by file name, runs the probe (a module body that prints one JSON value) in Node
    and returns that value."""

    def run(modules: dict[str, str], probe: str) -> object:
        for name, module in modules.items():
            (tmp_path / name).write_text(module, encoding="utf-8")
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", probe],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    return run
