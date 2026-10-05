# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools[woff]==4.60.1"]
# ///
"""Cut web/noto-sans-sc-*.woff2 out of Noto Sans SC.

Source: NotoSansSC[wght].ttf from github.com/google/fonts, ofl/notosanssc
(OFL, web/OFL-NotoSansSC.txt). Run through `make fonts`.

- latin: Latin-1 and the Latin punctuation, every weight. Small enough that
  Apple devices load it while their Chinese comes from PingFang.
- han-1, han-2: the 3755 characters of GB 2312 level 1 plus Chinese
  punctuation, weights 400 to 700, split at SPLIT so each file stays well
  under a ConfigMap's 1 MiB. Rarer characters fall through to the system.

The unicode-range lines fonts.css needs are printed; paste them there.
"""

import io
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

WEB = Path(__file__).resolve().parent.parent / "web"

# Punctuation Chinese text sets full width: it comes with the Han files, so a
# Chinese sentence never mixes in a Latin quote or dash.
CJK_PUNCT = [0x00B7, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026]
LATIN = [c for c in [*range(0x20, 0x7F), *range(0xA0, 0x100), *range(0x2000, 0x2070), 0x20AC, 0x2122, 0x2212] if c not in CJK_PUNCT]
PUNCT = CJK_PUNCT + [*range(0x3000, 0x3040), *range(0xFF00, 0xFFF0)]
# The first Han file takes the punctuation and U+4E00..SPLIT-1.
SPLIT = 0x6C00


def level_one() -> list[int]:
    chars = []
    for high in range(0xB0, 0xD8):
        for low in range(0xA1, 0xFF):
            try:
                chars.append(ord(bytes([high, low]).decode("gb2312")))
            except UnicodeDecodeError:
                pass
    return chars


def cut(font: TTFont, codepoints: list[int], name: str) -> None:
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    out = WEB / f"noto-sans-sc-{name}.woff2"
    font.flavor = "woff2"
    font.save(out)
    print(f"{out.name}: {out.stat().st_size} bytes")


def ranges(codepoints: list[int]) -> str:
    spans, start, prev = [], None, None
    for c in sorted(set(codepoints)):
        if start is None:
            start = prev = c
        elif c == prev + 1:
            prev = c
        else:
            spans.append((start, prev))
            start = prev = c
    spans.append((start, prev))
    return ", ".join(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}" for a, b in spans)


def weights(source: str, low: int, high: int) -> TTFont:
    """The font limited to weights low..high, reloaded so the subsetter sees whole tables."""
    buffer = io.BytesIO()
    instancer.instantiateVariableFont(TTFont(source), {"wght": (low, high)}).save(buffer)
    buffer.seek(0)
    return TTFont(buffer)


def main(source: str) -> None:
    han = level_one()
    first = PUNCT + [c for c in han if c < SPLIT]
    second = [c for c in han if c >= SPLIT]
    cut(TTFont(source), LATIN, "latin")
    cut(weights(source, 400, 700), first, "han-1")
    cut(weights(source, 400, 700), second, "han-2")
    # unicode-range names what a file could hold, so ranges cover whole blocks
    # rather than listing each character.
    print("latin:", ranges(LATIN))
    print("han-1:", ranges(PUNCT) + f", U+4E00-{SPLIT - 1:04X}")
    print("han-2:", f"U+{SPLIT:04X}-9FFF")


if __name__ == "__main__":
    main(sys.argv[1])
