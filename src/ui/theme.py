class ThemeManager:
    # --- PALETTES ---
    THEMES = {
        "Cyber": {
            "BACKGROUND": "#050505",       # Deep Black
            "CARD_BG": "#151515",          # Lighter Black
            "TEXT_MAIN": "#FFFFFF",        # White
            "TEXT_DIM": "#808080",         # Gray
            "ACCENT": "#00E5FF",           # Neon Cyan
            "ACCENT_DIM": "#00606B",       # Darker Cyan
            "WARNING": "#FF0040",          # Neon Red
            "GAUGE_BG": "#151515"
        },
        "Standard": {
            "BACKGROUND": "#242424",       # Standard CTk Dark Gray
            "CARD_BG": "#333333",          # Lighter Gray
            "TEXT_MAIN": "#FFFFFF",
            "TEXT_DIM": "#AAAAAA",
            "ACCENT": "#3B8ED0",           # Standard Blue
            "ACCENT_DIM": "#1F4B6D",
            "WARNING": "#E04F5F",          # Soft Red
            "GAUGE_BG": "#333333"
        },
        "Matrix": {
            "BACKGROUND": "#000000",
            "CARD_BG": "#001100",
            "TEXT_MAIN": "#00FF00",        # Matrix Green
            "TEXT_DIM": "#005500",
            "ACCENT": "#00FF00",
            "ACCENT_DIM": "#003300",
            "WARNING": "#FFFFFF",
            "GAUGE_BG": "#001100"
        },
        "Amber": {
            "BACKGROUND": "#000000",
            "CARD_BG": "#1A1A1A",
            "TEXT_MAIN": "#FFC107",        # BMW Orange/Amber
            "TEXT_DIM": "#B08D55",
            "ACCENT": "#FFCA28",
            "ACCENT_DIM": "#5C4500",
            "WARNING": "#FF0000",
            "GAUGE_BG": "#1A1A1A"
        },
        "Crimson": {
            "BACKGROUND": "#0D0000",
            "CARD_BG": "#260000",
            "TEXT_MAIN": "#FFFFFF",
            "TEXT_DIM": "#FF9999",
            "ACCENT": "#FF0000",           # Pure Red
            "ACCENT_DIM": "#550000",
            "WARNING": "#FFFF00",          # Yellow warning (contrast)
            "GAUGE_BG": "#260000"
        },
        "Synthwave": {
            "BACKGROUND": "#240046",       # Deep Purple
            "CARD_BG": "#3C096C",
            "TEXT_MAIN": "#E0AAFF",        # Light Lilac
            "TEXT_DIM": "#9D4EDD",
            "ACCENT": "#FF00FF",           # Magenta
            "ACCENT_DIM": "#5A189A",
            "WARNING": "#FF9E00",          # Orange
            "GAUGE_BG": "#3C096C"
        },
        "Solar (Light)": {
            "BACKGROUND": "#F0F2F5",       # Light Gray (White-ish)
            "CARD_BG": "#FFFFFF",          # Pure White Cards
            "TEXT_MAIN": "#1A1A1A",        # Dark Text
            "TEXT_DIM": "#666666",
            "ACCENT": "#007AFF",           # iOS Blue
            "ACCENT_DIM": "#D0E0FF",
            "WARNING": "#FF3B30",
            "GAUGE_BG": "#FFFFFF"
        }
    }

    current_theme = THEMES["Standard"]

    @classmethod
    def set_theme(cls, theme_name):
        if theme_name in cls.THEMES:
            cls.current_theme = cls.THEMES[theme_name]
            return True
        return False

    @classmethod
    def get(cls, key):
        return cls.current_theme.get(key, "#FFFFFF")