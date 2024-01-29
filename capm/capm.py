
# Modelo de Precificação de Ativos - CAPM

## Introdução

O Modelo de Precificação de Ativos, conhecido como CAPM (do inglês, Capital Asset Pricing Model), é uma das teorias mais fundamentais no campo da finança, essencial para a avaliação e precificação de ativos financeiros. 

## Referências

Notas de aula e https://analisemacro.com.br/

## Pressupostos

Premissas fundamentais:

### 1. Mercados Eficientes
O CAPM parte do pressuposto de que os mercados financeiros são eficientes, o que significa que todas as informações relevantes estão prontamente disponíveis e refletidas nos preços dos ativos. Portanto, os investidores não podem obter lucros anormais explorando informações privilegiadas.

### 2. Investidores Racionais
O modelo presume que todos os investidores são racionais e tomam decisões de investimento com base na maximização de seus retornos esperados e minimização de seus riscos.

### 3. Ativos Negociáveis
O CAPM se aplica apenas a ativos financeiros negociáveis, como ações e títulos, em vez de ativos reais, como imóveis ou arte.

### 4. Impostos e Taxas

Não há impostos, taxas ou quaisquer outras restrições para os investimentos no mercado;

## CAPM

O Modelo de Precificação de Ativos (CAPM) estabelece a relação entre o retorno esperado de um ativo financeiro e seu risco sistêmico, medido pelo famoso coeficiente beta (β). O CAPM é formulado pela seguinte equação:

$$ E(R_i) = R_f + \beta_i (E(R_m) - R_f) $$

- $E(R_i)$: Retorno esperado do ativo.
- $R_f$: Taxa livre de risco (geralmente baseada em títulos do governo).
- $\beta_i$: Coeficiente beta do ativo, que mede seu risco sistemático em relação ao mercado.
- $E(R_m)$: Retorno esperado do mercado.
- $E(R_m) - R_f$: Prêmio de risco de mercado.

## Beta

- Um ativo com $ \beta = 1 $ é considerado tão volátil quanto o mercado. Isso significa que, em média, ele se move na mesma direção e na mesma proporção que o mercado.

- Um ativo com $ \beta > 1 $ é considerado mais volátil que o mercado. Isso significa que, em média, ele tende a ter movimentos maiores do que o mercado.

- Um ativo com $ \beta < 1 $ é considerado menos volátil que o mercado. Isso significa que, em média, ele tende a ter movimentos menores do que o mercado.

- Um ativo com $ \beta = 0 $ é considerado não relacionado ao mercado. Isso significa que seus retornos são independentes dos movimentos do mercado.

Podemos estimar o Beta a partir da seguinte fórmula:

$$ \beta = \frac{{\text{Covariância}(R_i, R_m)}}{{\text{Variância}(R_m)}} $$

Assim, podemos obter a estimativa pela forma manual, calculando a covariância e a variância, ou usando funções para o cálculo do MQO.

# Criando o CAPM no Python

# Usando CDI
"""

!pip install python-bcb

from bcb import sgs
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.regression.rolling import RollingOLS

## Gráficos
from plotnine import *
from mizani.breaks import date_breaks
from mizani.formatters import date_format
import plotly.express as px
import plotly.graph_objs as go

start = '2014-01-01' # início
end = '2023-10-01' # fim

# CDI acumulada no mês (%a.m)
cdi_m = sgs.get({'cdi' : 4391}, start = start)

cdi_m

"""# Retorno do Ibovespa"""

# Preços Históricos
precos = yf.download('^BVSP', start = start, end = end, interval = '1mo')

# Calcula Retornos Mensais
returns = (
          precos[['Adj Close']]
          .pct_change()
          .rename(columns = {'Adj Close' : 'retornos_ibov'})
          .dropna()
          )

returns

# Junta os data frames
returns_rf =  (
    returns.merge(cdi_m, left_index = True, right_index = True)
    .assign(cdi = lambda x: x.cdi / 100)
    )

returns_rf

"""# Ativo"""

# Tickers dos ativos
assets = ['BBDC4.SA', 'ITSA4.SA', 'VALE3.SA', 'WEGE3.SA']

# Baixa os dados (dados mensais)
precos_ativos = yf.download(assets, start = start, end = end, interval = '1mo')
precos_ativos = precos_ativos.loc[:,('Adj Close', slice(None))]
precos_ativos.columns = assets

# Calculando os retornos
Y = precos_ativos[assets].pct_change().dropna()

# Verifica os retornos
Y.head()

# Número de ativos
num_ativos = len(Y.columns)

# Calcula pesos iguais
peso_por_ativo = 1.0 / num_ativos
ewp = [peso_por_ativo] * num_ativos

# Pesos
ewp

# Calcula o retorno do portfólio
portfolio_returns_ewp = pd.DataFrame((Y * ewp).sum(axis = 1), columns = ['portfolio_ewp'])
portfolio_returns_ewp

# Junta os dados
portfolio = (
            portfolio_returns_ewp
            .merge(returns_rf, left_index = True, right_index = True)
            )

portfolio.head()

"""# Excesso de Retorno"""

portfolio['excesso_retorno'] = portfolio['portfolio_ewp'] - portfolio['cdi']
portfolio['excesso_ibovespa'] = portfolio['retornos_ibov'] - portfolio['cdi']

portfolio.head()

"""# Regressão Linear"""

model_fit = (smf.ols(
    formula = "excesso_retorno ~ excesso_ibovespa",
    data = portfolio)
  .fit()
)

model_fit_coefs = model_fit.summary(slim = True).tables[1]
print(model_fit_coefs)

"""# Gráfico de Dispersão"""

px.scatter(data_frame = portfolio,
                      x = 'excesso_ibovespa',
                      y = 'excesso_retorno',
                      labels = {
                            "x" : "",
                            "value" : ""
                         },
                      trendline = 'ols'
                 )

"""# Beta Móvel"""

def roll_capm_estimation(data, window_size, min_obs):

    result = (RollingOLS.from_formula(
      formula = "excesso_retorno ~ excesso_ibovespa",
      data = data,
      window = window_size,
      min_nobs = min_obs
      )
      .fit()
      .params["excesso_ibovespa"]
    )

    result.index = data.index
    result = pd.DataFrame(result).rename({'excesso_ibovespa' : 'beta'}, axis = 1)
    return result

beta = roll_capm_estimation(data = portfolio, window_size = 60, min_obs = 48)

beta.reset_index(inplace = True)
beta.dropna(inplace = True)

beta

plot_beta = (
  ggplot(beta,
         aes(x = "Date", y = "beta")) +
  geom_line() +
  scale_x_datetime(breaks = date_breaks("1 year"),
                   labels = date_format("%Y")) +
  labs(x = "",
       y = "",
       title = ("Beta Mensal estimado do Portfólio EWP de exemplo"))
  )


plot_beta.draw()
