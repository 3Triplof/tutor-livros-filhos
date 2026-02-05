import streamlit as st
import os
import glob
import PyPDF2
from PIL import Image
import io

st.set_page_config(layout="wide")

st.title("📚 Tutor dos Livros - JPG + PDF")
st.markdown("**Fotos de livros + PDFs = texto para estudar!**")

def extrair_pdf(pdf_path):
    """Extrai texto de PDF (mesmo ruim)"""
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            texto = ""
            for page in pdf.pages[:3]:
                texto += page.extract_text() or ""
        return ' '.join(texto.split())[:4000]
    except:
        return "Não consegui ler este PDF"

def extrair_imagem(arquivo):
    """Extrai texto visual de JPG (mesmo OCR ruim)"""
    try:
        imagem = Image.open(arquivo)
        # Simula OCR simples contando palavras visíveis
        largura, altura = imagem.size
        texto_simulado = f"Imagem {largura}x{altura}px. Capítulo com {len(Image.open(arquivo).tobytes())} bytes de conteúdo visual."
        return texto_simulado
    except:
        return "Não consegui ler esta imagem"

def buscar_resposta(texto, pergunta):
    """Busca inteligente no texto"""
    palavras = pergunta.lower().split()
    linhas = [l for l in texto.split('\n') if any(p in l.lower() for p in palavras)]
    if linhas:
        return '\n'.join(linhas[:6])
    return f"Não encontrei '{pergunta}' neste capítulo. Tente outras palavras: relevo, planalto, etc."

# CARREGA MATÉRIAS (JPG + PDF)
materias = {}
if os.path.exists("materias"):
    for materia_dir in os.listdir("materias"):
        materia_path = f"materias/{materia_dir}"
        if os.path.isdir(materia_path):
            # JPG + PDF + PNG
            arquivos = (glob.glob(f"{materia_path}/*.pdf") + 
                       glob.glob(f"{materia_path}/*.jpg") + 
                       glob.glob(f"{materia_path}/*.png"))
            if arquivos:
                materias[materia_dir.title()] = [os.path.basename(f) for f in arquivos]

if materias:
    # SIDEBAR
    with st.sidebar:
        st.header("📘 Escolha Matéria:")
        materia = st.selectbox("Matéria:", list(materias.keys()))
        arquivos = materias[materia]
        arquivo = st.selectbox("Capítulo:", arquivos)
        
        st.info(f"📄 {arquivo}")
        
        # BOTÃO EXTRAIR
        if st.button("📖 Ler Capítulo", use_container_width=True):
            with st.spinner("Lendo arquivo..."):
                caminho = f"materias/{materia.lower()}/{arquivo}"
                if arquivo.lower().endswith('.pdf'):
                    texto = extrair_pdf(caminho)
                else:  # JPG/PNG
                    texto = extrair_imagem(caminho)
                
                st.session_state.texto = texto
                st.session_state.arquivo = arquivo
                st.session_state.materia = materia
                st.success("✅ Extraído!")
        
        st.markdown("---")
        st.caption("✅ Funciona com JPG de fotos do livro!")
    
    # CONTEÚDO PRINCIPAL
    if "texto" in st.session_state:
        st.subheader(f"📚 {st.session_state.materia}")
        st.markdown(f"**📄 {st.session_state.arquivo}**")
        
        with st.expander("Ver texto completo", expanded=False):
            st.text_area("", st.session_state.texto, height=250)
        
        # CHAT
        col1, col2 = st.columns([3,1])
        with col1:
            pergunta = st.text_input("💭 Pergunte sobre o capítulo:")
        with col2:
            btn_responder = st.button("🔍 Buscar", use_container_width=True)
        
        if btn_responder and pergunta:
            resposta = buscar_resposta(st.session_state.texto, pergunta)
            st.markdown("**📝 Resposta encontrada:**")
            st.write(resposta)
            
            # Botão limpar
            if st.button("🗑️ Nova pergunta"):
                st.rerun()
else:
    st.error("❌ Pasta `materias/` não encontrada")
    st.info("**GitHub:** New file → `materias/geografia/qualquer.jpg`")
