import streamlit as st
from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image
import datetime
import io
import os
import base64
import requests
from openai import OpenAI

# --- INITIALIZE OpenAI (Tier 1 / GPT-5.1 Optimized) ---
openai_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key) if openai_key else None

# --- TORO BRANDING ---
TORO_NAVY_HEX = "#003152"    
TORO_GOLD_HEX = "#f4c244"    

st.set_page_config(page_title="Toro AI Design Engine v5.1", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {TORO_NAVY_HEX}; color: white; }}
    .stButton>button {{ background-color: {TORO_GOLD_HEX} !important; color: {TORO_NAVY_HEX} !important; font-weight: bold !important; border-radius: 4px; }}
    .stTextArea>div>textarea, .stTextInput>div>div>input {{ background-color: rgba(255,255,255,0.1) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    h1, h2, h3, p, label {{ color: white !important; font-family: 'Inter', sans-serif; }}
    </style>
    """, unsafe_allow_html=True)

# --- HELPERS ---
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def download_image(url):
    try:
        response = requests.get(url)
        return io.BytesIO(response.content)
    except:
        return None

# --- AI ENGINE: GPT-5.1 ARCHITECT ---
def synthesize_product(uploaded_files, instructions):
    if not client: return "ERROR: API Key Missing"
    try:
        # Using GPT-5.1 for the highest fidelity design reasoning
        msgs = [{"role": "user", "content": [{"type": "text", "text": f"Instruction: {instructions}. Create a professional, hyper-realistic product mockup prompt for the generation engine based on these reference images. Focus on material texture and Toro branding."}]}]
        for f in uploaded_files:
            msgs[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(f.getvalue())}"}})
        
        # GPT-5.1 Vision Analysis
        analysis = client.chat.completions.create(model="gpt-5.1", messages=msgs)
        master_prompt = analysis.choices[0].message.content
        
        # Image Generation (Using the most advanced image model available in your Tier)
        gen = client.images.generate(model="dall-e-3", prompt=master_prompt, size="1024x1024", quality="hd")
        return gen.data[0].url
    except Exception as e:
        if "insufficient_quota" in str(e):
            return "ERROR: Account Balance is $0. Click 'Buy credits' in OpenAI Billing."
        return f"ERROR: {str(e)}"

# --- EXPORT LOGIC (Editable PPTX & Pro PDF) ---
def create_docs(prod_name, version, mode, img_bytes, notes):
    # PPTX Generation
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(0.8))
    rect.fill.solid()
    rect.fill.foreground_color.rgb = RGBColor(0, 49, 82)
    
    title_header = "TECHNICAL SPECIFICATION" if mode == "Tech Pack Generator" else "FEEDBACK CARD"
    title_box = slide.shapes.add_textbox(Inches(0.2), Inches(0.1), Inches(8), Inches(0.5))
    title_box.text_frame.text = f"TORO | {title_header} | {version}"
    title_box.text_frame.paragraphs[0].font.color.rgb = RGBColor(255,255,255)
    
    slide.shapes.add_picture(io.BytesIO(img_bytes), Inches(0.5), Inches(1.2), height=Inches(5))
    
    # Editable Comments for Feedback Card
    if mode == "Feedback Card Generator":
        tb = slide.shapes.add_textbox(Inches(6.2), Inches(1.5), Inches(3.5), Inches(4))
        tb.text_frame.word_wrap = True
        tb.text_frame.text = f"DESIGNER FEEDBACK:\n\n{notes}"
        arrow = slide.shapes.add_shape(MSO_SHAPE.BENT_ARROW, Inches(5.7), Inches(1.6), Inches(0.4), Inches(0.4))
        arrow.fill.solid()
        arrow.fill.foreground_color.rgb = RGBColor(244, 194, 68)

    ppt_io = io.BytesIO()
    prs.save(ppt_io)
    return ppt_io.getvalue()

# --- UI LAYOUT ---
col_logo_1, col_logo_2 = st.columns([1, 4])
with col_logo_1:
    if os.path.exists("logo.png"): st.image("logo.png", width=180)
st.markdown("<h1 style='text-align: center;'>Simplify Your Design. Scale Your Business.</h1>", unsafe_allow_html=True)

mode = st.radio("Tool Mode", ["Tech Pack Generator", "Feedback Card Generator"], horizontal=True)

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("Inputs")
    prod_name = st.text_input("Product Name")
    version = "P1" if mode == "Tech Pack Generator" else st.selectbox("Round", ["R1", "R2", "R3"])
    uploads = st.file_uploader("References", accept_multiple_files=True)
    
    if mode == "Tech Pack Generator":
        instr = st.text_area("GPT-5.1 Synthesis Instructions")
        if st.button("SYNTHESIZE NEW PRODUCT"):
            with st.spinner("GPT-5.1 analyzing and generating..."):
                res = synthesize_product(uploads, instr)
                if res.startswith("ERROR"): st.error(res)
                else: 
                    img_data = download_image(res)
                    if img_data: st.session_state['gen_bytes'] = img_data.getvalue()
        notes_to_export = st.text_area("Final Specifications")
    else:
        notes_to_export = st.text_area("Feedback Comments")

with c2:
    st.subheader("Output Preview")
    active_img = None
    if mode == "Tech Pack Generator" and 'gen_bytes' in st.session_state:
        active_img = st.session_state['gen_bytes']
        st.image(active_img, caption="GPT-5.1 Synthesized Output")
    elif uploads:
        active_img = uploads[0].getvalue()
        st.image(active_img, caption="Reference Upload")

    if active_img:
        st.write("---")
        pptx_data = create_docs(prod_name, version, mode, active_img, notes_to_export)
        st.download_button(f"📥 DOWNLOAD {version} EDITABLE PPTX", data=pptx_data, file_name=f"Toro_{prod_name}.pptx")
