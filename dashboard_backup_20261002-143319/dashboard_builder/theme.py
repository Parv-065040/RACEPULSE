"""RACEPULSE dashboard design system."""

BACKGROUND = "#080B10"
PANEL = "#0E131A"
PANEL_ALT = "#111821"
BORDER = "#27313C"
TEXT = "#E8EDF2"
MUTED = "#7F8B98"

NORMAL = "#36D399"
TELEMETRY = "#22D3EE"
STRATEGY = "#A78BFA"
COMMERCIAL = "#F5C451"
WARNING = "#F59E0B"
CRITICAL = "#EF4444"

GRID_COLUMNS = 24

BASE_TIME = {
    "from": "now-30m",
    "to": "now",
}

REFRESH = "5s"

FONT_FAMILY = "Inter"

PANEL_DEFAULTS = {
    "transparent": False,
    "background": PANEL,
    "border": True,
}
