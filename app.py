import streamlit as st
import os

st.set_page_config(layout="wide")

st.title("📚 Tutor dos Livros")
st.markdown("**Matéria → Capítulo → Pergunte**")

# Lista arquivos LOCALMENTE
if os.path.exists("materias"):
    materias = {}
    for materia in os.listdir("materias"):
        path = f"materias/{materia}"
        if os.path.isdir(path):
            pdfs = [f for f in os.listdir(path) if f.endswith('.pdf')]
            if pdfs:
                materias[materia.title()] = pdfs
    
    if materias:
        # SIDEBAR
        materia = st.sidebar.selectbox("Matéria:", list(materias.keys()))
        pdfs = materias[materia]
        pdf = st.sidebar.selectbox("Capítulo:", pdfs)
        
        st.sidebar.success(f"📖 {materia} - {pdf}")
        
        # MOSTRA CONTEÚDO DO PDF (SIMPLE)
        with open(f"materias/{materia.lower()}/{pdf}", 'r', encoding='latin1', errors='ignore') as f:
            conteudo = f.read()[:2000]
        
        st.subheader(f"📄 {pdf}")
        st.write(conteudo[:1000])
        
        # CHAT SIMPLES
        pergunta = st.text_input("💭 Pergunta:")
        if st.button("Responder") and pergunta:
            # Busca palavras-chave
            linhas = [l for l in conteudo.split('\n') if any(p in l.lower() for p in pergunta.lower().split())]
            resposta = "\n".join(linhas[:5]) if linhas else "Não encontrei no capítulo."
            st.write(f"**Resposta:** {resposta}")
    else:
        st.error("Nenhum PDF encontrado!")
else:
    st.error("Crie pasta: materias/geografia/cap13-geografia.pdf")
