# design

The family look that overnightworks products share (tokens, fonts, two classes
and five Svelte components), for the engineers of those products.

## Quick start

Distribution is a GitHub release. It carries:

- the wheel `overnightworks_design-<version>-py3-none-any.whl` (import `design`):
  `design/static/design.css` and `design/static/fonts/`;
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

## Documentation

- [Vision](docs/VISION.md): what design is for and what it is not.
- [Stylesheet reference](docs/stylesheet.md): the classes, tokens, wording and
  legal-row markup.
- [Architecture](docs/ARCHITECTURE.md): the parts, the trust and the proof.

## Release

A release is dispatched with the version alone and passes quality's release gate
before it builds the wheel and the tarball, tags `main` and attaches both and the
token list to a GitHub release. The release notes carry the hashes for the pins.
The dispatch command and the repository's targeted checks are in
[AGENTS.md](AGENTS.md).

## Licence

[MIT](LICENSE). The fonts keep their OFL licences, shipped beside them.
