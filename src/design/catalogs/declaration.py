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
    declaration = Declaration(
        source=_source(table),
        catalogs=_path(table, "catalogs") or DEFAULT.catalogs,
        typescript=_path(table, "typescript") or DEFAULT.typescript,
        python=_path(table, "python"),
    )
    if declaration.python is not None:
        if declaration.python == Path(PYPROJECT):
            raise DeclarationError(f"{TABLE} python must not be {PYPROJECT}, the file that holds the declaration")
        for key, directory in (("catalogs", declaration.catalogs), ("typescript", declaration.typescript)):
            if declaration.python.is_relative_to(directory):
                raise DeclarationError(f"{TABLE} python must lie outside the {key} directory {str(directory)!r}")
    return declaration


def _filesystem_problem(root: Path, path: Path, *, file: bool) -> str | None:
    """Why a path inside `root` cannot hold a file (or a directory): a file on the way or a thing of the wrong kind."""
    if blocking := next((parent for parent in path.parents if (root / parent).is_file()), None):
        return f"{blocking.as_posix()!r} is a file, so nothing can lie below it"
    if file and (root / path).is_dir():
        return f"{path.as_posix()!r} is a directory, not a file"
    if not file and (root / path).is_file():
        return f"{path.as_posix()!r} is a file, not a directory"
    return None


def _check_filesystem(root: Path, declaration: Declaration) -> None:
    for key, path, file in (
        ("catalogs", declaration.catalogs, False),
        ("typescript", declaration.typescript, False),
        ("python", declaration.python, True),
    ):
        if path is not None and (problem := _filesystem_problem(root, path, file=file)):
            raise DeclarationError(f"{TABLE} {key}: {problem}")


def read_declaration(root: Path) -> Declaration:
    """The declaration of the pyproject.toml in `root`; the default where there is none."""
    path = root / PYPROJECT
    if not path.is_file():
        return DEFAULT
    try:
        declaration = declaration_from(tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError as error:
        raise DeclarationError(f"{path} is not valid TOML: {error}") from error
    _check_filesystem(root, declaration)
    return declaration
