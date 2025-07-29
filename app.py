import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Painel de Engenharia - Editável", layout="wide")

# ---------- Autenticação por usuário e senha ----------
USERS = {"engenharia": "senha123", "comercial": "senha456"}
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""

if not st.session_state.autenticado:
    st.title("Acesso Restrito")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in USERS and USERS[usuario] == senha:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

DATA_FILE = "dados_engenharia.json"

# ---------- Funções auxiliares ----------
def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))
    return pd.DataFrame(columns=["Cliente", "Pré-entrega", "Código Schumann", "Descrição", "Data Limite ENG", "Prioridade", "Status", "Em Estoque"])

def salvar_dados(df):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4, ensure_ascii=False)

# ---------- Layout ----------
st.title("Painel de Engenharia - Gestão de Projetos (Editável)")

# Carregar dados
st.session_state.df = carregar_dados() if "df" not in st.session_state else st.session_state.df

# ---------- Adição de novo item ----------
st.sidebar.header("Adicionar Novo Item")
with st.sidebar.form("novo_item"):
    cliente = st.text_input("Cliente")
    pre_entrega = st.text_input("Pré-entrega (dd/mm)")
    cod_schumann = st.text_input("Código Schumann")
    descricao = st.text_area("Descrição")
    data_limite = st.text_input("Data Limite ENG (dd/mm/yyyy)")
    prioridade = st.selectbox("Prioridade", ["URGENTE", "0.1-Prioridade 2", "0.2-Prioridade 1", "2.0-Prioridade 2"])
    status = st.text_input("Status")
    em_estoque = st.selectbox("Em Estoque", ["Sim", "Não"])
    submit = st.form_submit_button("Adicionar")

    if submit:
        nova_linha = {
            "Cliente": cliente,
            "Pré-entrega": pre_entrega,
            "Código Schumann": cod_schumann,
            "Descrição": descricao,
            "Data Limite ENG": data_limite,
            "Prioridade": prioridade,
            "Status": status,
            "Em Estoque": em_estoque
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nova_linha])], ignore_index=True)
        salvar_dados(st.session_state.df)
        st.success("Item adicionado com sucesso.")

# ---------- Edição dos dados ----------
st.subheader("Editar Tabela de Itens")
if len(st.session_state.df) > 0:
    delete_index = st.number_input("Digite o índice da linha para excluir (0 a N):", min_value=0, max_value=len(st.session_state.df)-1, step=1)
    if st.button("Excluir linha selecionada"):
        st.session_state.df = st.session_state.df.drop(st.session_state.df.index[delete_index]).reset_index(drop=True)
        salvar_dados(st.session_state.df)
        st.success("Linha excluída com sucesso!")

edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    key="editavel"
)

if st.button("Salvar alterações"):
    st.session_state.df = edited_df
    salvar_dados(edited_df)
    st.success("Alterações salvas com sucesso!")

# ---------- Gantt ----------
st.subheader("Gráfico de Gantt - Prazo Engenharia")
gantt_df = st.session_state.df.copy()
gantt_df = gantt_df[gantt_df["Data Limite ENG"].notna() & (gantt_df["Data Limite ENG"] != "")]

try:
    def parse_data_limite(date_str):
        try:
            return pd.to_datetime(date_str, format="%d/%m/%Y")
        except:
            return pd.to_datetime(date_str + f"/{datetime.today().year}", format="%d/%m/%Y")

    gantt_df["Finish"] = gantt_df["Data Limite ENG"].apply(parse_data_limite)
    gantt_df["Start"] = pd.to_datetime("today")
    gantt_df["Atrasado"] = gantt_df["Finish"] < datetime.now()
    gantt_df["Cor"] = gantt_df["Atrasado"].map(lambda x: "Atrasado" if x else gantt_df["Prioridade"])

    fig = px.timeline(
        gantt_df,
        x_start="Start",
        x_end="Finish",
        y="Descrição",
        color="Cor",
        title="Prazos por Prioridade",
        labels={"Descrição": "Item", "Start": "Início", "Finish": "Prazo"}
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=500,
        xaxis_title="Data",
        yaxis_title="Descrição",
        bargap=0.2
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning("Não foi possível gerar o gráfico de Gantt. Verifique os dados de datas.")
