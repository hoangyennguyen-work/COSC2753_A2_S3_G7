# pages/history.py

import os
import streamlit as st
from PIL import Image

from auth import get_db, get_user_by_username
from db import Prediction, ChatLog
from utils import save_prediction_pdf

def history_page():
    st.title("Prediction History")
    st.markdown(
        "Here you can view your past predictions, download reports, or review AI conversations."
    )

    # ─── GLOBAL CSS ───
    st.markdown("""
        <style>
        /* PDF button = green */
        div[data-testid="stDownloadButton"] > button {
            background-color: #28a745 !important;
            color: white !important;
            white-space: nowrap !important; 
        }

        /* Delete button = red */
        div[data-testid="stButton"] > button {
            background-color: #dc3545 !important;
            color: white !important;
            white-space: nowrap !important; 
        }

        /* Make both buttons same size */
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stButton"] > button {
            padding: 0.75rem 1.5rem !important;
            font-size: 16px !important;
            border-radius: 0.5rem !important;
            line-height: 1.2 !important;
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ─── load user & predictions ───
    username = st.session_state.user
    db = next(get_db())
    user = get_user_by_username(db, username)
    preds = (
        db.query(Prediction)
          .filter(Prediction.user_id == user.id)
          .order_by(Prediction.timestamp.desc())
          .all()
    )

    if not preds:
        st.info("🛑 You have no past predictions yet.")
        return

    # ─── render each prediction ───
    for pred in preds:
        st.markdown("----")
        st.markdown(
            f"### Prediction ID: <span style='color:grey'>{pred.id}</span>",
            unsafe_allow_html=True
        )
        st.markdown("##### Overview")

        # four columns: thumbnail | details | PDF | Delete
        col1, col2, col3, col4 = st.columns([1, 4, 1, 1], gap="medium")

        # ─ thumbnail ─
        if os.path.exists(pred.image_path):
            col1.image(Image.open(pred.image_path), use_container_width =True)
        else:
            col1.warning("🖼️ Image not found")

        # ─ details ─
        with col2:
            st.markdown(f"""
              <p style="margin:0;color:grey"><strong>Date:</strong> {pred.timestamp:%Y-%m-%d %H:%M:%S}</p>
              <p style="margin:0;color:grey"><strong>Estimated Age:</strong> {pred.predicted_age:.1f} days</p>
              <p style="margin:0;color:grey"><strong>Variety:</strong> {pred.predicted_var}</p>
              <p style="margin:0;color:grey"><strong>Health Status:</strong> {pred.disease_label.capitalize()}</p>
            """, unsafe_allow_html=True)

        # ─ PDF download (green & sized) ─
        if os.path.exists(pred.image_path):
            pdf_bytes = save_prediction_pdf(
                age=pred.predicted_age,
                variety=pred.predicted_var,
                label=pred.disease_label,
                img=Image.open(pred.image_path)
            )
            col3.download_button(
                label="PDF",
                data=pdf_bytes,
                file_name=f"report_{pred.id}.pdf",
                mime="application/pdf",
                key=f"dl_{pred.id}"
            )

            with col4:
                delete = st.button("Delete", key=f"del_{pred.id}")

            if delete:
                db.delete(pred)
                db.commit()
                st.success("Prediction deleted.")
                st.rerun()

        # ─ AI Conversation expander ─
        with st.expander("💬 View AI Conversation", expanded=False):
            chats = (
                db.query(ChatLog)
                  .filter(ChatLog.prediction_id == pred.id)
                  .order_by(ChatLog.timestamp.asc())
                  .all()
            )
            if not chats:
                st.info("❌ No conversation was recorded for this prediction.")
            else:
                for log in chats:
                    st.chat_message("user").markdown(f"**You:** {log.user_question}")
                    st.chat_message("assistant").markdown(f"**AI:** {log.ai_response}")
