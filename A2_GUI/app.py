# app.py

import streamlit as st
from config import PAGE_TITLE, PAGE_LAYOUT
from components.profile import profile_page  # ← Add this line


# — Streamlit page configuration —
st.set_page_config(
    page_title="Paddy-Rice-Web",
    layout="centered",
    initial_sidebar_state="auto"
)

# — Core imports (unchanged) —
from db import init_db
from auth import verify_token
from components.auth import signup_page, login_page
from components.predict import predict_page
from components.history import history_page

# ← horizontal menu widget
from streamlit_option_menu import option_menu

def main():
    # 1) Ensure our tables exist
    init_db()

    # 2) Default to login if not set
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # 3) Check token
    token = st.session_state.get("token")
    if token:
        username = verify_token(token)

        if username:
            # ────────── NAVBAR ──────────
            selected = option_menu(
                menu_title=" Paddy Doctor 🌾",
                options=[
                    "Predict",
                    "History",
                    f"{username}",
                    "Log Out",
                ],
                icons=[
                    "",       # Predict
                    "clock-history",    # History
                    "person-circle",    # Hello (static)
                    "box-arrow-right",  # Log Out
                ],
                default_index=0,
                orientation="horizontal",
                styles={
                    # container around all pills
                    "container": {"padding": "0!important", "background-color": "#f8f9fa"},
                    # your title on the left
                    "menu-title": {"font-size": "20px", "font-weight": "600"},
                    # all pills
                    "nav-link": {"font-size": "16px", "color": "#495057"},
                    # hover state
                    "nav-link:hover": {"background-color": "#e9ecef"},
                    # active/selected pill
                    "nav-link-selected": {
                        "background-color": "#e0e0e0",
                        "color": "#333",
                    },
                }
            )

            # ────────── ROUTING ──────────
            if selected == "Predict":
                predict_page()
            elif selected == "History":
                history_page()
            elif selected == username:
                profile_page()

            else:  # "Log Out"
                for k in ("token", "user"):
                    st.session_state.pop(k, None)
                st.success("You’ve been logged out.")
                st.rerun()

            return  # done

        else:
            # invalid/expired token → force re-login
            st.warning("Session expired, please log in again.")
            st.session_state.pop("token", None)
            st.rerun()

    # 4) Not logged in: show Login or Sign-Up
    if st.session_state.auth_mode == "login":
        login_page()
    else:
        signup_page()

def main():
    # 1) Ensure our tables exist
    init_db()

    # 2) Default to login if not set
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # 3) Check token
    token = st.session_state.get("token")
    if token:
        username = verify_token(token)

        if username:
            # ────────── NAVBAR ──────────
            selected = option_menu(
    menu_title="Paddy Doctor 🌾",
    options=[
        "Predict",
        "History",
        f"{username}",
        "Log Out",
    ],
    icons=[
        "calculator",       # Predict
        "clock-history",    # History
        "person-circle",    # Hello (static)
        "box-arrow-right",  # Log Out
    ],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "0 20px",
            "background-color": "#ffffff",
            "box-shadow": "none"
        },
        # Center menu title
        "menu-title": {
            "font-size": "22px",
            "font-weight": "700",
            "color": "#2E7D32",
            "padding": "0 15px",
            "margin": "0 auto",       # center horizontally by auto left/right margin
            "user-select": "none",
            "text-align": "center",  # center text inside title container
            "flex": "1",             # allow title to expand and center
        },
        "nav-link": {
            "font-size": "16px",
            "color": "#555555",
            "padding": "8px 20px",
            "border-radius": "8px",
            "transition": "background-color 0.3s ease, color 0.3s ease",
            "border-bottom": "none",  # remove bottom border/underline if any
            "box-shadow": "none",     # remove shadows that look like lines
        },
        "nav-link:hover": {
            "background-color": "#E8F5E9",
            "color": "#2E7D32",
        },
        "nav-link-selected": {
            "background-color": "#4CAF50",
            "color": "white",
            "font-weight": "700",
            "box-shadow": "none"
        },
    }
            )

            # ────────── ROUTING ──────────
            if selected == "Predict":
                predict_page()
            elif selected == "History":
                history_page()
            elif selected == username:
                profile_page()

            else:  # "Log Out"
                for k in ("token", "user"):
                    st.session_state.pop(k, None)
                st.success("You’ve been logged out.")
                st.rerun()

            return  # done

        else:
            # invalid/expired token → force re-login
            st.warning("Session expired, please log in again.")
            st.session_state.pop("token", None)
            st.rerun()

    # 4) Not logged in: show Login or Sign-Up
    if st.session_state.auth_mode == "login":
        login_page()
    else:
        signup_page()

if __name__ == "__main__":
    main()