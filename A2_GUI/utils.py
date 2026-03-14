# utils.py
 
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors  
from PIL import Image
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
 
def save_prediction_pdf(age: float, variety: str, label: str, img: Image.Image) -> bytes:
    """
    Generate a nicer‑looking PDF report but keep the same I/O contract.
    """
    buffer = io.BytesIO()
    c       = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    # ── 1) Header bar ──────────────────────────────────────────────────
    header_h = 60
    c.setFillColor(colors.HexColor("#A1B37D "))  
    c.rect(0, height - header_h, width, header_h, stroke=0, fill=1)
 
    # Report title – centered
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.white)
    c.drawCentredString(width / 2, height - header_h + 26, "Paddy Prediction Report")
 
    # Centered timestamp below the title
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#eeeeee"))
    now = datetime.now().strftime("Generated on: %Y-%m-%d  %H:%M:%S")
    c.drawCentredString(width / 2, height - header_h + 10, now)
 
    # Reset fill color for rest of the page
    c.setFillColor(colors.black)
 
 
    # ── 2) Image block ────────────────────────────────────────────────
    # convert PIL → ImageReader
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG")
    img_buf.seek(0)
    rl_img = ImageReader(img_buf)
 
    # scale to 70 % page width, preserve aspect
    max_w = width * 0.7
    aspect = img.height / img.width
    img_w  = max_w
    img_h  = img_w * aspect
    if img_h > height * 0.4:
        img_h = height * 0.4
        img_w = img_h / aspect
 
    # centred horizontally
    img_x = (width - img_w) / 2
    img_y = height - header_h - img_h - 40
    c.drawImage(rl_img, img_x, img_y, width=img_w, height=img_h, mask='auto')
    # subtle border
    c.setLineWidth(0.3)
    c.rect(img_x, img_y, img_w, img_h)
 
    # ── 3) Prediction details “card” (centered and padded) ──────────────
    card_h = 100
    card_w = width * 0.6  # narrower for centering
    card_padding = 20
    card_x = (width - card_w) / 2
    card_y = img_y - card_h - 50  # more spacing from image
 
    # background
    c.setFillColor(colors.HexColor("#f6f8f3"))
    c.roundRect(card_x, card_y, card_w, card_h, 8, stroke=0, fill=1)
 
    # title
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1e5631"))
    c.drawString(card_x + card_padding, card_y + card_h - 24, "Prediction Summary")
 
    # details
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    details = [
        f"Age (days):   {age:.1f}",
        f"Variety:      {variety}",
        f"Health:       {label.capitalize()}",
    ]
    for i, line in enumerate(details):
        c.drawString(card_x + card_padding, card_y + card_h - 44 - i * 20, line)
 
    # ── 4) Footer line (optional) ─────────────────────────────────────
    c.setStrokeColor(colors.HexColor("#9BAF7C"))
    c.setLineWidth(0.8)
    c.line(40, 40, width - 40, 40)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 28, "© 2025 Paddy Doctor")
 
    # ── Finish ────────────────────────────────────────────────────────
    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
 
# Initialize the client
_client = genai.Client(api_key=GEMINI_API_KEY)
 
def gemini_chat(user_message: str, history: list[dict]) -> str:
    """
    Send the full chat history + this user message to Gemini 2.0 Flash
    and return the assistant's reply.
    """
    # 1) Record user turn
    history.append({"role": "user", "content": user_message})
 
    # 2) Extract just the text parts for generate_content
    #    The SDK will wrap each string as user/model based on turn ordering.
    contents = [msg["content"] for msg in history]
 
    # 3) Call generate_content (NOT chat_model)
    response = _client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents
    )
 
    # 4) Extract and record assistant turn
    reply = response.text
    history.append({"role": "assistant", "content": reply})
 
    return reply