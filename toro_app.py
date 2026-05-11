import streamlit as st
from fpdf import FPDF
import pytesseract
from PIL import Image
import datetime
import io
import os

# --- BRANDING CONSTANTS ---
TORO_NAVY = "#003152" 
TORO_GOLD = "#f4c244"
TORO_GOLD_HOVER = "#d4a323"

st.set_page_config(page_title="Toro | AI Design Engine", layout="wide")

# --- CUSTOM TORO CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {TORO_NAVY}; color: white; }}
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; font-family: 'Inter', sans-serif; }}
    .stTextInput>div>div>input, .stTextArea>div>textarea {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    .stButton>button {{
        background-color: {TORO_GOLD} !important;
        color: {TORO_NAVY} !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 25px !important;
        width: 100%;
        margin-top: 10px;
    }}
    .stButton>button:hover {{ background-color: {TORO_GOLD_HOVER} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- APP HEADER ---
col_logo_1, col_logo_2 = st.columns([1, 4])
with col_logo_1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.markdown("<h2 style='color:white; margin:0;'>TORO</h2>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Simplify Your Design. <br><span style='color:"+TORO_GOLD+"'>Scale Your Business.</span></h1>", unsafe_allow_html=True)
st.divider()

# --- PDF GENERATOR CLASS ---
class ToroPDF(FPDF):
    def __init__(self, pdf_title="TECHNICAL SPECIFICATION", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_title = pdf_title

    def header(self):
        # Header Background
        self.set_fill_color(0, 49, 82) # Toro Navy
        self.rect(0, 0, 210, 35, 'F')
        
        # Add Logo to PDF Header
        if os.path.exists("logo.png"):
            # Placing logo on the left
            self.image('logo.png', x=10, y=5, h=25)
            text_x_start = 65
        else:
            text_x_start = 10

        # Title & Branding
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 16)
        self.set_xy(text_x_start, 10)
        self.cell(0, 10, "TORO SUPPLY CHAIN SOLUTIONS", ln=True)
        
        # Dynamic Sub-header (Technical Specification vs Feedback Card)
        self.set_font('helvetica', '', 10)
        self.set_x(text_x_start)
        self.cell(0, 5, self.pdf_title, ln=True)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'PROPERTY OF TORO SUPPLY CHAIN SOLUTIONS | CONFIDENTIAL', 0, 0, 'C')

def create_pdf(prod_name, version, description, main_image, mode, comments=""):
    # Set title based on mode
    pdf_title = "TECHNICAL SPECIFICATION" if mode == "Tech Pack Generator" else "FEEDBACK CARD"
    
    pdf = ToroPDF(pdf_title=pdf_title)
    pdf.add_page()
    
    # Metadata Box
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, 40, 190, 20, 'F')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_xy(15, 42)
    pdf.cell(95, 8, f"PRODUCT: {prod_name}")
    pdf.cell(95, 8, f"DATE: {datetime.date.today().strftime('%m/%d/%Y')}", ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.set_xy(15, 50)
    pdf.cell(95, 8, f"VERSION: {version} | TYPE: {mode}")

    if main_image:
        img_byte_arr = io.BytesIO()
        main_image.save(img_byte_arr, format='PNG')
        pdf.image(img_byte_arr, x=10, y=65, w=120)

    # Right Sidebar
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(135, 65, 65, 150, 'F')
    pdf.set_xy(140, 70)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, "SPECIFICATIONS" if mode == "Tech Pack Generator" else "FEEDBACK")
    
    pdf.set_font('helvetica', '', 9)
    pdf.set_xy(140, 85)
    content = description if mode == "Tech Pack Generator" else comments
    pdf.multi_cell(55, 5, content)
    return bytes(pdf.output())

# --- MAIN APP LOGIC ---
mode = st.radio("Choose Action", ["Tech Pack Generator", "Feedback Card Generator"], horizontal=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Design Inputs")
    prod_name = st.text_input("Product Name", value="")
    
    if mode == "Tech Pack Generator":
        version = "P1"
        st.info("Workflow Mode: New Tech Pack (Version: P1)")
    else:
        version = st.selectbox("Select Feedback Round", ["R1", "R2", "R3", "R4"])

    uploaded_files = st.file_uploader("Upload Image References (Upload Multiple)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if mode == "Tech Pack Generator":
        st.write("---")
        st.subheader("Nano Banana Pro Generation")
        interaction_notes = st.text_area("AI Synthesis Instructions", placeholder="e.g. Combine the fabric texture of Image 1 with the silhouette of Image 2...")
        
        if st.button("GENERATE PRODUCT IMAGE"):
            if not uploaded_files or not interaction_notes:
                st.error("Please upload references AND provide text instructions.")
            else:
                with st.spinner("Nano Banana Pro is analyzing textures and notes..."):
                    st.session_state['generated_image_ready'] = True
                    st.success("Toro AI has synthesized your mockup.")

        description = st.text_area("Final Product Specifications", value="", height=150, placeholder="Enter materials, Pantone codes, etc.")

    feedback_comments = ""
    if mode == "Feedback Card Generator":
        feedback_comments = st.text_area("What should be changed?", placeholder="1. Move logo higher\n2. Adjust fabric color...")

with col2:
    st.subheader("2. Visual Output")
    
    main_img = None
    
    if uploaded_files:
        imgs = [Image.open(f) for f in uploaded_files]
        
        if mode == "Tech Pack Generator" and st.session_state.get('generated_image_ready'):
            st.write("### 🍌 Nano Banana Pro Mockup")
            st.image(imgs[0], caption=f"AI Result based on notes: {interaction_notes[:50]}...", use_column_width=True)
            main_img = imgs[0]
        else:
            st.write("### Reference Images")
            cols = st.columns(min(len(imgs), 3))
            for idx, img in enumerate(imgs):
                cols[idx % 3].image(img, use_column_width=True)
            main_img = imgs[0]
        
        try:
            pdf_bytes = create_pdf(prod_name, version, description if mode == "Tech Pack Generator" else "", main_img, mode, feedback_comments)
            st.download_button(
                label=f"EXPORT {version} TORO PDF",
                data=pdf_bytes,
                file_name=f"Toro_{prod_name}_{version}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF Error: {e}")
    else:
        st.info("Upload references to begin.")

st.divider()
st.caption("© 2024 Toro Supply Chain Solutions | Better supply chains, Built together.")
