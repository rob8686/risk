import yfinance as yf
import numpy as np
import math
import pandas as pd
import pymongo
import datetime
import json
import datetime as dt

class Var():

    def __init__(self, fx_converted_df, yf_dict, collection):
        self.collection = collection
        self.fx_converted_df = fx_converted_df
        #self.perc_return_df = self.combined_df.pct_change().dropna().reset_index()
        self.yf_dict = yf_dict
        self.factors = ['SPY','^TNX','BZ=F','^NYICDX','IGLN.L','^VIX']
        self.risk_factor_df = self.get_factors()
        self.fx_converted_df.index = pd.to_datetime(self.fx_converted_df.index)
        self.combined_df = pd.merge(self.fx_converted_df,self.risk_factor_df, left_index=True, right_index=True).pct_change().dropna().reset_index()
        self.weights = self.position_weights()
        self.tickers = self.fx_converted_df.columns

    def get_var(self):
        result = {}
        x_date = self.combined_df[self.factors].to_numpy()
        x = x_date[:,0:].astype(float)
        #print('Linear Model111111111111111111111')
        #print(self.linear_model(x))
        #print('FACTOR222222')
        #print(self.factor_var2())
        result['parametric_var'] = self.parametric_var()
        result['factor_var'] = self.factor_var2()
        result['tickers'] = list(self.tickers) 
        #result['factor_var'] = self.factor_var()
        result['stress_tests'] = self.stress_tests()
        result['hist_series'] = self.hist_series()
        return result

    def position_weights(self):
        weights = []
        for col in self.fx_converted_df.columns:
            weight = self.yf_dict[col][1]
            weights.append(weight)
        weights_array = np.asarray(weights)
        return weights_array
    
    def hist_series(self):
        return_df = self.combined_df.drop(self.factors, axis=1)
        weighted_return_df = self.weights * return_df.loc[:, return_df.columns != 'Date']
        weighted_return_df['return'] = weighted_return_df.sum(axis=1)
        hist, bin_edges = np.histogram( list(weighted_return_df['return']),bins=20)

        def create_dict(frequency, result):
            return {'frequency': frequency,'return':result}

        combined = list(map(create_dict, hist.tolist(), bin_edges.tolist()))
        return list(combined)
    
    def parametric_var(self):
        returns = self.combined_df.drop(self.factors, axis=1).drop('Date',axis=1).to_numpy()
        weights = self.position_weights()
        cov = np.cov(returns.T.astype(float))
        corr = np.around(np.corrcoef(returns.T.astype(float)),2)
        #myList = list(np.around(np.array(myList),2))
        print(len(returns[0]))
        print(returns.ndim)
        print()
        if len(returns[0]) != 1:
            std_dev = math.sqrt(weights @ cov @ weights.T)
        else:
            std_dev = .2
        #print('STD DEV',std_dev * math.sqrt(260))
        var_1_day = std_dev * 2.33
        #print('var_1_day',var_1_day)
        #print(corr)
        #print()
        return {'var_1_day': var_1_day,'correlation':corr.tolist()}
    
    def linear_model(self, x):

        x_date = self.combined_df[self.factors].to_numpy()
        x = x_date[:,0:].astype(float)
        
        y_df = self.combined_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']
        #print('Linear Model!!!!!!!!!!')
        result={}
        result_array = np.array([])
        column_length = len(y_df.columns)
        factor_num = len(self.factors) 
        result_array = np.zeros(shape=(column_length, factor_num))

        for idx, ticker in enumerate(y_df.columns):
            #print('Index',idx)
            #print()
            y = y_df[ticker].to_numpy()
            b = np.linalg.inv(x.T @ x) @ x.T @ y
            #print(ticker)
            #print(b)
            #print('XCXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            #print(x)
            result[ticker] = b
            result_array[idx] = b
            #print()

        return result_array
    
    def factor_var2(self):
        
        ci_99 = int(round(self.combined_df.iloc[:, 0].count() *.01,0))
        x_date = self.combined_df[self.factors].to_numpy()
        #print(self.combined_df.dtypes)
        dates = list(self.combined_df['Date'].dt.strftime('%Y-%m-%d'))
        x = x_date[:,0:].astype(float)
        b = self.linear_model(x)

        y_df = self.combined_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']
        y = self.combined_df[self.factors].to_numpy()
        result = y @ b.T

        sorted_result = np.sort(result, axis=0)
        individual_var = sorted_result[ci_99] #if this sorting individually?

        combined_result = np.zeros((np.shape(result)[0],np.shape(result)[1]+1))
        hist_series = result.sum(axis=1)
        combined_result[:,-1] = hist_series
        combined_result[:,0:-1] = result
        sorted_combined_result = combined_result[combined_result[:, 1].argsort()]

        sorted_hist_series = np.sort(hist_series)
        var_1d = sorted_combined_result[ci_99]

        chart_list = []
        for idx, pl in enumerate(hist_series.tolist()):
            row_dict = {}
            row_dict['name'] = dates[idx]
            row_dict['PL'] = pl
            chart_list.append(row_dict)
             
        return {'var_1d':var_1d.tolist(), 'individual_var':individual_var.tolist(),'var_history':hist_series.tolist(), 'dates': dates,'chart_list':chart_list}
    
    def stress_tests(self):

        stresses = np.array([
          [.1, 0, 0, 0, 0, 0],
          [.05, 0, 0, 0, 0, 0],
          [-.1, 0, 0, 0, 0, 0],
          [-.05, 0, 0, 0, 0, 0],
          [0,.1, 0, 0, 0, 0],
          [0, -.1, 0, 0, 0, 0],
          [0, 0, 0, .1, 0, 0],  
          [0, 0, 0, -.1, 0, 0],
         ])
        
        #print('Stress Tests')
        #print(stresses)

        b = self.linear_model(1)

        #print(b)
        result = stresses @ b.T
        stress_result = result.sum(axis=1).tolist()
        stress_names = ['Equity up 10%', 'Equity up 5%', 'Equity down 10%', 'Equity down 5%', 
                        'Interest Rates up 10%','Interest Rates down 10%', 'Dollar up 10%','Dollar down 10%']
        

        def create_dict(stress_names, stress_result):
            return {'stress': stress_names,'result':stress_result}

        combined_stress = list(map(create_dict, stress_names, stress_result))
        
        #combined_stress = dict(zip(stress_names, stress_result))

        #print(result)
        #print(stress_result)
        #print(combined_stress)
        print()
        return {'stress_tests':combined_stress}
        

    
    def factor_var(self):
        
        #perc_return_df = self.combined_df#.pct_change().dropna()#.reset_index()#self.perc_return(self.combined_df)
        ci_99 = int(round(self.combined_df.iloc[:, 0].count() *.01,0))
        data = {}
        individual_var = {}

        x_date = self.combined_df[self.factors].to_numpy()
        x = x_date[:,0:].astype(float)

        y_df = self.combined_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']

        for ticker in y_df.columns:
            y = y_df[ticker].to_numpy()
            b = np.linalg.inv(x.T @ x) @ x.T @ y
            #print(ticker)
            #print(b)
            result_list = []
            for row in x_date:
                #print(row)
                result = row * b
                #print(row)
                #print('RESULTTTTTTTTTTT')
                #print(result)
                result_list.append(result.item(0))
            data[ticker] = result_list
            var = sorted(result_list)[ci_99-1] 
            individual_var[ticker] = var
            print()

        date_list = [date for date in self.combined_df['Date']]
        data['Date'] = date_list
        result_df = pd.DataFrame.from_dict(data)
        result_df['fund_return'] = result_df.sum(axis=1)
        result_df = result_df.sort_values(by=['fund_return'])
        var_1d = abs(result_df.iloc[ci_99]['fund_return'])
        var_20d = var_1d * math.sqrt(20)
        pl_history = result_df[['Date','fund_return']].to_json(orient="columns")
        return {'var_1d':var_1d, 'individual_var':individual_var,'var_history':pl_history}

    def get_factors(self):
        max_factor_date  = datetime.datetime.fromtimestamp(max(self.collection.find_one({'_id':999999})['factor_data']['index']) / 1e3 ).date()
        max_fund_date = datetime.datetime.strptime(max(self.fx_converted_df.index),'%Y-%m-%d').date()

        if max_factor_date >= max_fund_date:
            print('DATA CHECK PASSED!!!')
            factor_data = self.collection.find_one({'_id':999999})['factor_data']
            data = pd.read_json(json.dumps(factor_data), orient='split')
        else:
            print('DATA CHECK FAILED!!!')
            ticker_string = ''
            for ticker in self.factors:
                ticker_string = ticker_string + ticker +' '
        
            data = yf.download(tickers=ticker_string, period="1y",
                interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)
            data = data['Close'].fillna(method="ffill").dropna()
            factor_json = json.loads(data.to_json(orient='split'))
            self.collection.replace_one({'_id':999999},{'factor_data':factor_json},upsert=True)

        data.index.rename('Date',inplace=True)
        return data
    
        
#def var(weights, data):
def var(fx_converted_df, yf_dict):
    np.array([[.1, 0,0,0,0], [3, 4]])

#weighted_return_df = pd.DataFrame()
#self.positions[self.benchmark] = [1, 1]

#for ticker in self.positions:
    #percent_aum = self.positions[ticker][1]
    #weighted_return_df[ticker] = self.percent_return_df[ticker] * percent_aum 

