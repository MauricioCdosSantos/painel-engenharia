import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="Painel de Engenharia - Editável", layout="wide")

# ---------- Autenticação por usuário e senha ----------
USERS = {
    "engenharia": "senha123",
    "comercial": "senha456",
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
            return pd.DataFrame(data).reindex(columns=COLUMNS)
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

# ---------- Layout ----------
st.title("Painel de Engenharia - Gestão de Projetos (Editável)")
st.caption(f"Usuário logado: {st.session_state.usuario}")

# Carregar dados
if "df" not in st.session_state:
    st.session_state.df = carregar_dados()

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

# ---------- Abas ----------
abas = st.tabs(["Administração", "Projetista: Sandro", "Projetista: Alysson", "Indicadores"])

# ---------- Aba Administração ----------
with abas[0]:
    st.subheader("Adicionar Novo Item")
    with st.form("form_administracao"):
        col1, col2, col3 = st.columns(3)
        with col1:
            prioridade = st.selectbox("Prioridade", ["1", "2", "3"])
            status = st.selectbox("Status", ["esperando", "fazendo", "feito"])
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
            unidade_projeto = st.selectbox("Unidade de Tempo Projeto", ["min", "h", "dia"])
            valor_projeto = st.number_input("Valor Tempo Projeto", min_value=0, step=1)
        with col3:
            unidade_detalhamento = st.selectbox("Unidade de Tempo Detalhamento", ["min", "h", "dia"])
            valor_detalhamento = st.number_input("Valor Tempo Detalhamento", min_value=0, step=1)
            desenhos = st.text_input("Desenhos")
            projetistas = ["Sandro", "Alysson"]
            proj_projeto = st.selectbox("Projetista Projeto", projetistas)
            proj_detalhamento = st.selectbox("Projetista Detalhamento", projetistas)

        def converter_para_horas(valor, unidade):
            if unidade == "min":
                return round(valor / 60, 2)
            elif unidade == "dia":
                return round(valor * 24, 2)
            return valor

        if st.form_submit_button("Adicionar"):
            tempo_projeto = converter_para_horas(valor_projeto, unidade_projeto)
            tempo_detalhamento = converter_para_horas(valor_detalhamento, unidade_detalhamento)
            novo_item = dict(zip(COLUMNS, [
                prioridade, status, pedido, entrega, cliente, cod_cliente,
                cod_schumann, descricao, quantidade, em_estoque,
                data_limite, tempo_projeto, tempo_detalhamento, desenhos,
                proj_projeto, proj_detalhamento
            ]))
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([novo_item])], ignore_index=True)
            salvar_dados(st.session_state.df)
            st.success("Item adicionado com sucesso.")
            st.rerun()

    st.subheader("Excluir Item")
    index_excluir = st.text_input("Digite o índice da linha para excluir")
    if st.button("Excluir linha selecionada"):
        if index_excluir.isdigit() and int(index_excluir) in st.session_state.df.index:
            st.session_state.df.drop(index=int(index_excluir), inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            if st.session_state.df.empty:
                st.session_state.df = carregar_dados()
            salvar_dados(st.session_state.df)
            st.success("Linha excluída com sucesso.")
            st.rerun()
        else:
            st.warning("Índice inválido")

    st.subheader("Tabela Completa")
    st.dataframe(st.session_state.df, use_container_width=True)

# ---------- Abas por Projetista ----------
projetistas = ["Sandro", "Alysson"]
for i, proj in enumerate(projetistas):
    with abas[i+1]:
        df_proj = df_filtrado[(df_filtrado["Projetista Projeto"] == proj) | (df_filtrado["Projetista Detalhamento"] == proj)]
        st.subheader(f"Projeto Atual - {proj}")
        projetos_disponiveis = df_proj[df_proj["Status"] != "feito"]["Descrição do item"].dropna().unique().tolist()
        projeto_selecionado = st.selectbox("Selecione o projeto que está sendo executado", options=projetos_disponiveis, key=f"projeto_{proj}")

        if projeto_selecionado:
            if st.button(f"Iniciar projeto", key=f"iniciar_{proj}"):
                st.session_state[f"inicio_{proj}"] = datetime.now()
                st.session_state.df.loc[st.session_state.df["Descrição do item"] == projeto_selecionado, "Status"] = "fazendo"
                salvar_dados(st.session_state.df)
                registrar_tempo(proj, projeto_selecionado, "inicio")
                st.rerun()
            if st.button("Parar projeto", key=f"parar_{proj}"):
                motivo = st.text_input("Motivo da parada", key=f"motivo_{proj}")
                if motivo:
                    registrar_tempo(proj, projeto_selecionado, "parada", motivo)
                    st.success("Parada registrada")
            if st.button("Finalizar projeto", key=f"finalizar_{proj}"):
                registrar_tempo(proj, projeto_selecionado, "fim")
                st.session_state.df.loc[st.session_state.df["Descrição do item"] == projeto_selecionado, "Status"] = "feito"
                salvar_dados(st.session_state.df)
                st.success("Projeto finalizado")
                st.rerun()

        st.subheader(f"Tabela de Itens - {proj}")
        try:
            st.dataframe(df_proj[COLUMNS[:-2]], use_container_width=True)
        except KeyError as e:
            st.warning("Erro ao carregar colunas. Verifique se todos os nomes estão corretos.")
            st.exception(e)

        st.subheader(f"Gráfico de Gantt - {proj}")
        if not df_proj.empty:
            gantt_df = df_proj[df_proj["Data Limite ENG"].notna() & (df_proj["Data Limite ENG"] != "")].copy()
            try:
                def parse_data_limite(date_str):
                    try:
                        return pd.to_datetime(date_str, format="%d/%m/%Y")
                    except:
                        return pd.to_datetime(date_str + f"/{datetime.today().year}", format="%d/%m/%Y")

                gantt_df["Finish"] = gantt_df["Data Limite ENG"].apply(parse_data_limite)
                gantt_df["Tempo"] = gantt_df.apply(lambda row: float(row["Tempo Projeto"]) if row["Projetista Projeto"] == proj else float(row["Tempo Detalhamento"]), axis=1)
                gantt_df["Start"] = gantt_df["Finish"] - gantt_df["Tempo"].apply(lambda x: timedelta(hours=x))
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
        else:
            st.info("Nenhum dado disponível para este projetista.")

# ---------- Indicadores ----------
with abas[-1]:
    st.subheader("Indicadores de Tempo de Projetos")
    if os.path.exists(TEMPOS_FILE):
        with open(TEMPOS_FILE, "r", encoding="utf-8") as f:
            registros = json.load(f)
        df_tempos = pd.DataFrame(registros)
        df_tempos["timestamp"] = pd.to_datetime(df_tempos["timestamp"])

        tempo_execucao = df_tempos.pivot_table(index=["usuario", "projeto"], columns="acao", values="timestamp", aggfunc="first").reset_index()
        tempo_execucao["duracao"] = (tempo_execucao["fim"] - tempo_execucao["inicio"]).dt.total_seconds() / 3600
        st.dataframe(tempo_execucao.dropna(subset=["duracao"]), use_container_width=True)
        st.bar_chart(tempo_execucao.set_index("projeto")["duracao"])
    else:
        st.info("Nenhuma execução registrada ainda.")


