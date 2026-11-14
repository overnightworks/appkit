# ruff: noqa: T201 - the command line's one output owner; it prints what it wrote
"""Generates ``src/lib/turn-outcome.ts`` from agents' pinned release.

agents owns the closed set of stop outcomes. This script reads the one member
``agents/agents-vocabulary.json`` from the release wheel that ``agents_vocabulary_pin.toml`` pins by
url and sha256, and writes the committed ``TurnOutcome`` type. With ``--pin <url> <sha256>`` it first
fetches that release and, once the digest holds, raises the pin. The output is deterministic, so CI
regenerates it and requires an empty diff.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tomllib
import urllib.request
import zipfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, TYPE_CHECKING, Final, Protocol, cast

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

ROOT: Final = Path(__file__).resolve().parent.parent
PIN_PATH: Final = Path("scripts/agents_vocabulary_pin.toml")
MODULE_PATH: Final = Path("src/lib/turn-outcome.ts")
VOCABULARY_MEMBER: Final = "agents/agents-vocabulary.json"
SUPPORTED_VERSION: Final = 1
_URL: Final = re.compile(r"^https://[\x21\x23-\x5b\x5d-\x7e]+$")
_SHA256: Final = re.compile(r"^[0-9a-f]{64}$")
_PIN_COMMENT: Final = (
    "# The agents release whose vocabulary design generates TurnOutcome from. Raise it with\n"
    "# `uv run python scripts/generate_turn_outcome.py --pin <url> <sha256>`.\n"
)
_TOKEN: Final = re.compile(r"^[a-z][a-z0-9_]*$")
_FETCH_SECONDS: Final = 60

type Fetch = Callable[[str], bytes]


class UrlOpener(Protocol):
    def __call__(self, url: str, *, timeout: float) -> AbstractContextManager[IO[bytes]]: ...


class VocabularyError(Exception):
    """The pin, the wheel or the vocabulary is not what this script reads."""


@dataclass(frozen=True)
class Pin:
    url: str
    sha256: str


def fetch(url: str, *, open_url: UrlOpener = urllib.request.urlopen) -> bytes:
    with open_url(url, timeout=_FETCH_SECONDS) as response:
        return response.read()


def read_pin(path: Path) -> Pin:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise VocabularyError(f"the pin file {path} is missing") from error
    document = tomllib.loads(text)
    url, sha256 = document.get("url"), document.get("sha256")
    if not isinstance(url, str) or not isinstance(sha256, str):
        raise VocabularyError(f"the pin file {path} must hold a url and a sha256 string")
    return Pin(url, sha256)


def validate_pin(pin: Pin) -> None:
    if not _URL.fullmatch(pin.url):
        raise VocabularyError(f"the release url must be an https address, not {pin.url!r}")
    if not _SHA256.fullmatch(pin.sha256):
        raise VocabularyError("the sha256 must be 64 lowercase hex digits")


def write_pin(path: Path, pin: Pin) -> None:
    pin_text = f"url = {json.dumps(pin.url)}\nsha256 = {json.dumps(pin.sha256)}\n"
    path.write_text(_PIN_COMMENT + pin_text, encoding="utf-8")


def check_digest(wheel: bytes, sha256: str) -> None:
    if hashlib.sha256(wheel).hexdigest() != sha256:
        raise VocabularyError("the wheel does not match the pinned sha256")


def vocabulary_bytes(wheel: bytes) -> bytes:
    """The vocabulary file, read in memory from the wheel without extracting it."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(wheel))
    except zipfile.BadZipFile as error:
        raise VocabularyError("the wheel is no zip archive") from error
    with archive:
        try:
            return archive.read(VOCABULARY_MEMBER)
        except KeyError as error:
            raise VocabularyError(f"the wheel holds no {VOCABULARY_MEMBER}") from error


def parse_stop_outcomes(raw: bytes) -> tuple[str, ...]:
    """Reads ``version`` and ``stop_outcomes`` only; every other key is ignored."""
    try:
        document: object = json.loads(raw)
    except ValueError as error:
        raise VocabularyError("the vocabulary is no JSON") from error
    if not isinstance(document, dict):
        raise VocabularyError("the vocabulary must be a JSON object")
    fields = cast("dict[str, object]", document)
    version = fields.get("version")
    if type(version) is not int or version != SUPPORTED_VERSION:
        raise VocabularyError(f"the vocabulary version must be {SUPPORTED_VERSION}")
    values = fields.get("stop_outcomes")
    if not isinstance(values, list) or not values:
        raise VocabularyError("the vocabulary needs a non-empty list 'stop_outcomes'")
    tokens: list[str] = []
    for value in cast("list[object]", values):
        if not isinstance(value, str) or not _TOKEN.fullmatch(value):
            raise VocabularyError(f"'stop_outcomes' holds {value!r}, which is no token like 'busy'")
        if value in tokens:
            raise VocabularyError(f"'stop_outcomes' holds {value!r} twice")
        tokens.append(value)
    return tuple(tokens)


def render(pin: Pin, outcomes: tuple[str, ...]) -> str:
    union = " | ".join(f"'{token}'" for token in outcomes)
    return (
        "// Generated by scripts/generate_turn_outcome.py; do not edit.\n"
        f"// agents release: {pin.url}\n"
        f"// sha256: {pin.sha256}\n"
        "\n"
        "/**\n"
        " * Why an agent's turns at a place do not answer, as the agents service states it (`StopOutcome`); apps\n"
        " * pass the stated value unchanged.\n"
        " */\n"
        f"export type TurnOutcome = {union};\n"
    )


def generate(root: Path, pin: Pin, wheel: bytes) -> None:
    check_digest(wheel, pin.sha256)
    outcomes = parse_stop_outcomes(vocabulary_bytes(wheel))
    (root / MODULE_PATH).write_text(render(pin, outcomes), encoding="utf-8")


def main(argv: Sequence[str], *, root: Path = ROOT, download: Fetch = fetch) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pin",
        nargs=2,
        metavar=("URL", "SHA256"),
        help="raise the pin to this release, once its sha256 holds",
    )
    arguments = parser.parse_args(argv)
    try:
        pin = Pin(*arguments.pin) if arguments.pin else read_pin(root / PIN_PATH)
        validate_pin(pin)
        generate(root, pin, download(pin.url))
    except VocabularyError as error:
        print(f"error: {error}")
        return 1
    if arguments.pin:
        write_pin(root / PIN_PATH, pin)
    print(f"wrote {MODULE_PATH} from {pin.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
