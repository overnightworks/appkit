from design.catalogs.catalog import RawEntry


def entry(context, text, translation="", *, fuzzy=False, plural=False):
    return RawEntry(context=context, text=text, translation=translation, fuzzy=fuzzy, plural=plural)


def family(key, **texts):
    """The entries of one plural family as the source catalog writes them, by category."""
    return tuple(entry(f"{key}.{category}", text) for category, text in texts.items())
