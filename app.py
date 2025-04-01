import os
import streamlit as st
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
import glob

from agent import create_agent
from utils import carregar_faq, carregar_multiplos_faqs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

load_dotenv()

st.set_page_config(
    page_title="Chat FourBank",
    page_icon="🏦",
    layout="wide",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #f5f7fa; }
    .chat-container {
        height: 75vh;
        overflow-y: auto;
        padding: 1rem;
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .sidebar-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .sidebar-action {
        background-color: #f3f4f6;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        border-left: 3px solid #3b82f6;
    }
    .sidebar-action:hover {
        background-color: #e5e7eb;
        transform: translateX(3px);
    }
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #2563eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTextInput input { border-radius: 0.375rem; }
    .app-title {
        text-align: center;
        color: #1f2937;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .stChatMessage {
        background-color: white !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        border: 1px solid #e5e7eb !important;
        white-space: pre-wrap;
    }
    .stChatMessage [data-testid="chatAvatarIcon"] {
        width: 32px !important;
        height: 32px !important;
    }
</style>
""", unsafe_allow_html=True)

if 'cliente_id' not in st.session_state:
    st.session_state.cliente_id = "1"

if 'vectorstore' not in st.session_state:
    try:
        pdf_files = glob.glob(os.path.join("data", "*.pdf"))
        if pdf_files:
            with st.spinner("Carregando base de conhecimento..."):
                if len(pdf_files) == 1:
                    st.session_state.vectorstore = carregar_faq(pdf_files[0])
                else:
                    st.session_state.vectorstore = carregar_multiplos_faqs(pdf_files)
        else:
            st.error("Nenhum arquivo PDF encontrado no diretório 'data'")
            st.session_state.vectorstore = None
    except Exception as e:
        st.error(f"Erro ao carregar a base de conhecimento: {e}")
        logger.error(f"Erro ao carregar a base de conhecimento: {e}", exc_info=True)
        st.session_state.vectorstore = None

if 'agent' not in st.session_state:
    st.session_state.agent = create_agent(
        st.session_state.cliente_id,
        st.session_state.vectorstore
    )

if 'messages' not in st.session_state:
    st.session_state.messages = st.session_state.agent.get_messages()

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if 'sent_message' not in st.session_state:
    st.session_state.sent_message = None

clientes = {
    "1": {"nome": "João Silva", "saldo": 5000.00, "conta": "12345-6", "tipo": "Conta Corrente"},
    "2": {"nome": "Maria Santos", "saldo": 8500.00, "conta": "65432-1", "tipo": "Conta Premium"},
    "3": {"nome": "Carlos Oliveira", "saldo": 2300.00, "conta": "98765-4", "tipo": "Conta Básica"}
}

def enviar_mensagem(texto):
    if st.session_state.sent_message == texto or st.session_state.is_processing:
        return

    st.session_state.is_processing = True
    st.session_state.sent_message = texto

    try:
        st.session_state.messages.append(HumanMessage(content=texto))
        with st.spinner(""):
            resposta = st.session_state.agent.invoke(texto)
            st.session_state.messages = st.session_state.agent.get_messages()
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
        st.session_state.messages.append(
            AIMessage(content="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou reformule sua pergunta.")
        )
    finally:
        st.session_state.is_processing = False
        st.rerun()

st.markdown("<div style='text-align: center; font-size: 0.8rem; color: #6b7280;'>streamlit app</div>", unsafe_allow_html=True)
st.markdown("<div class='app-title'><h2>Chat FourBank</h2></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("<h3>Configurações</h3>", unsafe_allow_html=True)
    cliente_selecionado = st.selectbox(
        "Selecione um cliente",
        options=list(clientes.keys()),
        format_func=lambda x: f"{clientes[x]['nome']}",
        key="cliente_selectbox"
    )

    if cliente_selecionado != st.session_state.cliente_id:
        st.session_state.cliente_id = cliente_selecionado
        st.session_state.is_processing = False
        st.session_state.sent_message = None
        st.session_state.agent = create_agent(
            st.session_state.cliente_id,
            st.session_state.vectorstore
        )
        st.session_state.messages = st.session_state.agent.get_messages()
        st.rerun()

    if st.button("Iniciar chat", key="iniciar_chat"):
        st.session_state.is_processing = False
        st.session_state.sent_message = None
        st.session_state.agent = create_agent(
            st.session_state.cliente_id,
            st.session_state.vectorstore
        )
        st.session_state.messages = st.session_state.agent.get_messages()
        st.rerun()

    st.markdown("<h3>Ações Rápidas</h3>", unsafe_allow_html=True)
    if st.button("Consultar Saldo"):
        enviar_mensagem("Olá, tudo bem? Seu saldo é de:")
    if st.button("Fazer Transferência"):
        enviar_mensagem("Olá, como vai? Vou te ajudar! Para quem vamos transferir?")
    if st.button("Ver Extrato"):
        enviar_mensagem("Gostaria de visualizar o extrato da conta, por favor.")

    st.markdown("<h3>Ficha do Cliente</h3>", unsafe_allow_html=True)
    cliente_atual = clientes[st.session_state.cliente_id]

    cliente_html = f"""
    <div class="sidebar-card">
        <p><strong>Nome:</strong> {cliente_atual['nome']}</p>
        <p><strong>Conta:</strong> {cliente_atual['conta']}</p>
        <p><strong>Tipo:</strong> {cliente_atual['tipo']}</p>
        <p><strong>Desde:</strong> Janeiro 2023</p>
    </div>
    """
    st.markdown(cliente_html, unsafe_allow_html=True)

    st.markdown("<h3>Resumo Financeiro</h3>", unsafe_allow_html=True)
    resumo_html = f"""
    <div class="sidebar-card">
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; font-weight: 600; color: #1f2937;">R$ {cliente_atual['saldo']:.2f}</div>
            <div style="font-size: 0.8rem; color: #6b7280;">Saldo Disponível</div>
        </div>
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; font-weight: 600; color: #1f2937;">R$ 1,200.00</div>
            <div style="font-size: 0.8rem; color: #6b7280;">Fatura do Cartão</div>
        </div>
        <div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #1f2937;">3</div>
            <div style="font-size: 0.8rem; color: #6b7280;">Transações Recentes</div>
        </div>
    </div>
    """
    st.markdown(resumo_html, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 30px; text-align: center; font-size: 0.8rem; color: #6b7280;'>Laboratório de Inovação - <a href='#' style='color: #3b82f6; text-decoration: none;'>Foursys</a> | 2025</div>", unsafe_allow_html=True)

with col2:
    if st.button("Novo Chat", type="primary"):
        st.session_state.is_processing = False
        st.session_state.sent_message = None
        st.session_state.agent = create_agent(
            st.session_state.cliente_id,
            st.session_state.vectorstore
        )
        st.session_state.messages = st.session_state.agent.get_messages()
        st.rerun()

    filtered_messages = []
    prev_content = None

    for msg in st.session_state.messages:
        if hasattr(msg, 'type') and msg.type == 'function':
            continue
        current_content = msg.content if hasattr(msg, 'content') else None
        if current_content != prev_content:
            filtered_messages.append(msg)
            prev_content = current_content

    chat_container = st.container()

    with chat_container:
        for msg in filtered_messages:
            if isinstance(msg, HumanMessage):
                with st.chat_message("user", avatar="👤"):
                    st.write(msg.content)
            elif isinstance(msg, AIMessage):
                with st.chat_message("assistant", avatar="🏦"):
                    st.write(msg.content)

    mensagem = st.chat_input("Digite sua mensagem...", key="chat_input", disabled=st.session_state.is_processing)
    if mensagem and not st.session_state.is_processing:
        enviar_mensagem(mensagem)
