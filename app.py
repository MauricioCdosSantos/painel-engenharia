import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
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
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

DATA_FILE = "dados_engenharia.json"

# ---------- Funções auxiliares ----------
def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))
    return pd.DataFrame(columns=[
        "Prioridade", "Status", "Nº Pedido", "Data Entrega Pedido", "Cliente",
        "Cód. Cliente", "Código Schumann", "Descrição do item", "Quantidade",
        "Em Estoque", "Data Limite ENG", "Tempo Estimado", "Desenhos",
        "Projetista Projeto", "Projetista Detalhamento"
    ])

def salvar_dados(df):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4, ensure_ascii=False)

# ---------- Layout ----------
st.title("Painel de Engenharia - Gestão de Projetos (Editável)")
st.caption(f"Usuário logado: {st.session_state.usuario}")

# Carregar dados
st.session_state.df = carregar_dados() if "df" not in st.session_state else st.session_state.df

# ---------- Filtros ----------
st.sidebar.header("Filtros")
filtro_cliente = st.sidebar.multiselect("Cliente", options=st.session_state.df["Cliente"].dropna().unique())
filtro_prioridade = st.sidebar.multiselect("Prioridade", options=st.session_state.df["Prioridade"].dropna().unique())
filtro_status = st.sidebar.multiselect("Status", options=st.session_state.df["Status"].dropna().unique())
filtro_estoque = st.sidebar.radio("Em Estoque", options=["Todos", "Sim", "Não"], index=0)

# ---------- Aplicar filtros ----------
df_filtrado = st.session_state.df.copy()
if filtro_cliente:
    df_filtrado = df_filtrado[df_filtrado["Cliente"].isin(filtro_cliente)]
if filtro_prioridade:
    df_filtrado = df_filtrado[df_filtrado["Prioridade"].isin(filtro_prioridade)]
if filtro_status:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]
if filtro_estoque != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Em Estoque"] == filtro_estoque]

# ---------- Abas por Projetista ----------
projetistas = ["Sandro", "Alysson"]
abas = st.tabs([f"Projetista: {p}" for p in projetistas])

for i, proj in enumerate(projetistas):
    with abas[i]:
        df_proj = df_filtrado[(df_filtrado["Projetista Projeto"] == proj) | (df_filtrado["Projetista Detalhamento"] == proj)]

        st.subheader(f"Tabela de Itens - {proj}")
        try:
            st.dataframe(df_proj[[
                "Prioridade", "Status", "Nº Pedido", "Data Entrega Pedido", "Cliente",
                "Cód. Cliente", "Código Schumann", "Descrição do item", "Quantidade",
                "Em Estoque", "Data Limite ENG", "Tempo Estimado", "Desenhos"
            ]], use_container_width=True)
        except KeyError as e:
            st.warning("Erro ao carregar colunas. Verifique se todos os nomes estão corretos.")
            st.exception(e)

        st.subheader("Adicionar Novo Item")
        with st.form(f"form_adicao_{proj}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                prioridade = st.selectbox("Prioridade", ["1", "2", "3"])
                status = st.selectbox("Status", ["esperando", "fazendo", "feito"])
                pedido = st.text_input("Nº Pedido")
                entrega = st.text_input("Data Entrega Pedido (dd/mm)")
                cliente = st.text_input("Cliente")
            with col2:
                cod_cliente = st.text_input("Cód. Cliente")
                cod_schumann = st.text_input("Código Schumann")
                descricao = st.text_input("Descrição do item")
                quantidade = st.number_input("Quantidade", min_value=1, step=1)
                em_estoque = st.selectbox("Em Estoque", ["Sim", "Não"])
            with col3:
                data_limite = st.text_input("Data Limite ENG (dd/mm)")
                tempo_estimado = st.number_input("Tempo Estimado (dias)", min_value=1, step=1)
                desenhos = st.text_input("Desenhos")
                proj_projeto = st.selectbox("Projetista Projeto", projetistas)
                proj_detalhamento = st.selectbox("Projetista Detalhamento", projetistas)

            if st.form_submit_button("Adicionar"):
                novo_item = {
                    "Prioridade": prioridade,
                    "Status": status,
                    "Nº Pedido": pedido,
                    "Data Entrega Pedido": entrega,
                    "Cliente": cliente,
                    "Cód. Cliente": cod_cliente,
                    "Código Schumann": cod_schumann,
                    "Descrição do item": descricao,
                    "Quantidade": quantidade,
                    "Em Estoque": em_estoque,
                    "Data Limite ENG": data_limite,
                    "Tempo Estimado": tempo_estimado,
                    "Desenhos": desenhos,
                    "Projetista Projeto": proj_projeto,
                    "Projetista Detalhamento": proj_detalhamento
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([novo_item])], ignore_index=True)
                salvar_dados(st.session_state.df)
                st.success("Item adicionado com sucesso.")
                st.rerun()

        st.subheader(f"Gráfico de Gantt - {proj}")
        gantt_df = df_proj[df_proj["Data Limite ENG"].notna() & (df_proj["Data Limite ENG"] != "")].copy()

        try:
            def parse_data_limite(date_str):
                try:
                    return pd.to_datetime(date_str, format="%d/%m/%Y")
                except:
                    return pd.to_datetime(date_str + f"/{datetime.today().year}", format="%d/%m/%Y")

            gantt_df["Finish"] = gantt_df["Data Limite ENG"].apply(parse_data_limite)
            gantt_df["Tempo"] = gantt_df["Tempo Estimado"].fillna(0).astype(int)
            gantt_df["Start"] = gantt_df["Finish"] - gantt_df["Tempo"].apply(lambda x: timedelta(days=int(x)))
            gantt_df["Atrasado"] = gantt_df["Finish"] < datetime.now()
            gantt_df["Cor"] = gantt_df.apply(lambda row: "Atrasado" if row["Atrasado"] else row["Prioridade"], axis=1)

            fig = px.timeline(
                gantt_df,
                x_start="Start",
                x_end="Finish",
                y="Descrição do item",
                color="Cor",
                title=f"Prazos por Prioridade - {proj}",
                labels={"Descrição do item": "Item", "Start": "Início", "Finish": "Prazo"}
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=500, bargap=0.2)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("Não foi possível gerar o gráfico de Gantt para este projetista. Verifique os dados de datas.")
            st.exception(e)

