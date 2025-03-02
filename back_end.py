import numpy as np
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpInteger, value

def otimizar_portfolio_inteiro_ajustado(lista_acoes, cotacoes_historicas, classificacoes_risco, dividendos_historicos, orcamento_total):
    n = len(lista_acoes)
    
    R_i = []  # Retorno total esperado para cada ação
    A_i = []  # Ajuste de risco para cada ação
    P_i = []  # Preço atual de cada ação

    for acao in lista_acoes:
        # Preços e dividendos
        precos = cotacoes_historicas[acao]
        dividendos = dividendos_historicos[acao]
        
        # Preço atual e preço inicial
        preco_atual = precos[-1]
        preco_inicial = precos[0]
        
        # Valorização percentual
        valorizacao = (preco_atual - preco_inicial) / preco_inicial
        
        # Retorno de dividendos (% em relação ao preço inicial)
        retorno_dividendos = sum(dividendos) / preco_inicial
        
        # Retorno total
        retorno_total = valorizacao + retorno_dividendos
        R_i.append(retorno_total)
        
        # Ajuste pelo risco (normalizando entre 0 e 1)
        risco = classificacoes_risco[acao]
        ajuste_risco = (risco - 1) / 4  # Risco de 1 a 5
        A_i.append(ajuste_risco)
        
        # Preço atual
        P_i.append(preco_atual)
    
    R_i = np.array(R_i)
    A_i = np.array(A_i)
    P_i = np.array(P_i)
    
    # Criando o modelo de otimização
    modelo = LpProblem(name="otimizacao_portfolio", sense=LpMaximize)
    
    # Variáveis de decisão (quantidade inteira de ações a comprar)
    x = {i: LpVariable(name=f"x{i}", lowBound=0, cat="Integer") for i in range(n)}
    
    # Função objetivo: Maximizar o retorno total ajustado pelo risco
    modelo += lpSum([R_i[i] * A_i[i] * x[i] for i in range(n)]), "Retorno_Total_Ajustado"
    
    # Restrição de orçamento total (ajustado)
    modelo += lpSum([P_i[i] * x[i] for i in range(n)]) <= orcamento_total, "Restricao_Orcamento"
    
    # Restrição de não investir mais que 50% do orçamento em uma única ação
    for i in range(n):
        modelo += P_i[i] * x[i] <= 0.5 * orcamento_total, f"Restricao_Max_50porcento_{i}"
    
    # Resolver o problema
    status = modelo.solve()
    
    # Estrutura da Lista para o Dataframe
    list_investimento = []
    list_acoes_a_investir = []
    list_qtd_acoes = []

    # Verificar se uma solução ótima foi encontrada
    if modelo.status == 1:
        investimento_total = 0
        for i in range(n):
            acao = lista_acoes[i]
            quantidade = int(x[i].varValue)
            investimento = quantidade * P_i[i]
            investimento_total += investimento
            list_investimento.append(investimento)
            list_acoes_a_investir.append(acao)
            list_qtd_acoes.append(quantidade)
        df = pd.DataFrame({
            'Ação': list_acoes_a_investir,
            'Valor a ser Investido': list_investimento,
            'Qtd de ações a comprar': list_qtd_acoes
        })
        return investimento_total, df
        