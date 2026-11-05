"""Guards against 'dark text on dark background': every palette pair must meet WCAG AA (4.5:1)."""
import re
from pathlib import Path
import theme

ROOT = Path(__file__).resolve().parent.parent


def _lum(h):
    r, g, b = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_palette_pairs_are_readable():
    surfaces = [theme.BG, theme.SURFACE, theme.SURFACE2, theme.SIDEBAR]
    for fg in (theme.TEXT, theme.MUTED, theme.LINK):
        for bg in surfaces:
            assert ratio(fg, bg) >= 4.5, (fg, bg, round(ratio(fg, bg), 2))


def test_streamlit_config_matches_palette():
    cfg = (ROOT / ".streamlit" / "config.toml").read_text()
    for key, val in (("backgroundColor", theme.BG), ("secondaryBackgroundColor", theme.SURFACE), ("textColor", theme.TEXT)):
        assert re.search(rf'{key}\s*=\s*"{val}"', cfg, re.I), key
    assert 'base = "dark"' in cfg


def test_app_css_has_no_dim_text_colours():
    s = (ROOT / "app.py").read_text(encoding="utf-8")
    css = s[s.index("<style>"):s.index("</style>")]
    bad = []
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        for c in re.findall(r"(?<![-\w])color:\s*(#[0-9A-Fa-f]{6})", m.group(2)):
            if ratio(c, theme.SURFACE) < 4.5 and ratio(c, theme.BG) < 4.5:      # dark text, unreadable on both
                bad.append((m.group(1).strip()[:40], c))
    assert not bad, bad


def test_chat_text_always_forced_light():
    assert 'stChatMessage"] *' in theme.CSS and theme.TEXT in theme.CSS
