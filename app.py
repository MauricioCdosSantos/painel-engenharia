import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="Painel de Engenharia - Editável", layout="wide")

# ---------- Autenticação por usuário e senha ----------
USERS = {
    "sandro": "123",
    "alysson": "123",
    "jonatan": "123",
    "rafael": "123",
    "felipe": "123",
    "roberson": "123",
    "ianca": "123",
    "tiago": "123",
    "cristian": "123",
    "ilario": "123",
    "flavio": "123",
    "mauricio": "123"
}

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
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

DATA_FILE = "dados_engenharia.json"
TEMPOS_FILE = "tempos_execucao.json"
COLUMNS = [
    "Prioridade", "Status", "Nº Pedido", "Data Entrega Pedido", "Cliente",
    "Cód. Cliente", "Código Schumann", "Descrição do item", "Quantidade",
    "Em Estoque", "Data Limite ENG", "Tempo Projeto", "Tempo Detalhamento", "Desenhos",
    "Projetista Projeto", "Projetista Detalhamento"
]

# ---------- Funções auxiliares ----------
def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = None
            return df[COLUMNS]
    return pd.DataFrame(columns=COLUMNS)

def salvar_dados(df):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4, ensure_ascii=False)

def registrar_tempo(usuario, projeto, acao, motivo=None):
    entrada = {
        "usuario": usuario,
        "projeto": projeto,
        "acao": acao,
        "motivo": motivo,
        "timestamp": datetime.now().isoformat()
    }
    if os.path.exists(TEMPOS_FILE):
        with open(TEMPOS_FILE, "r", encoding="utf-8") as f:
            registros = json.load(f)
    else:
        registros = []
    registros.append(entrada)
    with open(TEMPOS_FILE, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)

def carregar_tempos():
    if os.path.exists(TEMPOS_FILE):
        with open(TEMPOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ---------- Interface principal ----------
st.title("Painel de Engenharia")
df = carregar_dados()
st.dataframe(df, use_container_width=True)

# Exibe abas por usuário
abas = ["Administração"] + [f"Projetista: {nome.capitalize()}" for nome in USERS.keys()] + ["Indicadores"]
aba = st.selectbox("Selecione a aba", abas)

if aba == "Administração":
    st.subheader("Tabela Completa")
    st.dataframe(df, use_container_width=True)

elif aba == "Indicadores":
    tempos = carregar_tempos()
    registros_df = pd.DataFrame(tempos)
    if not registros_df.empty:
        registros_df["timestamp"] = pd.to_datetime(registros_df["timestamp"])
        registros_df["data"] = registros_df["timestamp"].dt.date
        tempo_total = registros_df.groupby("usuario")["timestamp"].count().reset_index(name="Eventos")
        st.subheader("Resumo de Eventos por Usuário")
        st.dataframe(tempo_total, use_container_width=True)

        st.subheader("Linha do Tempo de Ações")
        fig = px.timeline(registros_df.sort_values(by="timestamp"), x_start="timestamp", x_end="timestamp", y="usuario", color="acao", title="Ações dos Projetistas")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado de tempo registrado ainda.")

else:
    nome_projetista = aba.split(": ")[1].lower()
    filtrado = df[(df["Projetista Projeto"].str.lower() == nome_projetista) | (df["Projetista Detalhamento"].str.lower() == nome_projetista)]
    st.subheader(f"Tarefas do Projetista: {nome_projetista.capitalize()}")
    st.dataframe(filtrado, use_container_width=True)

    projetos_disponiveis = filtrado["Descrição do item"].unique().tolist()
    projeto_atual = st.selectbox("Selecione o projeto que está trabalhando", [""] + projetos_disponiveis)

    if projeto_atual:
        col1, col2, col3 = st.columns(3)
        if col1.button("Iniciar Projeto"):
            registrar_tempo(st.session_state.usuario, projeto_atual, "inicio")
            st.success("Início registrado.")
        if col2.button("Parar Projeto"):
            motivo = st.text_input("Informe o motivo da parada")
            if motivo:
                registrar_tempo(st.session_state.usuario, projeto_atual, "parada", motivo)
                st.success("Parada registrada.")
        if col3.button("Finalizar Projeto"):
            registrar_tempo(st.session_state.usuario, projeto_atual, "fim")
            st.success("Projeto finalizado.")
