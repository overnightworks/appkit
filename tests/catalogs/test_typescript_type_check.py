import subprocess
from pathlib import Path

import pytest

from design.catalogs.catalog import Entry, Key, LanguageTag, SourceCatalog
from design.catalogs.typescript import render

REPOSITORY = Path(__file__).resolve().parent.parent.parent
CATALOG = SourceCatalog(
    language=LanguageTag("de"),
    entries=(Entry(key=Key("table.seatFree"), text="Frei"), Entry(key=Key("app.name"), text="Skat")),
)


def type_check(directory: Path, probe: str) -> subprocess.CompletedProcess[str]:
    (directory / "de.ts").write_text(render(CATALOG), encoding="utf-8")
    (directory / "consumer.ts").write_text(probe, encoding="utf-8")
    return subprocess.run(
        [
            "pnpm",
            "exec",
            "tsc",
            "--noEmit",
            "--strict",
            "--ignoreConfig",
            "--target",
            "ES2022",
            "--module",
            "ESNext",
            "--moduleResolution",
            "bundler",
            "--skipLibCheck",
            str(directory / "consumer.ts"),
        ],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_consumer_using_catalog_keys_passes_tsc_strict(tmp_path):
    probe = (
        'import { words, type Key } from "./de";\n'
        'const key: Key = "table.seatFree";\n'
        'export const text: string = words[key] + words["app.name"];\n'
    )

    result = type_check(tmp_path, probe)

    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    "probe",
    [
        pytest.param('import type { Key } from "./de";\nexport const key: Key = "table.nope";\n', id="key type"),
        pytest.param('import { words } from "./de";\nexport const text = words["table.nope"];\n', id="lookup"),
    ],
)
def test_a_consumer_using_a_wrong_key_fails_tsc_strict(tmp_path, probe):
    result = type_check(tmp_path, probe)

    assert result.returncode != 0
    assert "table.nope" in result.stdout
