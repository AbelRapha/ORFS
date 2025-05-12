import streamlit as st
import yfinance as yf
from back_end import otimizar_portfolio_inteiro_ajustado
import investpy
import time
from curl_cffi import requests

# Config Session Yfinance  
session = requests.Session(impersonate="chrome")

# Título da Aplicação
st.title('Análise de Ações Brasileiras')

@st.cache_data
def obter_lista_acoes_brasileiras():
    acoes = investpy.stocks.get_stocks(country='brazil')
    lista_acoes = acoes['symbol'].tolist()
    lista_acoes = [symbol + '.SA' for symbol in lista_acoes]
    return lista_acoes


# Carrega a lista de ações
lista_acoes = obter_lista_acoes_brasileiras()

# Coleta o valor do orçamento
orcamento = st.number_input('Digite o valor do orçamento que você possui para investimento')

if lista_acoes:
    # Seleção de Ações
    acoes_selecionadas = st.multiselect(
        'Selecione as ações que deseja analisar:',
        options=lista_acoes
    )

    # Dicionário para armazenar as classificações de risco
    classificacoes_risco = {}

    if acoes_selecionadas:
        for acao in acoes_selecionadas:
            # Entrada para classificação de risco
            risco = st.slider(
                f'Classifique o risco da {acao} (1 = Muito Arriscado, 5 = Pouco Arriscado):',
                min_value=1, max_value=5, value=3
            )
            classificacoes_risco[acao] = risco

        # Período para dados históricos
        periodo = st.selectbox(
            'Selecione o período para os dados históricos:',
            options=['1y', '2y', '5y', 'max']
        )

        data = {}

        # Dicionários para armazenar os dados históricos e dividendos
        cotacoes_historicas = {}
        dividendos_historicos = {}

        # Barra de progresso
        progresso = st.progress(0)
        total_acoes = len(acoes_selecionadas)

        # Obtendo dados para cada ação selecionada
        for indice, acao in enumerate(acoes_selecionadas):
            try:
                ticker = yf.Ticker(acao, session = session)
                historico = ticker.history(period=periodo)
                dividendos = ticker.dividends
                data[acao] = {
                    'historico': historico,
                    'dividendos': dividendos
                }
                cotacoes_historicas[acao] = historico['Close'].tolist()
                dividendos_historicos[acao] = dividendos.tolist()

            except Exception as e:
                st.error(f'Erro ao obter dados para {acao}: {e}')
                continue

            # Atualiza a barra de progresso
            progresso.progress((indice + 1) / total_acoes)

        # Exibindo os dados
        for acao in acoes_selecionadas:
            if acao in data:
                st.subheader(f'Dados da {acao}')
                st.write('**Classificação de Risco:**', classificacoes_risco[acao])

                if not data[acao]['historico'].empty:
                    st.line_chart(data[acao]['historico']['Close'], height=250, use_container_width=True)
                else:
                    st.write('Dados de cotações não disponíveis.')

                if not data[acao]['dividendos'].empty:
                    st.bar_chart(data[acao]['dividendos'], height=250, use_container_width=True)

                else:
                    st.write('Esta ação não distribuiu dividendos no período selecionado.')
            else:
                st.write(f'Dados da {acao} não disponíveis.')

         ## Simulação       
        st.write('Clique aqui para saber qual ação deve comprar com o orçamento disponível')
        botao = st.button('Simular')
        if botao:
            investimento_total, df = otimizar_portfolio_inteiro_ajustado(acoes_selecionadas,cotacoes_historicas,classificacoes_risco,dividendos_historicos,orcamento)
            st.write(f'Valor do investimento total: R$ {investimento_total:.2f}')
            st.write(df.sort_values(by=['Qtd de ações a comprar'], ascending=False))       
    else:
        st.write('Selecione ao menos uma ação para visualizar os dados.')
else:
    st.write('A lista de ações não pôde ser carregada.')
