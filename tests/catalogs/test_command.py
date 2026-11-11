import pytest

from design.catalogs.command import MODULES, SOURCE_LANGUAGE, main


@pytest.fixture
def module_path(project):
    return project / MODULES / f"{SOURCE_LANGUAGE}.ts"


@pytest.fixture
def clean_source(write_source, catalog_text, block):
    return write_source(catalog_text(block("table.seatFree", "Frei"), block("app.name", "Skat")))


def test_main_writes_the_typed_source_module_from_the_source_catalog(clean_source, module_path):
    assert main([]) == 0

    written = module_path.read_text(encoding="utf-8")
    assert 'export const language = "de";' in written
    assert '    "table.seatFree": "Frei",' in written


def test_main_run_again_gives_the_same_bytes(clean_source, module_path):
    main([])
    first = module_path.read_bytes()

    assert main([]) == 0
    assert module_path.read_bytes() == first


def test_main_check_passes_on_a_current_module_and_writes_nothing(clean_source, module_path):
    main([])
    before = module_path.stat().st_mtime_ns

    assert main(["--check"]) == 0
    assert module_path.stat().st_mtime_ns == before


@pytest.mark.parametrize("content", [None, "// edited by hand\n"], ids=["missing", "differing"])
def test_main_check_fails_naming_a_missing_or_differing_module_and_writes_nothing(
    clean_source, module_path, capsys, content
):
    if content is not None:
        module_path.parent.mkdir(parents=True)
        module_path.write_text(content, encoding="utf-8")

    assert main(["--check"]) == 1

    assert module_path.name in capsys.readouterr().err
    assert (module_path.read_text(encoding="utf-8") if module_path.exists() else None) == content


@pytest.mark.parametrize("arguments", [[], ["--check"]])
@pytest.mark.parametrize(
    ("entries", "key"),
    [
        pytest.param([(None, "Schlicht")], "Schlicht", id="no msgctxt"),
        pytest.param([("seat_free", "Frei")], "seat_free", id="bad key"),
        pytest.param([("table.seatFree", "Frei", "Free")], "table.seatFree", id="non-empty msgstr"),
        pytest.param([("table.seatFree", "Frei"), ("table.seatFree", "Platz")], "table.seatFree", id="duplicate"),
    ],
)
def test_main_fails_naming_file_and_key_of_a_broken_entry_and_writes_nothing(
    write_source, catalog_text, block, module_path, capsys, arguments, entries, key
):
    write_source(catalog_text(*(block(*entry) for entry in entries)))

    assert main(arguments) == 1

    error = capsys.readouterr().err
    assert "de.po" in error
    assert key in error
    assert not module_path.exists()


def test_main_fails_naming_the_source_catalog_when_it_is_missing(project, source_path, capsys):
    assert main([]) == 1

    assert "de.po" in capsys.readouterr().err


@pytest.mark.parametrize("arguments", [[], ["--check"]])
@pytest.mark.parametrize(
    ("damage", "line"),
    [
        pytest.param('msgctxt "app.name"\nmsgid "Skat\nmsgstr ""\n', 11, id="unterminated msgid"),
        pytest.param('msgctxt "app.name"\nmsgid "Skat"\nmsgstr ""\nthis is garbage\n', 13, id="garbage line"),
        pytest.param('msgctxt "table.title"\nmsgid "Tisch"\n', 11, id="missing msgstr"),
    ],
)
def test_main_fails_naming_file_and_line_of_a_malformed_catalog_and_writes_nothing(
    write_source, catalog_text, block, module_path, capsys, arguments, damage, line
):
    write_source(catalog_text(block("table.seatFree", "Frei"), damage))

    assert main(arguments) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert f"de.po:{line}" in output.err
    assert not module_path.exists()
