import streamlit as st
from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image, ImageDraw
import datetime
import io
import os
import base64
import requests
from openai import OpenAI
import json

# --- INITIALIZE OpenAI ---
# Ensure you have OPENAI_API_KEY in Streamlit Cloud -> Settings -> Secrets
openai_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key) if openai_key else None

# --- TORO BRANDING ---
TORO_NAVY = (0, 49, 82)      
TORO_NAVY_HEX = "#003152"    
TORO_GOLD = (244, 194, 68)   
TORO_GOLD_HEX = "#f4c244"    

st.set_page_config(page_title="Toro AI Design Engine", layout="wide")

# --- CUSTOM CSS (Toro Website Look & Feel) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {TORO_NAVY_HEX}; color: white; }}
    .stButton>button {{ background-color: {TORO_GOLD_HEX} !important; color: {TORO_NAVY_HEX} !important; font-weight: bold !important; width: 100%; border: none; }}
    .stTextArea>div>textarea, .stTextInput>div>div>input {{ background-color: rgba(255,255,255,0.1) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    h1, h2, h3, p, label {{ color: white !important; font-family: 'Inter', sans-serif; }}
    </style>
    """, unsafe_allow_html=True)

# --- HELPERS ---
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def download_image(url):
    if not url or not url.startswith("http"):
        return None
    response = requests.get(url)
    return io.BytesIO(response.content)

# --- ENGINE: SYNTHESIS (GPT-4o Vision + DALL-E 3) ---
def synthesize_product(uploaded_files, instructions):
    if not client:
        st.error("OpenAI API Key not found. Please add it to Streamlit Secrets.")
        return None
    
    try:
        # GPT-4o analyzes textures/shape to write a DALL-E prompt
        msgs = [{"role": "user", "content": [{"type": "text", "text": f"Instructions: {instructions}. Create a professional, hyper-realistic product mockup prompt for DALL-E 3 based on these images."}]}]
        for f in uploaded_files:
            msgs[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(f.getvalue())}"}})
        
        analysis = client.chat.completions.create(model="gpt-4o", messages=msgs)
        prompt = analysis.choices[0].message.content
        
        gen = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="hd")
        return gen.data[0].url
    except Exception as e:
        st.error(f"Synthesis Failed: {e}")
        return None

# --- EXPORT ENGINE (Editable PPTX) ---
def export_pptx(prod_name, version, mode, img_bytes, comments_text):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Header Bar
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(0.8))
    rect.fill.solid()
    rect.fill.foreground_color.rgb = RGBColor(*TORO_NAVY)
    
    # Title logic
    header_title = "TECHNICAL SPECIFICATION" if mode == "Tech Pack Generator" else "FEEDBACK CARD"
    title_text = f"TORO | {header_title} | {version}"
    
    title = slide.shapes.add_textbox(Inches(0.2), Inches(0.1), Inches(8), Inches(0.5))
    tf = title.text_frame
    tf.text = title_text
    tf.paragraphs[0].font.color.rgb = RGBColor(255,255,255)
    tf.paragraphs[0].font.bold = True
    
    # Product Image
    slide.shapes.add_picture(io.BytesIO(img_bytes), Inches(0.5), Inches(1.2), height=Inches(5))
    
    # Editable Comments & Arrows for Feedback
    if mode == "Feedback Card Generator" and comments_text:
        lines = comments_text.split('\n')
        for i, line in enumerate(lines[:5]): # Limit to first 5 for layout
            if line.strip():
                # Text Box
                tb = slide.shapes.add_textbox(Inches(6.2), Inches(1.5 + (i*0.9)), Inches(3.5), Inches(0.8))
                tb.text_frame.word_wrap = True
                tb.text_frame.text = line.strip()
                # Arrow
                arrow = slide.shapes.add_shape(MSO_SHAPE.BENT_ARROW, Inches(5.7), Inches(1.6 + (i*0.9)), Inches(0.4), Inches(0.4))
                arrow.fill.solid()
                arrow.fill.foreground_color.rgb = RGBColor(*TORO_GOLD)

    ppt_io = io.BytesIO()
    prs.save(ppt_io)
    return ppt_io.getvalue()

# --- APP UI ---
col_logo_1, col_logo_2 = st.columns([1, 4])
with col_logo_1:
    if os.path.exists("logo.png"): st.image("logo.png", width=180)
st.markdown("<h1 style='text-align: center;'>Simplify Your Design. Scale Your Business.</h1>", unsafe_allow_html=True)

mode = st.radio("Select Action", ["Tech Pack Generator", "Feedback Card Generator"], horizontal=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Design Inputs")
    prod_name = st.text_input("Product Name", value="")
    version = "P1" if mode == "Tech Pack Generator" else st.selectbox("Select Round", ["R1", "R2", "R3"])
    
    uploads = st.file_uploader("Upload Image References", accept_multiple_files=True)
    
    if mode == "Tech Pack Generator":
        notes = st.text_area("Synthesis Instructions", placeholder="Describe how to blend images...")
        if st.button("GENERATE NEW PRODUCT IMAGE"):
            with st.spinner("AI Synthesizing New Mockup..."):
                url = synthesize_product(uploads, notes)
                img_data = download_image(url)
                if img_data:
                    st.session_state['gen_bytes'] = img_data.getvalue()
        
        specs = st.text_area("Final Specifications", value="")
    else:
        feedback = st.text_area("Feedback Comments", placeholder="1. Comment one\n2. Comment two...")

with col2:
    st.subheader("2. Visual Output")
    active_img = None
    
    if mode == "Tech Pack Generator" and 'gen_bytes' in st.session_state:
        active_img = st.session_state['gen_bytes']
        st.image(active_img, caption="AI Synthesized Mockup")
    elif uploads:
        active_img = uploads[0].getvalue()
        st.image(active_img, caption="Reference Preview")

    if active_img:
        st.write("---")
        ppt_data = export_pptx(prod_name, version, mode, active_img, feedback if mode == "Feedback Card Generator" else "")
        st.download_button(f"📥 DOWNLOAD EDITABLE {version} PPTX", data=ppt_data, file_name=f"Toro_{prod_name}.pptx")

st.divider()
st.caption("© 2024 Toro Supply Chain Solutions | Better supply chains, Built together.")
