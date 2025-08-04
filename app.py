import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="Painel de Engenharia", layout="wide")

USERS = {
    "sandro": "123",
    "alysson": "123",
    "jonatan": "123",
    "rafael": "123",
    "felipe": "123",
    "roberson": "123",
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

if st.session_state.autenticado:
    DATA_FILE = "dados_engenharia.json"
    TEMPOS_FILE = "tempos_execucao.json"
    COLUMNS = [
        "Prioridade", "Status Projeto", "Status Detalhamento", "Nº Pedido", "Cliente",
        "Cód. Cliente", "Código Schumann", "Descrição do item",
        "Qtd. Estoque", "Data Limite ENG", "Tempo Projeto", "Tempo Detalhamento", "Desenhos",
        "Projetista Projeto", "Projetista Detalhamento"
    ]

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

    def registrar_tempo(usuario, projeto, tipo, acao, motivo=None):
        entrada = {
            "usuario": usuario,
            "projeto": projeto,
            "tipo": tipo,
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

        df = carregar_dados()
        idxs = df[df["Descrição do item"] == projeto].index
        for idx in idxs:
            col_status = "Status Projeto" if tipo == "Projeto" else "Status Detalhamento"
            if acao == "inicio":
                df.at[idx, col_status] = "em processo"
            elif acao == "parada":
                df.at[idx, col_status] = "em pausa"
            elif acao == "fim":
                df.at[idx, col_status] = "concluído"
        salvar_dados(df)

    def carregar_tempos():
        if os.path.exists(TEMPOS_FILE):
            with open(TEMPOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def to_hours(valor, unidade):
        return valor / 60 if unidade == "min" else valor * 24 if unidade == "dia" else valor

    # conteúdo da aplicação (painel de engenharia) continua aqui...
    # (nada mais fora desse bloco, garante segurança e performance)
