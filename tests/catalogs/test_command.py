import pytest

from design.catalogs.command import SOURCE_LANGUAGE, main


@pytest.fixture
def module_path(module_for):
    return module_for(SOURCE_LANGUAGE)


@pytest.fixture
def clean_source(write_source, catalog_text, block):
    return write_source(catalog_text(block("table.seatFree", "Frei"), block("app.name", "Skat")))


@pytest.fixture
def clean_translation(clean_source, write_catalog, catalog_text, block):
    """The Polish translation of `clean_source`, current."""
    return write_catalog(
        "pl",
        catalog_text(block("table.seatFree", "Frei", "Wolne"), block("app.name", "Skat", "Skat (pl)"), language="pl"),
    )


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


@pytest.mark.parametrize("language", [SOURCE_LANGUAGE, "pl"])
@pytest.mark.parametrize(
    ("content", "sentence"),
    [(None, "the module is missing"), ("// edited by hand\n", "the module differs from its catalog")],
    ids=["missing", "differing"],
)
def test_main_check_fails_naming_a_missing_or_differing_module_and_writes_nothing(
    clean_translation, module_for, capsys, language, content, sentence
):
    main([])
    module = module_for(language)
    if content is None:
        module.unlink()
    else:
        module.write_text(content, encoding="utf-8")

    assert main(["--check"]) == 1

    error = capsys.readouterr().err
    assert module.name in error
    assert f"{sentence}; run design-catalogs" in error
    assert (module.read_text(encoding="utf-8") if module.exists() else None) == content


def test_main_writes_a_typed_module_for_every_other_catalog(clean_translation, module_for):
    assert main([]) == 0

    written = module_for("pl").read_text(encoding="utf-8")
    assert 'import type { Words } from "./de";' in written
    assert "export const words: Words = {" in written
    assert '    "table.seatFree": "Wolne",' in written


def test_main_check_passes_on_current_modules_of_every_language_and_writes_nothing(clean_translation, module_for):
    main([])
    before = [module_for(language).stat().st_mtime_ns for language in (SOURCE_LANGUAGE, "pl")]

    assert main(["--check"]) == 0
    assert [module_for(language).stat().st_mtime_ns for language in (SOURCE_LANGUAGE, "pl")] == before


def test_main_check_fails_naming_a_file_in_the_module_directory_that_no_catalog_produces(
    clean_translation, module_for, capsys
):
    main([])
    stray = module_for("xx")
    stray.write_text("// left over\n", encoding="utf-8")

    assert main(["--check"]) == 1

    assert stray.name in capsys.readouterr().err


def test_main_without_check_leaves_a_file_no_catalog_produces_alone(clean_translation, module_for):
    stray = module_for("xx")
    stray.parent.mkdir(parents=True)
    stray.write_text("// left over\n", encoding="utf-8")

    assert main([]) == 0
    assert stray.read_text(encoding="utf-8") == "// left over\n"


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
        pytest.param('msgctxt "app.name"\n  msgid "Skat\nmsgstr ""\n', 11, id="indented unterminated msgid"),
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


@pytest.mark.parametrize("arguments", [[], ["--check"]])
@pytest.mark.parametrize(
    ("translation", "language", "named"),
    [
        pytest.param([("table.seatFree", "Frei", "Wolne")], "pl", ["pl.po", "app.name"], id="missing key"),
        pytest.param(
            [("table.seatFree", "Frei", "Wolne"), ("app.name", "Skat", "Skat"), ("table.extra", "Extra", "Dodatek")],
            "pl",
            ["pl.po", "table.extra"],
            id="extra key",
        ),
        pytest.param(
            [("table.seatFree", "Frei", ""), ("app.name", "Skat", "Skat")],
            "pl",
            ["pl.po", "table.seatFree"],
            id="empty",
        ),
        pytest.param(
            [("table.seatFree", "Platz frei", "Wolne"), ("app.name", "Skat", "Skat")],
            "pl",
            ["pl.po", "table.seatFree", "Platz frei", "Frei"],
            id="older than its source",
        ),
        pytest.param(
            [("table.seatFree", "Frei", "Wolne"), ("app.name", "Skat", "Skat")],
            "en",
            ["pl.po", "Language"],
            id="header names another language",
        ),
    ],
)
def test_main_fails_naming_file_key_and_texts_of_a_broken_translation_and_writes_nothing(
    clean_source, write_catalog, catalog_text, block, module_for, capsys, arguments, translation, language, named
):
    write_catalog("pl", catalog_text(*(block(*entry) for entry in translation), language=language))

    assert main(arguments) == 1

    error = capsys.readouterr().err
    assert all(name in error for name in named)
    assert not module_for("pl").exists()
    assert not module_for(SOURCE_LANGUAGE).exists()


def test_main_fails_naming_a_fuzzy_translation_entry(clean_source, write_catalog, catalog_text, block, capsys):
    write_catalog(
        "pl",
        catalog_text(
            block("table.seatFree", "Frei", "Wolne", fuzzy=True), block("app.name", "Skat", "Skat"), language="pl"
        ),
    )

    assert main([]) == 1

    assert "table.seatFree is fuzzy" in capsys.readouterr().err


def test_main_fails_naming_a_catalog_whose_file_name_is_no_language_tag(
    clean_source, write_catalog, catalog_text, block, capsys
):
    write_catalog("pl_PL", catalog_text(block("table.seatFree", "Frei", "Wolne"), language="pl_PL"))

    assert main([]) == 1

    assert "pl_PL.po" in capsys.readouterr().err


def test_main_fails_naming_a_source_catalog_whose_header_names_another_language(
    write_source, catalog_text, block, module_path, capsys
):
    write_source(catalog_text(block("table.seatFree", "Frei"), language="en"))

    assert main([]) == 1

    assert "de.po" in capsys.readouterr().err
    assert not module_path.exists()


def test_main_fails_naming_a_source_entry_with_msgid_plural_and_says_plural_forms_are_not_used(
    write_source, catalog_text, capsys
):
    write_source(
        catalog_text('msgctxt "table.seats"\nmsgid "Platz"\nmsgid_plural "Plätze"\nmsgstr[0] ""\nmsgstr[1] ""\n')
    )

    assert main([]) == 1

    error = capsys.readouterr().err
    assert "table.seats" in error
    assert "plural forms are not used" in error


@pytest.mark.parametrize("language", [SOURCE_LANGUAGE, "pl"])
def test_main_fails_naming_a_catalog_that_is_not_utf8_without_a_traceback(
    clean_translation, write_catalog, module_for, capsys, language
):
    write_catalog(language, b'msgctxt "app.name"\nmsgid "Gr\xfc\xdfe"\nmsgstr ""\n')

    assert main([]) == 1

    assert f"{language}.po" in capsys.readouterr().err
    assert not module_for(language).exists()
