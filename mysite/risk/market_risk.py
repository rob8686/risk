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
    

    def __init__(self, fx_converted_df, position_info, fund, as_of_date, HistVarSeries, MarketRiskStatistics,HistogramBins, MarketRiskCorrelation, FactorData):
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
        self.as_of_date = as_of_date
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
        self.weights =  np.asarray([self.position_info[col][1] for col in self.fx_converted_df.columns])
        self.linear_model = self.calc_linear_model()
        self.tickers = self.fx_converted_df.columns


    def get_var(self):
        """
        Method runs market risk calculations calculations.

        """
        
        self.MarketRiskStatistics.objects.filter().delete()
        self.HistogramBins.objects.all().delete()
        self.parametric_var()
        self.factor_var()
        self.stress_tests()
        self.histogram()

    
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


    def parametric_var(self):
        """
        Create the Parametric VaR data (VaR and correlation matrix) and create MarketRiskStatistics and MarketRiskCorrelation objects.

        """

        returns = self.fx_converted_df.pct_change().dropna().to_numpy()
        weights = self.weights
 
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
            row_dict['as_of_date'] = '2023-12-08'
            row_dict['pl'] = pl
            row_dict['fund'] = self.fund
            chart_list.append(row_dict)
 
        self.HistVarSeries.objects.all().delete()
        hist_var_series_objs = [self.HistVarSeries(**data) for data in chart_list]
        self.HistVarSeries.objects.bulk_create(hist_var_series_objs)
        self.MarketRiskStatistics.objects.create(as_of_date='2023-12-08', catagory='var_result' ,type='hist_var_result',value=var_1d, fund=self.fund )
        
    
    def stress_tests(self):
        """
        Calcualte the stress testing results.

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
            return {'as_of_date':'2023-12-08','catagory':'stress_test','type': stress_names,'value':stress_result,'fund':self.fund}

        combined_stress_new = list(map(create_stress_test_obj, stress_names, stress_result))
        market_risk_stat_objs = [self.MarketRiskStatistics(**data) for data in combined_stress_new]
        self.MarketRiskStatistics.objects.bulk_create(market_risk_stat_objs)

    
    def get_factors(self):
        """
        Get the factor timeseries from Yahoo Finance and save and return it.

        Returns:
        pandas.DataFrame: df containing factor data 

        """

        factor_data = self.FactorData.objects.filter(as_of_date='2024-01-23')

        # if factor data for the as of date is not already in the DB retrieve the data from yfinance 
        if factor_data.count() == 0:
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
    
    
        

