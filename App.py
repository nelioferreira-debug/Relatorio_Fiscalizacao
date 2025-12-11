import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SGF - Gestão de Fiscalização", page_icon="⚡", layout="wide")

# --- CREDENCIAIS DE LOGIN ---
# Em um sistema real, isso estaria num banco seguro. Para hoje, serve assim.
USUARIOS = {
    "CAMPOS": "CAMPOS987",
    "LAGOS": "LAGOS987",
    "SERRANA": "SERRANA987",
    "MACAE": "MACAE987",
    "SUL": "SUL987",
    "SÃO GONÇALO": "SÃO GONÇALO987",
    "NITEROI": "NITEROI987",
    "MAGÉ": "MAGÉ987",
    "NOROESTE": "NOROESTE987",
    "ADMIN": "ADMIN123" # Mestre
}

# --- LISTAS DE OPÇÕES ---
OPCOES_JUSTIFICATIVA = [
    "", "Agrupamento", "Falha não apontada", "Med retirado/padrão demolido", 
    "Poste sem acesso", "Poste de ferro", "Pontalete sem acesso", "Sem justificativa",
    "Corte não evidenciado", "Risco de execução", "Trâmite inferior", 
    "Trâmite superior", "Sem Ação - Contrato Encerrado"
]

OPCOES_OBS = [
    "", "Agrupamento de medidores impede identificar o ramal correto/barramento",
    "Procedimento correto", "Sem fornecimento e sem medidor",
    "Impedimento de amarração de escada/veiculo/muro/vegetação/outros",
    "Poste sem possibilidade de amarração da escada com segurança",
    "Impedimento de acesso ao poste/pontalete para identificar o ramal",
    "Sem evidências do retorno/mau evidenciado/foto fora dor E-Order",
    "Sem vestigio de corte", "Rede proxima a alta/insetos/ameaça de violência/poste podre ou danificado",
    "Solicitado ramal/executado no poste ou medidor", "Solicitado poste/executado medidor",
    "Solicitado poste/executado ramal", "Solicitado medidor/executado poste"
]

# --- CONEXÃO COM GOOGLE SHEETS ---
def carregar_dados():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # TTL=0 garante que os dados não ficam velhos no cache
    df = conn.read(worksheet="Dados", ttl=0)
    # Converte ID para texto para evitar erro de busca
    if 'ID' in df.columns:
        df['ID'] = df['ID'].astype(str)
    return df, conn

