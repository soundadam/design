# Brand marks

`src/build_vector_logos.py` (`make brand`) composes the Mexican-hat marks
from `src/wordmark-trace.svg` and writes the SVGs into `web/`. The PNG and
ICO icons in `web/` are rendered from those SVGs by hand (below).

| File | Use |
| --- | --- |
| `web/waveform.svg` | Lockup on light pages |
| `web/waveform-dark.svg` | Lockup on dark pages: same hat, light wordmark |
| `web/mark.svg` | Nine-cell cutout; keep the hole transparent |
| `web/mark-compact.svg` | Compact hat; pair with type |
| `web/mark-compact-on-blue.svg` | Tile only (touch icon) |
| `web/favicon.svg` | Tab icon: the compact hat, never the lockup (the wordmark vanishes at 16px) |
| `web/favicon.ico` | Legacy `/favicon.ico` fallback |
| `web/apple-touch-icon.png` | iOS; from compact-on-blue |
| `web/icon-192.png` | 192 PNG from the nine-cell mark (alpha hole) |

NewAPI's Logo setting points at the site's `/favicon.svg`: it applies Logo
as the tab icon and sits it next to `SystemName`, so it must not be the
lockup.

Do not put the blue hat on a black canvas. Do not sit compact-on-blue next
to the wordmark. `archive/` is the unused stroke mark.

After a geometry change, re-render the PNG / ICO icons (needs
`rsvg-convert`, `magick`, and Pillow for a PNG-compressed 256px ICO frame):

```sh
rsvg-convert -w 192 -h 192 web/mark.svg -o web/icon-192.png
rsvg-convert -w 180 -h 180 web/mark-compact-on-blue.svg -o web/apple-touch-icon.png
TMP=$(mktemp -d)
for s in 16 32 48 256; do
  rsvg-convert -w "$s" -h "$s" web/mark-compact.svg -o "$TMP/c-$s.png"
  magick -size "${s}x${s}" xc:'#ffffff' "$TMP/c-$s.png" -composite PNG32:"$TMP/w-$s.png"
done
python3 - <<PY
from pathlib import Path
from PIL import Image
tmp = Path("$TMP")
Image.open(tmp / "w-256.png").convert("RGBA").save(
    "web/favicon.ico",
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (256, 256)],
    bitmap_format="png",
)
PY
```
