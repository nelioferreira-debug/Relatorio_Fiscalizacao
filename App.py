import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import time
import urllib.parse 

# --- CONFIGURAÇÃO DA PÁGINA (OTIMIZADA PARA MOBILE) ---
# initial_sidebar_state="collapsed" -> Começa com o menu fechado para ganhar espaço no celular
st.set_page_config(
    page_title="SGF - Gestão de Fiscalização", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CREDENCIAIS DE LOGIN ---
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
    "ADMIN": "ADMIN123"
}

# --- DE-PARA DE MUNICÍPIOS (Código -> Nome) ---
DE_PARA_MUNICIPIOS = {
    "4157": "CAMPOS DO GOYTACAZES", "4169": "CARDOSO MOREIRA", "4130": "SÃO FRANCISCO DO ITABAPOANA", "4158": "SÃO JOÃO DA BARRA",
    "4359": "BOM JESUS DO ITABAPOANA", "4365": "ITALVA", "4360": "ITAPERUNA", "4361": "LAJE DO MURIAÉ",
    "4362": "NATIVIDADE", "4363": "PORCIÚNCULA", "4322": "SÃO JOSÉ DE UBÁ", "4364": "VARRE-SAI",
    "1239": "ARARUAMA", "1231": "IGUABA GRANDE", "1238": "SAQUAREMA", "2109": "SILVA JARDIM",
    "1324": "ARMAÇÃO DE BÚZIOS", "1329": "ARRAIAL DO CABO", "1342": "CABO FRIO", "1341": "SÃO PEDRO DA ALDEIA",
    "4544": "BOM JARDIM", "4546": "CANTAGALO", "4535": "CARMO", "4545": "CORDEIRO",
    "4537": "DUAS BARRAS", "4523": "MACUCO", "4251": "SANTA MARIA MADALENA", "4547": "SÃO SEBASTIÃO DO ALTO",
    "4248": "TRAJANO DE MORAIS", "4225": "CARAPEBUS", "4243": "CASIMIRO DE ABREU", "4250": "CONCEIÇÃO DE MACABU",
    "4249": "MACAÉ", "4268": "QUISSAMÃ", "4240": "RIO DAS OSTRAS", "4432": "APERIBE",
    "4455": "CAMBUCI", "4452": "ITAOCARA", "4454": "MIRACEMA", "4453": "SANTO ANTÔNIO DE PÁDUA",
    "4456": "SÃO FIDELIS", "2221": "DUQUE DE CAXIAS", "2233": "CACHOEIRAS DE MACACU", "2226": "GUAPIMIRIM",
    "2227": "MAGÉ", "1407": "MARICÁ", "1401": "NITERÓI", "2106": "ITABORAÍ",
    "2108": "RIO BONITO", "2111": "TANGUÁ", "2102": "SÃO GONÇALO", "3110": "AREAL",
    "3105": "PARAIBA DO SUL", "3103": "PETRÓPOLIS", "3166": "SÃO JOSÉ DO VALE DO RIO PRETO", "3104": "TRÊS RIOS",
    "3236": "NOVA FRIBURGO", "3234": "SUMIDOURO", "3228": "TERESÓPOLIS", "1119": "ANGRA DOS REIS",
    "1120": "MANGARATIBA", "1117": "PARATY", "3315": "BOCAINA DE MINAS", "3367": "ITATIAIA",
    "3316": "PORTO REAL", "3318": "RESENDE"
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

OPCOES_CONF_GRIDS = ["", "Justificado", "Não Conforme", "Sem vestígio", "Trâmite Divergente"]
OPCOES_SANCAO = ["", "I", "II", "III", "NÃO APLICADA"]
OPCOES_MULTA = ["", "SIM", "NÃO", "EM ANDAMENTO"]

# --- CONEXÃO COM GOOGLE SHEETS ---
def carregar_dados():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dados", ttl=0)
    if 'ID' in df.columns:
        df['ID'] = df['ID'].astype(str).str.replace(r'\.0$', '', regex=True)
    return df, conn

def salvar_dados(conn, df):
    try:
        conn.update(worksheet="Dados", data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- FUNÇÕES DE AJUDA ---
def limpar_dado(valor):
    if pd.isna(valor) or str(valor).strip() == "" or str(valor).lower() == "nan":
        return "-"
    return str(valor)

def formatar_sem_decimal(valor):
    try:
        if pd.isna(valor) or str(valor).strip() == '':
            return "-"
        return str(int(float(valor)))
    except:
        return str(valor)

def limpar_input_edicao(valor):
    if pd.isna(valor) or str(valor).strip() == "" or str(valor).lower() == "nan":
        return ""
    return str(valor)

# --- TELA DE LOGIN (OTIMIZADA) ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown("<h1 style='text-align: center; color: #00549F;'>⚡ SGF - Login</h1>", unsafe_allow_html=True)
    
    # Removemos as colunas [1,2,1] que espremiam a tela no celular.
    # Agora usamos um container centralizado mais fluido.
    col_login = st.columns([1, 10, 1]) # Margem pequena nos lados, foco no meio
    
    with col_login[1]:
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
    st.stop()

# --- APLICAÇÃO PRINCIPAL ---
st.sidebar.title(f"📍 {st.session_state['usuario']}")
if st.sidebar.button("Sair / Logout"):
    st.session_state['logado'] = False
    st.rerun()

try:
    df, conn = carregar_dados()
except Exception as e:
    st.error("⚠️ Erro ao ler a planilha.")
    st.stop()

usuario_atual = st.session_state['usuario']
if usuario_atual == "ADMIN":
    df_user = df
else:
    if 'polo' in df.columns:
        df_user = df[df['polo'] == usuario_atual]
    else:
        st.error("Coluna 'polo' não encontrada na planilha!")
        df_user = pd.DataFrame()

# --- ABAS DO SISTEMA ---
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral (Dashboard)", "🏢 Meu Polo", "📝 Tratar Pendências"])

# --- ABA 1: DASHBOARD EXECUTIVO ---
with tab1:
    # Identidade Visual (Azul Enel)
    st.markdown("""
        <style>
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #00549F;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #00549F;'>📊 Dashboard Executivo de Fiscalização</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # Métricas Principais
    total_ordens = len(df)
    # Considera tratado se o campo Justificativa_polo não estiver vazio
    tratados_geral = df[df['Justificativa_polo'].notna() & (df['Justificativa_polo'] != "")].shape[0]
    pendentes_geral = total_ordens - tratados_geral
    percentual_geral = (tratados_geral / total_ordens * 100) if total_ordens > 0 else 0

    if 'Estado de Fornecimento' in df.columns:
        qtd_autoreligado = df[df['Estado de Fornecimento'].astype(str).str.lower() == 'autoreligado'].shape[0]
        perc_autoreligado = (qtd_autoreligado / total_ordens * 100) if total_ordens > 0 else 0
    else:
        perc_autoreligado = 0

    if 'Instalação do Lacre' in df.columns:
        qtd_com_lacre = df[~df['Instalação do Lacre'].astype(str).str.lower().str.contains('sem', na=True)].shape[0]
        perc_lacre = (qtd_com_lacre / total_ordens * 100) if total_ordens > 0 else 0
    else:
        perc_lacre = 0

    # Layout de linha única (6 colunas)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Fiscalizações", total_ordens)
    m2.metric("Concluídas", tratados_geral, delta=f"{percentual_geral:.1f}%")
    m3.metric("Pendentes", pendentes_geral, delta=f"-{pendentes_geral}", delta_color="inverse")
    m4.metric("Dias Restantes", "5", "Estimativa")
    m5.metric("% Com Lacre", f"{perc_lacre:.1f}%")
    m6.metric("% Autoreligado", f"{perc_autoreligado:.1f}%", delta_color="off")

    st.markdown("---")
    st.markdown("<h3 style='color: #00549F;'>🔎 Focos da Fiscalização</h3>", unsafe_allow_html=True)
    
    g1, g2 = st.columns(2)
    
    cores_pizza = ['#00549F', '#A0A0A0', '#FFA500']
    
    with g1:
        if 'classificacao' in df.columns:
            st.caption("Distribuição por Resultado (Conformidade)")
            df_class = df['classificacao'].value_counts().reset_index()
            df_class.columns = ['Resultado', 'Qtd']
            fig_pizza = px.pie(df_class, values='Qtd', names='Resultado', 
                             color_discrete_sequence=cores_pizza,
                             hole=0.4)
            st.plotly_chart(fig_pizza, use_container_width=True)
            
    with g2:
        if 'status' in df.columns:
            st.caption("Top 5 Tipos de Irregularidades/Divergências")
            df_status = df['status'].value_counts().head(5).reset_index()
            df_status.columns = ['Tipo Divergência', 'Qtd']
            fig_bar = px.bar(df_status, x='Qtd', y='Tipo Divergência', orientation='h',
                           color='Qtd', color_continuous_scale='Blues')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<h3 style='color: #00549F;'>🏆 Performance dos Polos</h3>", unsafe_allow_html=True)
    
    p1, p2 = st.columns(2)

    with p1:
        if 'polo' in df.columns:
            df_polo_vol = df['polo'].value_counts().reset_index()
            df_polo_vol.columns = ['Polo', 'Total']
            df_polo_vol = df_polo_vol.sort_values('Total', ascending=True)
            
            fig_vol = px.bar(df_polo_vol, x='Total', y='Polo', orientation='h',
                           text='Total', title="Volume de Fiscalizações por Polo",
                           color_discrete_sequence=['#00549F'])
            fig_vol.update_traces(textposition='outside')
            st.plotly_chart(fig_vol, use_container_width=True)

    with p2:
        if 'polo' in df.columns:
            df_polo_stats = df.groupby('polo').agg(
                Total=('ID', 'count'),
                Preenchidos=('Justificativa_polo', lambda x: x[x != ""].count())
            ).reset_index()
            
            df_polo_stats['Percentual'] = (df_polo_stats['Preenchidos'] / df_polo_stats['Total']) * 100
            df_polo_stats = df_polo_stats.sort_values('Percentual', ascending=True)

            fig_perf = px.bar(df_polo_stats, x='Percentual', y='polo', orientation='h',
                            text=df_polo_stats['Percentual'].apply(lambda x: f'{x:.1f}%'),
                            title="Ranking de Conclusão (%)",
                            color_discrete_sequence=['#4093D6'])
            
            fig_perf.update_traces(textposition='outside')
            fig_perf.update_layout(xaxis_range=[0, 115]) 
            st.plotly_chart(fig_perf, use_container_width=True)

# --- ABA 2: MEU POLO ---
with tab2:
    st.subheader(f"Dados de {usuario_atual}")
    st.metric("Minhas Pendências", len(df_user))
    if not df_user.empty:
        st.dataframe(df_user.head(10), use_container_width=True)
        csv = df_user.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Meus Dados (CSV)", csv, "meus_dados.csv", "text/csv")

# --- ABA 3: TRATAR PENDÊNCIAS ---
with tab3:
    st.header("Tratamento de Justificativas")
    if df_user.empty:
        st.info("Nenhuma ordem para exibir.")
    else:
        lista_ids = df_user['ID'].unique().tolist()
        
        if 'indice_navegacao' not in st.session_state:
            st.session_state['indice_navegacao'] = 0
            
        if st.session_state['indice_navegacao'] >= len(lista_ids):
             st.session_state['indice_navegacao'] = 0

        id_selecionado = st.selectbox("Pesquise o ID da Ordem:", lista_ids, index=st.session_state['indice_navegacao'])
        
        mascara = df['ID'] == id_selecionado
        
        if not mascara.any():
            st.error("ID não encontrado.")
        else:
            idx = df[mascara].index[0]
            linha = df.loc[idx]
            
            # Cálculos de Data
            diferenca_texto = "-"
            data_exec_completa = "-"
            data_solic_formatada = "-" 

            try:
                dt_solic = pd.to_datetime(linha.get('data_solic_corte'), dayfirst=True, errors='coerce')
                if pd.notna(dt_solic):
                    data_solic_formatada = dt_solic.strftime("%d/%m/%Y")

                str_data_exec = str(linha.get('data_exec_corte', ''))
                str_hora_exec = str(linha.get('hora_exec_corte', ''))
                if str_data_exec != 'nan' and str_data_exec != '':
                    str_completa = f"{str_data_exec} {str_hora_exec}".strip()
                    dt_exec = pd.to_datetime(str_completa, dayfirst=True, errors='coerce')
                    if pd.notna(dt_exec):
                        data_exec_completa = dt_exec.strftime("%d/%m/%Y %H:%M:%S")
                    if pd.notna(dt_solic) and pd.notna(dt_exec):
                        delta = dt_exec - dt_solic
                        diferenca_texto = str(delta).replace("days", "dias").replace("day", "dia")
            except Exception:
                diferenca_texto = "Erro no cálculo"

            st.markdown("---")
            
            # --- PREPARAÇÃO DE DADOS PARA EXIBIÇÃO ---
            val_id_formatado = formatar_sem_decimal(linha.get('ID'))
            val_cliente_formatado = formatar_sem_decimal(linha.get('numero_cliente'))
            codigo_municipio_limpo = formatar_sem_decimal(linha.get('municipio'))
            nome_municipio = DE_PARA_MUNICIPIOS.get(codigo_municipio_limpo, codigo_municipio_limpo)

            # --- BLOCOS DE DADOS ---
            with st.expander("👤 Dados do Cliente & ID", expanded=True):
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: st.text_input("ID (Código)", value=val_id_formatado) 
                with c2: st.text_input("Cliente", value=val_cliente_formatado)
                with c3: st.text_input("Polo", value=limpar_dado(linha.get('polo')), disabled=True)
                with c4: st.text_input("Município", value=nome_municipio, disabled=True)
                with c5: st.text_input("Descrição Rede", value=limpar_dado(linha.get('desc_rede')), disabled=True)

            with st.expander("🔎 Detalhes da Fiscalização (Foco)", expanded=False):
                f1, f2, f3 = st.columns(3)
                with f1:
                    st.write(f"**Mês Fisc:** {limpar_dado(linha.get('mês_fisc'))}")
                    st.write(f"**Data Início:** {limpar_dado(linha.get('Hora de início'))}")
                    st.write(f"**Ordem:** {limpar_dado(linha.get('Numero Ordem'))}")
                    st.write(f"**Parafuso Seg.:** {limpar_dado(linha.get('Possui parafuso de segurança?'))}")
                    st.write(f"**Disjuntor:** {limpar_dado(linha.get('Possui dispositivo do Disjuntor?'))}")
                with f2:
                    st.write(f"**Lacre:** {limpar_dado(linha.get('Instalação do Lacre'))}")
                    st.write(f"**Trâmite Enc.:** {limpar_dado(linha.get('Trâmite encontrado'))}")
                    st.write(f"**Tipo Padrão:** {limpar_dado(linha.get('Tipo do Padrão'))}")
                    st.write(f"**UC Habitada:** {limpar_dado(linha.get('UC Habitada?'))}")
                    st.write(f"**Fornecimento:** {limpar_dado(linha.get('Estado de Fornecimento'))}")
                with f3:
                    st.info(f"**Trâmite:** {limpar_dado(linha.get('tramite'))}")
                    st.info(f"**Retorno:** {limpar_dado(linha.get('retorno'))}")
                    st.error(f"**Classificação:** {limpar_dado(linha.get('classificacao'))}")
                    st.error(f"**Status:** {limpar_dado(linha.get('status'))}")

            with st.expander("✂️ Dados do Corte & SLA", expanded=False):
                # Organização em uma única linha com 5 colunas
                crt1, crt2, crt3, crt4, crt5 = st.columns(5)
                with crt1: st.write(f"**Mês Corte:** {limpar_dado(linha.get('mês_corte'))}")
                with crt2: st.write(f"**Ordem Corte:** {limpar_dado(linha.get('num_ordem_serv_crt'))}")
                with crt3: st.write(f"**Descrição:** {limpar_dado(linha.get('descricao_tipo'))}")
                with crt4: st.write(f"**Tipo Corte:** {limpar_dado(linha.get('Tipo_corte'))}")
                with crt5: st.write(f"**Grupo:** {limpar_dado(linha.get('grupo'))}")

                st.markdown("##### ⏳ Análise de Tempo")
                t1, t2, t3 = st.columns(3)
                with t1:
                    st.text_input("Data Solicitação", value=data_solic_formatada, disabled=True)
                with t2:
                    st.text_input("Data Execução (Final)", value=data_exec_completa, disabled=True)
                with t3:
                    st.text_input("Diferença (Exec - Solic)", value=diferenca_texto, disabled=True)

            st.markdown("### ✍️ Preenchimento do Polo")
            
            with st.form("form_tratativa"):
                col_e1, col_e2, col_e3 = st.columns(3)
                # OBS: Adicionamos 'key' única (id_selecionado) para forçar o reset dos campos ao trocar de ID
                with col_e1:
                    st.markdown("**Análise do Polo**")
                    val_just = linha.get('Justificativa_polo')
                    idx_just = OPCOES_JUSTIFICATIVA.index(val_just) if val_just in OPCOES_JUSTIFICATIVA else 0
                    nova_just = st.selectbox("Justificativa", OPCOES_JUSTIFICATIVA, index=idx_just, key=f"just_{id_selecionado}")
                    val_obs = linha.get('Obs_polo')
                    idx_obs = OPCOES_OBS.index(val_obs) if val_obs in OPCOES_OBS else 0
                    nova_obs = st.selectbox("Observação", OPCOES_OBS, index=idx_obs, key=f"obs_{id_selecionado}")

                with col_e2:
                    st.markdown("**Conformidade & Notificação**")
                    nova_conf = st.selectbox("Conformidade Polo", ["", "Conforme", "Não Conforme"], 
                                           index=1 if linha.get('Conformidade_polo') == "Conforme" else 2 if linha.get('Conformidade_polo') == "Não Conforme" else 0,
                                           key=f"conf_{id_selecionado}")
                    val_grids = linha.get('Conformidade_grids')
                    idx_grids = OPCOES_CONF_GRIDS.index(val_grids) if val_grids in OPCOES_CONF_GRIDS else 0
                    nova_conf_grids = st.selectbox("Conformidade Grids", OPCOES_CONF_GRIDS, index=idx_grids, key=f"grids_{id_selecionado}")
                    nova_notificacao = st.selectbox("Notificação?", ["", "SIM", "NÃO"], 
                                                  index=1 if linha.get('NOTIFICAÇÃO?') == "SIM" else 2 if linha.get('NOTIFICAÇÃO?') == "NÃO" else 0,
                                                  key=f"notif_{id_selecionado}")

                with col_e3:
                    st.markdown("**Sanções e Multas**")
                    val_sancao = linha.get('SANÇÃO')
                    idx_sancao = OPCOES_SANCAO.index(val_sancao) if val_sancao in OPCOES_SANCAO else 0
                    nova_sancao = st.selectbox("Sanção", OPCOES_SANCAO, index=idx_sancao, key=f"sancao_{id_selecionado}")
                    
                    val_valor_limpo = limpar_input_edicao(linha.get('VALOR'))
                    novo_valor = st.text_input("Valor (R$)", value=val_valor_limpo, key=f"valor_{id_selecionado}")
                    
                    val_multa = linha.get('MULTA?')
                    idx_multa = OPCOES_MULTA.index(val_multa) if val_multa in OPCOES_MULTA else 0
                    nova_multa = st.selectbox("Multa?", OPCOES_MULTA, index=idx_multa, key=f"multa_{id_selecionado}")
                    
                    val_valor_multa_limpo = limpar_input_edicao(linha.get('VALOR MULTA'))
                    novo_valor_multa = st.text_input("Valor Multa (R$)", value=val_valor_multa_limpo, key=f"vmulta_{id_selecionado}")

                st.markdown("---")
                
                b1, b2, b3 = st.columns(3)
                with b1:
                    btn_salvar = st.form_submit_button("💾 Salvar", type="primary")
                with b2:
                    btn_limpar = st.form_submit_button("🧹 Limpar Dados")
                with b3:
                    btn_finalizar = st.form_submit_button("📧 Finalizar e Enviar")

                if btn_salvar:
                    df.at[idx, 'Justificativa_polo'] = nova_just
                    df.at[idx, 'Obs_polo'] = nova_obs
                    df.at[idx, 'Conformidade_polo'] = nova_conf
                    df.at[idx, 'Conformidade_grids'] = nova_conf_grids
                    df.at[idx, 'NOTIFICAÇÃO?'] = nova_notificacao
                    df.at[idx, 'SANÇÃO'] = nova_sancao
                    df.at[idx, 'VALOR'] = novo_valor
                    df.at[idx, 'MULTA?'] = nova_multa
                    df.at[idx, 'VALOR MULTA'] = novo_valor_multa
                    
                    sucesso = salvar_dados(conn, df)
                    if sucesso:
                        try:
                            idx_atual_lista = lista_ids.index(id_selecionado)
                            if idx_atual_lista + 1 < len(lista_ids):
                                st.session_state['indice_navegacao'] = idx_atual_lista + 1
                                st.success("✅ Salvo com sucesso! Carregando próximo...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.success("✅ Salvo! Você chegou ao fim da lista.")
                                st.balloons()
                                st.info("🎉 Não há mais pendências.")
                        except ValueError:
                            pass

                if btn_limpar:
                    colunas_para_limpar = [
                        'Justificativa_polo', 'Obs_polo', 'Conformidade_polo', 
                        'Conformidade_grids', 'NOTIFICAÇÃO?', 'SANÇÃO', 
                        'VALOR', 'MULTA?', 'VALOR MULTA'
                    ]
                    for col in colunas_para_limpar:
                        df.at[idx, col] = ""
                    
                    sucesso = salvar_dados(conn, df)
                    if sucesso:
                        st.warning("🧹 Dados apagados!")
                        time.sleep(1)
                        st.rerun()

                if btn_finalizar:
                    total_conforme = df_user[df_user['Conformidade_polo'] == 'Conforme'].shape[0]
                    total_nao_conforme = df_user[df_user['Conformidade_polo'] == 'Não Conforme'].shape[0]
                    destinatario = "nelio.goncalves@enel.com"
                    assunto = "Justificativas Finalizadas"
                    corpo = f"Nélio,\nAs justificativas foram finalizadas:\nPolo: {usuario_atual}\nConforme: {total_conforme}\nNão Conforme: {total_nao_conforme}"
                    params = {"subject": assunto, "body": corpo}
                    query_string = urllib.parse.urlencode(params).replace("+", "%20")
                    mailto_link = f"mailto:{destinatario}?{query_string}"
                    
                    st.success("Resumo gerado!")
                    st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background-color:#4CAF50;color:white;padding:15px;border:none;border-radius:12px;cursor:pointer;">📤 Enviar E-mail</button></a>', unsafe_allow_html=True)