def salvar_dados(conn, df):
    try:
        conn.update(worksheet="Dados", data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- TELA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown("<h1 style='text-align: center;'>⚡ SGF - Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login"):
            user = st.selectbox("Selecione o Polo", list(USUARIOS.keys()))
            pwd = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                if USUARIOS.get(user) == pwd:
                    st.session_state['logado'] = True
                    st.session_state['usuario'] = user
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
    st.stop() # Para a execução aqui se não estiver logado

# --- APLICAÇÃO PRINCIPAL ---
st.sidebar.title(f"📍 {st.session_state['usuario']}")
if st.sidebar.button("Sair / Logout"):
    st.session_state['logado'] = False
    st.rerun()

# Carrega os dados
try:
    df, conn = carregar_dados()
except Exception as e:
    st.error("⚠️ Erro ao ler a planilha. Verifique se a aba se chama 'Dados' e se o robô é Editor.")
    st.stop()

# Filtra os dados baseado no usuário logado
usuario_atual = st.session_state['usuario']
if usuario_atual == "ADMIN":
    df_user = df
else:
    # Filtra onde a coluna 'polo' é igual ao usuário logado
    if 'polo' in df.columns:
        df_user = df[df['polo'] == usuario_atual]
    else:
        st.error("Coluna 'polo' não encontrada na planilha!")
        df_user = pd.DataFrame()

# --- ABAS DO SISTEMA ---
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🏢 Meu Polo", "📝 Tratar Pendências"])

# ABA 1: Visão Geral (ADMIN vê tudo, Polo vê resumo geral)
with tab1:
    st.metric("Total de Ordens na Base", len(df))
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        # Gráfico de Fiscalizações por Dia
        if 'data_exec_corte' in df.columns:
            st.subheader("Fiscalizações por Dia")
            df_dia = df.groupby('data_exec_corte').size().reset_index(name='Qtd')
            fig1 = px.bar(df_dia, x='data_exec_corte', y='Qtd')
            st.plotly_chart(fig1, use_container_width=True)
    
    with col_g2:
        # Progresso de Justificativas
        if 'Justificativa_polo' in df.columns:
            st.subheader("Status de Tratamento")
            # Conta quantos têm justificativa preenchida
            tratados = df[df['Justificativa_polo'].notna() & (df['Justificativa_polo'] != "")].shape[0]
            total = len(df)
            progresso = (tratados / total) * 100 if total > 0 else 0
            st.progress(progresso / 100, text=f"{progresso:.1f}% Tratado ({tratados}/{total})")

# ABA 2: Visão do Polo Específico
with tab2:
    st.subheader(f"Dados de {usuario_atual}")
    st.metric("Minhas Pendências", len(df_user))
    
    if not df_user.empty:
        # Tabela simples
        st.dataframe(df_user.head(10), use_container_width=True)
        
        # Botão de Download
        csv = df_user.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Meus Dados (CSV)", csv, "meus_dados.csv", "text/csv")

# ABA 3: Edição e Tratativa
with tab3:
    st.header("Tratamento de Justificativas")
    
    # Seletor de Ordem (ID)
    if df_user.empty:
        st.info("Nenhuma ordem para exibir.")
    else:
        lista_ids = df_user['ID'].unique().tolist()
        id_selecionado = st.selectbox("Pesquise o ID da Ordem:", lista_ids)
        
        # Localiza a linha exata no DataFrame ORIGINAL (df) para editar
        # Usamos df (geral) e não df_user para garantir que editamos a base correta
        mascara = df['ID'] == id_selecionado
        
        if not mascara.any():
            st.error("ID não encontrado.")
        else:
            # Pega o índice da linha para editar
            idx = df[mascara].index[0]
            linha = df.loc[idx]
            
            st.markdown("---")
            
            # Blocos de Informação (Apenas Leitura)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.info(f"**Cliente:** {linha.get('numero_cliente', '-')}")
                st.write(f"**Município:** {linha.get('municipio', '-')}")
            with c2:
                st.info(f"**Retorno:** {linha.get('retorno', '-')}")
                st.write(f"**Rede:** {linha.get('desc_rede', '-')}")
            with c3:
                st.info(f"**Status:** {linha.get('status', '-')}")
                st.write(f"**Data:** {linha.get('data_exec_corte', '-')}")

            st.markdown("### ✍️ Preenchimento do Polo")
            
            with st.form("form_tratativa"):
                # Campos de Edição
                col_e1, col_e2 = st.columns(2)
                
                with col_e1:
                    # Tenta pegar o valor atual, se não existir, usa o primeiro da lista
                    val_just = linha.get('Justificativa_polo')
                    idx_just = OPCOES_JUSTIFICATIVA.index(val_just) if val_just in OPCOES_JUSTIFICATIVA else 0
                    nova_just = st.selectbox("Justificativa", OPCOES_JUSTIFICATIVA, index=idx_just)
                    
                    val_obs = linha.get('Obs_polo')
                    idx_obs = OPCOES_OBS.index(val_obs) if val_obs in OPCOES_OBS else 0
                    nova_obs = st.selectbox("Observação", OPCOES_OBS, index=idx_obs)

                with col_e2:
                    nova_conf = st.selectbox("Conformidade Polo", ["", "Conforme", "Não Conforme"], 
                                           index=1 if linha.get('Conformidade_polo') == "Conforme" else 2 if linha.get('Conformidade_polo') == "Não Conforme" else 0)
                    
                    nova_notificacao = st.selectbox("Notificação?", ["", "SIM", "NÃO"], 
                                                  index=1 if linha.get('NOTIFICAÇÃO?') == "SIM" else 2 if linha.get('NOTIFICAÇÃO?') == "NÃO" else 0)

                # Botão de Salvar
                if st.form_submit_button("💾 Salvar Tratativa", type="primary"):
                    # Atualiza o DataFrame em memória
                    df.at[idx, 'Justificativa_polo'] = nova_just
                    df.at[idx, 'Obs_polo'] = nova_obs
                    df.at[idx, 'Conformidade_polo'] = nova_conf
                    df.at[idx, 'NOTIFICAÇÃO?'] = nova_notificacao
                    
                    # Envia para o Google Sheets
                    sucesso = salvar_dados(conn, df)
                    
                    if sucesso:
                        st.success("✅ Salvo com sucesso no Google Sheets!")
                        time.sleep(1)
                        st.rerun()
