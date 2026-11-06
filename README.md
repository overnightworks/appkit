# appkit

The family look that overnightworks products share (tokens, fonts, two classes
and three Svelte components), for the engineers of those products.

## Quick start

Distribution is a GitHub release. It carries:

- the wheel `overnightworks_appkit-<version>-py3-none-any.whl` (import `appkit`):
  `appkit/static/appkit.css` and `appkit/static/fonts/`;
- `overnightworks-appkit-<version>.tgz`: the same stylesheet and fonts, plus the
  components `SignInPage`, `AccountMenu` and `LegalLinks`. It is the only npm
  distribution, and `svelte` ^5.20 is its only, peer, dependency;
- `appkit-<version>-tokens.txt`: the sorted custom-property names `appkit.css`
  defines.

An app that serves the stylesheet from Python pins the wheel by URL with its
hash:

```
https://github.com/overnightworks/appkit/releases/download/v<version>/overnightworks_appkit-<version>-py3-none-any.whl#sha256=<sha256>
```

A SvelteKit app pins the tarball by URL; its lockfile holds the integrity:

```
https://github.com/overnightworks/appkit/releases/download/v<version>/overnightworks-appkit-<version>.tgz
```

Then `import 'overnightworks-appkit/appkit.css'` and
`import { SignInPage } from 'overnightworks-appkit'`.

## SignInPage

The sign-in page in its three states. Props and behaviour are documented in
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

## Documentation

- [Stylesheet reference](docs/stylesheet.md): the classes, tokens, wording and
  legal-row markup.
- [Architecture](docs/ARCHITECTURE.md): the parts, the trust and the proof.

## Release

`scripts/publish_release v<version>` builds the wheel and the tarball, tags
`main` and attaches both and the token list to a GitHub release. It prints the
wheel's sha256 and the tarball's integrity for the pins. The repository's
targeted checks are in [AGENTS.md](AGENTS.md).

## Licence

[MIT](LICENSE). The fonts keep their OFL licences, shipped beside them.
