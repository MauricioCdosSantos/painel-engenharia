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

for i, nome in enumerate(["sandro", "alysson"], start=1):
    with tabs[i]:
        st.header(f"Projetista: {nome.capitalize()}")
        df_proj = df[df["Projetista Projeto"] == nome].copy()
        df_det = df[df["Projetista Detalhamento"] == nome].copy()

        df_proj["Tipo"] = "Projeto"
        df_det["Tipo"] = "Detalhamento"

        df_proj["Status"] = df_proj["Status Projeto"]
        df_det["Status"] = df_det["Status Detalhamento"]

        df_user = pd.concat([df_proj, df_det], ignore_index=True)
        df_user_display = df_user.drop(columns=["Status Projeto", "Status Detalhamento"])
        st.dataframe(df_user_display, use_container_width=True)

        st.subheader("Ações")
        projeto_sel = st.selectbox("Selecionar projeto", df_user["Descrição do item"].unique(), key=f"projeto_{nome}")
        tipo_sel = st.radio("Tipo de atividade", ["Projeto", "Detalhamento"], key=f"tipo_{nome}")

        if st.button("Iniciar", key=f"iniciar_{nome}"):
            registrar_tempo(nome, projeto_sel, tipo_sel, "inicio")
            st.rerun()

        motivo = st.text_input("Motivo da parada", key=f"motivo_{nome}")
        if st.button("Parar", key=f"parar_{nome}"):
            registrar_tempo(nome, projeto_sel, tipo_sel, "parada", motivo)
            st.rerun()

        if st.button("Finalizar", key=f"fim_{nome}"):
            registrar_tempo(nome, projeto_sel, tipo_sel, "fim")
            st.rerun()

        st.subheader(f"Gráfico de Gantt - {nome.capitalize()}")
        df_user_gantt = df_user[df_user["Status"] != "concluído"]
        df_user_gantt = df_user_gantt.sort_values(by=["Data Limite ENG", "Prioridade"])
        base_time = datetime.now().replace(hour=7, minute=10, second=0, microsecond=0)
        gantt_data = []
        for _, row in df_user_gantt.iterrows():
            duracao = row["Tempo Projeto"] if row["Tipo"] == "Projeto" else row["Tempo Detalhamento"]
            if duracao and duracao > 0:
                start_time = base_time
                horas_restantes = duracao
                while horas_restantes > 0:
                    end_time = start_time + timedelta(hours=horas_restantes)
                    if start_time.hour < 11 or (start_time.hour == 11 and start_time.minute <= 50):
                        bloco_fim = min(end_time, start_time.replace(hour=11, minute=50))
                    else:
                        start_time = start_time.replace(hour=13, minute=0)
                        bloco_fim = min(end_time, start_time.replace(hour=16, minute=50))
                    tarefa_duracao = (bloco_fim - start_time).total_seconds() / 3600
                    if tarefa_duracao > 0:
                        label = f"{row['Descrição do item']} ({row['Tipo']})"
                        gantt_data.append({"Tarefa": label, "Início": start_time, "Fim": bloco_fim})
                        horas_restantes -= tarefa_duracao
                    start_time = bloco_fim + timedelta(minutes=5)
        if gantt_data:
            gantt_df = pd.DataFrame(gantt_data)
            fig = px.timeline(gantt_df, x_start="Início", x_end="Fim", y="Tarefa", title=f"Gráfico de Gantt - {nome.capitalize()}")
            st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.header("Indicadores")
    registros = carregar_tempos()
    st.write(registros)

