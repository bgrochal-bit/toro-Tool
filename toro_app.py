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
from openai import OpenAI

# --- INITIALIZE OpenAI (2026 Model Suite) ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) if "OPENAI_API_KEY" in st.secrets else None

# --- TORO BRANDING ---
TORO_NAVY = "#003152" 
TORO_GOLD = "#f4c244"

st.set_page_config(page_title="Toro AI Design Engine", layout="wide")

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {TORO_NAVY}; color: white; }}
    .stButton>button {{ background-color: {TORO_GOLD} !important; color: {TORO_NAVY} !important; font-weight: bold !important; width: 100%; }}
    .stTextArea>div>textarea, .stTextInput>div>div>input {{ background-color: rgba(255,255,255,0.1) !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- HELPER: ENCODE FOR VISION ---
def encode_img(file):
    return base64.b64encode(file.getvalue()).decode('utf-8')

# --- ENGINE: ADVANCED IMAGE SYNTHESIS (GPT-Image 2.0) ---
def generate_synthesized_image(uploaded_files, notes):
    if not client: return None
    # Use GPT-4o to analyze the multiple images and create a master prompt for GPT-Image 2.0
    msgs = [{"role": "user", "content": [{"type": "text", "text": f"Analyze these product references. Instructions: {notes}. Create a technical prompt for GPT-Image 2.0 to synthesize a BRAND NEW product mockup blending these elements. Do not just copy one image."}]}]
    for f in uploaded_files:
        msgs[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_img(f)}"}})
    
    analysis = client.chat.completions.create(model="gpt-4o", messages=msgs)
    master_prompt = analysis.choices[0].message.content
    
    # Call the 2026 Advanced Image Model
    gen = client.images.generate(model="gpt-image-2.0", prompt=master_prompt, size="1024x1024", quality="hd")
    return gen.data[0].url

# --- ENGINE: EDITABLE PPTX GENERATOR ---
def create_pptx(prod_name, version, mode, image_bytes, comments_data=[]):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6]) # Blank layout
    
    # 1. Add Header Bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(1))
    shape.fill.solid()
    shape.fill.foreground_color.rgb = RGBColor(0, 49, 82) # Toro Navy
    
    # 2. Add Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(5), Inches(0.5))
    title_box.text_frame.text = f"TORO | {mode.upper()}"
    title_box.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
    title_box.text_frame.paragraphs[0].font.bold = True

    # 3. Add Main Product Image
    img_stream = io.BytesIO(image_bytes)
    slide.shapes.add_picture(img_stream, Inches(0.5), Inches(1.5), height=Inches(5))

    # 4. If Feedback Mode: Add EDITABLE Arrows and Text Boxes
    if mode == "Feedback Card Generator" and comments_data:
        for item in comments_data:
            # item = {'x': float, 'y': float, 'text': str}
            # Add Arrow
            arrow = slide.shapes.add_shape(MSO_SHAPE.BENT_ARROW, Inches(6.5), Inches(2 + item['id']), Inches(1), Inches(0.5))
            arrow.fill.solid()
            arrow.fill.foreground_color.rgb = RGBColor(244, 194, 68) # Toro Gold
            
            # Add Comment Text Box
            txBox = slide.shapes.add_textbox(Inches(7.5), Inches(2 + item['id']), Inches(2), Inches(1))
            tf = txBox.text_frame
            tf.text = f"{item['id']}. {item['text']}"
            tf.paragraphs[0].font.size = Pt(12)

    ppt_io = io.BytesIO()
    prs.save(ppt_io)
    return ppt_io.getvalue()

# --- APP UI ---
st.title("TORO AI Design Engine (v2026.1)")
mode = st.radio("Select Tool", ["Tech Pack Generator", "Feedback Card Generator"], horizontal=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    prod_name = st.text_input("Product Name", value="") # Empty by default
    version = "P1" if mode == "Tech Pack Generator" else st.selectbox("Round", ["R1", "R2", "R3"])
    
    uploads = st.file_uploader("Upload Multiple Reference Images", accept_multiple_files=True)
    
    if mode == "Tech Pack Generator":
        notes = st.text_area("Nano Banana Pro: Synthesis Instructions", value="", placeholder="Example: Combine the handle from Image 1 with the body of Image 2. Make the finish matte black.")
        if st.button("SYNTHESIZE NEW PRODUCT IMAGE"):
            with st.spinner("GPT-Image 2.0 is generating new pixels..."):
                st.session_state['gen_url'] = generate_synthesized_image(uploads, notes)
        
        specs = st.text_area("Technical Specifications", value="")
    else:
        feedback = st.text_area("Feedback Comments", value="", placeholder="1. Move logo higher\n2. Change material to brushed aluminum...")
        if st.button("GENERATE AI MARKUP"):
            st.session_state['markup_done'] = True

with col2:
    if uploads:
        st.subheader("Output Preview")
        display_img = Image.open(uploads[0]) # Placeholder logic for preview
        
        if mode == "Tech Pack Generator" and 'gen_url' in st.session_state:
            st.image(st.session_state['gen_url'], caption="Synthesized via GPT-Image 2.0")
        else:
            st.image(display_img)

        # EXPORT BUTTONS
        st.write("---")
        # Prepare PPTX
        img_for_ppt = io.BytesIO()
        display_img.save(img_for_ppt, format="PNG")
        
        # Simulated comment data for the arrow logic
        mock_comments = [{'id': 1, 'text': 'Move logo 20mm up', 'x': 5, 'y': 2}] if mode == "Feedback Card Generator" else []

        pptx_data = create_pptx(prod_name, version, mode, img_for_ppt.getvalue(), mock_comments)
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 DOWNLOAD EDITABLE PPTX", data=pptx_data, file_name=f"Toro_{prod_name}.pptx")
        with c2:
            st.button("📥 DOWNLOAD PDF (Coming Soon)")

st.caption("© 2024 Toro Supply Chain Solutions | Built with GPT-Image 2.0 & Vision Infrastructure")
