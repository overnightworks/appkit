import pytest

from design.catalogs.catalog import RawEntry
from design.catalogs.po_file import read_entries


def test_read_entries_returns_each_entry_with_its_context_text_and_flag(write_source, catalog_text, block):
    path = write_source(
        catalog_text(block("table.seatFree", "Frei"), block("table.title", "Tisch", "Table", fuzzy=True))
    )

    assert read_entries(path) == (
        RawEntry(context="table.seatFree", text="Frei", translation="", fuzzy=False),
        RawEntry(context="table.title", text="Tisch", translation="Table", fuzzy=True),
    )


def test_read_entries_skips_the_header_and_obsolete_entries(write_source, catalog_text, block):
    path = write_source(
        catalog_text(block("table.seatFree", "Frei"), '#~ msgctxt "gone.old"\n#~ msgid "x"\n#~ msgstr ""\n')
    )

    assert [entry.context for entry in read_entries(path)] == ["table.seatFree"]


@pytest.mark.parametrize(
    ("blocks", "contexts"),
    [
        pytest.param(("plain",), [None], id="without msgctxt"),
        pytest.param(("empty",), ["table.empty"], id="empty msgid"),
        pytest.param(("same", "same"), ["table.same", "table.same"], id="exact duplicate"),
    ],
)
def test_read_entries_keeps_the_entries_a_catalog_object_would_merge_or_drop(
    write_source, catalog_text, block, blocks, contexts
):
    built = {
        "plain": block(None, "Schlicht"),
        "empty": block("table.empty", ""),
        "same": block("table.same", "Gleich"),
    }
    path = write_source(catalog_text(*(built[name] for name in blocks)))

    assert [entry.context for entry in read_entries(path)] == contexts


def test_read_entries_unescapes_quotes_newlines_and_umlauts(write_source, catalog_text, block):
    path = write_source(catalog_text(block("table.quote", 'Er sagte \\"Hallo\\"\\nGr\u00fc\u00dfe')))

    assert read_entries(path)[0].text == 'Er sagte "Hallo"\nGr\u00fc\u00dfe'
