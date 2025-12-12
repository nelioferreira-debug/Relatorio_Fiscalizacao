import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import time
import urllib.parse # Necessário para criar o link de e-mail

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SGF - Gestão de Fiscalização", page_icon="⚡", layout="wide")

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
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🏢 Meu Polo", "📝 Tratar Pendências"])

with tab1:
    st.metric("Total de Ordens na Base", len(df))
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if 'data_exec_corte' in df.columns:
            st.subheader("Fiscalizações por Dia")
            df_dia = df.groupby('data_exec_corte').size().reset_index(name='Qtd')
            fig1 = px.bar(df_dia, x='data_exec_corte', y='Qtd')
            st.plotly_chart(fig1, use_container_width=True)
    with col_g2:
        if 'Justificativa_polo' in df.columns:
            st.subheader("Status de Tratamento")
            tratados = df[df['Justificativa_polo'].notna() & (df['Justificativa_polo'] != "")].shape[0]
            total = len(df)
            progresso = (tratados / total) * 100 if total > 0 else 0
            st.progress(progresso / 100, text=f"{progresso:.1f}% Tratado ({tratados}/{total})")

with tab2:
    st.subheader(f"Dados de {usuario_atual}")
    st.metric("Minhas Pendências", len(df_user))
    if not df_user.empty:
        st.dataframe(df_user.head(10), use_container_width=True)
        csv = df_user.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Meus Dados (CSV)", csv, "meus_dados.csv", "text/csv")

with tab3:
    st.header("Tratamento de Justificativas")
    if df_user.empty:
        st.info("Nenhuma ordem para exibir.")
    else:
        lista_ids = df_user['ID'].unique().tolist()
        
        # --- LÓGICA DE NAVEGAÇÃO SEGURA ---
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
            
            # Cálculo de Datas
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
            
            # --- FUNÇÕES AUXILIARES ---
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
                crt1, crt2, crt3 = st.columns(3)
                with crt1: st.write(f"**Ordem Corte:** {limpar_dado(linha.get('num_ordem_serv_crt'))}")
                with crt2: st.write(f"**Tipo Corte:** {limpar_dado(linha.get('Tipo_corte'))}")
                with crt3: st.write(f"**Grupo:** {limpar_dado(linha.get('grupo'))}")
                st.write(f"**Descrição:** {limpar_dado(linha.get('descricao_tipo'))}")
                st.write(f"**Mês Corte:** {limpar_dado(linha.get('mês_corte'))}")
                st.markdown("#### ⏳ Análise de Tempo")
                t1, t2, t3 = st.columns(3)
                with t1:
                    st.write("**Data Solicitação:**")
                    st.write(data_solic_formatada) 
                with t2:
                    st.write("**Data Execução (Final):**")
                    st.write(data_exec_completa)
                with t3:
                    st.metric(label="Diferença (Exec - Solic)", value=diferenca_texto)

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
                
                # --- BOTÕES DE AÇÃO ---
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
                        # Lógica para avançar automaticamente (SEM MEXER NO WIDGET DIRETAMENTE)
                        try:
                            # Descobre o índice atual na lista que está no seletor
                            idx_atual_lista = lista_ids.index(id_selecionado)
                            
                            # Se não for o último item, incrementa a variável de controle e recarrega
                            if idx_atual_lista + 1 < len(lista_ids):
                                st.session_state['indice_navegacao'] = idx_atual_lista + 1
                                st.success("✅ Salvo com sucesso! Carregando próximo...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.success("✅ Salvo! Você chegou ao fim da lista.")
                                st.balloons()
                                st.info("🎉 Não há mais pendências nesta lista. Por favor, clique no botão 'Finalizar e Enviar' (📧) acima para notificar a gestão.")
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
                        st.warning("🧹 Dados do polo foram apagados para esta ordem!")
                        time.sleep(1)
                        st.rerun()

                if btn_finalizar:
                    total_conforme = df_user[df_user['Conformidade_polo'] == 'Conforme'].shape[0]
                    total_nao_conforme = df_user[df_user['Conformidade_polo'] == 'Não Conforme'].shape[0]
                    
                    destinatario = "nelio.goncalves@enel.com"
                    assunto = "[Retorno Polo] - Justificativas Finalizadas"
                    corpo = (
                        f"Nélio,\n"
                        f"As analises sobre os Retornos das Fiscalizações foram finalizadas:\n\n"
                        f"Polo: {usuario_atual}\n"
                        f"Conforme: {total_conforme}\n"
                        f"Não Conforme: {total_nao_conforme}"
                    )
                    
                    params = {"subject": assunto, "body": corpo}
                    query_string = urllib.parse.urlencode(params).replace("+", "%20")
                    mailto_link = f"mailto:{destinatario}?{query_string}"
                    
                    st.success("Resumo gerado com sucesso!")
                    st.info("Clique abaixo para abrir seu e-mail:")
                    st.markdown(f'''
                        <a href="{mailto_link}" target="_blank">
                            <button style="
                                background-color: #4CAF50; 
                                border: none;
                                color: white;
                                padding: 15px 32px;
                                text-align: center;
                                text-decoration: none;
                                display: inline-block;
                                font-size: 16px;
                                margin: 4px 2px;
                                cursor: pointer;
                                border-radius: 12px;
                            ">
                                📤 Clique Aqui para Enviar o E-mail
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
