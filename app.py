import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

EMAILS_COMPLETO = {
    "sandro": "sandro@schumann.ind.br",
    "alysson": "alysson@schumann.ind.br",
    "jonatan": "jonatan@schumann.ind.br",
    "rafael": "rafael@schumann.ind.br",
    "felipe": "comercial@schumann.ind.br",
    "ianca": "comercial@schumann.ind.br",
    "mauricio": "mauricio@schumann.ind.br",
    "ilario": "ilario@schumann.ind.br",
    "flavio": "flavio@schumann.ind.br"
}

EMAILS_REDUZIDO = {
    "roberson": "roberson@schumann.ind.br",
    "tiago": "programacao@schumann.ind.br",
    "cristian": "pcp@schumann.ind.br"
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

def enviar_email_finalizacao(usuario, projeto):
    try:
        smtp_user = st.secrets["email"]["smtp_user"]
        smtp_pass = st.secrets["email"]["smtp_pass"]
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
    except Exception as e:
        st.error("Erro ao carregar configurações de e-mail do secrets.toml")
        return

    destinatarios = []
    incluir_indicadores = False

    if usuario in EMAILS_COMPLETO:
        destinatarios.append(EMAILS_COMPLETO[usuario])
        incluir_indicadores = True
    elif usuario in EMAILS_REDUZIDO:
        destinatarios.append(EMAILS_REDUZIDO[usuario])

    if not destinatarios:
        return

    assunto = f"Projeto Finalizado: {projeto}"
    corpo = f"<p>O projeto <strong>{projeto}</strong> foi finalizado por <strong>{usuario}</strong>.</p>"

    if incluir_indicadores and os.path.exists(TEMPOS_FILE):
        with open(TEMPOS_FILE, "r", encoding="utf-8") as f:
            registros = json.load(f)
        df_tempos = pd.DataFrame(registros)
        df_tempos["timestamp"] = pd.to_datetime(df_tempos["timestamp"])
        linha = df_tempos[(df_tempos["usuario"] == usuario) & (df_tempos["projeto"] == projeto)]
        inicio = linha[linha["acao"] == "inicio"]["timestamp"].min()
        fim = linha[linha["acao"] == "fim"]["timestamp"].max()
        duracao = (fim - inicio).total_seconds() / 3600 if pd.notna(inicio) and pd.notna(fim) else None
        if duracao:
            corpo += f"<p>Tempo total de execução: <strong>{duracao:.2f} horas</strong></p>"

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        st.warning(f"Falha ao enviar e-mail: {e}")
