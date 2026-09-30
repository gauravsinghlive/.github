"""
generate_terminal.py
====================

Generates:

    terminal-card.svg

Features:
    • Fetches Gaurav Singh's GitHub avatar
    • Converts the avatar into ASCII art
    • Row-by-row left → right reveal animation
    • Animated white cursor block
    • macOS-style terminal chrome
    • GitHub-style dark theme
    • Footer with whoami command

GitHub:
    https://github.com/gauravsingh7x

Run:
    pip install Pillow
    python generate_terminal.py
"""

import sys
import os
import html as _html

from urllib.request import urlopen, Request
from io import BytesIO


# ==============================================================================
# CONFIGURATION
# ==============================================================================

USERNAME = "gauravsingh7x"

DISPLAY_NAME = "Gaurav Singh"

ROLE = "Full Stack Developer · Open Source Enthusiast"


# ==============================================================================
# HELPERS
# ==============================================================================

def xe(value):
    """
    Escape text so it is safe inside SVG/XML.
    """
    return _html.escape(str(value), quote=True)


OUT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ==============================================================================
# FETCH GITHUB AVATAR
# ==============================================================================

print("[..] Fetching GitHub avatar ...")

try:

    avatar_url = (
        f"https://avatars.githubusercontent.com/"
        f"{USERNAME}?size=400"
    )

    request = Request(
        avatar_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    img_bytes = urlopen(
        request,
        timeout=20
    ).read()

    print(
        f"[OK] Avatar fetched "
        f"({len(img_bytes):,} bytes)"
    )

except Exception as error:

    sys.exit(
        f"[ERR] Avatar fetch failed: {error}"
    )


# ==============================================================================
# PILLOW
# ==============================================================================

try:

    from PIL import Image

except ImportError:

    sys.exit(
        "[ERR] Pillow is not installed.\n"
        "Run:\n\n"
        "    pip install Pillow"
    )


# ==============================================================================
# ASCII CONFIGURATION
# ==============================================================================

# Bright pixels → light characters
# Dark pixels   → dense characters

ASCII_CHARS = "  `.-':=+*csS%#@"


# Width and height of the ASCII portrait.

ART_W = 100
ART_H = 53


# ==============================================================================
# CONVERT AVATAR → GRAYSCALE
# ==============================================================================

print("[..] Converting avatar to ASCII ...")


image = Image.open(
    BytesIO(img_bytes)
).convert("L")


# Resize avatar to ASCII dimensions.

image = image.resize(
    (ART_W, ART_H),
    Image.LANCZOS
)


pixels = list(
    image.getdata()
)


# ==============================================================================
# GENERATE ASCII ROWS
# ==============================================================================

rows = []


for row_index in range(ART_H):

    row = ""

    for column_index in range(ART_W):

        pixel = pixels[
            row_index * ART_W
            + column_index
        ]

        # Invert brightness:
        #
        # white pixel → space
        # black pixel → @

        index = int(
            (255 - pixel)
            / 255
            * (len(ASCII_CHARS) - 1)
        )

        row += ASCII_CHARS[index]

    rows.append(row)


print(
    f"[OK] ASCII portrait generated "
    f"({ART_W} × {ART_H})"
)


# ==============================================================================
# SVG LAYOUT
# ==============================================================================

WIDTH = 840

ROW_HEIGHT = 15

ROW_Y_START = 37

FONT_SIZE = 12.9

ROW_DURATION = 0.11

TEXT_WIDTH = 800

TEXT_X = 20


# Footer position.

FOOTER_LINE_Y = (
    ROW_Y_START
    + ART_H * ROW_HEIGHT
)

FOOTER_TEXT_Y = (
    FOOTER_LINE_Y
    + 19
)

HEIGHT = (
    FOOTER_LINE_Y
    + 43
)


# ==============================================================================
# FOOTER
# ==============================================================================

WHOAMI_TEXT = (
    f"{USERNAME}@github:~$ whoami "
)


# Approximate monospace character width.

CURSOR_X = (
    TEXT_X
    + len(WHOAMI_TEXT) * 7.73
)


# ==============================================================================
# GENERATE ASCII ROW SVG
# ==============================================================================

rows_svg = ""


for index, row in enumerate(rows):

    # Each row starts slightly after the previous row.

    begin_time = (
        index * ROW_DURATION
    )

    y_top = (
        ROW_Y_START
        + index * ROW_HEIGHT
    )

    y_text = (
        y_top + 11.1
    )

    safe_row = xe(row)


    # --------------------------------------------------------------------------
    # Row clipping animation
    # --------------------------------------------------------------------------

    rows_svg += (
        f'<clipPath id="row{index}">'
        f'<rect '
        f'x="{TEXT_X}" '
        f'y="{y_top:.1f}" '
        f'height="{ROW_HEIGHT}" '
        f'width="0">'
        f'<animate '
        f'attributeName="width" '
        f'from="0" '
        f'to="{TEXT_WIDTH}" '
        f'begin="{begin_time:.3f}s" '
        f'dur="{ROW_DURATION}s" '
        f'fill="freeze"/>'
        f'</rect>'
        f'</clipPath>\n'
    )


    # --------------------------------------------------------------------------
    # ASCII row
    # --------------------------------------------------------------------------

    rows_svg += (
        f'<g clip-path="url(#row{index})">'
        f'<text '
        f'xml:space="preserve" '
        f'x="{TEXT_X}" '
        f'y="{y_text:.1f}" '
        f'fill="#c9d1d9" '
        f'font-size="{FONT_SIZE}" '
        f'textLength="{TEXT_WIDTH}" '
        f'lengthAdjust="spacing">'
        f'{safe_row}'
        f'</text>'
        f'</g>\n'
    )


    # --------------------------------------------------------------------------
    # Animated cursor
    # --------------------------------------------------------------------------

    rows_svg += (
        f'<rect '
        f'y="{y_top + 1:.1f}" '
        f'width="8" '
        f'height="13" '
        f'fill="#c9d1d9" '
        f'opacity="0">'

        f'<animate '
        f'attributeName="x" '
        f'from="{TEXT_X}" '
        f'to="{TEXT_X + TEXT_WIDTH}" '
        f'begin="{begin_time:.3f}s" '
        f'dur="{ROW_DURATION}s" '
        f'fill="freeze"/>'

        f'<set '
        f'attributeName="opacity" '
        f'to="0.85" '
        f'begin="{begin_time:.3f}s"/>'

        f'<set '
        f'attributeName="opacity" '
        f'to="0" '
        f'begin="{begin_time + ROW_DURATION:.3f}s"/>'

        f'</rect>\n'
    )


# ==============================================================================
# BUILD TERMINAL SVG
# ==============================================================================

svg = f"""<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}"
font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">

<defs>

  <!-- Terminal background -->

  <linearGradient
    id="terminal-bg"
    x1="0"
    y1="0"
    x2="0"
    y2="1">

    <stop
      offset="0"
      stop-color="#111722"/>

    <stop
      offset="1"
      stop-color="#0d1117"/>

  </linearGradient>

</defs>


<!-- ====================================================================== -->
<!-- Terminal background -->
<!-- ====================================================================== -->

<rect
  width="{WIDTH}"
  height="{HEIGHT}"
  rx="12"
  fill="url(#terminal-bg)"/>


<!-- ====================================================================== -->
<!-- Terminal border -->
<!-- ====================================================================== -->

<rect
  x="0.5"
  y="0.5"
  width="{WIDTH - 1}"
  height="{HEIGHT - 1}"
  rx="12"
  fill="none"
  stroke="#30363d"
  stroke-width="1"/>


<!-- ====================================================================== -->
<!-- Terminal header divider -->
<!-- ====================================================================== -->

<line
  x1="0"
  y1="30"
  x2="{WIDTH}"
  y2="30"
  stroke="#30363d"/>


<!-- ====================================================================== -->
<!-- macOS buttons -->
<!-- ====================================================================== -->

<circle
  cx="20"
  cy="15"
  r="5"
  fill="#ff5f56"/>

<circle
  cx="36"
  cy="15"
  r="5"
  fill="#ffbd2e"/>

<circle
  cx="52"
  cy="15"
  r="5"
  fill="#27c93f"/>


<!-- ====================================================================== -->
<!-- Terminal title -->
<!-- ====================================================================== -->

<text
  x="{WIDTH / 2:.1f}"
  y="19"
  fill="#7d8590"
  font-size="12"
  text-anchor="middle">

  {xe(USERNAME)}@github: ~$ ./portrait.sh

</text>


<!-- ====================================================================== -->
<!-- ASCII PORTRAIT -->
<!-- ====================================================================== -->

{rows_svg}


<!-- ====================================================================== -->
<!-- Footer divider -->
<!-- ====================================================================== -->

<line
  x1="0"
  y1="{FOOTER_LINE_Y:.1f}"
  x2="{WIDTH}"
  y2="{FOOTER_LINE_Y:.1f}"
  stroke="#30363d"/>


<!-- ====================================================================== -->
<!-- Footer whoami -->
<!-- ====================================================================== -->

<text
  x="20"
  y="{FOOTER_TEXT_Y:.1f}"
  fill="#7d8590"
  font-size="13">

  {xe(USERNAME)}@github:~$ whoami

  <tspan fill="#c9d1d9">
    {xe(DISPLAY_NAME)}
  </tspan>

</text>


<!-- ====================================================================== -->
<!-- Footer blinking cursor -->
<!-- ====================================================================== -->

<rect
  x="{CURSOR_X:.0f}"
  y="{FOOTER_TEXT_Y - 13:.1f}"
  width="8"
  height="14"
  fill="#c9d1d9">

  <animate
    attributeName="opacity"
    values="1;1;0;0"
    keyTimes="0;0.5;0.51;1"
    dur="1s"
    repeatCount="indefinite"/>

</rect>


</svg>
"""


# ==============================================================================
# WRITE FILE
# ==============================================================================

output_file = os.path.join(
    OUT_DIR,
    "terminal-card.svg"
)


with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(svg)


# ==============================================================================
# RESULT
# ==============================================================================

file_size = (
    os.path.getsize(output_file)
    // 1024
)


print()
print(
    "[OK] terminal-card.svg generated"
)

print(
    f"     Size: {WIDTH} × {HEIGHT}px"
)

print(
    f"     File: {file_size} KB"
)

print(
    f"     User: {DISPLAY_NAME}"
)

print(
    f"     GitHub: @{USERNAME}"
)

print()
print("Done!")
