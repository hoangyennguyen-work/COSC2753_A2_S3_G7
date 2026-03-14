import os
import streamlit as st
from PIL import Image
from datetime import datetime
from pathlib import Path

from models import predict_all
from auth import get_db, get_user_by_username
from db import Prediction, ChatLog
from utils import save_prediction_pdf, gemini_chat
from config import (
    SYSTEM_PROMPT,
    INTERPRET_PROMPT,
    ADVICE_PROMPT
)

# Store images in a web-usable relative folder
PREDICT_IMG_DIR = Path("prediction_images")
PREDICT_IMG_DIR.mkdir(parents=True, exist_ok=True)

def predict_page():
    st.title("Paddy Prediction")
    st.write("Upload a clear JPG image, then click **Run Prediction**.")

    # Initialize expander state
    if "expander_open" not in st.session_state:
        st.session_state.expander_open = False

    uploaded_file = st.file_uploader("Choose a JPG image", type=["jpg", "jpeg"])
    img = None

    # ✅ Priority: new upload > session-stored image
    if uploaded_file:
        try:
            img = Image.open(uploaded_file)
            # Store bytes (not UploadedFile object) in session to fix reload errors
            st.session_state.uploaded_image_bytes = uploaded_file.getvalue()
            # Center the image preview with fixed width using columns
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.image(img, caption="✅ Uploaded Image Preview", width=200)
        except:
            st.error("⚠️ Invalid image; upload a JPG.")
    elif "uploaded_image_bytes" in st.session_state:
        try:
            img = Image.open(io.BytesIO(st.session_state.uploaded_image_bytes))
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.image(img, caption="✅ Uploaded Image Preview", width=200)
        except:
            st.error("⚠️ Invalid image in session; please upload again.")

    st.markdown("---")

    prediction_ran_now = False

    # Run Prediction

    if st.button("🔍 Run Prediction"):
        if img is None:
            st.error("Please upload an image first.")
            return

        username = st.session_state.user
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        fname = f"{username}_{ts}.jpg"

        # Save image to prediction_images/
        image_relative_path = f"prediction_images/{fname}"
        image_full_path = PREDICT_IMG_DIR / fname
        img.save(image_full_path)

        status = st.empty()
        status.info("🔄 Running prediction…")

        age, variety, label = predict_all(img)
        status.empty()

        db = next(get_db())
        user = get_user_by_username(db, username)

        pred = Prediction(
            user_id=user.id,
            image_path=image_relative_path,  # ✅ save relative path
            predicted_age=float(age),
            predicted_var=variety,
            disease_label=label
        )
        db.add(pred)
        db.commit()

        # Store in session
        st.session_state.current_prediction = {
            "id": pred.id,
            "age": age,
            "variety": variety,
            "label": label,
            "region": user.region
        }

        prediction_ran_now = True
        st.success("Saved to history")

        # Show prediction results (your custom styled HTML)
        st.markdown("### Prediction Results")
        c1, c2, c3 = st.columns(3)

        c1.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:16px; color:gray;">Age (days)</div>
                <div style="font-size:24px; font-weight:bold;">{age:.1f}</div>
            </div>
        """, unsafe_allow_html=True)

        c2.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:16px; color:gray;">Variety</div>
                <div style="font-size:24px; font-weight:bold;">{variety}</div>
            </div>
        """, unsafe_allow_html=True)

        c3.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:16px; color:gray;">Health</div>
                <div style="font-size:24px; font-weight:bold;">{label.capitalize()}</div>
            </div>
        """, unsafe_allow_html=True)

        # Add vertical spacing before the download button
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        pdf = save_prediction_pdf(age, variety, label, img)
        st.download_button(
            "📄 Export",
            data=pdf,
            file_name=f"report_{ts}.pdf",
            mime="application/pdf"
        )
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)


    # If not just predicted but we have existing prediction, show it
    if not prediction_ran_now and "current_prediction" in st.session_state:
        ctx = st.session_state["current_prediction"]
        st.markdown("""
        <h3 style="text-align: center; margin-bottom: 0.5em;">Prediction Results</h3>
    """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        # Replace st.metric() with your custom styled markdown for consistency:
        c1.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:16px; color:gray;">Age (days)</div>
                <div style="font-size:24px; font-weight:bold;">{ctx['age']:.1f}</div>
            </div>
        """, unsafe_allow_html=True)

        c2.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:16px; color:gray;">Variety</div>
                <div style="font-size:24px; font-weight:bold;">{ctx['variety']}</div>
            </div>
        """, unsafe_allow_html=True)

        c3.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:16px; color:gray;">Health</div>
                <div style="font-size:24px; font-weight:bold;">{ctx['label'].capitalize()}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- AI Assistant Section ---
    ctx = st.session_state.get("current_prediction")
    if not ctx:
        return

    pid = ctx["id"]
    age = ctx["age"]
    variety = ctx["variety"]
    label = ctx["label"]
    region = ctx["region"]

    with st.expander("AI Assistant", expanded=st.session_state.expander_open):
        hkey = f"history_{pid or 'temp'}"
        if hkey not in st.session_state:
            st.session_state[hkey] = [{
                "role": "assistant",
                "content": SYSTEM_PROMPT.format(region=region)
            }]
        history = st.session_state[hkey]

        for msg in history[1:]:
            st.chat_message(msg["role"]).markdown(msg["content"])
        st.markdown("---")

        col1, col2, col3 = st.columns([1.5, 1.5, 7.5])
        interpret_clicked = col1.button("Interpret", key=f"interpret_{pid}")
        advice_clicked = col2.button("Advice", key=f"advice_{pid}")
        user_q = col3.chat_input("Type your question...", key=f"chat_{pid}")

        prompt = None
        if interpret_clicked:
            prompt = INTERPRET_PROMPT.format(age=age, variety=variety, label=label, region=region)
        elif advice_clicked:
            prompt = ADVICE_PROMPT.format(age=age, variety=variety, label=label, region=region)
        elif user_q:
            prompt = user_q

        if prompt:
            st.session_state.expander_open = True  # Keep assistant open after rerun
            reply = gemini_chat(prompt, history)
            if pid:
                db = next(get_db())
                db.add(ChatLog(
                    prediction_id=pid,
                    user_question=prompt,
                    ai_response=reply
                ))
                db.commit()
            st.rerun()

