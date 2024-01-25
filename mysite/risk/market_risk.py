import yfinance as yf
import numpy as np
import math
import pandas as pd
import pymongo
import datetime
import json
import datetime as dt

class Var():
    """
    Class calcualates market risk statistics.
    ...

    Methods:
    - _init__: Constructor for a market risk object.
    - get_var: Method runs markit risk calculations calculations.
    - position_weights: Get a np array containing the percent of AUM of each posiitons. 
    - histogram: Create the histogram data and create HistogramBins objects.
    - parametric_var: 
    """
    

    def __init__(self, fx_converted_df, position_info, fund, HistVarSeries, MarketRiskStatistics,HistogramBins, MarketRiskCorrelation, FactorData):
        """
        Constructor for a VaR object.

        Parameters
        ----------
            yf_data (pandas.DataFrame): Historical data containing the closing price for each position.  
            position_info (dict): Dict containing info (quantity, percent of AUM, etc.) for each position with percent of AUM at index 1. 
            fund (Fund): A fund object.
            HistVarSeries (HistVarSeries): LiquditiyResult class.
            MarketRiskStatistics (MarketRiskStatistics): MarketRiskStatistics class.
            HistogramBins (HistogramBins): HistogramBins class.
            MarketRiskCorrelation (MarketRiskCorrelation): MarketRiskCorrelation class. 
            FactorData (FactorData): MarketRiskCorrelation class. 

        """
        self.fund = fund
        self.HistVarSeries = HistVarSeries
        self.MarketRiskStatistics = MarketRiskStatistics
        self.HistogramBins = HistogramBins
        self.MarketRiskCorrelation = MarketRiskCorrelation
        self.FactorData = FactorData
        self.fx_converted_df = fx_converted_df
        self.position_info = position_info
        self.factors = ['spy','tnx','bz','nyicdx','igln','vix']
        self.risk_factor_df = self.get_factors()
        self.fx_converted_df.index = pd.to_datetime(self.fx_converted_df.index)
        self.combined_df = pd.merge(self.fx_converted_df,self.risk_factor_df, left_index=True, right_index=True).pct_change().dropna().reset_index()
        self.weights = self.position_weights()
        self.linear_model = self.calc_linear_model()
        self.tickers = self.fx_converted_df.columns


    def get_var(self):
        """
        Method runs market risk calculations calculations.

        """
        result = {}
        x_date = self.combined_df[self.factors].to_numpy()
        x = x_date[:,0:].astype(float)
        self.MarketRiskStatistics.objects.filter().delete()
        self.HistogramBins.objects.all().delete()
        self.parametric_var()
        result['factor_var'] = self.factor_var2()
        result['tickers'] = list(self.tickers) 
        #result['factor_var'] = self.factor_var()
        result['stress_tests'] = self.stress_tests()
        self.histogram()
        return result


    def position_weights(self):
        """
        Method runs markit risk calculations calculations.
        YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY

        """

        return np.asarray([self.position_info[col][1] for col in self.fx_converted_df.columns])
    
    
    def histogram(self):
        """
        Create the histogram data and create HistogramBins object.

        """

        return_df = self.combined_df.drop(self.factors, axis=1)

        # multiply the posiiton weights by the positions returns 
        weighted_return_df = self.weights * return_df.loc[:, return_df.columns != 'Date']

        # sum the weighted returns to get the portfolio return 
        weighted_return_df['return'] = weighted_return_df.sum(axis=1)

        # Calculate the histogram binds and frequncies and create HistogramBins object
        hist, bin_edges = np.histogram( list(weighted_return_df['return']),bins=20)

        def create_dict(frequency, result):
            return {'as_of_date':'2023-12-08', 'count': frequency,'bin':result, 'fund':self.fund}

        combined = list(map(create_dict, hist.tolist(), bin_edges.tolist()))
        histogram_objs = [self.HistogramBins(**data) for data in combined]
        self.HistogramBins.objects.bulk_create(histogram_objs)
        return list(combined)


    def parametric_var(self):
        """
        Create the Parametric VaR data (VaR and correlation matrix) and create MarketRiskStatistics and MarketRiskCorrelation objects.

        """

        returns = self.fx_converted_df.pct_change().dropna().to_numpy()
        weights = self.position_weights()
 
        correl_list =[]
        self.MarketRiskCorrelation.objects.all().delete()  

        # if more than one position create the correlation matrix and use the covarience matrix to calcualte VaR
        if len(self.tickers) > 1:
            corr = np.around(np.corrcoef(returns.T.astype(float)),2)
            cov = np.cov(returns.T.astype(float))
            std_dev = math.sqrt(weights @ cov @ weights.T)

            # prepare data to create MarketRiskCorrelation objects 
            for index, ticker in enumerate(self.tickers):
                for correl_index, correl_ticker in enumerate(self.tickers):
                    correl_list.append({'as_of_date':'2023-12-08','ticker': ticker,'to': correl_ticker, 'value': corr.tolist()[index][correl_index],'fund':self.fund})
            
        else:
            std_dev = np.std(returns) * weights[0]
            correl_list.append({'as_of_date':'2023-12-08','ticker': self.tickers[0],'to': self.tickers[0], 'value': 1,'fund':self.fund})

        var_1_day = std_dev * 2.33

        self.MarketRiskStatistics.objects.create(as_of_date='2023-12-08', catagory='var_result' ,type='parametric_var',value=var_1_day, fund=self.fund )
        market_risk_correl_objs = [self.MarketRiskCorrelation(**data) for data in correl_list]
        self.MarketRiskCorrelation.objects.bulk_create(market_risk_correl_objs)

    
    def calc_linear_model(self):
        """
        Calcualted the coefficents of the linear model 

        Returns:
        list[(str,str)]: list of tuples containing the ticker and currency of a position.

        """
        # indepentend variables -historical factor data
        x = self.combined_df[self.factors].to_numpy()

        # dependent variables -historical position data
        y_df = self.combined_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']

        
        column_length = len(y_df.columns)
        factor_num = len(self.factors) 
        result_array = np.zeros(shape=(column_length, factor_num))

        for idx, ticker in enumerate(y_df.columns):
            y = y_df[ticker].to_numpy()
            b = np.linalg.inv(x.T @ x) @ x.T @ y
            result_array[idx] = b
        
        print('Result Array')
        print(result_array)

        return result_array
    
    def factor_var2(self):
        
        ci_99 = int(round(self.combined_df.iloc[:, 0].count() *.01,0))
        x_date = self.combined_df[self.factors].to_numpy()
        dates = list(self.combined_df['Date'].dt.strftime('%Y-%m-%d'))
        x = x_date[:,0:].astype(float)
        b = self.linear_model

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
        sorted_combined_result = combined_result[combined_result[:, -1].argsort()]
        print('INDIVIDUAL VAR')
        individual_var = np.sort(combined_result,axis=0)[ci_99]

        sorted_hist_series = np.sort(hist_series)
        var_1d = sorted_combined_result[ci_99]

        chart_list = []
        for idx, pl in enumerate(hist_series.tolist()):
            row_dict = {}
            row_dict['name'] = dates[idx]
            row_dict['PL'] = pl
            chart_list.append(row_dict)

        chart_list_NEW = []
        for idx, pl in enumerate(hist_series.tolist()):
            row_dict = {}
            row_dict['date'] = dates[idx]
            row_dict['as_of_date'] = '2023-12-08'
            row_dict['pl'] = pl
            row_dict['fund'] = self.fund
            chart_list_NEW.append(row_dict)
 
        self.HistVarSeries.objects.all().delete()
        hist_var_series_objs = [self.HistVarSeries(**data) for data in chart_list_NEW]
        self.HistVarSeries.objects.bulk_create(hist_var_series_objs)
        self.MarketRiskStatistics.objects.create(as_of_date='2023-12-08', catagory='var_result' ,type='hist_var_result',value=individual_var[-1], fund=self.fund )
        
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
        
        b = self.linear_model

        result = stresses @ b.T
        stress_result = result.sum(axis=1).tolist()
        stress_names = ['Equity up 10%', 'Equity up 5%', 'Equity down 10%', 'Equity down 5%', 
                        'Interest Rates up 10%','Interest Rates down 10%', 'Dollar up 10%','Dollar down 10%']
        

        def create_dict(stress_names, stress_result):
            return {'stress': stress_names,'result':stress_result}

        def create_dict_NEW(stress_names, stress_result):
            return {'as_of_date':'2023-12-08','catagory':'stress_test','type': stress_names,'value':stress_result,'fund':self.fund}

        combined_stress = list(map(create_dict, stress_names, stress_result))

        combined_stress_new = list(map(create_dict_NEW, stress_names, stress_result))
        market_risk_stat_objs = [self.MarketRiskStatistics(**data) for data in combined_stress_new]
        self.MarketRiskStatistics.objects.bulk_create(market_risk_stat_objs)

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
            result_list = []
            for row in x_date:
                result = row * b
                result_list.append(result.item(0))
            data[ticker] = result_list
            var = sorted(result_list)[ci_99-1] 
            individual_var[ticker] = var

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
        """
        Get the factor timeseries from Yahoo Finance and save and return it

        Returns:
        pandas.DataFrame: df containing factor data 

        """

        factor_data = self.FactorData.objects.filter(as_of_date='2024-01-23')

        # if factor data for the as of date is already in the DB use that otherwise get data from yfinance 
        if factor_data.count() > 0:
            factor_data_df = pd.DataFrame(factor_data.values('date','spy','tnx','bz','nyicdx','igln','vix'))
        else:
            ticker_string = ''.join([ticker +' ' for ticker in ['SPY','^TNX','BZ=F','^NYICDX','IGLN.L','^VIX']])

            data = yf.download(tickers=ticker_string, period="1y",
                interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)

            data = data['Close'].fillna(method="ffill").dropna().reset_index()
            data['as_of_date'] = '2024-01-23'
            data.columns = [col.lower() for col in data.columns]
            data = data.rename(columns={"bz=f": "bz", "igln.l": "igln","^nyicdx": "nyicdx","^tnx": "tnx","^vix": "vix"}).to_dict('records')
            #DELTE THEIS DELTE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.FactorData.objects.all().delete()

            # Create and retrieve factor data objects
            factor_data_objs = [self.FactorData(**obj) for obj in data]
            self.FactorData.objects.bulk_create(factor_data_objs)
            factor_data = self.FactorData.objects.filter(as_of_date='2024-01-23')
            factor_data_df = pd.DataFrame(factor_data.values('date','spy','tnx','bz','nyicdx','igln','vix'))

        factor_data_df = factor_data_df.set_index('date')
        factor_data_df.index.rename('Date',inplace=True)

        return factor_data_df
    
    
        

