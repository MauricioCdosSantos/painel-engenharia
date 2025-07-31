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
    "Prioridade", "Status Projeto", "Status Detalhamento", "Nº Pedido", "Data Entrega Pedido", "Cliente",
    "Cód. Cliente", "Código Schumann", "Descrição do item", "Quantidade",
    "Em Estoque", "Data Limite ENG", "Tempo Projeto", "Tempo Detalhamento", "Desenhos",
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
            entrega = st.text_input("Data Entrega Pedido (dd/mm)")
            cliente = st.text_input("Cliente")
            cod_cliente = st.text_input("Cód. Cliente")
        with col2:
            cod_schumann = st.text_input("Código Schumann")
            descricao = st.text_input("Descrição do item")
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            em_estoque = st.selectbox("Em Estoque", ["Sim", "Não"])
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
                "Data Entrega Pedido": entrega,
                "Cliente": cliente,
                "Cód. Cliente": cod_cliente,
                "Código Schumann": cod_schumann,
                "Descrição do item": descricao,
                "Quantidade": quantidade,
                "Em Estoque": em_estoque,
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

    st.subheader("Tabela Completa")
    st.dataframe(df, use_container_width=True)

for i, nome_projetista in enumerate(["sandro", "alysson"], start=1):
    with tabs[i]:
        st.subheader(f"Projetista: {nome_projetista.capitalize()}")

        st.markdown("**Controles do Projeto**")
        projeto_selecionado = st.selectbox("Selecionar projeto", df[df["Projetista Projeto"] == nome_projetista]["Descrição do item"].unique(), key=f"projeto_{nome_projetista}")
        motivo_parada = st.text_input("Motivo da parada", key=f"motivo_{nome_projetista}")
        col1, col2, col3 = st.columns(3)
        if col1.button("Iniciar", key=f"iniciar_{nome_projetista}"):
            registrar_tempo(st.session_state.usuario, projeto_selecionado, "início")
        if col2.button("Parar", key=f"parar_{nome_projetista}"):
            registrar_tempo(st.session_state.usuario, projeto_selecionado, "parada", motivo_parada)
        if col3.button("Finalizar", key=f"finalizar_{nome_projetista}"):
            registrar_tempo(st.session_state.usuario, projeto_selecionado, "fim")

        st.divider()
        filtrado = df[((df["Projetista Projeto"] == nome_projetista) | (df["Projetista Detalhamento"] == nome_projetista)) & ~(df["Status Projeto"] == "feito")]
        filtrado = filtrado.sort_values(by=["Data Limite ENG", "Prioridade"], ascending=[True, True])
        st.dataframe(filtrado, use_container_width=True)

        gantt_df = pd.DataFrame()
        for _, row in filtrado.iterrows():
            if row["Projetista Projeto"] == nome_projetista:
                tempo = row["Tempo Projeto"]
            else:
                tempo = row["Tempo Detalhamento"]
            if pd.notna(tempo) and tempo > 0:
                inicio = datetime.now().replace(hour=7, minute=10, second=0, microsecond=0)
                fim = inicio + timedelta(hours=tempo)
                gantt_df = pd.concat([gantt_df, pd.DataFrame([{
                    "Tarefa": row["Descrição do item"],
                    "Início": inicio,
                    "Fim": fim
                }])])

        if not gantt_df.empty:
            fig = px.timeline(gantt_df, x_start="Início", x_end="Fim", y="Tarefa", title=f"Gráfico de Gantt - {nome_projetista.capitalize()}")
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum projeto com tempo estimado para exibir o Gantt.")

with tabs[3]:
    st.subheader("Indicadores")
    tempos = carregar_tempos()
    registros_df = pd.DataFrame(tempos)
    if not registros_df.empty:
        registros_df["timestamp"] = pd.to_datetime(registros_df["timestamp"])
        registros_df["data"] = registros_df["timestamp"].dt.date
        st.dataframe(registros_df, use_container_width=True)

        st.subheader("Linha do Tempo")
        fig = px.timeline(
            registros_df.sort_values(by="timestamp"),
            x_start="timestamp", x_end="timestamp", y="usuario",
            color="acao", title="Atividades"
        )
        fig.update_yaxes(categoryorder='total ascending')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de tempo registrado.")
