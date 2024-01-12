from .risk_functions import GetFx, Liquidity,Performance
from .market_risk import Var
import pandas as pd
import yfinance as yf
from datetime import datetime
from django.db.models import Sum

class RunRisk():
    def __init__(self, fund, positions, PerformanceHistory, PerformancePivots, LiquditiyResult, HistVarSeries, MarketRiskStatistics,HistogramBins, MarketRiskCorrelation, FactorData, FxData):
        self.fund = fund
        self.positions = positions
        self.benchmark = self.fund.benchmark
        self.fund_ccy = self.fund.currency
        self.benchmark_currency = {'SPY':'USD'}
        self.ticker_currency_list = self.get_positions_data()
        self.yf_data = self.get_yf_data()
        self.position_info = self.get_position_info()
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
        fx_converted_df = self.fx_convert()
        print(fx_converted_df[0])
        self.fund.refresh_portfolio(fx_converted_df[0])
        print(fx_converted_df)
        Performance(fx_converted_df[1], self.position_info, self.fund, self.PerformanceHistory, self.PerformancePivots).get_performance()
        self.yf_data.drop(columns=[self.benchmark],inplace=True, level=1)
        print(self.yf_data)
        Liquidity(self.yf_data,self.position_info, self.fund, self.LiquditiyResult).get_liquidity()
        Var(fx_converted_df[1].drop(columns=[self.benchmark]), self.position_info, self.fund, self.HistVarSeries, self.MarketRiskStatistics, 
            self.HistogramBins, self.MarketRiskCorrelation, self.FactorData).get_var()

    def get_positions_data(self):
        ticker_currency_list = list(self.positions.values_list("security__ticker","security__currency"))
        return ticker_currency_list
    
    def get_yf_data(self):
        unique_tickers = set(ticker[0] for ticker in self.ticker_currency_list)
        ticker_string = self.benchmark + ' ' + ' '.join(unique_tickers)
        data = yf.download(tickers=ticker_string, period="1y",
            interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)
        data.index = data.index.strftime('%Y-%m-%d')
        return data
    
    def get_fx_data(self):
        unique_currency_set = set(currency[1] for currency in self.ticker_currency_list)
        fx_data = GetFx(unique_currency_set,self.fund_ccy, self.FxData)
        fx_data_df = fx_data.get_fx()
        return fx_data_df
    
    def merge_yf_fx_data(self):
        # data should not include today
        today = datetime.today().strftime('%Y-%m-%d')
        fx_data = self.get_fx_data()
        fx_data.index = fx_data.index.astype(str)
        combined_df = self.yf_data['Close'].merge(fx_data, how='outer',left_index=True, right_index=True)
        #combined_df = self.yf_data['Close'].merge(fx_data.reset_index(), how='left',left_index=True, right_on='date')
        combined_df = combined_df[combined_df.index < today].fillna(method="ffill").dropna()
        return combined_df

    def fx_convert(self):

        fx_converted_df = pd.DataFrame()
        combined_df = self.merge_yf_fx_data()
        combined_df[self.fund_ccy] = 1
        for ticker, ccy in self.ticker_currency_list:
            fx_converted_df[ticker] = combined_df[ticker] * combined_df[ccy]
        fx_converted_df[self.benchmark] = combined_df[self.benchmark] * combined_df[self.benchmark_currency[self.benchmark]]
        return [combined_df, fx_converted_df] 

    def get_position_info(self):
        position_info_dict ={}
        for position in self.positions:
            sector = position.security.sector
            currency = position.security.currency
            quantity = self.positions.filter(security__ticker=position).aggregate(Sum("quantity"))['quantity__sum']
            percent_aum = self.positions.filter(security__ticker=position).aggregate(Sum("percent_aum"))['percent_aum__sum']
            position_info_dict[str(position)] = [quantity, percent_aum, sector, currency]
        return position_info_dict

    


