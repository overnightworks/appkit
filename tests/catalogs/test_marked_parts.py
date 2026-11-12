import pytest

from design.catalogs.catalog import (
    Entry,
    Key,
    LanguageTag,
    PluralCategory,
    RawEntry,
    SourceCatalog,
    read_source,
    read_translation,
    without_markers,
)

FILE = "frontend/src/lib/catalogs/de.po"
TRANSLATION_FILE = "frontend/src/lib/catalogs/pl.po"
GERMAN = frozenset({PluralCategory.ONE, PluralCategory.OTHER})
POLISH = frozenset({PluralCategory.ONE, PluralCategory.FEW, PluralCategory.MANY, PluralCategory.OTHER})


def entry(context, text, translation=""):
    return RawEntry(context=context, text=text, translation=translation, fuzzy=False, plural=False)


def family(key, **texts):
    """The entries of one plural family as the source catalog writes them, by category."""
    return tuple(entry(f"{key}.{category}", text) for category, text in texts.items())


@pytest.mark.parametrize(
    ("text", "sentence"),
    [
        pytest.param("Frei", "Frei", id="no marker"),
        pytest.param("{{x}} {name}", "{{x}} {name}", id="braces and gaps as written"),
        pytest.param("A {#strong}{n} takes{/strong} {{#b}}", "A {n} takes {{#b}}", id="marked part"),
    ],
)
def test_without_markers_is_the_text_with_its_markers_removed_and_everything_else_as_written(text, sentence):
    assert without_markers(text) == sentence


MARKER_REFUSALS = [
    pytest.param("Alles {/strong}", "{/strong}", id="a close without an open"),
    pytest.param("Alles {#strong}hier", "{#strong}", id="a part left open"),
    pytest.param("{#a}x {#b}y{/b}{/a}", "{#b}", id="a part inside a part"),
    pytest.param("{#a}x {#a}y{/a}{/a}", "{#a}", id="a part of one name inside itself"),
    pytest.param("{#a}x {#b}y{/a}{/b}", "{#b}", id="crossing parts"),
    pytest.param("{#a}x{/b}", "{/b}", id="a close of another name"),
    pytest.param("Alles {#strong}{/strong}", "{#strong}", id="an empty part"),
    pytest.param("Alles {#strong} \t{/strong}", "{#strong}", id="a part of white space"),
    pytest.param("Alles {#strong/}", "{#strong/}", id="a standalone marker"),
    pytest.param("Alles {#strong class=x}y{/strong}", "{#strong class=x}", id="an option"),
    pytest.param("Alles {#strong:x}y{/strong}", "{#strong:x}", id="a format spec"),
    pytest.param("Alles {#strong}y{/strong foo}", "{/strong foo}", id="an attribute on the close"),
    pytest.param("Alles {#my-name}y{/my-name}", "{#my-name}", id="a name that is no identifier"),
    pytest.param("Alles {#}y{/}", "{#}", id="no name"),
    pytest.param("Alles {# strong}y{/strong}", "{# strong}", id="a padded name"),
]


@pytest.mark.parametrize(("text", "named"), MARKER_REFUSALS)
def test_read_source_refuses_a_malformed_marker_with_one_finding_naming_the_key_and_the_marker(text, named):
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("table.seatFree", text),))

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seatFree")]
    assert findings[0].problem.startswith("is malformed")
    assert named in findings[0].problem


@pytest.mark.parametrize(("text", "named"), MARKER_REFUSALS)
def test_read_translation_refuses_a_malformed_marker_with_one_finding_naming_the_key(text, named):
    source = SourceCatalog(LanguageTag("de"), (Entry(Key("table.seatFree"), "Frei {#strong}hier{/strong}"),))

    _, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        POLISH,
        (entry("table.seatFree", "Frei {#strong}hier{/strong}", text),),
        source,
    )

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "table.seatFree")]
    assert named in findings[0].problem


def test_read_source_takes_a_marked_part_with_gaps_and_leaves_the_text_as_the_catalog_wrote_it():
    text = "Archive {#strong}{count} takes{/strong} and delete {#strong}{deleted}{/strong}. {#code}x{/code}"

    catalog, findings = read_source(FILE, LanguageTag("de"), GERMAN, (entry("retention.confirm", text),))

    assert findings == ()
    assert [item.text for item in catalog.entries] == [text]


@pytest.fixture
def marked_source():
    return SourceCatalog(
        language=LanguageTag("de"),
        entries=(Entry(Key("home.powered"), "{#strong}A{/strong} und {#strong}B{/strong} mit {#code}{name}{/code}"),),
    )


