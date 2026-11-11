"""The only filesystem boundary of the command: catalog files are read here, generated modules read and written."""

import re
from io import BytesIO
from typing import TYPE_CHECKING

from babel.messages.catalog import Catalog, Message
from babel.messages.pofile import PoFileError, PoFileParser

from design.catalogs.catalog import RawEntry

if TYPE_CHECKING:
    from pathlib import Path


STRING_LINE = re.compile(rb'(msg\w+(\[\d+\])?\s+)?"(?:[^"\\]|\\.)*"\s*')


class CatalogFileError(Exception):
    """A catalog file that cannot be read; the message names the file and, when known, the line."""


class _EveryEntry(Catalog):
    """A catalog that keeps every entry in file order.

    Babel's own catalog merges entries with the same msgctxt and msgid, and treats an empty msgid
    as the header, so a duplicate or an empty entry would never reach a check.
    """

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[Message] = []

    def __setitem__(self, id, message: Message) -> None:  # noqa: A002 - Babel's parameter name
        self.entries.append(message)


def _require_closed_strings(path: Path, content: bytes) -> None:
    """Babel cuts the last character off a string whose closing quote is missing, so no error would show."""
    for number, line in enumerate(content.splitlines(), start=1):
        if line.startswith((b"msg", b'"')) and not STRING_LINE.fullmatch(line):
            raise CatalogFileError(f"{path}:{number}: the string is not closed by a quote")


def read_entries(path: Path) -> tuple[RawEntry, ...]:
    catalog = _EveryEntry()
    try:
        content = path.read_bytes()
        _require_closed_strings(path, content)
        PoFileParser(catalog, ignore_obsolete=True, abort_invalid=True).parse(BytesIO(content))
    except FileNotFoundError:
        raise CatalogFileError(f"{path}: the source catalog is missing") from None
    except PoFileError as error:
        problem = error.args[0].removesuffix(f" on {error.lineno}")
        raise CatalogFileError(f"{path}:{error.lineno + 1}: {problem}") from error
    entries = catalog.entries
    if entries and entries[0].context is None and not entries[0].id:
        entries = entries[1:]
    return tuple(RawEntry(message.context, str(message.id), str(message.string), message.fuzzy) for message in entries)


def read_module(path: Path) -> str | None:
    """The text of a generated module, or None when it does not exist."""
    return path.read_text(encoding="utf-8") if path.is_file() else None


def write_module(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
