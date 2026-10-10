# soundadam design

The visual system every soundadam surface draws from: colour, type, spacing
and shape tokens (light and dark), the fonts, the marks, and the component
stylesheet for member consoles. Everything served lives flat in [`web/`](web/).

| File | What it is |
| --- | --- |
| `web/tokens.css` | All tokens. Light on `:root`; dark applies on pages that opt in |
| `web/fonts.css` | `@font-face` for Noto Sans SC (a Latin file, two Han files) and Fira Code, relative to itself; `--font-sans` prefers an installed Noto and PingFang, so most devices download only part of it |
| `web/header.css` | The top bar both sites share (see [Top bar](#top-bar)) |
| `web/console.css` | Member-console components (see [Console](#console)) |
| `web/*.woff2`, `web/OFL-*.txt` | Fonts and their licences; the Noto files are cut by `make fonts` ([fonts/subset.py](fonts/subset.py)) |
| `web/waveform.svg`, `web/waveform-dark.svg` | Lockup for light and dark pages |
| `web/mark*.svg`, `web/favicon.*`, `web/*.png` | Marks and icons ([brand/README.md](brand/README.md)) |
| `web/nav-*.svg` | Sidebar icons, drawn as CSS masks in the current text colour |
| `web/version.txt` | The release's own version; consumers check the mount against it |

## Consumers

Each consumer takes a released version at build or deploy time and serves
the files from its own origin. Nothing loads them from another host at
runtime.

| Consumer | How it takes a release |
| --- | --- |
| soundadam.com (`soundadam/www-src`) | Hugo module `github.com/soundadam/design`, version in its `go.mod`; mounts are in [hugo.toml](hugo.toml) |
| my.soundadam.com (`soundadam/platform-gitops`) | Flux `OCIRepository` on `oci://ghcr.io/soundadam/design` pinned to one tag, the same `DESIGN_VERSION` its pages carry; `web/` becomes ConfigMaps `design`, `design-han-1` and `design-han-2` ([web/kustomization.yaml](web/kustomization.yaml)), mounted together as one directory and served at `/_design/<version>/` only while `version.txt` matches |

## Dark mode

A page opts in with `<html data-theme="auto">` and then follows the system
setting. A page without the attribute stays light.

## Top bar

soundadam.com and my.soundadam.com carry the same dark, full-width bar, so a
reader moves between them from the top of any page. It is dark in both
themes, so the logo is always `waveform-dark.svg`.

```html
<header class="site-bar">
 <div class="site-header"><div class="site-header-inner">
  <div class="site-header-brand"><a class="site-logo" href="https://soundadam.com/">
    <img src="…/waveform-dark.svg" alt="soundadam" width="183" height="40"></a></div>
  <nav class="site-header-menu" aria-label="…">
   <div class="site-header-items">
    <div class="mega-item">
     <p class="mega-item__label"><a href="…/projects/">Projects</a>
      <button class="mega-item__toggle" aria-expanded="false" aria-controls="mega-projects"><span></span></button></p>
     <div class="mega-panel" id="mega-projects"><div class="mega-panel__columns">
      <div class="mega-panel__column"><p class="mega-panel__title">…</p><hr>
       <ul class="mega-panel__links"><li><a href="…">
        <span class="mega-panel__label">…</span><span class="mega-panel__desc">…</span></a></li></ul>
      </div></div></div>
    </div>
   </div>
   <div class="site-header-cta"><a href="https://my.soundadam.com/">Console</a></div>
  </nav>
  <div class="site-header-language">…</div>   <!-- or <span class="site-header-account">name …</span> -->
  <button class="hamburger" aria-expanded="false" aria-controls="…">
   <span class="hamburger-box"><span class="hamburger-inner"></span></span></button>
 </div></div>
</header>
```

The toggle buttons, panels and hamburger need a script, which the page
supplies: it adds `.is-enhanced` to `.site-header`, `.is-open` to an open
`.mega-item`, and `.is-active` to the open drawer and its hamburger. A page
without one (the consoles) leaves them out and keeps plain links; on narrow
screens those wrap onto a second row. A current section's link carries
`aria-current`.

## Console

Load the stylesheets in order, then build the page from the [top bar](#top-bar)
and these blocks:

```html
<html lang="zh-CN" data-theme="auto">
<link rel="stylesheet" href="/_design/3.0.0/fonts.css">
<link rel="stylesheet" href="/_design/3.0.0/tokens.css">
<link rel="stylesheet" href="/_design/3.0.0/header.css">
<link rel="stylesheet" href="/_design/3.0.0/console.css">

<header class="site-bar">…</header>
<main class="console">
  <section><h2>…</h2> … </section>
</main>
<footer class="console-footer"><p>…</p></footer>
```

| Block | Classes |
| --- | --- |
| Section (flat: a heading and a hairline, no card) | `section`, `h2`, `.hint` (`.hint.lead` above content), `.notice` (`.notice.ok` for a success receipt) |
| Status | `.pill.ok` / `.warn` / `.bad` / `.muted`; `.dot`, `.dot.on` |
| Figures | `.tiles` > `.tile[.ok\|.warn\|.bad\|.muted]` > `.label`, `.figure`, `.meter > span`, `.caption`; `.status-line` |
| Product links | `ul.products > li > a > b + small` |
| Segmented control | `.segmented > a[aria-current]`, `> button[aria-pressed]`, or `> label > input[type=radio]` in a form: two to five short exclusive options, equal width, applied on click |
| Tabs | `.tabset > .segmented > label > input[type=radio]`, then `.panel` × n (up to five; order pairs them) |
| Glance panel | `section.glance > .glance-bar > .segmented.glance-view + .segmented.glance-range` (radios), then `.glance-pane` × ranges, each holding `.glance-page` × views (up to five of each; order pairs them). A framed panel embedded from another service; no script switches it |
| Heatmap | `.heat > i[data-level=0–4]`, one column a week with Monday on top; `.out` greys a day outside the chosen range, `.none` marks a day with no record |
| Breakdown | `ul.breakdown > li.series-N > .swatch + span(name) + small(detail) + b(share)` |
| Placeholder | `.pending[aria-busy=true] > span × 3–4` where slow content will go; it shows after 0.2 s and hides once a sibling follows it, so the server can stream the page and write the content after it |
| Code and fields | `pre`, `.row > input + .button` |
| Buttons | `.button`, `.button.secondary`, `.button.danger`; `.button.compact` sizes one to its content for table rows; `.actions` wraps a lone one |
| Form fields | `.fields > label.field > span + input\|select` (`.field.wide` spans the row) |
| Toggles | `.toggles > label.toggle > input[type=checkbox] + span`: pick several short options inline; `.inline` lines up toggles and buttons |
| Lists | `ul.list > li` (last child is the muted value), `ul.chips > li` |
| Options | `.options > label.option > input[type=radio] + span > b + small`: exclusive options that need a line of explanation; the checked one carries a checkmark, and the page applies it on change |
| Chart | `svg.chart` of `rect`s, then `.axis > span × 2`; `.qr` holds an SVG code |
| Stacked chart | `svg.chart.stacked` of `rect.series-N` (N = 1–6, 6 is「其他」), `ul.legend > li.series-N > .swatch` |
| Table | `.table-wrap > table.data`, `.num` on number cells, `.share > span` as a share bar (takes `.series-N`) |
| Sidebar | `.console-shell > nav.console-sidebar + main.console`. The nav holds `input#side-toggle.side-toggle`, then `label.side-bar[for=side-toggle]` (`i.nav-icon.nav-menu`, a `span` naming the current page, `i.nav-icon.nav-chevron`), then `.side-list` with `a` (概览, led by `i.nav-icon.nav-grid`) and `.side-group > span.side-title(i.nav-icon.nav-<icon> + name) + a…`; a link to another site ends with `i.nav-icon.nav-external`; current link `aria-current="page"`, icons `aria-hidden="true"`. Wide screens show the list as a column and hide the bar; narrow screens show the bar and open the list when the box is checked. On wide screens the sidebar sits against the window's left edge at full height, the top bar's contents span the window, and every page's content container has the same width, so neither the sidebar nor the title moves between pages. A `.console-footer` goes inside `main`. A plain page's content uses `--console-width` at the container's left; `.console-shell.wide` lets a dashboard use the whole container |

Motion: the blocks in `main` fade up one after another on load, and a
same-origin navigation keeps the top bar and sidebar in place while only
the content cross-fades (`@view-transition`, Chrome and Safari 18). Both
are off under `prefers-reduced-motion`.

## Releases

A tag `vX.Y.Z` on `main` publishes `web/`
([.github/workflows/release.yml](.github/workflows/release.yml)); set
`web/version.txt` to `X.Y.Z` in the same change, or the release stops.
Consumers pin one version, so a release reaches production only when
platform-gitops moves its pin together with the pages that use it.

- **Major** when a consumer's page could break: a token, class, or file is
  removed or renamed, or the console markup changes shape.
- **Minor** for new tokens, classes, or files.
- **Patch** for value changes.

## Checks

```sh
make check   # tests (declared variables, contrast in both themes, artifact file list), gofmt, kustomize render
make brand   # regenerate the SVG marks from brand/src/
```
