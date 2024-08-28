import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Configuração do locale para formatação de moeda
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas", layout="wide")

# Dados de login (em produção, use um banco de dados seguro)
users = {
    "admin": "password123",
    "Guilherme": "D2*5la10",
    "Roberto": "88226106",
    "João": "1234",
    "Vanessa": "password123",
    "Jacqueline": "123"
}

# Função para verificar as credenciais do usuário
def check_credentials(username, password):
    if username in users and users[username] == password:
        return True
    return False

# Tela de login
def login():
    st.title("Login")
    st.image("SuperCarnes_Logo-background-removed.png", width=300)  # Ajuste o tamanho da imagem conforme necessário
    st.header("Por favor, faça o login para acessar o Dashboard")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

# Função para logout
def logout():
    st.session_state["logged_in"] = False
    if "username" in st.session_state:
        username = st.session_state["username"]
        if "active_sessions" in st.session_state:  # Verifica se 'active_sessions' está presente no estado de sessão
           if username in st.session_state['active_sessions']:
            st.session_state['active_sessions'].pop(username)  # Remove o usuário do dicionário de sessões ativas
        st.rerun()    

# Função para mostrar a página principal após o login
def main_page():
    # Carregando os dados do novo arquivo Excel
    df_vendas = pd.read_excel("01-05.xls")

    # Convertendo a coluna de datas para o tipo datetime
    df_vendas["DTSAIDA"] = pd.to_datetime(df_vendas["DTSAIDA"], errors='coerce')

    # Adicionando coluna de mês e ano
    df_vendas["Mês"] = df_vendas["DTSAIDA"].apply(lambda x: f"{x.year}-{x.month:02d}" if pd.notnull(x) else None)
    
    # Lista de vendedores permitidos para Vanessa
    vendedores_vanessa = [
        "RCA: 19 - Aline de Almeida Melo",
        "RCA: 30 - Carla",
        "RCA: 33 - Diane Silva de Andrade",
        "RCA: 32 - Edileide de Jesus",
        "RCA: 10 - Jaqueline de Andrade",
        "RCA: 8 - Roseli Freire Martins"
    ]
    
    # Filtro de vendedores com base no usuário logado
    username = st.session_state["username"]
    if username == "Vanessa":
        df_vendas = df_vendas[df_vendas["CODUSUR"].isin(vendedores_vanessa)]

    # Obtenha a lista de vendedores e produtos a partir dos dados
    vendedores = list(df_vendas["CODUSUR"].unique())
    produtos = list(df_vendas["DESCRICAO"].unique())
    
    # Filtros na barra lateral
    st.sidebar.image("SuperCarnes_Logo-background-removed.png", use_column_width=True)  # Adicione o caminho correto para sua imagem
    st.sidebar.header("Filtros")
    all_months = df_vendas["Mês"].dropna().unique()
    all_months.sort()
    month = st.sidebar.selectbox("Selecione o Mês", all_months)
    
    vendedores_com_todos = ['Todos'] + vendedores
    vendedor = st.sidebar.multiselect("Selecione o Vendedor", vendedores_com_todos, default=[])
    
    produtos_com_todos = ['Todos'] + produtos
    produtos_selecionados = st.sidebar.multiselect("Selecione os Produtos", produtos_com_todos, default=[])

    # Filtrando os dados
    if 'Todos' in vendedor:
        df_vendas_filtered = df_vendas[(df_vendas["Mês"] == month)]
    else:
        df_vendas_filtered = df_vendas[(df_vendas["Mês"] == month) & (df_vendas["CODUSUR"].isin(vendedor))]
    
    if 'Todos' not in produtos_selecionados:
        df_vendas_filtered = df_vendas_filtered[df_vendas_filtered["DESCRICAO"].isin(produtos_selecionados)]

    # Agrupando os dados por dia para somar o valor total vendido por dia para cada vendedor e produto
    df_vendas_grouped = df_vendas_filtered.groupby(["DTSAIDA", "CODUSUR", "DESCRICAO"])[["SUM(VLVENDA)"]].sum().reset_index()   

    # Título do dashboard
    st.title("Dashboard de Vendas")

    # Resumo
    st.header(f"Resumo do mês: {month}")
    total_vendas = df_vendas_grouped["SUM(VLVENDA)"].sum()
    st.write(f"Total Vendido: {locale.currency(total_vendas, grouping=True)}")
    st.write("Atualização: 27/05/2024 08:00")

    # Layout das colunas
    col1, col2 = st.columns(2)

    # Gráfico de Faturamento por Dia e por Vendedor
    fig_date_vendedor_produto = px.bar(df_vendas_grouped, x="DTSAIDA", y="SUM(VLVENDA)", color="CODUSUR",
                                   title="Faturamento por Dia, Vendedor e Produto",
                                   labels={"SUM(VLVENDA)": "Valor Vendido (R$)", "DTSAIDA": "Data"},
                                   hover_data={"DTSAIDA": "|%d/%m/%Y", "SUM(VLVENDA)": ":,.2f", "CODUSUR": "Vendedor", "DESCRICAO": "Produto"})
    fig_date_vendedor_produto.update_traces(hovertemplate='<b>Data</b>: %{x|%d/%m/%Y}<br><b>Vendedor</b>: %{marker.color}<br><b>Produto</b>: %{customdata[1]}<br><b>Valor Vendido</b>: R$ %{y:,.2f}')
    fig_date_vendedor_produto.update_layout(xaxis_title="Data", yaxis_title="Valor Vendido (R$)")
    col1.plotly_chart(fig_date_vendedor_produto, use_container_width=True)

    # Gráfico de Faturamento por Vendedor
    Vendedor_Total = df_vendas_filtered.groupby(["CODUSUR", "DESCRICAO"])[["SUM(VLVENDA)"]].sum().reset_index()
    fig_vendedor = px.bar(Vendedor_Total, x="CODUSUR", y="SUM(VLVENDA)", color="CODUSUR", title="Faturamento por Vendedor e Produto (Mês)",
                      labels={"SUM(VLVENDA)": "Valor Vendido (R$)", "CODUSUR": "Vendedor"},
                      hover_data={"CODUSUR": True, "SUM(VLVENDA)": ":,.2f", "DESCRICAO": "Produto"})
    fig_vendedor.update_traces(hovertemplate='<b>Vendedor</b>: %{x}<br><b>Produto</b>: %{customdata[1]}<br><b>Valor Vendido</b>: R$ %{y:,.2f}')
    fig_vendedor.update_layout(xaxis_title="Vendedor", yaxis_title="Valor Vendido (R$)", legend_title="Vendedor")
    col2.plotly_chart(fig_vendedor, use_container_width=True)

    # Agrupando os dados por vendedor para somar o valor total vendido por vendedor
    Vendedor_Total = df_vendas_filtered.groupby("CODUSUR")[["SUM(VLVENDA)"]].sum().reset_index()

    # Centralizar o gráfico de Pizza - Faturamento por Vendedor
    fig_kind = px.pie(Vendedor_Total, values="SUM(VLVENDA)", names="CODUSUR", title="Faturamento por Vendedor (Mês)",
                      labels={"SUM(VLVENDA)": "Valor Vendido (R$)", "CODUSUR": "Vendedor"},
                      hover_data={"CODUSUR": True, "SUM(VLVENDA)": ":,.2f"})
    fig_kind.update_traces(hovertemplate='<b>Vendedor</b>: %{label}<br><b>Valor Vendido</b>: R$ %{value:,.2f}')
    fig_kind.update_traces(textinfo='percent+label')
    fig_kind.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        title_x=0.5,  # Centraliza o título do gráfico
        font=dict(
            family="Arial, sans-serif",
            size=16,  # Aumenta o tamanho da fonte
            color="White"  # Define a cor da fonte
        ),
    )

    # Criar uma única coluna para centralizar o gráfico
    col_centered = st.columns(1)
    with col_centered[0]:
        st.plotly_chart(fig_kind, use_container_width=True)

    # Seção de Vendas por Produto
    st.header("Vendas por Produto")

    # Gráfico de Vendas por Produto por Dia
    fig_produto_dia = px.bar(df_vendas_filtered, x="DTSAIDA", y="SUM(VLVENDA)", color="DESCRICAO", title="Vendas por Produto por Dia",
                             labels={"SUM(VLVENDA)": "Valor Vendido (R$)", "DTSAIDA": "Data", "DESCRICAO": "Produto"},
                             hover_data={"DTSAIDA": "|%d/%m/%Y", "SUM(VLVENDA)": ":,.2f", "CODUSUR": "Vendedor"})
    fig_produto_dia.update_traces(hovertemplate='<b>Data</b>: %{x|%d/%m/%Y}<br><b>Produto</b>: %{marker.color}<br><b>Valor Vendido</b>: R$ %{y:,.2f}<br><b>Vendedor</b>: %{customdata[0]}')
    fig_produto_dia.update_layout(xaxis_title="Data", yaxis_title="Valor Vendido (R$)", legend_title="Produto")
    col3, col4 = st.columns(2)
    col3.plotly_chart(fig_produto_dia, use_container_width=True)

    # Gráfico de Vendas por Produto por Mês
    produto_total_mes = df_vendas_filtered.groupby(["Mês", "DESCRICAO"])[["SUM(VLVENDA)"]].sum().reset_index()
    fig_produto_mes = px.bar(produto_total_mes, x="DESCRICAO", y="SUM(VLVENDA)", color="DESCRICAO", title="Vendas por Produto por Mês",
                             labels={"SUM(VLVENDA)": "Valor Vendido (R$)", "DESCRICAO": "Produto"},
                             hover_data={"Mês": True, "SUM(VLVENDA)": ":,.2f"})
    fig_produto_mes.update_traces(hovertemplate='<b>Mês</b>: %{x}<br><b>Valor Vendido</b>: R$ %{y:,.2f}')
    fig_produto_mes.update_layout(xaxis_title="Mês", yaxis_title="Valor Vendido (R$)")
    col4.plotly_chart(fig_produto_mes, use_container_width=True)

    # Gráfico de Pizza - Distribuição das Vendas por Produto
    fig_produto_pizza = px.pie(df_vendas_filtered, values="SUM(VLVENDA)", names="DESCRICAO", title="Distribuição das Vendas por Produto (Mês)",
                               labels={"SUM(VLVENDA)": "Valor Vendido (R$)", "DESCRICAO": "Produto"},
                               hover_data={"DESCRICAO": True, "SUM(VLVENDA)": ":,.2f"})
    fig_produto_pizza.update_traces(hovertemplate='<b>Produto</b>: %{label}<br><b>Valor Vendido</b>: R$ %{value:,.2f}')
    fig_produto_pizza.update_traces(textinfo='percent+label')
    fig_produto_pizza.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        title_x=0.5,  # Centraliza o título do gráfico
        font=dict(
            family="Arial, sans-serif",
            size=16,  # Aumenta o tamanho da fonte
            color="White"  # Define a cor da fonte
        ),
    )

    # Criar uma única coluna para centralizar o gráfico
    col_centered_produto = st.columns(1)
    with col_centered_produto[0]:
        st.plotly_chart(fig_produto_pizza, use_container_width=True)

# Lógica de login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    if st.button("Logout"):
        logout()
    else:
        main_page()

        