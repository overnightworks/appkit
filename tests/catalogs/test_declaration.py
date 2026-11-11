from pathlib import Path

import pytest

from design.catalogs.catalog import LanguageTag
from design.catalogs.declaration import DEFAULT, Declaration, DeclarationError, declaration_from, read_declaration


def declared(**table: object) -> Declaration:
    return declaration_from({"tool": {"design-catalogs": table}})


def test_declaration_without_the_table_is_the_default():
    assert declaration_from({"project": {"name": "skat"}}) == DEFAULT
    assert declaration_from({}) == DEFAULT
    assert declaration_from({"tool": {"ruff": {}}}) == DEFAULT
    assert declaration_from({"tool": "ruff"}) == DEFAULT


def test_default_declares_no_python_module():
    assert DEFAULT.python is None


def test_declaration_takes_every_key_from_the_table_and_the_rest_from_the_default():
    declaration = declared(source="en", python="src/app/words.py")

    assert declaration == Declaration(
        source=LanguageTag("en"),
        catalogs=DEFAULT.catalogs,
        typescript=DEFAULT.typescript,
        python=Path("src/app/words.py"),
    )
    assert declared(catalogs="locales", typescript="web/words").catalogs == Path("locales")
    assert declared(catalogs="locales", typescript="web/words").typescript == Path("web/words")


@pytest.mark.parametrize(
    ("value", "path"), [("frontend/../src/words", "src/words"), ("./words", "words"), ("words/", "words")]
)
def test_declaration_reads_a_path_inside_the_repository_in_its_normal_form(value, path):
    assert declared(typescript=value).typescript == Path(path)


@pytest.mark.parametrize(
    ("table", "named"),
    [
        pytest.param({"sources": "de"}, "sources", id="unknown key"),
        pytest.param({"source": 1}, "source", id="source of the wrong type"),
        pytest.param({"catalogs": ["a"]}, "catalogs", id="catalogs of the wrong type"),
        pytest.param({"typescript": True}, "typescript", id="typescript of the wrong type"),
        pytest.param({"python": 3.5}, "python", id="python of the wrong type"),
        pytest.param({"source": "DE"}, "source", id="source that is no language tag"),
        pytest.param({"catalogs": "/etc/catalogs"}, "catalogs", id="absolute path"),
        pytest.param({"typescript": "../words"}, "typescript", id="path above the repository"),
        pytest.param({"typescript": "a/../../words"}, "typescript", id="path leaving the repository by a detour"),
        pytest.param({"python": ""}, "python", id="empty path"),
        pytest.param({"python": "."}, "python", id="the repository itself"),
        pytest.param({"python": "pyproject.toml"}, "python", id="the declaration's own file"),
        pytest.param({"python": "./pyproject.toml"}, "python", id="the declaration's own file by a detour"),
        pytest.param({"python": "frontend/src/lib/catalogs/de.po"}, "python", id="python in the catalogs directory"),
        pytest.param(
            {"catalogs": "locales", "python": "locales/words.py"},
            "python",
            id="python in a declared catalogs directory",
        ),
    ],
)
def test_declaration_fails_in_one_sentence_naming_the_table_and_the_key(table, named):
    with pytest.raises(DeclarationError) as error:
        declared(**table)

    message = str(error.value)
    assert "tool.design-catalogs" in message
    assert named in message
    assert "\n" not in message


def test_declaration_fails_naming_the_table_when_it_is_no_table():
    with pytest.raises(DeclarationError, match=r"tool\.design-catalogs must be a table"):
        declaration_from({"tool": {"design-catalogs": "words"}})


def test_read_declaration_reads_the_table_of_the_root_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[tool.design-catalogs]\nsource = "en"\n', encoding="utf-8")

    assert read_declaration(tmp_path).source == LanguageTag("en")


def test_read_declaration_without_a_pyproject_is_the_default(tmp_path):
    assert read_declaration(tmp_path) == DEFAULT


def test_read_declaration_fails_naming_a_pyproject_that_is_no_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool\n", encoding="utf-8")

    with pytest.raises(DeclarationError, match=r"pyproject\.toml"):
        read_declaration(tmp_path)


@pytest.mark.parametrize(
    ("table", "existing_file", "existing_directory", "named"),
    [
        pytest.param({"python": "src"}, None, "src", "python", id="python that is a directory"),
        pytest.param({"python": "src/app/words.py"}, "src", None, "python", id="python whose parent is a file"),
        pytest.param({"catalogs": "locales"}, "locales", None, "catalogs", id="catalogs that is a file"),
        pytest.param({"typescript": "web/words"}, "web", None, "typescript", id="typescript below a file"),
    ],
)
def test_read_declaration_fails_in_one_sentence_naming_the_table_and_the_key_of_a_path_the_filesystem_refuses(
    tmp_path, table, existing_file, existing_directory, named
):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.design-catalogs]\n" + "".join(f'{key} = "{value}"\n' for key, value in table.items()), encoding="utf-8"
    )
    if existing_file:
        (tmp_path / existing_file).write_text("", encoding="utf-8")
    if existing_directory:
        (tmp_path / existing_directory).mkdir()

    with pytest.raises(DeclarationError) as error:
        read_declaration(tmp_path)

    message = str(error.value)
    assert f"tool.design-catalogs {named}" in message
    assert "\n" not in message


def test_read_declaration_takes_declared_paths_that_do_not_exist_yet(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[tool.design-catalogs]\npython = "src/app/words.py"\n', encoding="utf-8")

    assert read_declaration(tmp_path).python == Path("src/app/words.py")
