.PHONY: check test brand artifact

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
