import yfinance as yf
import numpy as np
import math
import pandas as pd

class Var():

    def __init__(self, fx_converted_df, yf_dict):
        self.fx_converted_df = fx_converted_df
        #self.perc_return_df = self.combined_df.pct_change().dropna().reset_index()
        self.yf_dict = yf_dict
        self.factors = ['SPY','^TNX','BZ=F','^NYICDX','IGLN.L','^VIX']
        risk_factor_df = self.get_factors()
        self.fx_converted_df.index = pd.to_datetime(self.fx_converted_df.index)
        self.combined_df = pd.merge(self.fx_converted_df,risk_factor_df, left_index=True, right_index=True).pct_change().dropna().reset_index()
        self.weights = self.position_weights()

    def get_var(self):
        result = {}
        result['parametric_var'] = self.parametric_var()
        result['factor_var'] = self.factor_var()
        return result


    def position_weights(self):
        weights = []
        for col in self.fx_converted_df.columns:
            weight = self.yf_dict[col][1]
            weights.append(weight)
        weights_array = np.asarray(weights)
        return weights_array
    
    def parametric_var(self):
        print(self.combined_df)
        returns = self.combined_df.drop(self.factors, axis=1).drop('Date',axis=1).to_numpy()
        weights = self.position_weights()
        cov = np.cov(returns.T.astype(float))
        corr = np.corrcoef(returns.T.astype(float))
        std_dev = math.sqrt(weights @ cov @ weights.T)
        print('STD DEV',std_dev * math.sqrt(260))
        var_1_day = std_dev * 2.33
        print('var_1_day',var_1_day)
        print(corr)
        print()
        return {'var_1_day': var_1_day,'correlation':corr}
    
    def factor_var(self):
        
        perc_return_df = self.combined_df#.pct_change().dropna()#.reset_index()#self.perc_return(self.combined_df)
        ci_99 = int(round(perc_return_df.iloc[:, 0].count() *.01,0))
        data = {}
        individual_var = {}

        x_date = perc_return_df[self.factors].to_numpy()
        x = x_date[:,0:].astype(float)

        y_df = perc_return_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']

        for ticker in y_df.columns:
            y = y_df[ticker].to_numpy()
            b = np.linalg.inv(x.T @ x) @ x.T @ y
            print(ticker)
            print(b)
            result_list = []
            for row in x_date:
                #print(row)
                result = row * b
                result_list.append(result.item(0))
            data[ticker] = result_list
            var = sorted(result_list)[ci_99-1] 
            individual_var[ticker] = var
            print()

        date_list = [date for date in perc_return_df['Date']]
        data['Date'] = date_list
        result_df = pd.DataFrame.from_dict(data)
        result_df['fund_return'] = result_df.sum(axis=1)
        result_df = result_df.sort_values(by=['fund_return'])
        var_1d = abs(result_df.iloc[ci_99]['fund_return'])
        var_20d = var_1d * math.sqrt(20)
        pl_history = result_df[['Date','fund_return']].to_json(orient="columns")
        return {'var_1d':var_1d, 'individual_var':individual_var,'var_history':pl_history}

    def get_factors(self):
        ticker_string = ''
        for ticker in self.factors:
            ticker_string = ticker_string + ticker +' '
        
        data = yf.download(tickers=ticker_string, period="1y",
            interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)

        data = data['Close'].fillna(method="ffill").dropna()

        return data 
        
#def var(weights, data):
def var(fx_converted_df, yf_dict):
    print('Market Risk!')
    print(fx_converted_df)
    print(yf_dict)

#weighted_return_df = pd.DataFrame()
#self.positions[self.benchmark] = [1, 1]

#for ticker in self.positions:
    #percent_aum = self.positions[ticker][1]
    #weighted_return_df[ticker] = self.percent_return_df[ticker] * percent_aum 

