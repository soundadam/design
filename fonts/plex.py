# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools[woff]==4.60.1"]
# ///
"""Cut web/plex-sans-*.woff2 out of IBM Plex Sans and IBM Plex Sans SC.

Sources (OFL, web/OFL-IBMPlex.txt), run through `make fonts-plex`:
- LATIN: IBMPlexSans[wdth,wght].ttf from github.com/google/fonts,
  ofl/ibmplexsans.
- SC: the directory fonts/complete/woff2/hinted of the npm package
  @ibm/plex-sans-sc (1.1.0), which IBM publishes from github.com/IBM/plex.

- latin: the characters of the Noto Latin file (subset.LATIN), normal width,
  weights 400 to 600. Chinese punctuation stays out of it.
- han-400, han-600: GB 2312 level 1 and Chinese punctuation, one file a
  weight. Plex Sans SC has no variable font, so the system ships two weights
  only (tokens.css, --weight-*); each file is about 0.7 MB and gets a
  ConfigMap of its own.

The unicode-range lines fonts.css needs are printed; paste them there.
"""

import io
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# fonts/subset.py, next to this file.
from subset import LATIN, PUNCT, WEB, level_one, ranges


def cut(font: TTFont, codepoints: list[int], name: str) -> None:
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.hinting = False
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    out = WEB / f"plex-sans-{name}.woff2"
    font.flavor = "woff2"
    font.save(out)
    print(f"{out.name}: {out.stat().st_size} bytes")


def main(latin: str, sc: str) -> None:
    buffer = io.BytesIO()
    instancer.instantiateVariableFont(TTFont(latin), {"wdth": 100, "wght": (400, 600)}).save(buffer)
    buffer.seek(0)
    cut(TTFont(buffer), LATIN, "latin")
    han = PUNCT + level_one()
    for weight, style in [(400, "Regular"), (600, "SemiBold")]:
        cut(TTFont(Path(sc) / f"IBMPlexSansSC-{style}.woff2"), han, f"han-{weight}")
    print("latin:", ranges(LATIN))
    print("han:", ranges(PUNCT) + ", U+4E00-9FFF")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
