import yfinance as yf
import numpy as np
import math
import pandas as pd

class Var():
    def __init__(self, fx_converted_df, yf_dict):
        self.fx_converted_df = fx_converted_df

        self.fx_converted_np = self.fx_converted_df[:-1].dropna().to_numpy()
        self.yf_dict = yf_dict
        self.factors = ['SPY','^TNX','BZ=F','^NYICDX','IGLN.L','^VIX']
        risk_factor_df = self.get_factors()
        print('MERGE!!!!!!!!!!!!')
        self.fx_converted_df.index = pd.to_datetime(self.fx_converted_df.index)
        print(self.fx_converted_df.columns)
        print(fx_converted_df.index.dtype)
        print(fx_converted_df.index)
        print(self.fx_converted_df.head())
        
        print(risk_factor_df.head())
        print(risk_factor_df.columns)
        print(risk_factor_df.index.dtype)
        print(risk_factor_df.index)
        combined_df = pd.merge(self.fx_converted_df,risk_factor_df, left_index=True, right_index=True)
        print(combined_df)
        print(combined_df.head())
        #print(risk_factor_df.index[0] == fx_converted_df.index[0])
        print()



        self.percent_return_df = self.fx_converted_df.dropna().pct_change()
        self.np_percent_return = self.percent_return_df.to_numpy()
        #self.percent_return_df.to_csv("Std_test.csv")

        self.weights = self.position_weights()
        self.weighted_return = np.dot(self.perc_return(self.fx_converted_df), self.position_weights())
        print('HELLOOOOOOO!!!!!!!!!!!!!')
        print(self.weighted_return)
        print(self.parametric_var())
        print('PANDAS STD')
        print(np.nanstd(self.percent_return_df)*math.sqrt(260))
        print(self.percent_return_df)

        self.factors = ['SPY','^TNX','BZ=F','^NYICDX','IGLN.L','^VIX']

    def position_weights(self):
        weights = []
        for col in self.fx_converted_df.columns:
            weight = self.yf_dict[col][1]
            weights.append(weight)
        weights_array = np.asarray(weights)
        return weights_array

    def perc_return(self,df):
        #returns = np.diff(self.fx_converted_df,axis=0)
        returns = np.diff(df,axis=0)
        fx_converted_np = df[:-1].dropna().to_numpy()
        #perc_returns = returns / self.fx_converted_np
        perc_returns = returns / fx_converted_np
        return perc_returns

    def parametric_var(self):
        df = self.fx_converted_df
        weights = self.position_weights()
        cov = np.cov(self.perc_return(df).T.astype(float))
        corr = np.corrcoef(self.perc_return(df).T.astype(float))
        print()
        print('Correaltion')
        print(corr)
        print('Covar')
        print(cov)
        std_dev = math.sqrt(np.dot(np.dot(weights,cov),weights.T))
        var_1_day = std_dev * 2.33
        print('port std dev2',math.sqrt(np.dot(np.dot(weights,cov),weights.T))*math.sqrt(260))
        print('var_1_day')
        print(var_1_day)
        return var_1_day
    
    def factor_var(self):
        pass

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

