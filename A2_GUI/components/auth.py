import streamlit as st
from sqlalchemy.exc import IntegrityError

from db import SessionLocal, User
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    get_db,
    get_user_by_username,
    get_user_by_email,
)


# ────────────────────────────────────────────────────────────────────────────────
# Global page settings
# ────────────────────────────────────────────────────────────────────────────────


def center_title(text: str, emoji: str = "") -> None:
    """Big centered page title with an optional emoji."""
    st.markdown(
        f"<h1 style='text-align:center;margin-bottom:0.25em;'>{emoji} {text}</h1>",
        unsafe_allow_html=True,
    )


# ────────────────────────────────────────────────────────────────────────────────
#  Sign‑Up
# ────────────────────────────────────────────────────────────────────────────────
def signup_page() -> None:
    """Render the farmer sign‑up form."""
    center_title("Sign‑Up", "🚜")

    # put EVERYTHING for the form inside the middle column
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        # placeholders for inline validation feedback
        username_error = st.empty()
        email_error    = st.empty()
        region_error   = st.empty()
        password_error = st.empty()

        # input fields
        username = st.text_input("Username", help="Pick a unique username")
        email    = st.text_input("Email",    help="Your email address")
        region   = st.text_input("Region",   help="e.g., Mekong Delta")
        password = st.text_input(
            "Password", type="password", help="Create a strong password"
        )

        # ── Create Account button ────────────────────────────────────────────
        if st.button("Create Account", use_container_width=True):
            has_error = False
            if not username:
                username_error.error("Username is required.")
                has_error = True
            if not email:
                email_error.error("Email is required.")
                has_error = True
            if not region:
                region_error.error("Region is required.")
                has_error = True
            if not password:
                password_error.error("Password is required.")
                has_error = True
            if has_error:
                return

            db = next(get_db())

            if get_user_by_username(db, username):
                username_error.error("Username already taken.")
                return
            if get_user_by_email(db, email):
                email_error.error("Email already registered.")
                return

            hashed_pw = hash_password(password)
            new_user = User(
                username=username,
                email=email,
                region=region,
                password_hash=hashed_pw,
            )
            db.add(new_user)
            try:
                db.commit()
                st.success("Account created! You can now log in.")
            except IntegrityError:
                db.rollback()
                st.error("An error occurred. Please try again.")

        st.markdown("---")

        # ── Link to log‑in page ──────────────────────────────────────────────
        if st.button("Already have an account? Log In", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()


# ────────────────────────────────────────────────────────────────────────────────
#  Log‑In
# ────────────────────────────────────────────────────────────────────────────────
def login_page() -> None:
    """Render the farmer log‑in form."""
    center_title("Login", "🔐")

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        username_error = st.empty()
        password_error = st.empty()

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # ── Log In button ────────────────────────────────────────────────────
        if st.button("Log In", use_container_width=True):
            has_error = False
            if not username:
                username_error.error("Username is required.")
                has_error = True
            if not password:
                password_error.error("Password is required.")
                has_error = True
            if has_error:
                return

            db   = next(get_db())
            user = get_user_by_username(db, username)

            if not user or not verify_password(password, user.password_hash):
                password_error.error("Invalid username or password.")
                return

            # successful log‑in
            token = create_access_token(subject=username)
            st.session_state.token = token
            st.session_state.user  = username
            st.success(f"Hello, {username}! You’re now logged in.")
            st.rerun()

        st.markdown("---")

        # ── Link to sign‑up page ────────────────────────────────────────────
        if st.button("Don’t have an account? Sign Up", use_container_width=True):
            st.session_state.auth_mode = "signup"
            st.rerun()
