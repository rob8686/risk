import yfinance as yf
import numpy as np
import math
import pandas as pd


class Var():
    """
    Class calcualates market risk statistics.
    ...

    Methods:
    - _init__: Constructor for a market risk object.
    - get_var: Method runs markit risk calculations calculations.
    - histogram: Create the histogram data and create HistogramBins objects.
    - parametric_var: Create the Parametric VaR data (VaR and correlation matrix) and create MarketRiskStatistics and MarketRiskCorrelation objects.
    - calc_linear_model: Calcualte the coefficents of the linear model.
    - factor_var: Calcualte the historical factor VaR and P&L timeseries.
    - stress_tests: Calcualte the stress testing results.
    - get_factors: Get the factor timeseries from Yahoo Finance and save and return it.
    """
    

    def __init__(self, fx_converted_df, position_info, fund, as_of_date, factor_data):
        """
        Constructor for a VaR object.

        Parameters
        ----------
            yf_data (pandas.DataFrame): Historical data containing the closing price for each position.  
            position_info (dict): Dict containing info (quantity, percent of AUM, etc.) for each position with percent of AUM at index 1. 
            fund (Fund): A fund object.
            as_of_date (str): the date the risk results will be generated for.
            factor_data (pandas.DataFrame); historical factor data.

        """
        self.fund = fund
        self.as_of_date = as_of_date
        self.risk_factor_df = factor_data
        self.fx_converted_df = fx_converted_df
        self.position_info = position_info
        self.factors = ['spy','tnx','bz','nyicdx','igln','vix']
        self.fx_converted_df.index = pd.to_datetime(self.fx_converted_df.index)
        self.combined_df = pd.merge(self.fx_converted_df,self.risk_factor_df, left_index=True, right_index=True).pct_change().dropna().reset_index()
        self.weights =  np.asarray([self.position_info[col][1] for col in self.fx_converted_df.columns])
        self.linear_model = self.calc_linear_model()
        self.tickers = self.fx_converted_df.columns


    def get_var(self):
        """
        Method runs market risk calculations calculations.

        """

        parametric_var_data = self.parametric_var()
        factor_data = self.factor_var()
        stress_test_data = self.stress_tests()
        historgram_data = self.histogram()

        return [historgram_data, parametric_var_data,factor_data, stress_test_data]

    
    def histogram(self):
        """
        Create the histogram data and create HistogramBins object.

        Returns:
        list: dicts containing data to create histogram objects

        """

        return_df = self.combined_df.drop(self.factors, axis=1)

        # multiply the posiiton weights by the positions returns 
        weighted_return_df = self.weights * return_df.loc[:, return_df.columns != 'Date']

        # sum the weighted returns to get the portfolio return 
        weighted_return_df['return'] = weighted_return_df.sum(axis=1)

        # Calculate the histogram binds and frequncies and create HistogramBins object
        hist, bin_edges = np.histogram( list(weighted_return_df['return']),bins=20)

        def create_dict(frequency, result):
            return {'as_of_date':self.as_of_date, 'count': frequency,'bin':result, 'fund':self.fund}

        combined = list(map(create_dict, hist.tolist(), bin_edges.tolist()))

        return combined


    def parametric_var(self):
        """
        Create the Parametric VaR data (VaR and correlation matrix) and create MarketRiskStatistics and MarketRiskCorrelation objects.

        Returns:
        list: [1 day VaR result, dicts containing data to create correlation objects]

        """

        returns = self.fx_converted_df.pct_change().dropna().to_numpy()
        weights = self.weights
 
        correl_list =[]

        # if more than one position create the correlation matrix and use the covarience matrix to calcualte VaR
        if len(self.tickers) > 1:
            corr = np.around(np.corrcoef(returns.T.astype(float)),2)
            cov = np.cov(returns.T.astype(float))
            std_dev = math.sqrt(weights @ cov @ weights.T)

            # prepare data to create MarketRiskCorrelation objects 
            for index, ticker in enumerate(self.tickers):
                for correl_index, correl_ticker in enumerate(self.tickers):
                    correl_list.append({'as_of_date':self.as_of_date,'ticker': ticker,'to': correl_ticker, 'value': corr.tolist()[index][correl_index],'fund':self.fund})
            
        else:
            std_dev = np.std(returns) * weights[0]
            correl_list.append({'as_of_date':self.as_of_date,'ticker': self.tickers[0],'to': self.tickers[0], 'value': 1,'fund':self.fund})

        var_1_day = std_dev * 2.33

        return [var_1_day, correl_list]

    
    def calc_linear_model(self):
        """
        Calcualte the coefficents of the linear model. 

        Returns:
        numpy.ndarray: the factor model coefficents.

        """
        # indepentend variables - historical factor data
        x = self.combined_df[self.factors].to_numpy()

        # dependent variables - historical position data
        y_df = self.combined_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']

        # Calcualte the dimensions of the array that will be returned
        column_length = len(y_df.columns)
        factor_num = len(self.factors) 
        coefficient_array = np.zeros(shape=(column_length, factor_num))

        # calcualte the coefficients for each ticker using least-squares estimation: b = (X^T.X)-1.X^T.Y
        for idx, ticker in enumerate(y_df.columns):
            y = y_df[ticker].to_numpy()
            b = np.linalg.inv(x.T @ x) @ x.T @ y
            coefficient_array[idx] = b
        
        return coefficient_array
    
    def factor_var(self):
        """
        Calcualte the historical factor VaR and P&L timeseries.

        Returns:
        list: [1 day VaR result, dicts containing data to create historical VaR objects]

        """
        
        dates = list(self.combined_df['Date'].dt.strftime('%Y-%m-%d'))

        # calcualte the linear model coefficents for each ticker
        b = self.linear_model

        # get a np array containing dependent variables
        y_df = self.combined_df.drop(self.factors, axis=1)
        y_df = self.weights * y_df.loc[:, y_df.columns != 'Date']
        y = self.combined_df[self.factors].to_numpy()

        # calcualte the estimated returns using the factor model
        result = y @ b.T

        # get the sorted fund return and get the return at the 99 percentile (99% VaR)
        portfolio_returns = result.sum(axis=1)
        sorted_portfolio_returns = np.sort(portfolio_returns)
        ci_99 = int(round(sorted_portfolio_returns.size *.01,0))
        var_1d = sorted_portfolio_returns[ci_99]

        # create the historical VaR series objects  
        chart_list = []
        for idx, pl in enumerate(portfolio_returns.tolist()):
            row_dict = {}
            row_dict['date'] = dates[idx]
            row_dict['as_of_date'] = self.as_of_date
            row_dict['pl'] = pl
            row_dict['fund'] = self.fund
            chart_list.append(row_dict)

        return [var_1d,chart_list]
        
    
    def stress_tests(self):
        """
        Calcualte the stress testing results.

        Returns:
        list: dicts containing data to create historical VaR objects

        """

        # array of stress testing parameters 
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
        
        # calcualte the linear model coefficents for each ticker
        b = self.linear_model

        # calcualte the returns for each stress test
        result = stresses @ b.T

        # sum the stress testing results for each ticker
        stress_result = result.sum(axis=1).tolist()

        # create the stress testing objects
        stress_names = ['Equity up 10%', 'Equity up 5%', 'Equity down 10%', 'Equity down 5%', 
                        'Interest Rates up 10%','Interest Rates down 10%', 'Dollar up 10%','Dollar down 10%']
        
        def create_stress_test_obj(stress_names, stress_result):
            return {'as_of_date':self.as_of_date,'catagory':'stress_test','type': stress_names,'value':stress_result,'fund':self.fund}

        combined_stress_result = list(map(create_stress_test_obj, stress_names, stress_result))

        return combined_stress_result

    
    
    
        

