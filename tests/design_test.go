// Package tests checks web/ as its consumers read it: the variables the
// stylesheets use, the colours each theme resolves to, and the file list
// the cluster artifact carries.
package tests

import (
	"math"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"testing"
)

const web = "../web"

var (
	comment     = regexp.MustCompile(`(?s)/\*.*?\*/`)
	declaration = regexp.MustCompile(`(?s)--([a-z0-9-]+)\s*:\s*(.*?);`)
	varUse      = regexp.MustCompile(`var\(--([a-z0-9-]+)\)`)
	colorLit    = regexp.MustCompile(`#[0-9a-fA-F]{3,8}\b|rgba?\(`)
	cssURL      = regexp.MustCompile(`url\("([^"]+)"\)`)
	hexColor    = regexp.MustCompile(`^#([0-9a-fA-F]{6})$`)
	varOnly     = regexp.MustCompile(`^var\(--([a-z0-9-]+)\)$`)
)

func read(t *testing.T, name string) string {
	t.Helper()
	b, err := os.ReadFile(filepath.Join(web, name))
	if err != nil {
		t.Fatal(err)
	}
	return comment.ReplaceAllString(string(b), "")
}

// themes returns the light declarations (the first :root block) and the
// dark overrides (the block inside the prefers-color-scheme query).
func themes(t *testing.T) (light, dark map[string]string) {
	t.Helper()
	css := read(t, "tokens.css")
	split := strings.Index(css, "@media (prefers-color-scheme: dark)")
	if split < 0 {
		t.Fatal("tokens.css has no dark block")
	}
	parse := func(block string) map[string]string {
		out := map[string]string{}
		for _, m := range declaration.FindAllStringSubmatch(block, -1) {
			out[m[1]] = strings.Join(strings.Fields(m[2]), " ")
		}
		return out
	}
	return parse(css[:split]), parse(css[split:])
}

func stylesheets(t *testing.T) []string {
	t.Helper()
	names, err := filepath.Glob(filepath.Join(web, "*.css"))
	if err != nil || len(names) == 0 {
		t.Fatalf("no stylesheets in %s: %v", web, err)
	}
	for i, n := range names {
		names[i] = filepath.Base(n)
	}
	return names
}

func TestEveryVariableIsDeclared(t *testing.T) {
	light, _ := themes(t)
	for _, name := range stylesheets(t) {
		for _, m := range varUse.FindAllStringSubmatch(read(t, name), -1) {
			if _, ok := light[m[1]]; !ok {
				t.Errorf("%s uses --%s, which tokens.css does not declare", name, m[1])
			}
		}
	}
}

// A dark override with a misspelt name silently does nothing.
func TestDarkOverridesDeclaredTokens(t *testing.T) {
	light, dark := themes(t)
	for name := range dark {
		if _, ok := light[name]; !ok && name != "" {
			t.Errorf("dark block sets --%s, which the light block does not declare", name)
		}
	}
}

func TestColoursOnlyInTokens(t *testing.T) {
	for _, name := range stylesheets(t) {
		if name == "tokens.css" {
			continue
		}
		if lit := colorLit.FindString(read(t, name)); lit != "" {
			t.Errorf("%s writes colour %q; declare a token in tokens.css", name, lit)
		}
	}
}

func resolve(t *testing.T, theme map[string]string, name string) (r, g, b float64) {
	t.Helper()
	value := theme[name]
	for range 8 {
		m := varOnly.FindStringSubmatch(value)
		if m == nil {
			break
		}
		value = theme[m[1]]
	}
	m := hexColor.FindStringSubmatch(value)
	if m == nil {
		t.Fatalf("--%s resolves to %q, not a #rrggbb colour", name, value)
	}
	n, _ := strconv.ParseUint(m[1], 16, 32)
	return float64(n>>16) / 255, float64(n>>8&0xff) / 255, float64(n&0xff) / 255
}

