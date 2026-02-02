import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpoint
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import glob

st.set_page_config(page_title="Tutor por Matérias", layout="wide")

# Cache para livros organizados
@st.cache_resource
def load_books_by_subject():
    docs = []
    materia_index = {}
    
    if not os.path.exists("materias"):
        st.error("Crie pasta 'materias/' com subpastas por matéria!")
        return None, None
    
    # Escaneia todas as matérias
    for materia_dir in os.listdir("materias"):
        materia_path = f"materias/{materia_dir}"
        if os.path.isdir(materia_path):
            materia_caps = []
            caps_path = f"{materia_path}/*.pdf"
            caps_files = glob.glob(caps_path) + glob.glob(f"{materia_path}/*.txt")
            
            for cap_file in caps_files:
                if cap_file.endswith('.pdf'):
                    loader = PyPDFLoader(cap_file)
                else:
                    loader = TextLoader(cap_file, encoding='utf-8')
                docs.extend(loader.load())
                materia_caps.append(os.path.basename(cap_file))
            
            materia_index[materia_dir.replace('-', ' ').title()] = materia_caps
    
    # Processa documentos
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    
    return vectorstore, materia_index

@st.cache_resource
def setup_qa(vectorstore):
    llm = HuggingFaceEndpoint(
        repo_id="google/flan-t5-large",
        temperature=0.3,
        max_length=512
    )
    template = """Você é um tutor para crianças. Use APENAS o contexto dos livros fornecidos.
    
    Matéria: {subject}
    Capítulo: {chapter}
    Contexto: {context}
    Pergunta: {question}
    
    Responda de forma lúdica e educativa para crianças de 6-10 anos:"""
    prompt = PromptTemplate(template=template, input_variables=["context", "question", "subject", "chapter"])
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever(search_kwargs={"k": 4}))
    return qa, prompt

# Interface principal
st.title("📚 Tutor Organizado por Matérias e Capítulos")
st.markdown("**Navegue por matéria → capítulo → faça perguntas!**")

# Sidebar: Navegação por matéria
st.sidebar.header("🗂️ Escolha a Matéria")
vectorstore, materias = load_books_by_subject()

if vectorstore and materias:
    materia_selecionada = st.sidebar.selectbox("Matéria:", list(materias.keys()))
    
    # Mostra capítulos da matéria
    capitulos = materias[materia_selecionada]
    capitulo_selecionado = st.sidebar.selectbox("Capítulo:", capitulos)
    
    st.sidebar.success(f"🔍 Buscando em: **{materia_selecionada} - {capitulo_selecionado}**")
    
    # Chat principal
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if prompt := st.chat_input(f"Pergunte sobre {materia_selecionada} - {capitulo_selecionado}"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando os livros..."):
                # Passa contexto da matéria/capítulo
                result = qa.invoke({
                    "query": prompt,
                    "subject": materia_selecionada,
                    "chapter": capitulo_selecionado
                })
                response = result["result"]
                st.write(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Botão limpar chat
        if st.button("🗑️ Nova conversa"):
            st.session_state.messages = []
            st.rerun()
            
else:
    st.info("👈 **Crie a pasta `materias/` com esta estrutura:**\n```\nmaterias/\n├── matematica/\n│   ├── cap1.pdf\n│   └── cap2.pdf\n├── portugues/\n└── historia/\n```")

# Status dos livros carregados
if materias:
    st.sidebar.markdown("### 📖 Livros Carregados")
    for materia, caps in materias.items():
        st.sidebar.write(f"**{materia}**: {len(caps)} capítulos")
