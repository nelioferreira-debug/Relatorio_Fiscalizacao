import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SGF - Gestão de Fiscalização", page_icon="⚡", layout="wide")

# --- LOGIN ---
USUARIOS = {
    "CAMPOS": "CAMPOS987", "LAGOS": "LAGOS987", "SERRANA": "SERRANA987",
    "MACAE": "MACAE987", "SUL": "SUL987", "SÃO GONÇALO": "SÃO GONÇALO987",
    "NITEROI": "NITEROI987", "MAGÉ": "MAGÉ987", "NOROESTE": "NOROESTE987",
    "ADMIN": "ADMIN123"
}

# --- FUNÇÕES ---
def carregar_dados():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dados", ttl=0)
    df['ID'] = df['ID'].astype(str) # Garante que ID é texto
    return df, conn

def salvar_dados(conn, df):
    conn.update(worksheet="Dados", data=df)
    st.cache_data.clear()

# --- TELA LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown("<h1 style='text-align:center'>⚡ SGF Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login"):
            user = st.selectbox("Polo", list(USUARIOS.keys()))
            pwd = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if USUARIOS[user] == pwd:
                    st.session_state['logado'] = True
                    st.session_state['usuario'] = user
                    st.rerun()
                else:
                    st.error("Senha incorreta")
    st.stop() # Para o código aqui se não estiver logado

# --- SISTEMA PRINCIPAL ---
st.sidebar.title(f"📍 {st.session_state['usuario']}")
if st.sidebar.button("Sair"):
    st.session_state['logado'] = False
    st.rerun()

# Carrega Dados
try:
    df, conn = carregar_dados()
except Exception as e:
    st.error(f"Erro na conexão com Planilha: {e}")
    st.stop()

# Filtra dados do usuário
user_atual = st.session_state['usuario']
df_user = df if user_atual == "ADMIN" else df[df['polo'] == user_atual]

tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🏢 Meu Polo", "📝 Justificar"])

with tab1:
    st.metric("Total Fiscalizações", len(df))
    # Gráfico simples
    if not df.empty and 'data_exec_corte' in df.columns:
        fig = px.bar(df.groupby('data_exec_corte').size().reset_index(name='Qtd'), x='data_exec_corte', y='Qtd')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.metric("Total Polo", len(df_user))
    if not df_user.empty and 'status' in df_user.columns:
        fig2 = px.pie(df_user, names='status')
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.header("Tratamento de Pendências")
    ids = df_user['ID'].unique().tolist()
    if not ids:
        st.info("Nenhuma ordem encontrada.")
    else:
        sel_id = st.selectbox("Selecione ID da Ordem", ids)
        # Filtra linha
        mask = df['ID'] == sel_id
        idx = df[mask].index[0]
        row = df.loc[idx]
        
        # Mostra dados (Resumido para caber na tela)
        st.info(f"Cliente: {row.get('numero_cliente', '-')} | Endereço: {row.get('desc_rede', '-')}")
        
        with st.form("justificativa"):
            c1, c2 = st.columns(2)
            with c1:
                just = st.selectbox("Justificativa", ["", "Agrupamento", "Sem acesso", "Outros"], index=0)
                obs = st.text_area("Obs Polo", value=str(row.get('Obs_polo', '')))
            with c2:
                conf = st.selectbox("Conformidade", ["", "Conforme", "Não Conforme"], index=0)
            
            if st.form_submit_button("Salvar"):
                df.at[idx, 'Justificativa_polo'] = just
                df.at[idx, 'Obs_polo'] = obs
                df.at[idx, 'Conformidade_polo'] = conf
                salvar_dados(conn, df)
                st.success("Salvo com sucesso!")
                time.sleep(1)
                st.rerun()


n
