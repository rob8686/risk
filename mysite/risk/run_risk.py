from .risk_functions import GetFx, Liquidity,Performance
from .market_risk import Var
import pandas as pd
import yfinance as yf
from datetime import datetime
from django.db.models import Sum

class RunRisk():
    """
    Class runs risk for a fund
    ...

    Methods:
    - _init__: Constructor for a run risk object.
    - run_risk: Method runs risk calculations for a fund.
    - get_positions_data: Method filteres data to retrieve the ticker and currency of the position object.
    - get_yf_data: Method retrives historical data from Yahoo Finance for a collection of tickers.
    - get_fx_data: Method retrives historical FX data.
    - merge_yf_fx_data: Method merges Yahoo Finance and FX dataframes.
    - fx_convert: Method converts position prices from the position currency to the fund currency.
    - get_position_info: Method gets info [quantity,percent AUM, sector, currency] on entered positions

    """

    def __init__(self, fund, positions, PerformanceHistory, PerformancePivots, LiquditiyResult, HistVarSeries, MarketRiskStatistics,HistogramBins, MarketRiskCorrelation, FactorData, FxData):
        """
        Constructor for a run risk object.

        Parameters
        ----------
            fund (Fund) : a fund object.
            positions list(Posiiton): list of related position.
        """

        self.fund = fund
        self.positions = positions
        self.benchmark = self.fund.benchmark
        self.fund_ccy = self.fund.currency
        # Update!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.benchmark_currency = {'SPY':'USD'}
        self.ticker_currency_list = self.get_positions_data()
        self.position_info = self.get_position_info()
        self.yf_data = self.get_yf_data()
        self.LiquditiyResult = LiquditiyResult
        self.PerformanceHistory = PerformanceHistory
        self.PerformancePivots = PerformancePivots
        self.HistVarSeries = HistVarSeries
        self.MarketRiskStatistics = MarketRiskStatistics
        self.HistogramBins = HistogramBins
        self.MarketRiskCorrelation = MarketRiskCorrelation
        self.FactorData = FactorData
        self.FxData = FxData

    def run_risk(self):
        """
        Method runs risk calculations for a fund.
        """

        fx_converted_df = self.fx_convert()
        self.fund.refresh_portfolio(fx_converted_df[0])
        Performance(fx_converted_df[1], self.position_info, self.fund, self.PerformanceHistory, self.PerformancePivots).get_performance()

        if self.benchmark not in self.position_info.keys():
            self.yf_data.drop(columns=[self.benchmark],inplace=True, level=1)
            fx_converted_df[1].drop(columns=[self.benchmark],inplace=True)

        Liquidity(self.yf_data,self.position_info, self.fund, self.LiquditiyResult).get_liquidity()
        Var(fx_converted_df[1], self.position_info, self.fund, self.HistVarSeries, self.MarketRiskStatistics, 
            self.HistogramBins, self.MarketRiskCorrelation, self.FactorData).get_var()
        
        
    def get_positions_data(self):
        """
        Method filteres data to retrieve the ticker and currency of the position object.

        Returns:
        list[(str,str)]: list of tuples containing the ticker and currency of a position.
        """

        ticker_currency_list = list(self.positions.values_list("security__ticker","security__currency"))
        return ticker_currency_list
    
    def get_yf_data(self):
        """
        Method retrives historical data from Yahoo Finance for a collection of tickers.

        Returns:
        pandas.DataFrame: data retrieved from Yahoo Finance for specified tickers.        
        """

        unique_tickers = set(ticker[0] for ticker in self.ticker_currency_list)
        ticker_string = self.benchmark + ' ' + ' '.join(unique_tickers)
        data = yf.download(tickers=ticker_string, period="1y",
            interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)
        data.index = data.index.strftime('%Y-%m-%d')

        if not isinstance(data.columns, pd.MultiIndex):
            multi_index_cols = pd.MultiIndex.from_tuples([(col, list(self.position_info.keys())[0]) for col in data.columns])
            data.columns = multi_index_cols

        return data
    
    def get_fx_data(self):
        """
        Method retrives historical FX data. 

        Returns:
        pandas.DataFrame: dataframe containing FX data.        
        """
        unique_currency_set = set(currency[1] for currency in self.ticker_currency_list)
        fx_data = GetFx(unique_currency_set,self.fund_ccy, self.FxData)
        fx_data_df = fx_data.get_fx()
        return fx_data_df
    
    def merge_yf_fx_data(self):
        """
        Method merges Yahoo Finance and FX dataframes. 

        Returns:
        pandas.DataFrame: combined Yahoo Finance and FX data.        
        """

        today = datetime.today().strftime('%Y-%m-%d') # data should not include today
        fx_data = self.get_fx_data()
        fx_data.index = fx_data.index.astype(str)
        combined_df = self.yf_data['Close'].merge(fx_data, how='outer',left_index=True, right_index=True)
        combined_df = combined_df[combined_df.index < today].fillna(method="ffill").dropna()
        return combined_df

    def fx_convert(self):
        """
        Method converts position prices from the position currency to the fund currency. 

        Returns:
        list[pandas.DataFrame]: returns the merged price and FX df and the FX converted df.        
        """

        fx_converted_df = pd.DataFrame()
        combined_df = self.merge_yf_fx_data()

        combined_df[self.fund_ccy] = 1
        for ticker, ccy in self.ticker_currency_list:
            fx_converted_df[ticker] = combined_df[ticker] * combined_df[ccy]
        fx_converted_df[self.benchmark] = combined_df[self.benchmark] * combined_df[self.benchmark_currency[self.benchmark]]
        return [combined_df, fx_converted_df] 

    def get_position_info(self):
        """
        Method gets info [quantity,percent AUM, sector, currency] on entered positions. 

        Returns:
        dict: a dict with tickers as keys and lists containing position info as values.
        """
        position_info_dict ={}
        for position in self.positions:
            sector = position.security.sector
            currency = position.security.currency
            quantity = self.positions.filter(security__ticker=position).aggregate(Sum("quantity"))['quantity__sum']
            percent_aum = self.positions.filter(security__ticker=position).aggregate(Sum("percent_aum"))['percent_aum__sum']
            position_info_dict[str(position)] = [quantity, percent_aum, sector, currency]
        return position_info_dict

    


