from .models import Security, Position, Fund, PerformanceHistory
from .risk_functions import GetFx, Liquidity,Performance
import pandas as pd
import yfinance as yf
from datetime import datetime
from django.db.models import Sum

class YFinaceData():
    def __init__(self, fund_id):
        self.fund_id = fund_id
        print(self.fund_id)
        self.fund = Fund.objects.filter(id=self.fund_id)[0]
        print()
        print('MODEL METHOD TEST!!!!!!! !!!')
        #print(self.fund.performance_history('2023-12-08'))
        print(PerformanceHistory.objects.performance_stats())
        print()
        #print(self.fund.performance_stats('2023-12-08'))
        print()
        self.positions = Position.objects.filter(fund=self.fund_id)
        self.benchmark = self.fund.benchmark
        self.fund_ccy = self.fund.currency
        self.benchmark_currency = {'SPY':'USD'}
        self.ticker_currency_list = self.get_positions_data()
        self.yf_data = self.get_yf_data()
        self.position_info = self.get_position_info()

    def run_risk(self):
        ## data.drop(columns=[benchmark],inplace=True, level=1)
        #liquidity_result = Liquidity(self.yf_data,self.position_info, self.fund.liquidity_limit).get_liquidity()
        #print(liquidity_result)

        fx_converted_df = self.fx_convert()

        performance_result = Performance(fx_converted_df, self.position_info, self.fund).get_performance()
        print(performance_result)
        #self.fund.performance_status = performance_result['performance']['pivots']['performance']['status']



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
        fx_data = GetFx(unique_currency_set,self.fund_ccy)
        fx_data_df = fx_data.get_fx()
        return fx_data_df
    
    def merge_yf_fx_data(self):
        # data should not include today
        today = datetime.today().strftime('%Y-%m-%d')
        fx_data = self.get_fx_data()
        combined_df = self.yf_data['Close'].merge(fx_data, how='left',left_index=True, right_index=True)
        combined_df = combined_df[combined_df.index < today].fillna(method="ffill").dropna()
        print(combined_df)
        return combined_df

    def fx_convert(self):

        fx_converted_df = pd.DataFrame()
        combined_df = self.merge_yf_fx_data()
        combined_df[self.fund_ccy] = 1
        for ticker, ccy in self.ticker_currency_list:
            fx_converted_df[ticker] = combined_df[ticker] * combined_df[ccy]
        fx_converted_df[self.benchmark] = combined_df[self.benchmark] * combined_df[self.benchmark_currency[self.benchmark]]
        return fx_converted_df

    def get_position_info(self):
        position_info_dict ={}
        for position in self.positions:
            sector = position.security.sector
            currency = position.security.currency
            quantity = self.positions.filter(security__ticker=position).aggregate(Sum("quantity"))['quantity__sum']
            percent_aum = self.positions.filter(security__ticker=position).aggregate(Sum("percent_aum"))['percent_aum__sum']
            position_info_dict[str(position)] = [quantity, percent_aum, sector, currency]
        print(position_info_dict)
        return position_info_dict

    


