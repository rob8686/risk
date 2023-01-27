import yfinance as yf
from datetime import datetime

ticker_string = 'UBI.PA'
ticker_string = 'TSLA UBI.PA HSBA.L'
today = datetime.today().strftime('%Y-%m-%d')
today = '2023-01-02'

data = yf.download(tickers=ticker_string, period="1y",
    interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)

print(today)
print(data)
print(data.fillna(method="ffill"))    
print(data[data.index < today]['Close'])
print(data[data.index < today]['Close'].fillna(method="ffill").dropna())
