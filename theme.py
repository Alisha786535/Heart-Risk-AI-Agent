"""One dark palette for the whole app. Every text/background pair is >= 4.5:1 (WCAG AA); see tests/test_theme.py.
Streamlit's native widgets (chat bubbles, tables, captions, tabs, expanders, sidebar) are styled explicitly so they
never fall back to Streamlit's dark-on-light defaults."""
import streamlit as st

BG, SURFACE, SURFACE2, SIDEBAR = "#0D1B2A", "#132237", "#1E2D3D", "#0A1628"
TEXT, MUTED, LINK, ACCENT = "#F0F4F8", "#A0AEC0", "#90CDF4", "#4A90D9"
BORDER = "#2E4057"

CSS = f"""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:{BG} !important; color:{TEXT} !important; }}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {{ background:{SIDEBAR} !important; }}
.stApp p, .stApp li, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp td, .stApp th, .stApp summary {{ color:{TEXT}; }}
.stApp a {{ color:{LINK} !important; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * , .stApp small {{ color:{MUTED} !important; }}
/* chat */
[data-testid="stChatMessage"] {{ background:{SURFACE} !important; border:1px solid {BORDER}; border-radius:12px; padding:12px 14px; }}
[data-testid="stChatMessage"] * {{ color:{TEXT} !important; }}
[data-testid="stChatMessage"] code {{ background:{SURFACE2} !important; color:{LINK} !important; }}
[data-testid="stChatInput"], [data-testid="stChatInput"] > div {{ background:{SURFACE2} !important; border-radius:10px; }}
[data-testid="stChatInput"] textarea {{ color:{TEXT} !important; background:{SURFACE2} !important; caret-color:{TEXT}; }}
[data-testid="stChatInput"] textarea::placeholder {{ color:{MUTED} !important; opacity:1; }}
/* tables, tabs, expanders, inputs, alerts */
[data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td {{ color:{TEXT} !important; background:{SURFACE} !important; border-color:{BORDER} !important; }}
[data-testid="stTable"] th {{ background:{SURFACE2} !important; }}
.stTabs [data-baseweb="tab"] {{ color:{MUTED} !important; }}
.stTabs [aria-selected="true"] {{ color:{TEXT} !important; }}
[data-testid="stExpander"] {{ background:{SURFACE} !important; border:1px solid {BORDER} !important; }}
[data-testid="stExpander"] * {{ color:{TEXT} !important; }}
.stTextInput input, .stNumberInput input, textarea, [data-baseweb="select"] > div {{ background:{SURFACE2} !important; color:{TEXT} !important; }}
[data-baseweb="popover"] *, [role="listbox"] * {{ color:{TEXT} !important; background:{SURFACE2} !important; }}
[data-testid="stAlert"] * {{ color:{TEXT} !important; }}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
