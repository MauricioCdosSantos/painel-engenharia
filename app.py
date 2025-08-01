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

DATA_FILE = "dados_engenharia.json"
TEMPOS_FILE = "tempos_execucao.json"
COLUMNS = [
    "Prioridade", "Status Projeto", "Status Detalhamento", "Nº Pedido", "Cliente",
    "Cód. Cliente", "Código Schumann", "Descrição do item", "Quantidade",
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

def to_hours(valor, unidade):
    return valor / 60 if unidade == "min" else valor * 24 if unidade == "dia" else valor

df = carregar_dados()
st.title("Painel de Engenharia")
tabs = st.tabs(["Administração", "Projetista: Sandro", "Projetista: Alysson", "Indicadores"])

with tabs[0]:
    st.subheader("Adicionar Novo Item")
    with st.form("form_adicionar"):
        col1, col2, col3 = st.columns(3)
        with col1:
            prioridade = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
            pedido = st.text_input("Nº Pedido")
            cliente = st.text_input("Cliente")
            cod_cliente = st.text_input("Cód. Cliente")
        with col2:
            cod_schumann = st.text_input("Código Schumann")
            descricao = st.text_input("Descrição do item")
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            qtd_estoque = st.number_input("Qtd. Estoque", min_value=0, step=1)
            data_limite = st.text_input("Data Limite ENG (dd/mm)")
            tempo_proj_valor = st.number_input("Valor Tempo Projeto", min_value=0, step=1)
            tempo_proj_unidade = st.selectbox("Unidade Projeto", ["min", "h", "dia"])
        with col3:
            tempo_det_valor = st.number_input("Valor Tempo Detalhamento", min_value=0, step=1)
            tempo_det_unidade = st.selectbox("Unidade Detalhamento", ["min", "h", "dia"])
            desenhos = st.text_input("Desenhos")
            proj_projeto = st.selectbox("Projetista Projeto", ["sandro", "alysson"])
            proj_detalhamento = st.selectbox("Projetista Detalhamento", ["sandro", "alysson"])

        if st.form_submit_button("Adicionar"):
            novo = {
                "Prioridade": prioridade,
                "Status Projeto": "esperando",
                "Status Detalhamento": "esperando",
                "Nº Pedido": pedido,
                "Cliente": cliente,
                "Cód. Cliente": cod_cliente,
                "Código Schumann": cod_schumann,
                "Descrição do item": descricao,
                "Quantidade": quantidade,
                "Qtd. Estoque": qtd_estoque,
                "Data Limite ENG": data_limite,
                "Tempo Projeto": round(to_hours(tempo_proj_valor, tempo_proj_unidade), 2),
                "Tempo Detalhamento": round(to_hours(tempo_det_valor, tempo_det_unidade), 2),
                "Desenhos": desenhos,
                "Projetista Projeto": proj_projeto,
                "Projetista Detalhamento": proj_detalhamento
            }
            df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
            salvar_dados(df)
            st.success("Item adicionado com sucesso.")
            st.rerun()

    st.subheader("Excluir Item")
    idx = st.text_input("Índice do item para excluir")
    if st.button("Excluir") and idx.isdigit():
        df.drop(index=int(idx), inplace=True)
        df.reset_index(drop=True, inplace=True)
        salvar_dados(df)
        st.rerun()

    st.subheader("Tabela Completa (Editável)")
    df_editado = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    if st.button("Salvar Alterações"):
        salvar_dados(df_editado)
        st.success("Alterações salvas com sucesso.")
        st.rerun()

with tabs[1]:
    st.header("Projetista: Sandro")
    st.dataframe(df[df["Projetista Projeto"] == "sandro"], use_container_width=True)

with tabs[2]:
    st.header("Projetista: Alysson")
    st.dataframe(df[df["Projetista Projeto"] == "alysson"], use_container_width=True)
