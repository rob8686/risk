import requests
import yfinance as yf
import json
import pandas as pd



fund_id = 1

#funds = Fund.objects.filter(id=fund_id)

#print(funds)

apikey='2M3IEELDCP3HPW2F'

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&outputsize=full&apikey={apikey}'
r = requests.get(url)
data = r.json()
#print('TYPEEEEEEEEEE')
#print(type(data))
#json1_data = json.loads(data)[0]

#print(data.keys())#['2003-10-17'])
#print(data['Meta Data'])
#print(data['Time Series FX (Daily)'])
print(data['Time Series FX (Daily)'])
print(data['Time Series FX (Daily)']['2022-07-18'])
print(type(data['Time Series FX (Daily)']))
#df = pd.read_json(data['Time Series FX (Daily)'])
#df =  pd.DataFrame.from_dict(data['Time Series FX (Daily)'])
df =  pd.DataFrame.from_dict(data['Time Series FX (Daily)']).T['4. close']
#closing = df.T['4. close']
#print(type(closing)) 
#print(closing)
print(df)



