import streamlit as st
import os
import glob
from pptxtpl import PdfToText  # Não, espera - vamos usar pytesseract

import streamlit as st
import os
from PIL import Image
import pytesseract
import io
import PyPDF2

st.set_page_config(layout="wide")

st.title("📚 Tutor dos Livros - PDFs + Fotos")
st.markdown("**Converte fotos de livros em texto + faz perguntas!**")

# SIDEBAR - escolhe matéria
if os.path.exists("materias"):
    materias = {}
    for materia in os.listdir("materias"):
        path = f"materias/{materia}"
        if os.path.isdir(path):
            arquivos = glob.glob(f"{path}/*.pdf") + glob.glob(f"{path}/*.jpg") + glob.glob(f"{path}/*.png")
            if arquivos:
                materias[materia.title()] = [os.path.basename(f) for f in arquivos]
    
    if materias:
        materia = st.sidebar.selectbox("Matéria:", list(materias.keys()))
        arquivos = materias[materia]
        arquivo = st.sidebar.selectbox("Capítulo:", arquivos)
        
        caminho = f"materias/{materia.lower()}/{arquivo}"
        st.sidebar.success(f"📖 {materia} - {arquivo}")
        
        # BOTÃO para extrair texto melhorado
        if st.sidebar.button("🔄 Extrair Texto", use_container_width=True):
            with st.spinner("Lendo PDF/Foto..."):
                if arquivo.endswith('.pdf'):
                    texto = extrair_pdf_melhorado(caminho)
                else:  # JPG/PNG
                    texto = extrair_imagem(caminho)
                
                st.session_state.texto = texto
                st.session_state.arquivo = arquivo
                st.success("✅ Texto extraído!")
        
        # UPLOAD NOVA FOTO ( direto na sidebar)
        uploaded_file = st.sidebar.file_uploader("📸 Nova foto do livro?", type=['jpg','png','pdf'])
        if uploaded_file:
            with open(f"materias/{materia.lower()}/{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.success(f"✅ {uploaded_file.name} salvo!")
            st.rerun()
    
    # CONTEÚDO EXTRAÍDO
    if "texto" in st.session_state:
        st.subheader(f"📄 {st.session_state.arquivo}")
        st.text_area("Texto do livro:", st.session_state.texto[:2000], height=300)
        
        # CHAT INTELIGENTE
        pergunta = st.text_input("💭 Pergunta sobre o capítulo:")
        if st.button("🔍 Responder") and pergunta:
            resposta = buscar_resposta(st.session_state.texto, pergunta)
            st.markdown(f"**📝 Resposta:**\n{resposta}")
else:
    st.error("Crie: materias/geografia/")

# FUNÇÕES MELHORADAS
def extrair_pdf_melhorado(pdf_path):
    texto = ""
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page in pdf.pages[:2]:
                texto += page.extract_text() or ""
    except:
        texto = "Erro no PDF - use foto JPG"
    return limpar_texto(texto)

def extrair_imagem(img_path):
    imagem = Image.open(img_path)
    texto = pytesseract.image_to_string(imagem, lang='por')  # Português!
    return limpar_texto(texto)

def limpar_texto(texto):
    return ' '.join(texto.split())[:5000]

def buscar_resposta(texto, pergunta):
    linhas = [l for l in texto.split('\n') if any(palavra in l.lower() 
                for palavra in pergunta.lower().split())][:6]
    return '\n'.join(linhas) if linhas else "Não encontrei esta resposta no capítulo :("
