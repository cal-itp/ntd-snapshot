# Define color palette here - easier to switch to DDS ones
# if needed, without importing yet another dependency

# Brand / primary colors
BRAND_COLORS = {
    "blue": "#5493B6",
    "yellow": "#FFB81C",
    "teal": "#00B2A9",
    "navy": "#162933",
}

# Neutral colors
NEUTRAL_COLORS = {
    "grey": "#4B4F54",
    "border": "#D9D9D6",
    "axis_label": "#374151",
    "axis_title": "#111827",
    "axis_line": "#9CA3AF",
    "background": "#FAFBFB",
    "surface": "#FFFFFF",
    "muted": "#F3F4F6",
    "subtle_text": "#6B7280",
    "light_grey": "#C4C8CF",
}

# Soft / pastel categorical colors
PASTEL_COLORS = [
    "#8FB3C9",  # Powder blue
    "#E9B58F",  # Peach
    "#91B68C",  # Sage green
    "#B99BC7",  # Thistle
    "#E6C76E",  # Soft yellow
    "#929FD0",  # Periwinkle
    "#D98FA3",  # Soft pink
    "#79B8AE",  # Mint
    "#A88BBE",  # Lavender
    "#E5A078",  # Apricot
    "#70B9C5",  # Light teal
    "#C39ACB",  # Orchid
    "#A4C887",  # Light lime
    "#DDBB83",  # Cream
    "#8799C4",  # Dusty blue
    "#E45756",  # Coral red
]

# Diverging colors (heatmaps)
DIVERGING_COLORS = {
    "redblue": ["#B2182B", "#F7F7F7", "#2166AC"],
    "bluegreen": ["#2166AC", "#F7F7F7", "#1B7837"],
}

CALITP_CATEGORY_BRIGHT_COLORS = [
    "#2EA8CE",  # darker blue
    "#EB9F3C",  # orange
    "#F4D837",  # yellow
    "#51BF9D",  # green
    "#8CBCCB",  # lighter blue
    "#9487C0",  # purple
]

CALITP_CATEGORY_BOLD_COLORS = [
    "#136C97",  # darker blue
    "#E16B26",  # orange
    "#F6BF16",  # yellow
    "#00896B",  # green
    "#7790A3",  # lighter blue
    "#5B559C",  # purple
]

# Default color palette
DEFAULT_CATEGORY_COLORS = list(BRAND_COLORS.values())
