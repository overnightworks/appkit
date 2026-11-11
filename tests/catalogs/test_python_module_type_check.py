import json
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def diagnostics(tmp_path):
    """The pyright strict findings of the files written to a temporary directory, as `rule: message` lines."""

    def check(**files: str) -> list[str]:
        for name, content in files.items():
            (tmp_path / f"{name}.py").write_text(content, encoding="utf-8")
        (tmp_path / "pyrightconfig.json").write_text(
            json.dumps({"typeCheckingMode": "strict", "pythonVersion": "3.14"}), encoding="utf-8"
        )
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


@pytest.fixture
def scenario():
    """The catalogs of a kind of catalog and a caller of the module generated from them."""

    def build(kind: str) -> tuple[tuple[tuple[str, dict[str, str]], ...], str]:
        plain = {"app_name": "Skat"}
        gaps = {"chat_greeting": "Hallo {name}"}
        families = {"table_seats_one": "{count} Platz", "table_seats_other": "{count} Plätze"}
        polish_families = {
            "table_seats_one": "{count} miejsce",
            "table_seats_few": "{count} miejsca",
            "table_seats_many": "{count} miejsc",
            "table_seats_other": "{count} miejsca",
        }
        text_import = "from words import text\n\n"
        return {
            "plain texts only": ((("de", plain),), text_import + 'sentence = text("de", "app.name")'),
            "gaps only": ((("de", gaps),), text_import + 'sentence = text("de", "chat.greeting", name="Eva")'),
            "plural families only": (
                (("de", families),),
                text_import + 'sentence = text("de", "table.seats", count=3)',
            ),
            "mixed": (
                (("de", plain | gaps | families), ("pl", plain | gaps | polish_families)),
                text_import + 'sentence = text("pl", "table.seats", count=3) + text("de", "chat.greeting", name="Eva")',
            ),
            "empty": (
                (("de", {}),),
                "from words import SOURCE_LANGUAGE, WORDS\n\nwords = WORDS[SOURCE_LANGUAGE]",
            ),
        }[kind]

    return build


@pytest.mark.parametrize("kind", ["plain texts only", "gaps only", "plural families only", "mixed", "empty"])
def test_a_generated_module_and_its_caller_pass_pyright_strict(diagnostics, module_text, scenario, kind):
    catalogs, caller = scenario(kind)

    assert diagnostics(words=module_text(*catalogs), caller=caller) == []