def powered(translation):
    return (entry("home.powered", "{#strong}A{/strong} und {#strong}B{/strong} mit {#code}{name}{/code}", translation),)


@pytest.mark.parametrize(
    "translation",
    [
        pytest.param("{#code}{name}{/code} z {#strong}B{/strong} i {#strong}A{/strong}", id="moved parts"),
        pytest.param(
            "{#strong}Aa Bb{/strong} {#strong}x{/strong} {#code}Ein Wort{/code} {name}", id="gap out of its part"
        ),
        pytest.param("{#strong}Neu {name}{/strong} {#strong}X{/strong} {#code}y{/code}", id="gap into another part"),
    ],
)
def test_read_translation_takes_markers_moved_and_gaps_moved_into_or_out_of_a_part(marked_source, translation):
    _, findings = read_translation(TRANSLATION_FILE, LanguageTag("pl"), POLISH, powered(translation), marked_source)

    assert findings == ()


@pytest.mark.parametrize(
    ("translation", "markers"),
    [
        pytest.param("{#strong}A{/strong} {#code}{name}{/code}", "the markers {#code, #strong}", id="a marker dropped"),
        pytest.param(
            "{#strong}A B{/strong} {#code}{name}{/code}", "the markers {#code, #strong}", id="a marker merged"
        ),
        pytest.param(
            "{#strong}A{/strong} {#strong}B{/strong} {#em}{name}{/em}",
            "the markers {#em, #strong, #strong}",
            id="a marker renamed",
        ),
        pytest.param(
            "{#strong}A{/strong} {#strong}B{/strong} {#strong}{name}{/strong}",
            "the markers {#strong, #strong, #strong}",
            id="a marker added",
        ),
        pytest.param("A B {name}", "no markers", id="no markers"),
    ],
)
def test_read_translation_names_the_key_and_both_marker_multisets_of_a_translation_whose_markers_differ(
    marked_source, translation, markers
):
    catalog, findings = read_translation(
        TRANSLATION_FILE, LanguageTag("pl"), POLISH, powered(translation), marked_source
    )

    assert [(finding.file, finding.key) for finding in findings] == [(TRANSLATION_FILE, "home.powered")]
    assert markers in findings[0].problem
    assert "the source has the markers {#code, #strong, #strong}" in findings[0].problem
    assert catalog.entries == ()


def test_read_translation_names_a_marker_the_source_lacks():
    source = SourceCatalog(LanguageTag("de"), (Entry(Key("table.seatFree"), "Frei"),))

    _, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        POLISH,
        (entry("table.seatFree", "Frei", "{#strong}Wolne{/strong}"),),
        source,
    )

    assert [finding.key for finding in findings] == ["table.seatFree"]
    assert "the source has no markers" in findings[0].problem


MARKED_SEATS = {"one": "{#strong}{count}{/strong} Platz", "other": "{#strong}{count}{/strong} Plätze"}


def test_read_source_refuses_a_family_whose_entries_carry_different_markers_and_names_each_set():
    _, findings = read_source(
        FILE,
        LanguageTag("de"),
        GERMAN,
        family("table.seats", one="{#strong}{count}{/strong} Platz", other="{count} Plätze"),
    )

    assert [(finding.file, finding.key) for finding in findings] == [(FILE, "table.seats")]
    assert "one has the markers {#strong}" in findings[0].problem
    assert "other has no markers" in findings[0].problem


def test_read_source_takes_a_family_whose_entries_carry_the_same_markers():
    _, findings = read_source(FILE, LanguageTag("de"), GERMAN, family("table.seats", **MARKED_SEATS))

    assert findings == ()


def test_read_translation_compares_the_markers_with_the_source_text_of_the_same_category_or_its_other():
    source = SourceCatalog(
        LanguageTag("de"), tuple(Entry(Key(f"table.seats.{category}"), text) for category, text in MARKED_SEATS.items())
    )
    translated = {
        category: ("{#strong}{count}{/strong} Platz" if category == "one" else "{#strong}{count}{/strong} Plätze")
        for category in ("one", "few", "many", "other")
    }
    texts = {
        **{category: f"{{#strong}}{{count}}{{/strong}} {category}" for category in translated},
        "few": "{count} few",
    }

    _, findings = read_translation(
        TRANSLATION_FILE,
        LanguageTag("pl"),
        POLISH,
        tuple(entry(f"table.seats.{category}", translated[category], text) for category, text in texts.items()),
        source,
    )

    assert [finding.key for finding in findings] == ["table.seats.few"]
    assert "no markers; the source has the markers {#strong}" in findings[0].problem
