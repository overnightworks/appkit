"""The generator turns agents' pinned release wheel into the TurnOutcome type, or fails loud."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import runpy
import sys
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from types import ModuleType

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "generate_turn_outcome.py"
RELEASE_URL = "https://releases.example/agents-1.0.0-py3-none-any.whl"
OUTCOMES = ["alpha_one", "beta", "gamma_3"]


def load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("generate_turn_outcome", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


generator = load_generator()


def wheel(document: object | None = None, member: str | None = None) -> bytes:
    document = {"version": 1, "stop_outcomes": OUTCOMES} if document is None else document
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(member or generator.VOCABULARY_MEMBER, json.dumps(document))
    return buffer.getvalue()


def digest_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def repository(tmp_path: Path, content: bytes | None) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src" / "lib").mkdir(parents=True)
    if content is not None:
        generator.write_pin(tmp_path / generator.PIN_PATH, generator.Pin(RELEASE_URL, digest_of(content)))
    return tmp_path


def run(root: Path, content: bytes, *argv: str) -> int:
    return generator.main(argv, root=root, download=lambda _url: content)


def test_the_type_names_every_release_token_in_order(tmp_path: Path) -> None:
    release = wheel({"version": 1, "stop_outcomes": OUTCOMES, "unknown": [1]})
    root = repository(tmp_path, release)

    assert run(root, release) == 0

    text = (root / generator.MODULE_PATH).read_text(encoding="utf-8")
    assert "export type TurnOutcome = 'alpha_one' | 'beta' | 'gamma_3';\n" in text
    assert RELEASE_URL in text
    assert digest_of(release) in text


def test_a_second_run_leaves_the_module_as_it_was(tmp_path: Path) -> None:
    release = wheel()
    root = repository(tmp_path, release)
    run(root, release)
    first = (root / generator.MODULE_PATH).read_bytes()

    run(root, release)

    assert (root / generator.MODULE_PATH).read_bytes() == first


@pytest.mark.parametrize(
    "release",
    [
        pytest.param(b"not a zip", id="no-zip"),
        pytest.param(wheel(member="agents/other.json"), id="member-missing"),
        pytest.param(wheel(["x"]), id="not-an-object"),
        pytest.param(wheel({"version": 2, "stop_outcomes": OUTCOMES}), id="other-version"),
        pytest.param(wheel({"version": True, "stop_outcomes": OUTCOMES}), id="boolean-version"),
        pytest.param(wheel({"stop_outcomes": OUTCOMES}), id="version-missing"),
        pytest.param(wheel({"version": 1}), id="outcomes-missing"),
        pytest.param(wheel({"version": 1, "stop_outcomes": []}), id="outcomes-empty"),
        pytest.param(wheel({"version": 1, "stop_outcomes": "busy"}), id="outcomes-not-a-list"),
        pytest.param(wheel({"version": 1, "stop_outcomes": [3]}), id="token-not-a-string"),
        pytest.param(wheel({"version": 1, "stop_outcomes": ["Busy"]}), id="token-malformed"),
        pytest.param(wheel({"version": 1, "stop_outcomes": ["busy", "busy"]}), id="token-twice"),
    ],
)
def test_a_release_the_generator_cannot_read_fails_loud_and_writes_nothing(tmp_path: Path, release: bytes) -> None:
    root = repository(tmp_path, release)

    assert run(root, release) == 1
    assert not (root / generator.MODULE_PATH).exists()


def test_a_vocabulary_that_is_no_json_is_refused(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(generator.VOCABULARY_MEMBER, "{")
    release = buffer.getvalue()
    root = repository(tmp_path, release)

    assert run(root, release) == 1


def test_a_wheel_that_does_not_match_the_pin_is_refused(tmp_path: Path) -> None:
    root = repository(tmp_path, wheel())

    assert run(root, wheel({"version": 1, "stop_outcomes": ["other"]})) == 1
    assert not (root / generator.MODULE_PATH).exists()


@pytest.mark.parametrize(
    "pin_text",
    [
        pytest.param(None, id="missing"),
        pytest.param('url = "https://releases.example/a.whl"\n', id="no-digest"),
        pytest.param('sha256 = "abc"\n', id="no-url"),
    ],
)
def test_a_missing_or_incomplete_pin_file_fails_loud(tmp_path: Path, pin_text: str | None) -> None:
    root = repository(tmp_path, None)
    if pin_text is not None:
        (root / generator.PIN_PATH).write_text(pin_text, encoding="utf-8")

    assert run(root, wheel()) == 1


def test_raising_the_pin_rewrites_the_pin_file_under_its_comment(tmp_path: Path) -> None:
    root = repository(tmp_path, wheel())
    raised = wheel({"version": 1, "stop_outcomes": ["other"]})

    assert run(root, raised, "--pin", RELEASE_URL + "2", digest_of(raised)) == 0

    pin = generator.read_pin(root / generator.PIN_PATH)
    assert pin == generator.Pin(RELEASE_URL + "2", digest_of(raised))
    assert (root / generator.PIN_PATH).read_text(encoding="utf-8").startswith("# ")
    assert "'other'" in (root / generator.MODULE_PATH).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("url", "sha256"),
    [
        pytest.param("http://releases.example/a.whl", "0" * 64, id="url-not-https"),
        pytest.param(RELEASE_URL, "ABC", id="sha256-malformed"),
    ],
)
def test_raising_the_pin_to_a_malformed_url_or_digest_is_refused_and_leaves_the_pin(
    tmp_path: Path, url: str, sha256: str
) -> None:
    release = wheel()
    root = repository(tmp_path, release)
    before = (root / generator.PIN_PATH).read_text(encoding="utf-8")

    assert run(root, release, "--pin", url, sha256) == 1
    assert (root / generator.PIN_PATH).read_text(encoding="utf-8") == before


def test_raising_the_pin_to_a_wheel_that_does_not_match_leaves_the_pin(tmp_path: Path) -> None:
    release = wheel()
    root = repository(tmp_path, release)
    before = (root / generator.PIN_PATH).read_text(encoding="utf-8")

    assert run(root, release, "--pin", RELEASE_URL + "2", "0" * 64) == 1
    assert (root / generator.PIN_PATH).read_text(encoding="utf-8") == before


def test_run_as_a_program_a_bad_pin_exits_one_with_the_error_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--pin", "http://releases.example/a.whl", "x"])

    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(SCRIPT), run_name="__main__")

    assert raised.value.code == 1
    assert capsys.readouterr().out.startswith("error: ")


def test_fetch_returns_the_bytes_the_address_serves() -> None:
    served = wheel()
    asked: list[str] = []

    def open_url(url: str, *, timeout: float) -> AbstractContextManager[io.BytesIO]:
        asked.append(url)
        return io.BytesIO(served)

    assert generator.fetch(RELEASE_URL, open_url=open_url) == served
    assert asked == [RELEASE_URL]
