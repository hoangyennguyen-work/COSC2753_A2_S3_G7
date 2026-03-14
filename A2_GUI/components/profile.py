import streamlit as st
from auth import get_db, get_user_by_username, hash_password
from sqlalchemy.exc import SQLAlchemyError

def profile_page():
    st.title(" Profile Settings")

    username = st.session_state.get("user")
    if not username:
        st.warning("No user logged in.")
        return

    db = next(get_db())
    user = get_user_by_username(db, username)
    if not user:
        st.error("User not found.")
        return

    # Initialize session defaults if not already set
    if "original_email" not in st.session_state:
        st.session_state.original_email = user.email
    if "original_region" not in st.session_state:
        st.session_state.original_region = user.region
    if "edit_email" not in st.session_state:
        st.session_state.edit_email = user.email
    if "edit_region" not in st.session_state:
        st.session_state.edit_region = user.region
    if "edit_pw" not in st.session_state:
        st.session_state.edit_pw = ""

    # Form fields
    email = st.text_input("Email", value=st.session_state.edit_email)
    region = st.text_input("Region", value=st.session_state.edit_region)
    new_pw = st.text_input("New Password (leave blank to keep unchanged)", type="password", value=st.session_state.edit_pw)

    # Update session state
    st.session_state.edit_email = email
    st.session_state.edit_region = region
    st.session_state.edit_pw = new_pw

    # ── Right-aligned action buttons ─────────────────────────────
    col_spacer, col_update, col_reset = st.columns([6, 2, 2])
    with col_update:
        update_clicked = st.button("Update Profile")
    with col_reset:
        reset_clicked = st.button("Reset")

    if update_clicked:
        try:
            user.email = email.strip()
            user.region = region.strip()
            if new_pw.strip():
                user.password_hash = hash_password(new_pw.strip())
            db.commit()

            st.session_state.original_email = user.email
            st.session_state.original_region = user.region
            st.session_state.edit_pw = ""

            st.success("✅ Profile updated successfully.")
            st.rerun()
        except SQLAlchemyError:
            db.rollback()
            st.error("❌ Failed to update profile.")

    if reset_clicked:
        st.session_state.edit_email = st.session_state.original_email
        st.session_state.edit_region = st.session_state.original_region
        st.session_state.edit_pw = ""
        st.rerun()

    st.markdown("---")

    # ── Centered Delete Button ──────────────────────────────────
    col_del1, col_del2, col_del3 = st.columns([3, 2, 3])
    with col_del1:
        if st.button("Delete My Account"):
            st.session_state.confirm_delete = True

    if st.session_state.get("confirm_delete", False):
        st.error("⚠️ This will permanently delete your account and all your predictions.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Delete"):
                try:
                    db.delete(user)
                    db.commit()
                    for k in ("user", "token", "current_prediction", "confirm_delete"):
                        st.session_state.pop(k, None)
                    st.success("🧹 Account deleted. Goodbye.")
                    st.rerun()
                except SQLAlchemyError:
                    db.rollback()
                    st.error("❌ Failed to delete account.")
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_delete = False
                st.rerun()
