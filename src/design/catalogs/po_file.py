"""The only reader of catalog files: a path becomes raw entries."""

from typing import TYPE_CHECKING

from babel.messages.catalog import Catalog, Message
from babel.messages.pofile import PoFileParser

from design.catalogs.catalog import RawEntry

if TYPE_CHECKING:
    from pathlib import Path


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


def read_entries(path: Path) -> tuple[RawEntry, ...]:
    catalog = _EveryEntry()
    with path.open("rb") as file:
        PoFileParser(catalog, ignore_obsolete=True).parse(file)
    return tuple(
        RawEntry(message.context, str(message.id), str(message.string), message.fuzzy)
        for message in catalog.entries
        if message.context is not None or message.id
    )
