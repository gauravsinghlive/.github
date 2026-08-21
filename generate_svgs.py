import json
import os
import urllib.request
import urllib.error


# ==============================================================================
# Configuration
# ==============================================================================

GITHUB_USERNAME = "gauravsingh7x"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# GitHub-style contribution colors
COLORS = [
    "#161b22",  # Level 0
    "#0e4429",  # Level 1
    "#006d32",  # Level 2
    "#26a641",  # Level 3
    "#39d353",  # Level 4
]

# Near-white green flash used during reveal
GLOW = [
    "#21262d",
    "#3dffa0",
    "#57ffb0",
    "#8dffcc",
    "#c8ffe8",
]


# ==============================================================================
# Graph configuration
# ==============================================================================

SQ = 11
GAP = 3
STEP = SQ + GAP

GRAPH_X = 34
GRAPH_Y = 28

WEEKS = 53
DAYS = 7

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


# ==============================================================================
# GitHub GraphQL query
# ==============================================================================

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name

    contributionsCollection {
      contributionCalendar {
        totalContributions

        months {
          name
          firstDay
          totalWeeks
          year
        }

        weeks {
          firstDay

          contributionDays {
            date
            contributionCount
            contributionLevel
            weekday
          }
        }
      }
    }
  }
}
"""


# ==============================================================================
# GitHub API
# ==============================================================================

def fetch_contributions():
    """
    Fetch the user's real GitHub contribution calendar.

    GitHub returns:
      - contributionCount
      - contributionLevel
      - date
      - weekday
      - weeks
      - months
      - totalContributions
    """

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is missing."
        )

    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "login": GITHUB_USERNAME
        },
    }

    request = urllib.request.Request(
        GITHUB_GRAPHQL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "gauravsingh7x-profile-generator",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        body = error.read().decode("utf-8", errors="replace")

        raise RuntimeError(
            f"GitHub API request failed "
            f"({error.code}): {body}"
        ) from error

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Unable to reach GitHub API: {error.reason}"
        ) from error

    # --------------------------------------------------------------------------
    # GraphQL errors
    # --------------------------------------------------------------------------

    if data.get("errors"):

        raise RuntimeError(
            "GitHub GraphQL error:\n"
            + json.dumps(
                data["errors"],
                indent=2,
            )
        )

    user = data.get("data", {}).get("user")

    if not user:

        raise RuntimeError(
            f"GitHub user '{GITHUB_USERNAME}' was not found."
        )

    calendar = (
        user
        .get("contributionsCollection", {})
        .get("contributionCalendar")
    )

    if not calendar:

        raise RuntimeError(
            "GitHub contribution calendar was not returned."
        )

    return user, calendar


# ==============================================================================
# Contribution level conversion
# ==============================================================================

def contribution_level(day):
    """
    Convert GitHub's contributionLevel enum into 0-4.

    GitHub normally returns:

        NONE
        FIRST_QUARTILE
        SECOND_QUARTILE
        THIRD_QUARTILE
        FOURTH_QUARTILE
    """

    level = day.get("contributionLevel", "NONE")

    mapping = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }

    return mapping.get(level, 0)


# ==============================================================================
# Flatten GitHub contribution weeks
# ==============================================================================

def flatten_contributions(calendar):
    """
    Convert GitHub's nested week/day structure into a list.

    Returns:

        [
            {
                "date": "...",
                "count": 5,
                "level": 2,
                "weekday": 3
            },
            ...
        ]
    """

    days = []

    for week in calendar.get("weeks", []):

        for day in week.get(
            "contributionDays",
            [],
        ):

            days.append(
                {
                    "date": day["date"],
                    "count": day["contributionCount"],
                    "level": contribution_level(day),
                    "weekday": day["weekday"],
                }
            )

    return days


# ==============================================================================
# Build contribution SVG
# ==============================================================================

def build_contrib(calendar):

    W = 850
    H = 165

    lines = []

    # --------------------------------------------------------------------------
    # SVG
    # --------------------------------------------------------------------------

    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">'
    )

    lines.append("<defs>")

    # --------------------------------------------------------------------------
    # Cell glow
    # --------------------------------------------------------------------------

    lines.append(
        '<filter id="cellglow" '
        'x="-70%" y="-70%" '
        'width="240%" height="240%">'

        '<feGaussianBlur '
        'stdDeviation="2" '
        'result="blur"/>'

        '<feMerge>'

        '<feMergeNode in="blur"/>'

        '<feMergeNode in="SourceGraphic"/>'

        '</feMerge>'

        '</filter>'
    )

    lines.append("</defs>")

    # --------------------------------------------------------------------------
    # Card background
    # --------------------------------------------------------------------------

    lines.append(
        f'<rect width="{W}" height="{H}" '
        'rx="16" '
        'fill="#0d1117" '
        'stroke="#30363d" '
        'stroke-width="1"/>'
    )

    # ==========================================================================
    # GitHub contribution weeks
    # ==========================================================================

    weeks = calendar.get("weeks", [])

    # GitHub normally returns approximately one year's worth of weeks.
    # We render the latest 53 weeks so the visual stays within the original
    # dimensions.
    weeks = weeks[-WEEKS:]

    # --------------------------------------------------------------------------
    # Month labels
    # --------------------------------------------------------------------------

    month_positions = {}

    for index, week in enumerate(weeks):

        first_day = week.get("firstDay", "")

        if len(first_day) >= 7:

            month_key = first_day[:7]

            if month_key not in month_positions:

                month_positions[month_key] = index

    for month_key, week_index in month_positions.items():

        try:
            month_number = int(
                month_key.split("-")[1]
            )

            month_name = MONTHS[
                month_number - 1
            ]

        except (ValueError, IndexError):

            continue

        x = (
            GRAPH_X
            + week_index * STEP
        )

        lines.append(
            f'<text x="{x}" y="18" '
            'fill="#8b949e" '
            'font-size="10" '
            'font-family="system-ui,sans-serif">'
            f'{month_name}'
            '</text>'
        )

    # --------------------------------------------------------------------------
    # Weekday labels
    # --------------------------------------------------------------------------

    for row, label in enumerate(
        [
            "Mon",
            "",
            "Wed",
            "",
            "Fri",
            "",
            "",
        ]
    ):

        if label:

            y = (
                GRAPH_Y
                + row * STEP
                + SQ
                - 1
            )

            lines.append(
                f'<text x="0" y="{y}" '
                'fill="#8b949e" '
                'font-size="9" '
                'font-family="system-ui,sans-serif">'
                f'{label}'
                '</text>'
            )

    # ==========================================================================
    # Animation
    # ==========================================================================

    anim_dur = 4.5
    pause = 2.5
    total = anim_dur + pause

    # Lower = steeper diagonal.
    SLANT = 0.6

    max_diag = (
        max(len(weeks) - 1, 1)
        + (DAYS - 1) * SLANT
    )

    # ==========================================================================
    # Render contribution cells
    # ==========================================================================

    for col, week in enumerate(weeks):

        contribution_days = week.get(
            "contributionDays",
            [],
        )

        # Map GitHub weekday to row.
        #
        # GitHub:
        #   0 = Sunday
        #   1 = Monday
        #   ...
        #   6 = Saturday
        #
        # Our graph:
        #   0 = Monday
        #   ...
        #   6 = Sunday

        day_by_row = {}

        for day in contribution_days:

            github_weekday = day.get(
                "weekday",
                0,
            )

            if github_weekday == 0:
                row = 6
            else:
                row = github_weekday - 1

            day_by_row[row] = day

        # ----------------------------------------------------------------------
        # Every row in the week
        # ----------------------------------------------------------------------

        for row in range(DAYS):

            day = day_by_row.get(row)

            if not day:
                continue

            level = contribution_level(day)

            count = day.get(
                "contributionCount",
                0,
            )

            color = COLORS[level]
            glow = GLOW[level]

            x = GRAPH_X + col * STEP
            y = GRAPH_Y + row * STEP

            square_id = (
                f"s{col}_{row}"
            )

            # ------------------------------------------------------------------
            # Diagonal reveal
            # ------------------------------------------------------------------

            diag = (
                col
                + row * SLANT
            )

            reveal_time = (
                diag
                / max_diag
            ) * anim_dur

            t0 = reveal_time / total

            # Brief glint
            t1 = min(
                t0 + 0.012,
                0.97,
            )

            t2 = min(
                t0 + 0.05,
                0.99,
            )

            # ------------------------------------------------------------------
            # Glow for high contribution levels
            # ------------------------------------------------------------------

            filter_attribute = (
                ' filter="url(#cellglow)"'
                if level >= 3
                else ""
            )

            # ------------------------------------------------------------------
            # Contribution cell
            # ------------------------------------------------------------------

            lines.append(
                f'<rect id="{square_id}" '
                f'x="{x}" y="{y}" '
                f'width="{SQ}" '
                f'height="{SQ}" '
                'rx="2" '
                f'fill="{color}" '
                'opacity="0"'
                f'{filter_attribute}>'
            )

            # ------------------------------------------------------------------
            # Fade-in
            # ------------------------------------------------------------------

            lines.append(
                '<animate '
                'attributeName="opacity" '
                'values="0;0;1;1" '
                f'keyTimes="0;{t0:.4f};'
                f'{t1:.4f};1" '
                f'dur="{total}s" '
                'repeatCount="indefinite"/>'
            )

            # ------------------------------------------------------------------
            # Shine
            # ------------------------------------------------------------------

            if level > 0:

                lines.append(
                    '<animate '
                    'attributeName="fill" '
                    f'values="{color};{color};'
                    f'{glow};{color}" '
                    f'keyTimes="0;{t0:.4f};'
                    f'{t1:.4f};{t2:.4f}" '
                    f'dur="{total}s" '
                    'repeatCount="indefinite" '
                    'calcMode="spline" '
                    'keySplines="'
                    '0 0 1 1;'
                    '0.1 0 0.2 1;'
                    '0.4 0 0.6 1'
                    '"/>'
                )

            lines.append("</rect>")

            # ------------------------------------------------------------------
            # Small white highlight
            # ------------------------------------------------------------------

            if level > 0:

                highlight_x = x + 2
                highlight_y = y + 2

                lines.append(
                    f'<rect '
                    f'x="{highlight_x}" '
                    f'y="{highlight_y}" '
                    'width="4" '
                    'height="2" '
                    'rx="1" '
                    'fill="white" '
                    'opacity="0" '
                    'pointer-events="none">'
                )

                lines.append(
                    '<animate '
                    'attributeName="opacity" '
                    'values="0;0;0.55;0" '
                    f'keyTimes="0;{t0:.4f};'
                    f'{t1:.4f};{t2:.4f}" '
                    f'dur="{total}s" '
                    'repeatCount="indefinite" '
                    'calcMode="spline" '
                    'keySplines="'
                    '0 0 1 1;'
                    '0 0 0.3 1;'
                    '0.5 0 1 1'
                    '"/>'
                )

                lines.append("</rect>")

            # ------------------------------------------------------------------
            # Tooltip
            #
            # The SVG title makes the real contribution count visible when
            # supported by the renderer.
            # ------------------------------------------------------------------

            lines.append(
                f'<title>'
                f'{day["date"]}: '
                f'{count} contributions'
                f'</title>'
            )

    # ==========================================================================
    # Hover
    # ==========================================================================

    lines.append(
        '<style>'

        'rect[id^="s"]{'
        'transition:filter .15s'
        '}'

        'rect[id^="s"]:hover{'
        'filter:brightness(1.65) '
        'drop-shadow(0 0 5px #39d353)'
        '}'

        '</style>'
    )

    lines.append("</svg>")

    return "\n".join(lines)


# ==============================================================================
# Terminal SVG
# ==============================================================================

def build_terminal():

    W = 900
    H = 520

    lines = []

    # --------------------------------------------------------------------------
    # SVG
    # --------------------------------------------------------------------------

    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">'
    )

    lines.append("<defs>")

    # --------------------------------------------------------------------------
    # Background
    # --------------------------------------------------------------------------

    lines.append(
        '<radialGradient id="bg1" '
        'cx="20%" cy="30%" r="60%">'

        '<stop offset="0%" '
        'stop-color="#0d2137"/>'

        '<stop offset="100%" '
        'stop-color="#0d1117"/>'

        '<animate '
        'attributeName="cx" '
        'values="20%;80%;20%" '
        'dur="10s" '
        'repeatCount="indefinite"/>'

        '<animate '
        'attributeName="cy" '
        'values="30%;70%;30%" '
        'dur="12s" '
        'repeatCount="indefinite"/>'

        '</radialGradient>'

        '<radialGradient id="bg2" '
        'cx="80%" cy="70%" r="50%">'

        '<stop offset="0%" '
        'stop-color="#0a1a2e" '
        'stop-opacity="0.8"/>'

        '<stop offset="100%" '
        'stop-color="#0d1117" '
        'stop-opacity="0"/>'

        '</radialGradient>'
    )

    # --------------------------------------------------------------------------
    # Terminal glow
    # --------------------------------------------------------------------------

    lines.append(
        '<filter id="termglow">'

        '<feGaussianBlur '
        'stdDeviation="8" '
        'result="blur"/>'

        '<feMerge>'

        '<feMergeNode in="blur"/>'

        '<feMergeNode in="SourceGraphic"/>'

        '</feMerge>'

        '</filter>'
    )

    # --------------------------------------------------------------------------
    # Glass
    # --------------------------------------------------------------------------

    lines.append(
        '<linearGradient id="glass" '
        'x1="0%" y1="0%" '
        'x2="0%" y2="100%">'

        '<stop offset="0%" '
        'stop-color="#161b22" '
        'stop-opacity="0.95"/>'

        '<stop offset="100%" '
        'stop-color="#0d1117" '
        'stop-opacity="0.98"/>'

        '</linearGradient>'
    )

    # --------------------------------------------------------------------------
    # Header
    # --------------------------------------------------------------------------

    lines.append(
        '<linearGradient id="headerGrad" '
        'x1="0%" y1="0%" '
        'x2="0%" y2="100%">'

        '<stop offset="0%" '
        'stop-color="#1c2128"/>'

        '<stop offset="100%" '
        'stop-color="#161b22"/>'

        '</linearGradient>'
    )

    # --------------------------------------------------------------------------
    # Border
    # --------------------------------------------------------------------------

    lines.append(
        '<linearGradient id="borderGlow" '
        'x1="0%" y1="0%" '
        'x2="100%" y2="100%">'

        '<stop offset="0%" '
        'stop-color="#00ffcc" '
        'stop-opacity="0.6"/>'

        '<stop offset="50%" '
        'stop-color="#0ea5e9" '
        'stop-opacity="0.3"/>'

        '<stop offset="100%" '
        'stop-color="#7c3aed" '
        'stop-opacity="0.6"/>'

        '<animate '
        'attributeName="x1" '
        'values="0%;100%;0%" '
        'dur="4s" '
        'repeatCount="indefinite"/>'

        '<animate '
        'attributeName="x2" '
        'values="100%;0%;100%" '
        'dur="4s" '
        'repeatCount="indefinite"/>'

        '</linearGradient>'
    )

    # --------------------------------------------------------------------------
    # Scanlines
    # --------------------------------------------------------------------------

    lines.append(
        '<pattern id="scanlines" '
        'x="0" y="0" '
        'width="900" height="3" '
        'patternUnits="userSpaceOnUse">'

        '<line '
        'x1="0" y1="1" '
        'x2="900" y2="1" '
        'stroke="white" '
        'stroke-opacity="0.03" '
        'stroke-width="1"/>'

        '</pattern>'
    )

    # --------------------------------------------------------------------------
    # Grid
    # --------------------------------------------------------------------------

    lines.append(
        '<pattern id="grid" '
        'x="0" y="0" '
        'width="40" height="40" '
        'patternUnits="userSpaceOnUse">'

        '<path '
        'd="M 40 0 L 0 0 0 40" '
        'fill="none" '
        'stroke="#ffffff" '
        'stroke-width="0.3" '
        'stroke-opacity="0.04"/>'

        '</pattern>'
    )

    # --------------------------------------------------------------------------
    # Clip
    # --------------------------------------------------------------------------

    lines.append(
        '<clipPath id="termclip">'

        '<rect '
        'x="30" y="30" '
        'width="840" '
        'height="460" '
        'rx="14"/>'

        '</clipPath>'
    )

    lines.append("</defs>")

    # ==========================================================================
    # Background
    # ==========================================================================

    lines.append(
        f'<rect width="{W}" height="{H}" '
        'fill="url(#bg1)"/>'
    )

    lines.append(
        f'<rect width="{W}" height="{H}" '
        'fill="url(#bg2)"/>'
    )

    lines.append(
        f'<rect width="{W}" height="{H}" '
        'fill="url(#grid)"/>'
    )

    # ==========================================================================
    # Particles
    #
    # Kept deterministic so the terminal background does not change every run.
    # ==========================================================================

    particle_seed = 42

    import random

    particle_random = random.Random(
        particle_seed
    )

    particles = [
        (
            particle_random.randint(50, 850),
            particle_random.randint(50, 470),
            round(
                particle_random.uniform(
                    0.3,
                    1.2,
                ),
                1,
            ),
            round(
                particle_random.uniform(
                    3,
                    9,
                ),
                1,
            ),
        )
        for _ in range(28)
    ]

    for px, py, radius, duration in particles:

        dy = particle_random.randint(
            -30,
            30,
        )

        lines.append(
            f'<circle '
            f'cx="{px}" '
            f'cy="{py}" '
            f'r="{radius}" '
            'fill="#00ffcc" '
            'opacity="0.15">'

            '<animate '
            'attributeName="cy" '
            f'values="{py};{py + dy};{py}" '
            f'dur="{duration}s" '
            'repeatCount="indefinite"/>'

            '<animate '
            'attributeName="opacity" '
            'values="0.05;0.25;0.05" '
            f'dur="{duration}s" '
            'repeatCount="indefinite"/>'

            '</circle>'
        )

    # ==========================================================================
    # Border
    # ==========================================================================

    lines.append(
        '<rect '
        'x="28" y="28" '
        'width="844" '
        'height="464" '
        'rx="15" '
        'fill="none" '
        'stroke="url(#borderGlow)" '
        'stroke-width="2">'

        '<animate '
        'attributeName="stroke-opacity" '
        'values="0.7;1;0.7" '
        'dur="3s" '
        'repeatCount="indefinite"/>'

        '</rect>'
    )

    # ==========================================================================
    # Floating terminal
    # ==========================================================================

    lines.append("<g>")

    lines.append(
        '<animateTransform '
        'attributeName="transform" '
        'type="translate" '
        'values="0 0;0 -4;0 0" '
        'dur="4s" '
        'repeatCount="indefinite" '
        'calcMode="spline" '
        'keySplines="'
        '0.45 0 0.55 1;'
        '0.45 0 0.55 1'
        '"/>'
    )

    # --------------------------------------------------------------------------
    # Body
    # --------------------------------------------------------------------------

    lines.append(
        '<rect '
        'x="30" y="30" '
        'width="840" '
        'height="460" '
        'rx="14" '
        'fill="url(#glass)" '
        'stroke="#30363d" '
        'stroke-width="1"/>'
    )

    lines.append(
        '<rect '
        'x="30" y="30" '
        'width="840" '
        'height="80" '
        'rx="14" '
        'fill="white" '
        'fill-opacity="0.025" '
        'clip-path="url(#termclip)"/>'
    )

    # --------------------------------------------------------------------------
    # Header
    # --------------------------------------------------------------------------

    lines.append(
        '<rect '
        'x="30" y="30" '
        'width="840" '
        'height="44" '
        'rx="14" '
        'fill="url(#headerGrad)"/>'
    )

    lines.append(
        '<rect '
        'x="30" y="58" '
        'width="840" '
        'height="16" '
        'fill="url(#headerGrad)"/>'
    )

    lines.append(
        '<line '
        'x1="30" y1="74" '
        'x2="870" y2="74" '
        'stroke="#30363d" '
        'stroke-width="1"/>'
    )

    # --------------------------------------------------------------------------
    # Buttons
    # --------------------------------------------------------------------------

    for fill_color, button_x in [
        ("#ff5f57", 55),
        ("#febc2e", 79),
        ("#28c840", 103),
    ]:

        lines.append(
            f'<circle '
            f'cx="{button_x}" '
            'cy="52" '
            'r="7" '
            f'fill="{fill_color}"/>'
        )

    # --------------------------------------------------------------------------
    # Title
    # --------------------------------------------------------------------------

    lines.append(
        '<text '
        'x="450" '
        'y="57" '
        'text-anchor="middle" '
        'fill="#8b949e" '
        'font-size="13" '
        'font-family="ui-monospace,monospace">'
        '~/portfolio'
        '</text>'
    )

    # --------------------------------------------------------------------------
    # Scanlines
    # --------------------------------------------------------------------------

    lines.append(
        '<rect '
        'x="30" '
        'y="74" '
        'width="840" '
        'height="416" '
        'fill="url(#scanlines)" '
        'clip-path="url(#termclip)"/>'
    )

    # --------------------------------------------------------------------------
    # Scan sweep
    # --------------------------------------------------------------------------

    lines.append(
        '<rect '
        'x="30" '
        'y="74" '
        'width="840" '
        'height="2" '
        'fill="white" '
        'fill-opacity="0.04" '
        'clip-path="url(#termclip)">'

        '<animate '
        'attributeName="y" '
        'values="74;490;74" '
        'dur="5s" '
        'repeatCount="indefinite" '
        'calcMode="spline" '
        'keySplines="'
        '0.4 0 0.6 1;'
        '0.4 0 0.6 1'
        '"/>'

        '</rect>'
    )

    # ==========================================================================
    # Typewriter
    # ==========================================================================

    prompt_chars = list(
        "$ whoami"
    )

    typing_dur = 8.0
    char_dur = 0.12
    delete_start = 1.5

    lines.append(
        '<text '
        'x="56" '
        'y="106" '
        'font-family="ui-monospace,Menlo,monospace" '
        'font-size="14" '
        'fill="#00ffcc">'
    )

    for i, char in enumerate(
        prompt_chars
    ):

        a0 = (
            i * char_dur
        ) / typing_dur

        a1 = min(
            (
                len(prompt_chars)
                * char_dur
                + delete_start
                + (
                    len(prompt_chars)
                    - i
                    - 1
                )
                * char_dur
                * 0.5
            ) / typing_dur,
            0.98,
        )

        lines.append(
            f'<tspan opacity="0">'
            f'{char}'

            '<animate '
            'attributeName="opacity" '
            'values="0;0;1;1;0;0" '
            f'keyTimes="0;{a0:.3f};'
            f'{min(a0 + 0.01, 0.99):.3f};'
            f'{a1:.3f};'
            f'{min(a1 + 0.02, 0.99):.3f};1" '
            f'dur="{typing_dur}s" '
            'repeatCount="indefinite"/>'

            '</tspan>'
        )

    lines.append("</text>")

    # ==========================================================================
    # Cursor
    # ==========================================================================

    cursor_end_x = (
        56
        + len(prompt_chars)
        * 8.5
    )

    typing_end = (
        len(prompt_chars)
        * char_dur
        / typing_dur
    )

    lines.append(
        '<rect '
        'x="56" '
        'y="92" '
        'width="8" '
        'height="14" '
        'fill="#00ffcc" '
        'rx="1">'

        '<animate '
        'attributeName="x" '
        f'values="56;'
        f'{cursor_end_x:.0f};56" '
        f'keyTimes="0;'
        f'{typing_end:.3f};1" '
        f'dur="{typing_dur}s" '
        'repeatCount="indefinite"/>'

        '<animate '
        'attributeName="opacity" '
        'values="1;0;1" '
        'dur="0.8s" '
        'repeatCount="indefinite"/>'

        '</rect>'
    )

    # ==========================================================================
    # Profile information
    # ==========================================================================

    reveal_start = (
        len(prompt_chars)
        * char_dur
        + 0.3
    )

    sections = [
        (
            "----------------------------------------------------",
            "#30363d",
            122,
        ),
        (
            "Name:  Gaurav Singh",
            "#e6edf3",
            140,
        ),
        (
            "Role:  Full Stack Developer",
            "#00ffcc",
            158,
        ),
        (
            "Stack:  React  Next.js  Node.js  TypeScript C# Java Core",
            "#8b949e",
            176,
        ),
        (
            "Focus:  Building modern web experiences",
            "#39d353",
            194,
        ),
        (
            "----------------------------------------------------",
            "#30363d",
            212,
        ),
    ]

    for index, (
        text,
        color,
        y_position,
    ) in enumerate(sections):

        at = min(
            (
                reveal_start
                + index * 0.28
            ) / typing_dur,
            0.97,
        )

        lines.append(
            '<text '
            f'x="56" '
            f'y="{y_position}" '
            'font-family="ui-monospace,Menlo,monospace" '
            'font-size="12.5" '
            f'fill="{color}" '
            'opacity="0">'

            f'{text}'

            '<animate '
            'attributeName="opacity" '
            'values="0;0;1;1" '
            f'keyTimes="0;{at:.3f};'
            f'{min(at + 0.04, 0.99):.3f};1" '
            f'dur="{typing_dur}s" '
            'repeatCount="indefinite"/>'

            '</text>'
        )

    lines.append("</g>")

    lines.append("</svg>")

    return "\n".join(lines)


# ==============================================================================
# Main
# ==============================================================================

def main():

    print(
        f"[INFO] Fetching real GitHub contributions "
        f"for {GITHUB_USERNAME}..."
    )

    user, calendar = fetch_contributions()

    total = calendar[
        "totalContributions"
    ]

    print(
        f"[INFO] GitHub user: "
        f"{user.get('name') or user['login']}"
    )

    print(
        f"[INFO] Total contributions: {total}"
    )

    weeks = calendar.get(
        "weeks",
        [],
    )

    print(
        f"[INFO] Contribution weeks received: "
        f"{len(weeks)}"
    )

    # --------------------------------------------------------------------------
    # Generate contribution SVG
    # --------------------------------------------------------------------------

    contribution_svg = build_contrib(
        calendar
    )

    with open(
        "github-contribution-animation.svg",
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            contribution_svg
        )

    print(
        "[OK] github-contribution-animation.svg written"
    )

    # --------------------------------------------------------------------------
    # Generate terminal SVG
    # --------------------------------------------------------------------------

    terminal_svg = build_terminal()

    with open(
        "terminal-card.svg",
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            terminal_svg
        )

    print(
        "[OK] terminal-card.svg written"
    )


# ==============================================================================
# Entry point
# ==============================================================================

if __name__ == "__main__":
    main()
