"""Where an app keeps its catalogs and generated modules: the one optional table of its root pyproject.toml."""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from design.catalogs.catalog import LanguageTag

if TYPE_CHECKING:
    from collections.abc import Mapping

TABLE = "tool.design-catalogs"
PYPROJECT = "pyproject.toml"
KEYS = ("source", "catalogs", "typescript", "python")


class DeclarationError(Exception):
    """The declaration is malformed; the message is one sentence naming the table and the key."""


@dataclass(frozen=True)
class Declaration:
    """The source language and the paths, relative to the repository root, the command works with."""

    source: LanguageTag
    catalogs: Path
    typescript: Path
    python: Path | None


DEFAULT = Declaration(
    source=LanguageTag("de"),
    catalogs=Path("frontend/src/lib/catalogs"),
    typescript=Path("frontend/src/lib/words"),
    python=None,
)


def _string(table: Mapping[str, object], key: str) -> str | None:
    value = table.get(key)
    if value is not None and not isinstance(value, str):
        raise DeclarationError(f"{TABLE} {key} must be a string")
    return value


def _path(table: Mapping[str, object], key: str) -> Path | None:
    value = _string(table, key)
    if value is None:
        return None
    path = Path(os.path.normpath(value))
    if path.is_absolute() or not path.parts or path.parts[0] == "..":
        raise DeclarationError(f"{TABLE} {key} must be a path inside the repository, not {value!r}")
    return path


def _source(table: Mapping[str, object]) -> LanguageTag:
    value = _string(table, "source")
    if value is None:
        return DEFAULT.source
    try:
        return LanguageTag(value)
    except ValueError as error:
        raise DeclarationError(f"{TABLE} source: {error}") from error


def declaration_from(pyproject: Mapping[str, object]) -> Declaration:
    """The declaration of a parsed pyproject.toml: its table over the defaults."""
    tool = pyproject.get("tool")
    table = tool.get("design-catalogs", {}) if isinstance(tool, dict) else {}
    if not isinstance(table, dict):
        raise DeclarationError(f"{TABLE} must be a table")
    if unknown := sorted(set(table) - set(KEYS)):
        raise DeclarationError(f"{TABLE} has the unknown key {unknown[0]!r}; its keys are {', '.join(KEYS)}")
    return Declaration(
        source=_source(table),
        catalogs=_path(table, "catalogs") or DEFAULT.catalogs,
        typescript=_path(table, "typescript") or DEFAULT.typescript,
        python=_path(table, "python"),
    )


def read_declaration(root: Path) -> Declaration:
    """The declaration of the pyproject.toml in `root`; the default where there is none."""
    path = root / PYPROJECT
    if not path.is_file():
        return DEFAULT
    try:
        return declaration_from(tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError as error:
        raise DeclarationError(f"{path} is not valid TOML: {error}") from error
