import streamlit as st
import pandas as pd
import datetime as dt

# Simula os dados extraídos da planilha da imagem
data = [
    {"Cliente": "CASP", "Pré-entrega": "09/06", "Código Schumann": "2020002903", "Descrição": "PENDULAR 3 SAIDAS Ø240 1045 MANUAL C/ ACION. ELET", "Data Limite ENG": "04/06", "Prioridade": "2.0-Prioridade 2", "Status": "Em desenvolvimento/Edição", "Em Estoque": "Sim"},
    {"Cliente": "GSI", "Pré-entrega": "01/07", "Código Schumann": "2020003582", "Descrição": "PEND. 3 S Ø320 PREMIUM MAN. C/ ACION. ELET. LINAK", "Data Limite ENG": "05/06", "Prioridade": "URGENTE", "Status": "", "Em Estoque": "Não"},
    {"Cliente": "SCHUMANN", "Pré-entrega": "05/06", "Código Schumann": "2021000036", "Descrição": "BIF.45° C/ PEND. Ø240 1045 ESP. PREMIUM C/ CX. DIR", "Data Limite ENG": "30/06", "Prioridade": "URGENTE", "Status": "Estrutura", "Em Estoque": "Não"},
    {"Cliente": "GSI", "Pré-entrega": "01/07", "Código Schumann": "2020003621", "Descrição": "BIF. Ø320 X 90° 1045 C/ ACIO. ELETRICO LINAK", "Data Limite ENG": "06/06", "Prioridade": "0.1-Prioridade 2", "Status": "Estrutura", "Em Estoque": "Não"},
    {"Cliente": "KW", "Pré-entrega": "15/08", "Código Schumann": "2010000863", "Descrição": "ANEL DO TELHADO SL 12 18 24", "Data Limite ENG": "", "Prioridade": "0.2-Prioridade 1", "Status": "Estrutura", "Em Estoque": "Não"},
]

df = pd.DataFrame(data)

# Conversão de datas
if "Data Limite ENG" in df.columns:
    df["Data Limite ENG"] = pd.to_datetime(df["Data Limite ENG"], format="%d/%m", errors='coerce').apply(
        lambda x: x.replace(year=dt.datetime.now().year) if pd.notnull(x) else x
    )

# Título
st.title("Painel de Engenharia - Gestão de Projetos")

# Filtros laterais
with st.sidebar:
    st.header("Filtros")
    cliente = st.multiselect("Cliente", df["Cliente"].unique())
    prioridade = st.multiselect("Prioridade", df["Prioridade"].unique())
    status = st.multiselect("Status", df["Status"].dropna().unique())
    estoque = st.radio("Em Estoque", options=["Todos", "Sim", "Não"], index=0)

# Aplicação de filtros
filtro = df.copy()
if cliente:
    filtro = filtro[filtro["Cliente"].isin(cliente)]
if prioridade:
    filtro = filtro[filtro["Prioridade"].isin(prioridade)]
if status:
    filtro = filtro[filtro["Status"].isin(status)]
if estoque != "Todos":
    filtro = filtro[filtro["Em Estoque"] == estoque]

# Destaque de urgentes
def cor_linha(row):
    if row["Prioridade"] == "URGENTE":
        return ["background-color: red; color: white"] * len(row)
    elif row["Status"] == "Estrutura":
        return ["background-color: #e6f2ff"] * len(row)
    else:
        return [""] * len(row)

# Tabela
st.subheader("Lista de Itens de Engenharia")
st.dataframe(filtro.style.apply(cor_linha, axis=1), use_container_width=True)

# Gráfico de prioridades
st.subheader("Distribuição de Prioridades")
st.bar_chart(df["Prioridade"].value_counts())
