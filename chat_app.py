"""Standalone chat page:  streamlit run chat_app.py
(For real use, pass the logged-in user's id from your auth instead of the text box.)"""
import streamlit as st
from chat_ui import render_chat

st.set_page_config(page_title="CardioGuide", page_icon="🫀", layout="wide")
uid = st.sidebar.text_input("User ID", value="demo_user", max_chars=64,
                            help="Letters, digits and . _ @ + - only")
render_chat(uid.strip() or "demo_user")
