# appkit

This package carries the design tokens and the console-page grammar that
overnightworks products share: lists of things with states, facts and fields,
and the family tokens and fonts every product wears. It refuses components,
product-specific page layout and JavaScript (until K7 of #25); a product renders
through this grammar with its own markup.

`appkit.css` and every shared part follow the family picture
[`docs/family.html`](docs/family.html). `ui-style.css` and `grammar.html` stay
frozen under agent-presentator's picture `docs/mockups/m0-lobby.html` at revision
`cf31929d328b000be8db5da0d8765d48109c4376` until #30 removes them.

Distribution is a GitHub release. Tags are never moved; a broken release gets
the next patch tag. A release carries:

- the wheel `overnightworks_appkit-<version>-py3-none-any.whl` (import
  `appkit`): `appkit/static/appkit.css`, the family tokens (light under `:root`,
  dark under the device media query and `[data-theme='dark']`) and the `@font-face` rules; and
  `appkit/static/fonts/`, Oswald 400 and 700 and Open Sans 400 and 600, latin
  and latin-ext, woff2, with each family's OFL licence;
- `overnightworks-appkit-<version>.tgz`, the npm form of the same stylesheet and
  fonts (`package.json` is `private`; the tarball is the only npm distribution):
  `import 'overnightworks-appkit/appkit.css'`, the fonts resolving through the
  CSS's relative `url()`;
- `ui-style.css`, frozen, as before;
- `appkit-<version>-tokens.txt`, the sorted custom-property names `appkit.css`
  defines.

Every pull request passes the shared quality gate (`quality / verdict`, from
`overnightworks/quality`): secret scan, workflow-security scan and SonarCloud analysis of the CSS, HTML and Python.

Pin the wheel by URL with its hash (`scripts/publish_release` prints the sha256):

```
https://github.com/overnightworks/appkit/releases/download/v0.7.0/overnightworks_appkit-0.7.0-py3-none-any.whl#sha256=<sha256>
```

A SvelteKit app takes the tarball, pinned by URL; pnpm writes its `sha512-`
integrity into the lockfile, and `scripts/publish_release` prints the same value
to compare:

```
https://github.com/overnightworks/appkit/releases/download/v0.7.0/overnightworks-appkit-0.7.0.tgz
```

A Python app (edge, songmaker's backend) takes the wheel; an app with a
frontend takes the tarball.

`ui-style.css` is still published at
`https://github.com/overnightworks/appkit/releases/download/v0.7.0/ui-style.css`.

Writing markup against it: [stylesheet reference](docs/stylesheet.md).

## Release

```sh
scripts/publish_release v<version>
```

It builds the wheel and packs the tarball, tags `main`, pushes the tag,
attaches both, `ui-style.css` and the token list, and prints the wheel's sha256
and the tarball's sha512 integrity for pins. It refuses unless the tag equals
the version in `pyproject.toml` and `package.json`, `pnpm` is installed, you are on a clean `main`
equal to `origin/main`, the tag is new and `gh` is logged in.

Tests: `uv run --frozen pytest -q tests`.
