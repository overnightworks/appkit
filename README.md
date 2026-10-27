# appkit

This package carries the design tokens and the console-page grammar that
overnightworks products share: lists of things with states, facts and fields,
and the family tokens and fonts every product wears. It refuses components,
product-specific page layout and JavaScript (until K7 of #25); a product renders
through this grammar with its own markup.

Owned by agent-presentator's blessed picture `docs/mockups/m0-lobby.html`.

Distribution is a GitHub release. Tags are never moved; a broken release gets
the next patch tag. A release carries:

- the wheel `overnightworks_appkit-<version>-py3-none-any.whl` (import
  `appkit`): `appkit/static/appkit.css`, the family tokens (dark under `:root`,
  light under `[data-theme='light']`) and the `@font-face` rules; and
  `appkit/static/fonts/`, Oswald 400 and 700 and Open Sans 400 and 600, latin
  and latin-ext, woff2, with each family's OFL licence;
- `ui-style.css`, frozen, as before;
- `appkit-<version>-tokens.txt`, the sorted custom-property names `appkit.css`
  defines.

Every pull request passes the shared quality gate (`quality / verdict`, from
`overnightworks/quality`): secret scan, workflow-security scan and SonarCloud analysis of the CSS, HTML and Python.

Pin the wheel by URL with its hash (`scripts/release` prints the sha256):

```
https://github.com/overnightworks/appkit/releases/download/v0.5.0/overnightworks_appkit-0.5.0-py3-none-any.whl#sha256=<sha256>
```

`ui-style.css` is still published at
`https://github.com/overnightworks/appkit/releases/download/v0.5.0/ui-style.css`.

Writing markup against it: [stylesheet reference](docs/stylesheet.md).

## Release

```sh
scripts/release v<version>
```

It builds the wheel, tags `main`, pushes the tag, attaches the wheel,
`ui-style.css` and the token list, and prints the wheel's sha256 for pins. It
refuses unless the tag equals the package version, you are on a clean `main`
equal to `origin/main`, the tag is new and `gh` is logged in.

Tests: `uv run --frozen pytest -q tests`.
