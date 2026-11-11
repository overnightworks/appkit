from pathlib import Path

import pytest

from design.catalogs.catalog import LanguageTag, PluralCategory, RawEntry
from design.catalogs.po_file import CatalogFileError, list_files, plural_categories, read_catalog


def test_read_catalog_returns_each_entry_with_its_context_text_and_flag(write_source, catalog_text, block):
    path = write_source(
        catalog_text(block("table.seatFree", "Frei"), block("table.title", "Tisch", "Table", fuzzy=True))
    )

    assert read_catalog(path).entries == (
        RawEntry(context="table.seatFree", text="Frei", translation="", fuzzy=False, plural=False),
        RawEntry(context="table.title", text="Tisch", translation="Table", fuzzy=True, plural=False),
    )


def test_read_catalog_skips_the_header_and_obsolete_entries(write_source, catalog_text, block):
    path = write_source(
        catalog_text(block("table.seatFree", "Frei"), '#~ msgctxt "gone.old"\n#~ msgid "x"\n#~ msgstr ""\n')
    )

    assert [entry.context for entry in read_catalog(path).entries] == ["table.seatFree"]


def test_read_catalog_skips_only_the_first_header_and_keeps_a_later_entry_without_msgctxt_and_msgid(
    write_source, catalog_text, block
):
    path = write_source(catalog_text(block("table.seatFree", "Frei"), block(None, "")))

    assert [entry.context for entry in read_catalog(path).entries] == ["table.seatFree", None]


def test_read_catalog_keeps_the_first_entry_of_a_catalog_without_header(write_source, block):
    path = write_source(block("table.seatFree", "Frei"))

    assert [entry.context for entry in read_catalog(path).entries] == ["table.seatFree"]


@pytest.mark.parametrize(
    ("blocks", "contexts"),
    [
        pytest.param(("plain",), [None], id="without msgctxt"),
        pytest.param(("empty",), ["table.empty"], id="empty msgid"),
        pytest.param(("same", "same"), ["table.same", "table.same"], id="exact duplicate"),
    ],
)
def test_read_catalog_keeps_the_entries_a_catalog_object_would_merge_or_drop(
    write_source, catalog_text, block, blocks, contexts
):
    built = {
        "plain": block(None, "Schlicht"),
        "empty": block("table.empty", ""),
        "same": block("table.same", "Gleich"),
    }
    path = write_source(catalog_text(*(built[name] for name in blocks)))

    assert [entry.context for entry in read_catalog(path).entries] == contexts


def test_read_catalog_unescapes_quotes_newlines_and_umlauts(write_source, catalog_text, block):
    path = write_source(catalog_text(block("table.quote", 'Er sagte \\"Hallo\\"\\nGr\u00fc\u00dfe')))

    assert read_catalog(path).entries[0].text == 'Er sagte "Hallo"\nGr\u00fc\u00dfe'


@pytest.mark.parametrize(
    ("header_language", "expected"),
    [pytest.param("pl", "pl", id="named"), pytest.param(None, None, id="absent")],
)
def test_read_catalog_returns_the_language_its_header_names(write_catalog, block, header_language, expected):
    header = 'msgid ""\nmsgstr ""\n' + (
        f'"Language: {header_language}\\n"\n' if header_language else '"X-Other: 1\\n"\n'
    )
    path = write_catalog("pl", header + "\n" + block("table.seatFree", "Frei", "Wolne"))

    assert read_catalog(path).language == expected


def test_read_catalog_gives_a_plural_entry_its_first_forms_and_marks_it_plural(write_catalog, catalog_text):
    plural = 'msgctxt "table.seats"\nmsgid "Platz"\nmsgid_plural "Plätze"\nmsgstr[0] ""\nmsgstr[1] ""\n'
    path = write_catalog("de", catalog_text(plural))

    assert read_catalog(path).entries == (
        RawEntry(context="table.seats", text="Platz", translation="", fuzzy=False, plural=True),
    )


def test_read_catalog_refuses_a_file_that_is_not_utf8_naming_the_file(write_catalog):
    path = write_catalog("de", b'msgctxt "a.b"\nmsgid "Gr\xfc\xdfe"\nmsgstr ""\n')

    with pytest.raises(CatalogFileError, match=r"de\.po.*UTF-8"):
        read_catalog(path)


def test_list_files_gives_the_files_of_a_directory_by_name_and_nothing_of_a_missing_one(tmp_path):
    (tmp_path / "b.ts").write_text("", encoding="utf-8")
    (tmp_path / "a.po").write_text("", encoding="utf-8")
    (tmp_path / "folder").mkdir()

    assert list_files(tmp_path) == (tmp_path / "a.po", tmp_path / "b.ts")
    assert list_files(tmp_path / "absent") == ()


@pytest.mark.parametrize(
    ("tag", "names"),
    [
        pytest.param("de", {"one", "other"}, id="german"),
        pytest.param("pl", {"one", "few", "many", "other"}, id="polish"),
        pytest.param("ja", {"other"}, id="japanese without a plural"),
        pytest.param("pt-BR", {"one", "many", "other"}, id="a tag with a region"),
    ],
)
def test_plural_categories_are_the_cldr_categories_of_the_language_and_other(tag, names):
    assert plural_categories(LanguageTag(tag), Path(f"{tag}.po")) == {PluralCategory(name) for name in names}


def test_plural_categories_refuse_a_language_babel_has_no_rules_for_naming_the_catalog_file():
    with pytest.raises(CatalogFileError, match=r"locales/tlh\.po: .*tlh"):
        plural_categories(LanguageTag("tlh"), Path("locales/tlh.po"))
