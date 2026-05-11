import streamlit as st
from fpdf import FPDF
import pytesseract
from PIL import Image
import datetime
import io
import os

# --- BRANDING CONSTANTS ---
TORO_NAVY = "#003152"  # Deep navy from your screenshot
TORO_GOLD = "#f4c244"  # Gold from the "Talk to an Expert" button
TORO_GOLD_HOVER = "#d4a323"

st.set_page_config(page_title="Toro | AI Design Engine", layout="wide")

# --- CUSTOM TORO CSS (Matching the Website Screenshot) ---
st.markdown(f"""
    <style>
    /* Global Background */
    .stApp {{
        background-color: {TORO_NAVY};
        color: white;
    }}
    
    /* Header Area */
    .toro-nav {{
        background-color: white;
        padding: 10px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid {TORO_GOLD};
        margin-bottom: 30px;
        border-radius: 4px;
    }}
    
    /* Text Styles */
    h1, h2, h3, p, label, .stMarkdown {{
        color: white !important;
        font-family: 'Inter', sans-serif;
    }}

    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>textarea {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* Toro Gold Buttons */
    .stButton>button {{
        background-color: {TORO_GOLD} !important;
        color: {TORO_NAVY} !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 25px !important;
        border-radius: 4px !important;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        background-color: {TORO_GOLD_HOVER} !important;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }}

    /* Radio Button Styles */
    .stRadio>div {{
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- APP HEADER (NAV BAR) ---
col_logo_1, col_logo_2 = st.columns([1, 4])
with col_logo_1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.markdown("<h2 style='color:white; margin:0;'>TORO</h2>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Simplify Your Design. <br><span style='color:"+TORO_GOLD+"'>Scale Your Business.</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.8;'>Toro AI-native technology that reduces cost and puts control back where it belongs with you.</p>", unsafe_allow_html=True)
st.divider()

# --- PDF GENERATOR CLASS ---
class ToroPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 49, 82) # Toro Navy
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 16)
        self.set_xy(10, 10)
        self.cell(0, 10, "TORO SUPPLY CHAIN SOLUTIONS", ln=True)
        self.set_font('helvetica', '', 10)
        self.cell(0, 5, "TECHNICAL SPECIFICATION", ln=True)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'PROPERTY OF TORO SUPPLY CHAIN SOLUTIONS | CONFIDENTIAL', 0, 0, 'C')

def create_pdf(prod_name, version, description, image, mode, comments=""):
    pdf = ToroPDF()
    pdf.add_page()
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

    if image:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        pdf.image(img_byte_arr, x=10, y=65, w=120)

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
    st.subheader("Configuration")
    prod_name = st.text_input("Product Name", "Americana Olly")
    version = st.selectbox("Round/Version", ["P1", "P2", "P3", "R1", "R2"])
    
    uploaded_file = st.file_uploader("Upload Sample Photo", type=["png", "jpg", "jpeg"])
    
    # CONDITION: Hide Description for Feedback Generator
    description = ""
    if mode == "Tech Pack Generator":
        if uploaded_file and st.button("AI Spec Extraction (OCR)"):
            with st.spinner("Analyzing..."):
                ocr_result = pytesseract.image_to_string(Image.open(uploaded_file))
                st.session_state['ocr_text'] = ocr_result
        
        description = st.text_area("Product Description / Tech Specs", 
                                   value=st.session_state.get('ocr_text', ""),
                                   height=200)

    feedback_comments = ""
    if mode == "Feedback Card Generator":
        feedback_comments = st.text_area("What should be changed?", placeholder="1. Move logo higher\n2. Adjust fabric color...")

with col2:
    st.subheader("Live Preview")
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_column_width=True)
        
        try:
            pdf_bytes = create_pdf(prod_name, version, description, img, mode, feedback_comments)
            st.download_button(
                label="GENERATE FINAL TORO PDF",
                data=pdf_bytes,
                file_name=f"Toro_{prod_name}_{version}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF Error: {e}")
    else:
        st.info("Please upload an image to generate the preview.")

st.divider()
st.caption("© 2024 Toro Supply Chain Solutions | Better supply chains, Built together.")
