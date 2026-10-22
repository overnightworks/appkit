# ui-style

This package carries the design tokens and the console-page grammar that
overnightworks products share: lists of things with states, facts and fields.
It refuses components, product-specific page layout, JavaScript and fonts; a
product renders through this grammar with its own markup.

Owned by agent-presentator's blessed picture `docs/mockups/m0-lobby.html`.

Distribution is one stylesheet, published as a GitHub release asset. Tags are
never moved; a broken release gets the next patch tag.

Every pull request passes the shared quality gate (`quality / verdict`, from
`overnightworks/quality`): secret scan, workflow-security scan and SonarCloud analysis of the CSS and HTML.

Pin:

```
https://github.com/overnightworks/ui-style/releases/download/v0.4.0/ui-style.css
```

Jinja and Svelte products vendor that file (do not hot-link it at runtime) and
load it before the product stylesheet.

Writing markup against it: [stylesheet reference](docs/stylesheet.md).

## Release

```sh
scripts/release v<version>
```

It tags `main`, pushes the tag and attaches `ui-style.css` as the release
asset. It refuses unless you are on a clean `main` equal to `origin/main`, the
tag is new and `gh` is logged in.
