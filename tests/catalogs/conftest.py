from typing import TYPE_CHECKING

import pytest

from design.catalogs.command import CATALOGS, SOURCE_LANGUAGE

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

HEADER = 'msgid ""\nmsgstr ""\n"Language: de\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n'


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
    return lambda *blocks: "\n".join((HEADER, *blocks))


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An app repository the command runs in."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def source_path(project: Path) -> Path:
    return project / CATALOGS / f"{SOURCE_LANGUAGE}.po"


@pytest.fixture
def write_source(source_path: Path) -> Callable[[str], Path]:
    def write(content: str) -> Path:
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(content, encoding="utf-8")
        return source_path

    return write
