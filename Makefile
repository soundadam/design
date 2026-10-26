.PHONY: check test brand artifact fonts fonts-plex

# The local gate; CI runs the same target.
check: test artifact
	@out="$$(gofmt -l tests/)"; test -z "$$out" || { echo "gofmt needed: $$out"; exit 1; }
	@echo "check ok"

test:
	go test ./tests/

# Renders the ConfigMap a release ships, so a broken generator list fails here.
artifact:
	kubectl kustomize web >/dev/null

# Regenerates the SVG marks in web/ from brand/src/. Run after a geometry
# change, then make check.
brand:
	python3 brand/src/build_vector_logos.py

# Recuts web/noto-sans-sc-*.woff2 from NotoSansSC[wght].ttf (google/fonts,
# ofl/notosanssc): make fonts SRC=path/to/NotoSansSC[wght].ttf, then copy
# the printed unicode-range lines into web/fonts.css.
fonts:
	uv run fonts/subset.py "$(SRC)"

# Recuts web/plex-sans-*.woff2: make fonts-plex LATIN=path/to/IBMPlexSans[wdth,wght].ttf
# (google/fonts, ofl/ibmplexsans) SC=path/to/fonts/complete/woff2/hinted (npm
# @ibm/plex-sans-sc), then copy the printed unicode-range lines into web/fonts.css.
fonts-plex:
	uv run fonts/plex.py "$(LATIN)" "$(SC)"
