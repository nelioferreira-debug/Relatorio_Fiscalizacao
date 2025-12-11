 import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal de Justificativas", page_icon="📝")

# --- FUNÇÕES AUXILIARES ---
FILE_DB = 'dados_justificativas.csv'

def carregar_dados():
    """Carrega os dados do arquivo CSV ou cria um novo se não existir."""
    if not os.path.exists(FILE_DB):
        # Cria um DataFrame vazio com as colunas necessárias
        return pd.DataFrame(columns=["Data_Envio", "Polo", "Mes_Referencia", "Justificativa"])
    return pd.read_csv(FILE_DB)

def salvar_dados(novo_dado):
    """Salva uma nova linha no arquivo CSV."""
    df = carregar_dados()
    # Concatena o novo dado com o DataFrame existente
    df = pd.concat([df, pd.DataFrame([novo_dado])], ignore_index=True)
    df.to_csv(FILE_DB, index=False)

# --- INTERFACE PRINCIPAL ---
st.title("📝 Sistema de Justificativas dos Polos")
st.markdown("---")

# Menu lateral para navegação
menu = st.sidebar.selectbox("Menu", ["Enviar Justificativa", "Área do Administrador"])

# --- PÁGINA DE ENVIO (Para os Polos) ---
if menu == "Enviar Justificativa":
    st.header("Envio de Justificativa Mensal")
    st.info("Preencha os dados abaixo para registrar a justificativa do seu polo.")

    with st.form("form_justificativa", clear_on_submit=True):
        # Lista de Polos (Você pode editar essa lista)
        lista_polos = ["Polo Centro", "Polo Norte", "Polo Sul", "Polo Leste", "Polo Oeste"]
        
        col1, col2 = st.columns(2)
        with col1:
            polo = st.selectbox("Selecione o Polo:", lista_polos)
        with col2:
            # Lista de meses para facilitar
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_ref = st.selectbox("Mês de Referência:", meses)
        
        texto_justificativa = st.text_area("Descreva a justificativa:", height=150)
        
        enviado = st.form_submit_button("Enviar Justificativa")

        if enviado:
            if not texto_justificativa:
                st.error("Por favor, escreva uma justificativa antes de enviar.")
            else:
                # Prepara os dados
                novo_registro = {
                    "Data_Envio": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Polo": polo,
                    "Mes_Referencia": mes_ref,
                    "Justificativa": texto_justificativa
                }
                
                # Salva
                salvar_dados(novo_registro)
                st.success(f"Justificativa do {polo} referente a {mes_ref} salva com sucesso!")

# --- ÁREA ADMINISTRATIVA (Para Você) ---
elif menu == "Área do Administrador":
    st.header("🔒 Acesso Restrito")
    
    # Senha simples para evitar curiosos (não é segurança de nível bancário!)
    senha = st.sidebar.text_input("Senha de Admin", type="password")
    
    if senha == "admin123":  # Você mudará essa senha depois
        st.success("Acesso Liberado")
        
        df = carregar_dados()
        
        if df.empty:
            st.warning("Nenhuma justificativa recebida ainda.")
        else:
            st.subheader("Registros Recebidos")
            
            # Filtros
            filtro_polo = st.multiselect("Filtrar por Polo", df["Polo"].unique())
            if filtro_polo:
                df = df[df["Polo"].isin(filtro_polo)]
            
            # Mostra a tabela interativa
            st.dataframe(df, use_container_width=True)
            
            # Botão para baixar em Excel/CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório Completo (CSV)",
                data=csv,
                file_name='relatorio_justificativas.csv',
                mime='text/csv',
            )
            
            # Métricas simples
            st.metric("Total de Justificativas", len(df))
    
    elif senha:
        st.error("Senha incorreta.")
    else:
        st.info("Digite a senha no menu lateral para visualizar os dados.")

# Rodapé
st.markdown("---")
st.caption("Desenvolvido para gestão de polos.")
