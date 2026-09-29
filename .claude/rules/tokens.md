# Values live in tokens.css; releases are a contract

**A colour is written only in `web/tokens.css`.** Other stylesheets use
`var(--…)`. `make check` fails on a colour literal elsewhere, on an
undeclared variable, on a dark override with no light declaration, and on a
text pair below 4.5:1 in either theme — extend the pair list in
`tests/design_test.go` when a component puts a new text colour on a new
background.

**Every new colour token gets a dark value or a reason it needs none.**
The dark block overrides colours and shadows only; sizes and spacing are
shared. `--color-paper` stays white on purpose.

**A change is checked on its consumers, not only here.** Changing a value
changes soundadam.com and every console on the next release. Look at both
in light and dark (www-src: both languages, both breakpoints) before
tagging.

**Pick the version by what a consumer's page could lose.** The cluster
follows `1.x` without review, so removing or renaming a token, class, or
file, or changing console markup, is a major release. See README.md.

**Nothing is loaded across origins at runtime.** A consumer takes a
release at build or deploy time and serves `web/` itself; do not add a
consumer that links this repository's files from another host.
