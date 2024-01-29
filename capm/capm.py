

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