func luminance(r, g, b float64) float64 {
	lin := func(c float64) float64 {
		if c <= 0.04045 {
			return c / 12.92
		}
		return math.Pow((c+0.055)/1.055, 2.4)
	}
	return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)
}

func contrast(t *testing.T, theme map[string]string, fg, bg string) float64 {
	a := luminance(resolve(t, theme, fg))
	b := luminance(resolve(t, theme, bg))
	return (math.Max(a, b) + 0.05) / (math.Min(a, b) + 0.05)
}

// Text/background pairs the components put together, held to WCAG AA
// (4.5:1) in both themes.
func TestTextContrast(t *testing.T) {
	pairs := [][2]string{
		{"color-contrast", "color-base"},
		{"color-contrast", "color-canvas"},
		{"color-contrast", "color-surface-muted"},
		{"color-muted", "color-surface"},
		{"color-muted", "color-surface-muted"},
		{"color-muted", "color-canvas"},
		{"color-link", "color-surface"},
		{"color-link", "color-accent-surface"},
		{"color-contrast", "color-accent-surface"},
		{"color-on-cta", "color-cta"},
		{"color-on-cta", "color-cta-hover"},
		{"color-ok", "color-ok-surface"},
		{"color-warn", "color-warn-surface"},
		{"color-bad", "color-bad-surface"},
		{"color-ok", "color-surface-muted"},
		{"color-warn", "color-surface-muted"},
		{"color-bad", "color-surface-muted"},
		{"color-bad", "color-surface"},
	}
	light, dark := themes(t)
	merged := map[string]string{}
	for k, v := range light {
		merged[k] = v
	}
	for k, v := range dark {
		merged[k] = v
	}
	for _, theme := range []struct {
		name   string
		values map[string]string
	}{{"light", light}, {"dark", merged}} {
		for _, p := range pairs {
			if c := contrast(t, theme.values, p[0], p[1]); c < 4.5 {
				t.Errorf("%s: --%s on --%s is %.2f:1, below 4.5:1", theme.name, p[0], p[1], c)
			}
		}
	}
}

// The cluster gets exactly the files the ConfigMap generator lists; a file
// added to web/ without a line there would be missing from every console.
func TestArtifactCarriesEveryFile(t *testing.T) {
	b, err := os.ReadFile(filepath.Join(web, "kustomization.yaml"))
	if err != nil {
		t.Fatal(err)
	}
	var listed []string
	for _, line := range strings.Split(string(b), "\n") {
		if item, ok := strings.CutPrefix(line, "      - "); ok {
			listed = append(listed, strings.TrimSpace(item))
		}
	}
	entries, err := os.ReadDir(web)
	if err != nil {
		t.Fatal(err)
	}
	var present []string
	for _, e := range entries {
		if !e.IsDir() && e.Name() != "kustomization.yaml" {
			present = append(present, e.Name())
		}
	}
	slices.Sort(listed)
	slices.Sort(present)
	if !slices.Equal(listed, present) {
		t.Errorf("web/kustomization.yaml lists %v\nweb/ holds %v", listed, present)
	}
}

func TestURLsResolve(t *testing.T) {
	for _, name := range stylesheets(t) {
		for _, m := range cssURL.FindAllStringSubmatch(read(t, name), -1) {
			if _, err := os.Stat(filepath.Join(web, m[1])); err != nil {
				t.Errorf("%s points at %s: %v", name, m[1], err)
			}
		}
	}
}

// version.txt names the release it ships in; consumers serve web/ under
// that version and refuse a mount that says otherwise. The release workflow
// checks it against the tag.
func TestVersionFile(t *testing.T) {
	b, err := os.ReadFile(filepath.Join(web, "version.txt"))
	if err != nil {
		t.Fatal(err)
	}
	if !regexp.MustCompile(`^[0-9]+\.[0-9]+\.[0-9]+\n$`).Match(b) {
		t.Errorf("version.txt is %q, want X.Y.Z and a newline", b)
	}
}
