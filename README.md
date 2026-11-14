# design

The family look that overnightworks products share (tokens, fonts, two classes
and nine Svelte components), for the engineers of those products.

## Quick start

Distribution is a GitHub release. It carries:

- the wheel `overnightworks_design-<version>-py3-none-any.whl` (import `design`):
  `design/static/design.css` and `design/static/fonts/`, the command
  `design-catalogs` ([Catalogs](#catalogs)) and the kit's Python words
  ([The kit's words](#the-kits-words));
- `overnightworks-design-<version>.tgz`: the same stylesheet and fonts, plus the
  components `SignInPage`, `AccountMenu`, `AgentControl`, `HearingSwitch`, `EarMark`, `HelperChat`, `LegalLinks`, `TurnState`, `Marked` and `AiMark` and the
  kit's words per language ([The kit's words](#the-kits-words)). It is the
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
	words={kitWords}
/>
```

## AccountMenu

The account panel for an app's popover. Props and behaviour are documented in
[`src/lib/types.ts`](src/lib/types.ts); [`LegalLinks`](#legallinks) is the legal row both
components render.

```svelte
<AccountMenu
	name="Felix"
	accountHref={accountConsoleUrl}
	onAccountOpen={() => popover.close(false)}
	appRows={[{ label: 'Settings', onSelect: openSettings }]}
	{legalLinks}
	{onLogOut}
	words={kitWords}
/>
```

## LegalLinks

The legal row, for a page without the account menu. `SignInPage` and `AccountMenu`
draw it with their own `words`; an app that draws it itself passes the same words.
The labels and addresses stay the app's.

```svelte
<LegalLinks links={legalLinks} words={kitWords} />
```

## AgentControl

The panel of rows with which a person calls an agent into a place and asks it
to leave again. The trigger and the popover stay with the app. Props and
behaviour are documented in [`src/lib/types.ts`](src/lib/types.ts). Without
`onSendAway` a row of an agent that is here shows its mark and name and no
action; an app that lets people send agents away passes the handler.

A call that ends without a seat shows briefly why on its row. The app passes the row as
`state: 'ended'` with an `outcome` (`'no-answer'`, `'busy'` or `'owner-absent'`); the row shows
the outcome in place of the waiting text, muted, with a small icon and no key. After four
seconds, the same in every app, the row is drawn like an `available` row and its call key
works as usual, until the app changes the row. The kit invents no reason: it shows the
outcome the app passes. While a call is under way the app passes the row as `inviting`, so an
ended outcome that repeats after a new call restarts the four seconds; the same ended outcome
passed again with no state change in between shows nothing new.

When the place holds no further agent, the app passes `full`; with no rows the panel then says
so ("Hier ist kein Platz für einen weiteren Agenten.", the sentence of the `place-full` refusal)
instead of the empty sentence. The kit does not decide when a place is full, and rows are drawn
unchanged.

```svelte
<AgentControl {rows} {onCall} {onSendAway} {refusal} words={kitWords} />
```

## HearingSwitch

One chip with a switch for an agent's hearing, drawn on a video: `kind="hear"` is
"Agent may hear me", `kind="listen"` is "I want to hear the agent". It is controlled: it
shows `on` and, when pressed, calls `onChange` with the negated value, so the app sets `on`
again or leaves it. The on colour is the app's `--accent`; the glass and the light ink are
the chip's own, because the chip always sits on a video. Where the chips stand, their
defaults and what a switch does stay with the app. Props and behaviour are documented in
[`src/lib/types.ts`](src/lib/types.ts).

```svelte
<HearingSwitch kind="hear" on={agentMayHear} onChange={(on) => (agentMayHear = on)} words={kitWords} />
```

## EarMark

The round ear that shows an agent hears a person, drawn on a video: the ear in a glass disc
ringed in the app's `--accent`, and the agent's name in a small pill beside it. Its accessible
name and title read "Mozart hears you" on the person's own tile (no `person`) and "Mozart hears
Anna" on another person's tile (`person="Anna"`), in the page's language. It is one image and
holds no state: the app mounts it only while the agent hears that person, places it on the
tile and stacks the marks of several agents (the marks stack cleanly in a column). The glass
and the light ink are the mark's own, because the mark always sits on a video; a long agent
name ends in an ellipsis within the width the app gives it. Props and behaviour are documented
in [`src/lib/types.ts`](src/lib/types.ts).

```svelte
<EarMark agent="Mozart" person="Anna" words={kitWords} />
```

## TurnState

The mark and the kit's word for the reason an agent's turns at a place do not answer, drawn beside
the agent's name: `outcome` is `not_enabled`, `busy`, `budget_spent` or `unavailable`, the values
the agents service states, and the part shows a small muted mark with the word in the page's
language. With `undefined` it renders nothing. It holds no state and no timer: the app passes the
last stated value and drops it when the agent's seat ends. A `here` row of `AgentControl` draws it
from the row's optional `turnState`; where an app draws the name itself, as at a seat, it places
`TurnState` beside the name. Props are documented in [`src/lib/types.ts`](src/lib/types.ts).

```svelte
<TurnState outcome="budget_spent" words={kitWords} />
```

## HelperChat

The conversation a person has with an app's helper agent, drawn from props alone: the message
list with the helper's tool-call rows, the answer as it grows, the thinking line and the
composer. Each helper message leads with `AiMark`. The part holds no fetch, no store and no
app data; the app owns the turn, the network, the header and notice before it, and the scroll
memory. The messages sit in an `ol` with `role="list"` named by the kit word
`helperChat.listLabel` with the helper's name, each one an `li` that begins with a visually hidden speaker line, the kit word
`helperChat.speaker` with `helperChat.you` for the person's messages and `helperName` for the
helper's, also on a message without a bubble; the list has no live region, so
the thinking line's `role="status"` is the only announcement, and the scrolling element has no
role. Message text arrives already shaped and is shown as written. The composer is
controlled through `draft` and `onDraft(draft, caret)`: Enter sends the trimmed draft and
Shift+Enter makes a new line; a plain Enter is always cancelled (also while a turn runs, while
the draft is empty and while read-only), nothing is sent during IME composition, and
`onComposerKeydown` runs first, so its `preventDefault()` keeps a keystroke from sending. The
app places its own pieces through props and snippets: `problemLine`, `toolCallTarget`,
`toolCallTitle`, `composerPopup` (inside the composer's box, which is `position: relative`),
`composerTop`, `readOnly` (a banner that also disables the composer), `history` (`loading` and
`failed` show instead of the list), `list` and `onListScroll`. The part is generic over the
app's message type, which reaches the snippets unchanged. It uses `design.css` tokens and the
app's `--accent` and `--on-accent`; the other visual values are its own. Props and behaviour
are documented in [`src/lib/types.ts`](src/lib/types.ts).

```svelte
<HelperChat
  {messages}
  {running}
  history={{ state: 'ready' }}
  helperName="Mozart"
  emptyHint="Ask Mozart about your song."
  placeholder="Ask for a rewrite…"
  {draft}
  onDraft={(text) => (draft = text)}
  onSend={send}
  words={kitWords}
/>
```

## Marked

A sentence with a part the page sets apart, as `design-catalogs` generates it
([Catalogs](#catalogs)), is a list of parts. `Marked` renders the list in place, with
no element and no white space of its own: the app gives one snippet for each marker
name, which receives the part, `{ text }`, and chooses the element. A missing snippet,
a snippet written in place for a name the sentence lacks and a snippet that takes the
text as a string are type errors. That holds only while the parts keep their literal
marker names: a list whose marker is typed `string` accepts a record of any keys, so a
missing snippet fails at render time. A parameter written as a plain name would leave a
default value no call reaches: a branch an app that measures with istanbul counts.

```svelte
<script lang="ts">
  import { Marked } from 'overnightworks-design';
  import { words } from './words/de';

  const parts = words['retention.archiveConfirm']({ count: 3, deleted: '2' });
</script>

{#snippet strong({ text }: { text: string })}<strong>{text}</strong>{/snippet}
{#snippet help({ text }: { text: string })}<a href="/help">{text}</a>{/snippet}

<p><Marked {parts} marked={{ strong, help }} /></p>
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

Pinning by git tag is an equal form of taking the generator; `uv lock` records
the commit of the tag:

```toml
[dependency-groups]
dev = ["overnightworks-design[catalogs] @ git+https://github.com/overnightworks/design@v<version>"]
```

- `design-catalogs` reads one `<tag>.po` per language and writes one TypeScript
  module per language, the loader `index.ts` beside them and, where the app
  declares one, a Python module.
- A text marks a part the page sets apart as `{#name}…{/name}`, and the module
  returns the sentence as a list of parts that [`Marked`](#marked) renders; the
  rules are LANG-25 in [Languages](docs/languages.md).
- `design-catalogs --check` writes nothing and fails on a broken catalog, a
  missing, empty, fuzzy or outdated translation, a module or loader that is
  missing or differs from its catalogs, and a file in the module directory that
  no catalog produces.
- `design-catalogs --sync` brings every translation catalog in line with the
  source by key, never by Babel's catalog update, and writes catalogs only. A
  missing key comes with the source text as `msgid` and an empty `msgstr`; a
  changed source text becomes the `msgid`, the old `msgstr` stays and the entry
  is marked fuzzy; a key the source dropped is removed; a plural family holds
  exactly the categories of its language, and a category the source lacks takes
  the source's `other` text. A catalog already in line with its source is not
  touched, and a second run changes no byte. A catalog the sync has to change
  keeps its header and the order of its entries and is rewritten through
  Babel's writer: its lines are wrapped at the fixed width, line endings become
  LF, a `#|` previous-msgid comment turns into a translator comment
  (`# | msgid "..."`), obsolete (`#~`) entries lose their flags and extracted
  comments, and the file ends in a blank line. It needs no network.

A change to the source texts goes in this order: sync, translate, generate, check.
Change the source catalog, run `design-catalogs --sync`, write the translations
and clear the fuzzy marks, run `design-catalogs` for the modules, and
`design-catalogs --check` in the app's lint and CI. `--sync` leaves empty and fuzzy entries behind, so `--check` fails
until the translations are written.

The loader names the languages, which always equal the catalog files, and
loads the words of one language as its own chunk through dynamic imports. Every
specifier between the generated modules ends in `.js`, as standard ESM needs, so
their compiled JavaScript loads under plain Node without a rewrite; a bundler, Vitest, Playwright and TypeScript with
`moduleResolution: bundler` map the ending to the `.ts` file. `loadWords` is called only with a member of
`languages`: an unknown language is a type error, and at run time the promise
rejects. The page reads `<html lang>` once, when it starts:

```ts
import { languages, loadWords, sourceLanguage } from "./words";
const tag = document.documentElement.lang;
const language = languages.find((candidate) => candidate === tag) ?? sourceLanguage;
const words = await loadWords(language);
```

The snippet's module is the page's one entry module, which no second chunk imports at
the same time, so it may await at its top level. The rule in [The kit's
words](#the-kits-words) is for a module that two chunks import.

Each run is in the directory that holds its declaration: the repository's root for an
app of one unit. A separately shipped unit in the same repository has its own
declaration, its own run and its own `--check`; its words never enter another unit's
catalog. The optional table `[tool.design-catalogs]` in that directory's
`pyproject.toml` overrides the defaults; paths are relative to that directory and
stay inside it, the TypeScript directory is not the catalogs directory, the
Python module lies outside both, and an unknown key or a wrong type fails:

```toml
[tool.design-catalogs]
source = "de"                           # the source language
catalogs = "frontend/src/lib/catalogs"  # <tag>.po per language
typescript = "frontend/src/lib/words"   # <tag>.ts per language
python = "src/app/words.py"             # no default: without it, no Python module
```

The Python module holds `Key` and `Language`, `SOURCE_LANGUAGE`, `LANGUAGES`,
`WORDS`, `plural_category(language, count)` and `text`, for the app's Python
tests and server. It needs no Babel at run time. A text names its gaps as
`{name}`; a plural family is one key whose entries are the CLDR categories of
each language. `text("de", "chat.greeting", name="Eva")` fills the gaps and
raises on a missing or an unknown one, and on an unknown language or key;
`text("de", "table.seats", count=3, name="Eva")` names a family by its key,
chooses the sentence by the count and fills `count` as plain digits. The page
gets the same from the TypeScript module, a family as `words["table.seats"](3, { name })`.

The Python module is `# fmt: off`, with single-quoted texts and lines longer
than the line length. An app whose ruff selects the line length (`E501`) or the
quote rules (`Q`) ignores them for that file:

```toml
[tool.ruff.lint.per-file-ignores]
"src/app/words.py" = ["E501", "Q"]
```

The module keeps one literal per key, so a text several keys share repeats, as
the standard wants a key per place. An app that SonarCloud analyses excludes
the module from its analysis in `sonar-project.properties`, as the repeated
literals trip `python:S1192`:

```properties
# generated by design-catalogs, gated by design-catalogs --check
sonar.exclusions=src/app/words.py
```

An app with 100 % coverage thresholds omits the generated Python module from its
measured set, because the module carries the paths for gaps and plural families
whether or not the app's catalog uses them. It also excludes the loader `index.ts`
from frontend coverage until a second language calls it.

The TypeScript modules use four spaces and double quotes; an app whose prettier
settings differ adds the words directory to `.prettierignore`:

```
frontend/src/lib/words/
```

The shape of the catalogs and the rules `--check` holds are in
[Languages](docs/languages.md).

## The kit's words

The words of `SignInPage`, `AccountMenu`, `AgentControl`, `HearingSwitch`, `EarMark`, `HelperChat`, `LegalLinks` and `TurnState` come from the
kit's own catalogs, which the kit builds with `design-catalogs` like an app. Each of the
seven takes them as the required prop `words: KitWords`, holds no default and reads no
language itself, so a page cannot show one language on another's page; the
examples above get `kitWords` from the `load` below. To override one word, pass a
spread typed as `KitWords`: `words={{ ...kitWords, "account.logOut": "Exit" }}`. The
tarball ships the words per language, each as its own chunk, and the package root
and the export `overnightworks-design/words` offer:

- `loadKitWords(language)`: the words of one language, as a promise. The kit reads
  no language itself; the caller passes it.
- `KitLanguage`: the languages the kit ships.
- `KitWords`: the shape of one language's words.

The export `overnightworks-design/words` holds these three and nothing else, no
component, so a plain Node process can import it, which the package root cannot: the root
re-exports `.svelte` files, which Node does not load. A Playwright spec names the kit's
texts from it:

```ts
// tests/sign-in.spec.ts
import { expect, test } from "@playwright/test";
import { loadKitWords } from "overnightworks-design/words";

test("the sign-in page offers the kit's log-in text", async ({ page }) => {
  const words = await loadKitWords("en");
  await page.goto("/en/");
  await expect(page.getByText(words["signIn.logIn"])).toBeVisible();
});
```

The wheel's `design.words` is the same words in Python, for an app's tests and
not for its server; it needs no Babel and no extra.

An app loads the kit's words for the page's language as it loads its own. A
prerendering `load` serves each language once; an app-owned module beside the
generated words directory checks that the kit ships every language the app offers:

```ts
// src/lib/languages.ts
import type { KitLanguage } from "overnightworks-design";
import { languages } from "./words";

void (languages satisfies readonly KitLanguage[]); // a language the kit lacks fails the type check
```

The `void` keeps typescript-eslint's `no-unused-expressions` rule quiet, which flags a
bare `satisfies` statement.

```ts
// src/routes/[language]/+page.ts
import { languages } from "$lib/words";

export const entries = () => languages.map((language) => ({ language }));
```

```ts
// src/routes/[language]/+layout.ts
import { loadKitWords } from "overnightworks-design";
import { languages, loadWords } from "$lib/words";

export const prerender = true;

export const load = async ({ params }) => {
  const language = languages.find((candidate) => candidate === params.language) ?? languages[0];
  return { words: await loadWords(language), kitWords: await loadKitWords(language) };
};
```

The root layout awaits both loaders in its `load`, as the example does, and never at the
top level of a module: some Safari versions reject a module with a top-level `await` that
two chunks import at once.

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
