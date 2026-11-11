# design

The family look that overnightworks products share (tokens, fonts, two classes
and five Svelte components), for the engineers of those products.

## Quick start

Distribution is a GitHub release. It carries:

- the wheel `overnightworks_design-<version>-py3-none-any.whl` (import `design`):
  `design/static/design.css` and `design/static/fonts/`, and the command
  `design-catalogs` ([Catalogs](#catalogs));
- `overnightworks-design-<version>.tgz`: the same stylesheet and fonts, plus the
  components `SignInPage`, `AccountMenu`, `AgentControl`, `LegalLinks` and `AiMark`. It is the
  only npm distribution, and `svelte` ^5.20 is its only, peer, dependency;
- `design-<version>-tokens.txt`: the sorted custom-property names `design.css`
  defines.

An app that serves the stylesheet from Python pins the wheel by URL with its
hash, which the release notes give:

```
https://github.com/overnightworks/design/releases/download/v<version>/overnightworks_design-<version>-py3-none-any.whl#sha256=<sha256>
```

A SvelteKit app pins the tarball by URL. pnpm writes the tarball's `sha512-`
integrity into the lockfile only when it downloads the tarball, not on a store
hit, and a frozen install enforces it; compare the lockfile's value with the
one at the top of the release notes, or enter that one:

```
https://github.com/overnightworks/design/releases/download/v<version>/overnightworks-design-<version>.tgz
```

Then `import 'overnightworks-design/design.css'` and
`import { SignInPage } from 'overnightworks-design'`.

## SignInPage

The sign-in page in its five states: signed out, signing in (in a separate window), window blocked (the browser blocked that window), login failed and no access. Props and behaviour are documented in
[`src/lib/types.ts`](src/lib/types.ts).

```svelte
<SignInPage
	appName="Hallucinai"
	state={{ page: 'signed-out', signInHref }}
	{legalLinks}
/>
```

## AccountMenu

The account panel for an app's popover. Props and behaviour are documented in
[`src/lib/types.ts`](src/lib/types.ts); `LegalLinks` is the legal row both
components render.

```svelte
<AccountMenu
	name="Felix"
	accountHref={accountConsoleUrl}
	onAccountOpen={() => popover.close(false)}
	appRows={[{ label: 'Settings', onSelect: openSettings }]}
	{legalLinks}
	{onLogOut}
/>
```

## AgentControl

The panel of rows with which a person calls an agent into a place and asks it
to leave again. The trigger and the popover stay with the app. Props and
behaviour are documented in [`src/lib/types.ts`](src/lib/types.ts).

```svelte
<AgentControl {rows} {onCall} {onSendAway} {refusal} />
```

## Catalogs

`design-catalogs` turns an app's gettext catalogs into typed modules, so that a
further language means adding a catalog file, not changing code. It is in the
wheel only, and it needs Babel, which only the extra `catalogs` installs: an app
that takes the wheel for `design.css` gets no Babel. An app pins the wheel with
the extra in its dev group, by release URL and sha256, which the release notes
give:

```toml
[dependency-groups]
dev = ["overnightworks-design[catalogs] @ https://github.com/overnightworks/design/releases/download/v<version>/overnightworks_design-<version>-py3-none-any.whl#sha256=<sha256>"]
```

- `design-catalogs` reads one `<tag>.po` per language and writes one TypeScript
  module per language and, where the app declares one, a Python module.
- `design-catalogs --check` writes nothing and fails on a broken catalog, a
  missing, empty or outdated translation, a module that is missing or differs
  from its catalogs, and a file in the module directory that no catalog
  produces.

Both run in the repository's root. The optional table `[tool.design-catalogs]` in
its `pyproject.toml` overrides the defaults; paths are relative to the root and
stay inside it, the Python module lies outside the other two directories, and an
unknown key or a wrong type fails:

```toml
[tool.design-catalogs]
source = "de"                           # the source language
catalogs = "frontend/src/lib/catalogs"  # <tag>.po per language
typescript = "frontend/src/lib/words"   # <tag>.ts per language
python = "src/app/words.py"             # no default: without it, no Python module
```

The Python module holds `Key` and `Language`, `SOURCE_LANGUAGE`, `LANGUAGES`,
`WORDS` and `text(language, key)`, for the app's Python tests and server. It
keeps its own layout (`# fmt: off`), and a text longer than the line length is
not wrapped, so an app that selects ruff's `E501` excludes the file. The shape of
the catalogs and the rules `--check` holds are in
[Languages](docs/languages.md).

## Documentation

- [Vision](docs/VISION.md): what design is for and what it is not.
- [Stylesheet reference](docs/stylesheet.md): the classes, tokens, wording and
  legal-row markup.
- [Architecture](docs/ARCHITECTURE.md): the parts, the trust and the proof.
- [Languages](docs/languages.md): the fleet standard for building apps so that a further language needs no code change.

## Release

A release is dispatched with the version alone and passes quality's release gate
before it builds the wheel and the tarball, tags `main` and attaches both and the
token list to a GitHub release. The release notes carry the hashes for the pins.
The dispatch command and the repository's targeted checks are in
[AGENTS.md](AGENTS.md).

## Licence

[MIT](LICENSE). The fonts keep their OFL licences, shipped beside them.
