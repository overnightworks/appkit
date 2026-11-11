import json
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent.parent
STRICT = {"typeCheckingMode": "strict", "pythonVersion": "3.14"}
TEXT_IMPORT = "from words import text\n\n"
PLAIN = {"app_name": "Skat"}
GAPS = {"chat_greeting": "Hallo {name}"}
FAMILIES = {"table_seats_one": "{count} Platz", "table_seats_other": "{count} Plätze"}
POLISH_FAMILIES = {
    "table_seats_one": "{count} miejsce",
    "table_seats_few": "{count} miejsca",
    "table_seats_many": "{count} miejsc",
    "table_seats_other": "{count} miejsca",
}


@pytest.fixture
def diagnostics(tmp_path):
    """The pyright strict findings of the files written to a temporary directory, as `rule: message` lines."""

    def check(**files: str) -> list[str]:
        for name, content in files.items():
            (tmp_path / f"{name}.py").write_text(content, encoding="utf-8")
        (tmp_path / "pyrightconfig.json").write_text(json.dumps(STRICT), encoding="utf-8")
        result = subprocess.run(
            ["pnpm", "exec", "pyright", "--outputjson", "--project", str(tmp_path)],
            cwd=REPOSITORY,
            capture_output=True,
            text=True,
            check=False,
        )
        report = json.loads(result.stdout)
        return [f"{item.get('rule')}: {item['message']}" for item in report["generalDiagnostics"]]

    return check


@pytest.mark.parametrize(
    ("catalogs", "caller"),
    [
        pytest.param((("de", PLAIN),), TEXT_IMPORT + 'sentence = text("de", "app.name")', id="plain texts only"),
        pytest.param(
            (("de", GAPS),), TEXT_IMPORT + 'sentence = text("de", "chat.greeting", name="Eva")', id="gaps only"
        ),
        pytest.param(
            (("de", FAMILIES),),
            TEXT_IMPORT + 'sentence = text("de", "table.seats", count=3)',
            id="plural families only",
        ),
        pytest.param(
            (("de", PLAIN | GAPS | FAMILIES), ("pl", PLAIN | GAPS | POLISH_FAMILIES)),
            TEXT_IMPORT + 'sentence = text("pl", "table.seats", count=3) + text("de", "chat.greeting", name="Eva")',
            id="mixed",
        ),
        pytest.param(
            (("de", {}),), "from words import SOURCE_LANGUAGE, WORDS\n\nwords = WORDS[SOURCE_LANGUAGE]", id="empty"
        ),
    ],
)
def test_a_generated_module_and_its_caller_pass_pyright_strict(diagnostics, module_text, catalogs, caller):
    words = module_text(*catalogs)

    assert diagnostics(words=words, caller=caller) == []
