# soundadam design

The visual system every soundadam surface draws from: colour, type, spacing
and shape tokens (light and dark), the fonts, the marks, and the component
stylesheet for member consoles. Everything served lives flat in [`web/`](web/).

| File | What it is |
| --- | --- |
| `web/tokens.css` | All tokens. Light on `:root`; dark applies on pages that opt in |
| `web/fonts.css` | `@font-face` for Manrope and Fira Code, relative to itself |
| `web/console.css` | Member-console components (see [Console](#console)) |
| `web/*.woff2`, `web/OFL-*.txt` | Fonts and their licences |
| `web/waveform.svg`, `web/waveform-dark.svg` | Lockup for light and dark pages |
| `web/mark*.svg`, `web/favicon.*`, `web/*.png` | Marks and icons ([brand/README.md](brand/README.md)) |

## Consumers

Each consumer takes a released version at build or deploy time and serves
the files from its own origin. Nothing loads them from another host at
runtime.

| Consumer | How it takes a release |
| --- | --- |
| soundadam.com (`soundadam/www-src`) | Hugo module `github.com/soundadam/design`, version in its `go.mod`; mounts are in [hugo.toml](hugo.toml) |
| my.soundadam.com (`soundadam/platform-gitops`) | Flux `OCIRepository` on `oci://ghcr.io/soundadam/design`, semver `1.x`; `web/` becomes ConfigMap `design` ([web/kustomization.yaml](web/kustomization.yaml)), served at `/_design/` |

## Dark mode

A page opts in with `<html data-theme="auto">` and then follows the system
setting. A page without the attribute stays light.

## Console

Load the three stylesheets in order, then build the page from these blocks:

```html
<html lang="zh-CN" data-theme="auto">
<link rel="stylesheet" href="/_design/fonts.css">
<link rel="stylesheet" href="/_design/tokens.css">
<link rel="stylesheet" href="/_design/console.css">

<header class="console-header"><div class="console-header-inner">
  <a class="console-brand" href="/"><picture>
    <source srcset="/_design/waveform-dark.svg" media="(prefers-color-scheme: dark)">
    <img src="/_design/waveform.svg" alt="soundadam" width="183" height="40">
  </picture></a>
  <nav class="console-nav"><a href="/" aria-current="page">概览</a>…</nav>
  <span class="who">name <span class="pill ok">正常</span></span>
</div></header>
<main class="console">
  <section><h2>…</h2> … </section>
</main>
<footer class="console-footer"><p>…</p></footer>
```

| Block | Classes |
| --- | --- |
| Card | `section`, `h2`, `.hint` (`.hint.lead` above content), `.notice` |
| Status | `.pill.ok` / `.warn` / `.bad`; `.dot`, `.dot.on` |
| Figures | `.tiles` > `.tile[.ok\|.warn\|.bad]` > `.label`, `.figure`, `.meter > span`, `.caption`; `.status-line` |
| Product links | `ul.products > li > a > b + small` |
| Tabs | `.tabset` > radios, `.tabs` > labels, `.panel` × n (up to four; order pairs them) |
| Code and fields | `pre`, `.row > input + .button` |
| Buttons | `.button`, `.button.secondary`, `.button.danger`; `.actions` wraps a lone one |
| Lists | `ul.list > li` (last child is the muted value), `ul.chips > li` |
| Choices | `.choices > label.choice > input + span > b + small` |
| Chart | `svg.chart` of `rect`s, then `.axis > span × 2`; `.qr` holds an SVG code |
| Stacked chart | `svg.chart.stacked` of `rect.series-N` (N = 1–6, 6 is「其他」), `ul.legend > li.series-N > .swatch` |
| Table | `.table-wrap > table.data`, `.num` on number cells, `.share > span` as a share bar (takes `.series-N`) |
| Sidebar | `.console-shell > nav.console-sidebar + main.console`; the nav holds `a` and `.side-group > .side-title + a…`, current link `aria-current="page"`; the header then spans the shell, and a `.console-footer` goes inside `main` |

## Releases

A tag `vX.Y.Z` on `main` publishes `web/`
([.github/workflows/release.yml](.github/workflows/release.yml)). The
cluster follows `1.x`, so a minor or patch release reaches production when
Flux next polls.

- **Major** when a consumer's page could break: a token, class, or file is
  removed or renamed, or the console markup changes shape.
- **Minor** for new tokens, classes, or files.
- **Patch** for value changes.

## Checks

```sh
make check   # tests (declared variables, contrast in both themes, artifact file list), gofmt, kustomize render
make brand   # regenerate the SVG marks from brand/src/
```
