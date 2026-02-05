import streamlit as st
import os, glob, PyPDF2, requests, base64
from PIL import Image

st.set_page_config(layout="wide")

st.title("🤖 Tutor Livros - GOOGLE VISION + DIAGNÓSTICO")
st.markdown("**Seu assistente de estudos!**")

VISION_KEY = st.secrets.get("GOOGLE_VISION_KEY", "")

def diagnosticar_vision_key():
    """Testa se API Key funciona"""
    if not VISION_KEY or VISION_KEY == "":
        return "❌ Vazio - configure Secrets"
    if not VISION_KEY.startswith("AIza"):
        return "❌ Formato inválido"
    return "✅ OK!"

def google_vision_ocr(image_path):
    """OCR com tratamento de TODOS os erros"""
    try:
        # Lê imagem
        with open(image_path, "rb") as f:
            image_content = base64.b64encode(f.read()).decode()
        
        url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_KEY}"
        payload = {
            "requests": [{
                "image": {"content": image_content},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["pt"]}
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        
        # 🔧 TRATAMENTO DE ERROS
        print(f"Status: {response.status_code}")
        print(f"Resposta: {data}")
        
        if response.status_code != 200:
            return f"❌ HTTP {response.status_code}: {data.get('error', {}).get('message', 'Erro desconhecido')}"
        
        if 'error' in data:
            return f"❌ API Error: {data['error'].get('message', 'Erro genérico')}"
        
        if 'responses' not in data or not data['responses']:
            return "❌ Sem 'responses' na resposta - API falhou"
        
        response_data = data['responses'][0]
        if 'error' in response_data:
            return f"❌ Imagem Error: {response_data['error'].get('message', 'Erro na imagem')}"
        
        texto = response_data.get('fullTextAnnotation', {}).get('text', 'Sem texto detectado')
        return texto.strip()[:5000] if texto else "Texto vazio"
        
    except Exception as e:
        return f"❌ Exceção: {str(e)}"

def extrair_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            texto = ""
            for page in pdf.pages[:2]:
                texto += page.extract_text() or ""
        return texto[:3000]
    except:
        return "Erro PDF"

def buscar_no_texto(texto, pergunta):
    """Busca inteligente no texto"""
    linhas = [l for l in texto.split('\n') if any(p in l.lower() for p in pergunta.lower().split())]
    return '\n'.join(linhas[:10]) if linhas else "Não encontrei no capítulo :("

# Sidebar
materias = {}
if os.path.exists("materias"):
    for dir in os.listdir("materias"):
        path = f"materias/{dir}"
        if os.path.isdir(path):
            files = glob.glob(f"{path}/*.jpg") + glob.glob(f"{path}/*.png") + glob.glob(f"{path}/*.pdf")
            if files:
                materias[dir.title()] = [os.path.basename(f) for f in files]

if materias:
    with st.sidebar:
        st.header("📚 Matérias")
        materia = st.selectbox("Matéria:", list(materias.keys()))
        arquivos = materias[materia]
        arquivo = st.selectbox("Foto:", arquivos)
        
        # Status API Key
        st.markdown("---")
        status = diagnosticar_vision_key()
        st.caption(f"🔑 Vision API: **{status}**")
        
        if st.button("🧿 GOOGLE OCR", use_container_width=True):
            caminho = f"materias/{materia.lower()}/{arquivo}"
            with st.spinner("Testando Google Vision..."):
                if arquivo.lower().endswith(('.jpg', '.png')):
                    texto = google_vision_ocr(caminho)
                else:
                    texto = extrair_pdf(caminho)
                
                st.session_state.texto = texto
                st.session_state.arquivo = arquivo
                st.session_state.materia = materia
                st.rerun()
    
    # ===== RESULTADO COM MOSTRAR/OCULTAR =====
    if "texto" in st.session_state:
        st.subheader(f"📄 {st.session_state.arquivo}")
        
        # Diagnóstico colorido
        texto = st.session_state.texto
        if texto.startswith("❌"):
            st.error(texto)
        elif "HTTP" in texto or "Error" in texto:
            st.warning(texto)
        else:
            st.success("✅ OCR funcionou!")
            
            # 🔽 NOVO: Checkbox mostrar/ocultar
            mostrar_texto = st.checkbox("👁️ Mostrar texto reconhecido", value=False)
            if mostrar_texto:
                st.text_area("Texto completo:", texto, height=400, key="texto_area")
            
            # 🔍 Busca (sempre visível)
            col1, col2 = st.columns([3, 1])
            with col1:
                pergunta = st.text_input("💭 Pergunta sobre o capítulo:")
            with col2:
                buscar = st.button("🔍 Buscar", use_container_width=True)
            
            if buscar and pergunta:
                resposta = buscar_no_texto(st.session_state.texto, pergunta)
                st.markdown("**📝 Resposta encontrada:**")
                st.write(resposta)
                
                # Limpar conversa
                if st.button("🗑️ Nova pergunta"):
                    st.rerun()
else:
    st.error("📁 materias/geografia/cap13-001-geografia.jpg")
