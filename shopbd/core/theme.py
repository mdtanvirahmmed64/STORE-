"""Turns the colors chosen in Admin → Theme & Colors into CSS variables."""

PRESETS = {
    # name: (main, header bg, header text, top bar/dark, accent, discount, page bg, text, footer)
    "orange": ("#f85606", "#f85606", "#ffffff", "#1a2b49", "#ffb400", "#e5383b", "#f4f5f7", "#1f2430", "#111a2e"),
    "amazon": ("#ff9900", "#131921", "#ffffff", "#232f3e", "#febd69", "#cc0c39", "#eaeded", "#0f1111", "#131a22"),
    "green": ("#12a150", "#12a150", "#ffffff", "#0b3d2c", "#ffc107", "#e5383b", "#f3f7f4", "#1c2b22", "#082a1e"),
    "blue": ("#1c7ed6", "#1c7ed6", "#ffffff", "#0b2545", "#ffb703", "#e63946", "#f1f5fa", "#1b263b", "#081a33"),
    "purple": ("#7048e8", "#5f3dc4", "#ffffff", "#2b1a5e", "#fcc419", "#e64980", "#f5f3fb", "#231942", "#1c1240"),
    "red": ("#d62828", "#d62828", "#ffffff", "#2b2d42", "#fcbf49", "#9d0208", "#f7f4f4", "#2b2d42", "#1d1e2c"),
    "pink": ("#e64980", "#e64980", "#ffffff", "#4a1942", "#ffd43b", "#c2255c", "#fdf3f7", "#3a1a2e", "#2e1027"),
    "teal": ("#0ca678", "#087f5b", "#ffffff", "#0b3c49", "#ffa94d", "#e03131", "#f1f8f6", "#16302b", "#082f2a"),
    "black": ("#212529", "#ffffff", "#212529", "#212529", "#f59f00", "#e03131", "#f8f9fa", "#212529", "#111315"),
}
PRESET_FIELDS = ("primary_color", "header_bg", "header_text", "secondary_color", "accent_color",
                 "discount_color", "page_bg", "text_color", "footer_bg")


def _rgb(hex_color):
    h = (hex_color or "#000000").lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def mix(color, other, amount):
    """amount=0 → color, amount=1 → other"""
    a, b = _rgb(color), _rgb(other)
    return _hex(tuple(x + (y - x) * amount for x, y in zip(a, b)))


def luminance(color):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_on(bg):
    """Black or white — whichever is easier to read on this background."""
    return "#1f2430" if luminance(bg) > 0.45 else "#ffffff"


def build_css_variables(t):
    dark_footer = luminance(t.footer_bg) < 0.45
    return {
        "--primary": t.primary_color,
        "--primary-dark": mix(t.primary_color, "#000000", 0.15),
        "--primary-light": mix(t.primary_color, "#ffffff", 0.25),
        "--primary-soft": mix(t.primary_color, "#ffffff", 0.9),
        "--on-primary": readable_on(t.primary_color),
        "--header-bg": t.header_bg,
        "--header-text": t.header_text,
        "--header-hover": mix(t.header_bg, t.header_text, 0.15),
        "--secondary": t.secondary_color,
        "--secondary-dark": mix(t.secondary_color, "#000000", 0.25),
        "--on-secondary": readable_on(t.secondary_color),
        "--on-secondary-muted": mix(readable_on(t.secondary_color), t.secondary_color, 0.3),
        "--accent": t.accent_color,
        "--on-accent": readable_on(t.accent_color),
        "--danger": t.discount_color,
        "--bg": t.page_bg,
        "--text": t.text_color,
        "--muted": mix(t.text_color, t.page_bg, 0.45),
        "--footer-bg": t.footer_bg,
        "--footer-text": mix(readable_on(t.footer_bg), t.footer_bg, 0.3),
        "--footer-heading": "#ffffff" if dark_footer else "#1f2430",
        "--radius": f"{t.corner_radius}px",
        "--radius-sm": f"{max(0, round(t.corner_radius * 0.8))}px",
        "--font-main": "system-ui" if t.font == "system" else f"'{t.font}'",
    }
