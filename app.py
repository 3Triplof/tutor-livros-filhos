import streamlit as st
import os, glob, PyPDF2, requests, base64
from PIL import Image

st.set_page_config(layout="wide")

st.title("🤖 Tutor Livros - GOOGLE VISION OCR")
st.markdown("**Foto JPG → TEXTO REAL do livro!**")

# API Key do Secrets
VISION_KEY = st.secrets.get("GOOGLE_VISION_KEY", "")

def google_vision_ocr(image_path):
    """OCR REAL - funciona com fotos ruins de livros"""
    try:
        # Lê imagem
        with open(image_path, "rb") as f:
            image_content = base64.b64encode(f.read()).decode()
        
        # Google Vision API
        url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_KEY}"
        payload = {
            "requests": [{
                "image": {"content": image_content},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["pt"]}
            }]
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        texto = data['responses'][0].get('fullTextAnnotation', {}).get('text', 'Erro OCR')
        return texto.strip()[:5000]
    except Exception as e:
        return f"Erro OCR: {str(e)}"

def extrair_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            texto = ""
            for page in pdf.pages[:2]:
                texto += page.extract_text() or ""
        return ' '.join(texto.split())[:3000]
    except:
        return "Erro PDF"

def buscar_no_texto(texto, pergunta):
    linhas = [l for l in texto.split('\n') if any(p in l.lower() for p in pergunta.lower().split())]
    return '\n'.join(linhas[:10]) if linhas else "Não encontrei no capítulo :("

# Sidebar - suas fotos
materias = {}
if os.path.exists("materias"):
    for dir in os.listdir("materias"):
        path = f"materias/{dir}"
        if os.path.isdir(path):
            files = glob.glob(f"{path}/*.jpg") + glob.glob(f"{path}/*.png") + glob.glob(f"{path}/*.pdf")
            if files:
                materias[dir.title()] = [os.path.basename(f) for f in files]

# INTERFACE
if materias:
    with st.sidebar:
        st.header("📚 Matérias")
        materia = st.selectbox("Matéria:", list(materias.keys()))
        arquivos = materias[materia]
        arquivo = st.selectbox("Foto/Capítulo:", arquivos)
        
        if VISION_KEY:
            if st.button("🧿 GOOGLE OCR", use_container_width=True):
                with st.spinner("Lendo foto com Google Vision..."):
                    caminho = f"materias/{materia.lower()}/{arquivo}"
                    if arquivo.lower().endswith(('.jpg', '.png')):
                        texto = google_vision_ocr(caminho)
                    else:
                        texto = extrair_pdf(caminho)
                    
                    st.session_state.texto = texto
                    st.session_state.arquivo = arquivo
                    st.success("✅ Texto extraído!")
        else:
            st.error("❌ Configure GOOGLE_VISION_KEY em Secrets!")
    
    # Resultado OCR
    if "texto" in st.session_state:
        st.subheader(f"📄 {st.session_state.arquivo}")
        st.text_area("Texto reconhecido:", st.session_state.texto, height=400)
        
        pergunta = st.text_input("💭 Pergunta:")
        if st.button("🔍 Buscar") and pergunta:
            resposta = buscar_no_texto(st.session_state.texto, pergunta)
            st.markdown(f"**📝 Encontrei:**\n{resposta}")
else:
    st.error("📁 Crie: materias/geografia/cap13-001-geografia.jpg")
