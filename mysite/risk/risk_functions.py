import yfinance as yf
import math
import requests
import datetime
import pandas as pd
import numpy as np
from collections import Counter

class RefreshPortfolio:
    def __init__(self, yf_data, positions):
        self.positions = positions
        self.closing = yf_data #['Close']

    def test(self):
        for position in self.positions:
            filterd_ticker_df = self.closing[str(position)]
            filterd_currency_df = self.closing[position.security.currency]
            max_date = filterd_ticker_df.index.max()
            closing_price = filterd_ticker_df[filterd_ticker_df.index == max_date].item()
            fx_rate = filterd_currency_df[filterd_currency_df.index == max_date].item()
            aum = position.fund.aum
            updated_quantity = math.floor((position.percent_aum * aum) / closing_price / fx_rate)
            position.last_price = closing_price
            position.quantity = updated_quantity
            position.price_date = max_date 
            position.mkt_value_local = closing_price * updated_quantity
            position.fx_rate = fx_rate
            position.mkt_value_base = position.mkt_value_local * fx_rate 
            position.percent_aum = position.mkt_value_base / aum
            position.save()

class GetFx:

    def __init__(self, currency_set,to_currency):
        self.currency_set = currency_set
        self.to_currency = to_currency

    def fx_from_api(self, from_currency):
        print(self.to_currency)
        print(from_currency)
        apikey='2M3IEELDCP3HPW2F'
        url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_currency}&to_symbol={self.to_currency}&outputsize=full&apikey={apikey}'
        r = requests.get(url)
        data = r.json()
        return data

    def json_to_df(self, fx_dict, from_currency):
        df =  pd.DataFrame.from_dict(fx_dict['Time Series FX (Daily)']).T['4. close']
        df = df.rename(from_currency)
        df = df.astype('float')
        return df

    def combined_fx_data(self):
        df = pd.DataFrame()

        for currency in self.currency_set:
            if currency != self.to_currency:
                fx_dict = self.fx_from_api(currency)
                fx_df = self.json_to_df(fx_dict,currency)
                df = pd.concat([df, fx_df],axis=1)
        
        return df

    def get_fx(self, from_currency, date):
        fx_dict = self.fx_from_api(from_currency)
        return fx_dict['Time Series FX (Daily)'][date]['4. close']

class Liquidity:
    def __init__(self, yf_data, positions):
        self.positions = positions
        self.average_volumne = yf_data['Volume'].reset_index().mean().to_dict()

    def get_liquidity(self):
        

        liquidity_result_dict = {}
        liquidity_result_list, cumulative_list = [], []

        for perc_adv in [['100%',1],['50%',.5],['30%',.3]]:
           #liquidity_result_dict[perc_adv[0]] = self.calc_liq_stats2(perc_adv[1]) 
            result = self.calc_liq_stats2(perc_adv[1])
            #liquidity_result_dict['cumulative'] = self.calc_cumulative(result)
            #cumulative_list.append(self.calc_cumulative(result))
            result['type'] = perc_adv[0]
            #print(self.calc_cumulative(result))
            liquidity_result_list.append(result)


        liquidity_result_dict['cumulative'] = self.calc_cumulative(liquidity_result_list)
        liquidity_result_dict['result'] = liquidity_result_list
        return liquidity_result_dict

    def calc_cumulative(self, data):
        cumulative_list, cumulative_total = [], 0
        cumulative_100, cumulative_50, cumulative_30 = 0, 0, 0
        for bucket in ['1','7','30','90','180','365','365+']: 
            cumulative_100, cumulative_50, cumulative_30 = data[0][bucket] + cumulative_100, data[1][bucket] + cumulative_50, data[2][bucket] + cumulative_30
            cumulative_dict = {
            'name' : bucket,
            '100' : cumulative_100,
            '50' :cumulative_50,
            '30' :cumulative_30,
            }
            cumulative_list.append(cumulative_dict)

        return cumulative_list

    def calc_liq_stats2(self,perc_adv):

        result_dict = {}
        result_list = []
        fund_dict = {}

        for ticker in self.average_volumne:

            average_vol = self.average_volumne[ticker] * perc_adv
            quantity = self.positions[ticker][0]
            perc_aum = self.positions[ticker][1]
            quantity_disposed_per_day = math.floor(average_vol * .1)
            days_to_liquidate = math.ceil(quantity / quantity_disposed_per_day)
            aum_disposed_per_day = perc_aum / days_to_liquidate
            qunatity_final_day = quantity % quantity_disposed_per_day
            aum_final_day = perc_aum % aum_disposed_per_day

            result = self.calc_liquidity_buckets2(
                days_to_liquidate,quantity_disposed_per_day,quantity,qunatity_final_day,aum_disposed_per_day, perc_aum, aum_final_day)
            result_dict[ticker] = result 
            result['type'] = ticker

            for bucket in ['1','7','30','90','180','365','365+']:
                try:
                    fund_dict[bucket] = fund_dict[bucket] + result[bucket] 
                except KeyError:                
                    fund_dict[bucket] = 0

            result_list.append(result)

        fund_dict['subRows'] = result_list
        return fund_dict           

    def calc_liq_stats(self,perc_adv):

        result_dict = {}

        for ticker in self.average_volumne:

            average_vol = self.average_volumne[ticker] * perc_adv
            quantity = self.positions[ticker][0]
            perc_aum = self.positions[ticker][1]
            quantity_disposed_per_day = math.floor(average_vol * .1)
            days_to_liquidate = math.ceil(quantity / quantity_disposed_per_day)
            aum_disposed_per_day = perc_aum / days_to_liquidate
            qunatity_final_day = quantity % quantity_disposed_per_day
            aum_final_day = perc_aum % aum_disposed_per_day
            result_list = []

            result = self.calc_liquidity_buckets2(
                days_to_liquidate,quantity_disposed_per_day,quantity,qunatity_final_day,aum_disposed_per_day, perc_aum, aum_final_day)
            result_dict[ticker] = result 
            result['type'] = ticker


        
        for fund in result:
            print(fund)
            print(result['type'])
            print()

        fund_dict = {}

        for fund in result_dict:
            for bucket in ['1','7','30','90','180','365','365+']:
                try:
                    #fund_dict[bucket] = {'perc_aum': fund_dict[bucket]['perc_aum'] + result_dict[fund][bucket]['perc_aum']}
                    #print(fund_dict[bucket]['perc_aum'])
                    print(result_dict[fund][bucket]['perc_aum'])
                    fund_dict[bucket] = fund_dict[bucket]['perc_aum'] + result_dict[fund][bucket]['perc_aum'] 
                except KeyError:                
                    #fund_dict[bucket] = {'perc_aum': 0}
                    fund_dict[bucket] = 0

        #result_dict['Fund'] = fund_dict
        fund_dict['subRows'] = [{'bucket': key1, **value1} for key1, value1 in result_dict.items()]
        return fund_dict

    def calc_liquidity_buckets(self,days_to_liquidate,quantity_disposed_per_day, quantity, qunatity_final_day,aum_disposed_per_day, perc_aum, aum_final_day):

        #bucket_dict = {
        #    '1':{'quantity':0,'perc_aum':0},'7':{'quantity':0,'perc_aum':0},
        #    '30':{'quantity':0,'perc_aum':0}, '90':{'quantity':0,'perc_aum':0},
        #    '180':{'quantity':0,'perc_aum':0},'365':{'quantity':0,'perc_aum':0},
        #    '365+':{'quantity':0,'perc_aum':0}}


        bucket_dict = {
            '1':{'perc_aum':0},'7':{'perc_aum':0},
            '30':{'perc_aum':0}, '90':{'perc_aum':0},
            '180':{'perc_aum':0},'365':{'perc_aum':0},
            '365+':{'perc_aum':0}}


        #if quantity < quantity_disposed_per_day:
            #bucket_dict['1']['quantity'], bucket_dict['1']['perc_aum'] = quantity, perc_aum
            #return bucket_dict


        if quantity < quantity_disposed_per_day:
            #bucket_dict['1']['quantity'], bucket_dict['1']['perc_aum'] = quantity, perc_aum
            bucket_dict['1']['perc_aum'] = perc_aum
            return bucket_dict

        for day in range(1,days_to_liquidate+1):

            if day < days_to_liquidate:
                amount_to_liquidate = quantity_disposed_per_day
                perc_amount_to_liquidate = aum_disposed_per_day
            else:
                amount_to_liquidate = qunatity_final_day
                perc_amount_to_liquidate = aum_final_day

            if day > 365:
                #bucket_dict['365+']['quantity'], self.fund_level_bucket_dict['365+']['quantity'] = bucket_dict['365+']['quantity'] + amount_to_liquidate
                bucket_dict['365+']['perc_aum'] = bucket_dict['365+']['perc_aum'] + perc_amount_to_liquidate
            else:
                for bucket in ['1','7','30','90','180','365']:
                    #bucket_dict[bucket]['bucket'] = bucket
                    if day <= int(bucket):
                        #bucket_dict[bucket]['quantity'] = bucket_dict[bucket]['quantity'] + amount_to_liquidate
                        bucket_dict[bucket]['perc_aum'] = bucket_dict[bucket]['perc_aum'] + perc_amount_to_liquidate
                        break 
        
        output_list = [{'bucket': key1, **value1} for key1, value1 in bucket_dict.items()]
        print('OUTPUT LIST!!!!!!!!!!!!!!!!')
        print(output_list)

        print(bucket_dict.values())
        return bucket_dict

    def calc_liquidity_buckets2(self,days_to_liquidate,quantity_disposed_per_day, quantity, qunatity_final_day,aum_disposed_per_day, perc_aum, aum_final_day):

        bucket_dict = {
            '1':0,'7':0, '30':0, '90':0,
            '180':0,'365':0,'365+':0 
            }

        if quantity < quantity_disposed_per_day:
            bucket_dict['1'] = perc_aum
            return bucket_dict

        for day in range(1,days_to_liquidate+1):

            if day < days_to_liquidate:
                perc_amount_to_liquidate = aum_disposed_per_day
            else:
                perc_amount_to_liquidate = aum_final_day

            if day > 365:
                bucket_dict['365+'] = bucket_dict['365+'] + perc_amount_to_liquidate
            else:
                for bucket in ['1','7','30','90','180','365']:
                    if day <= int(bucket):
                        bucket_dict[bucket] = bucket_dict[bucket] + perc_amount_to_liquidate
                        break 
        
        return bucket_dict
     


class RiskAnalytics:
    def __init__(self, yf_data, positions):
        self.positions = positions
        self.average_volumne = yf_data['Volume'].reset_index().mean().to_dict()
        self.average_volume_dict = self.adv()


    def adv(self):

        adv_dict = {}

        for ticker in self.average_volumne:
            adv_dict[ticker] = self.average_volumne[ticker]   

        return adv_dict 
        

    def calc_liquidity(self):
        
        liquidity_dict = {}    

        for ticker in self.positions:
            quantity = float(self.positions[ticker][0])
            adv = float(self.average_volume_dict[ticker])            
            liquidity_dict[ticker] = self.calc_liquidity_bucket(quantity,adv) 

        return liquidity_dict


    def calc_liquidity_bucket(self, quantity, adv):
        # calcualtes the number of days to liquidate position at 10% of ADV per day 
        max_liquid_per_day = adv * .1
        days_to_liquidate = math.ceil(quantity / max_liquid_per_day)
        amount_final_day = quantity % max_liquid_per_day 

        bucket_dict = {'1':0,'7':0,'30':0,'90':0,'180':0,'365':0,'365+':0}

        # create list of lists with day and amount elements
        liquidity_days_list = [[day,max_liquid_per_day] if day < days_to_liquidate 
                else [day,amount_final_day] 
                for day in range(1,days_to_liquidate +1)]

        for day in liquidity_days_list:
            if day[0] ==1:
                bucket_dict['1'] = bucket_dict['1'] + day[1] 
            elif day[0] <= 7:
                bucket_dict['7']= bucket_dict['7'] + day[1]
            elif day[0] <= 30:
                bucket_dict['30']= bucket_dict['30'] + day[1]
            elif day[0] <= 90:
                bucket_dict['90']= bucket_dict['90'] + day[1]
            elif day[0] <= 180:
                bucket_dict['180']= bucket_dict['180'] + day[1]
            elif day[0] <= 365:
                bucket_dict['365']= bucket_dict['365'] + day[1]
            else:
                bucket_dict['365+']= day[1]

        return bucket_dict

class Performance:
    def __init__(self, yf_data, positions, benchmark):
        self.positions = positions
        self.yf_data = yf_data
        self.percent_return_df = self.yf_data.pct_change()
        self.benchmark = benchmark
        self.benchmark_return = self.percent_return_df[benchmark]

    def get_performance(self):

        performance_dict = {'performance':{}}

        weighted_returns = self.calc_weighted_returns()
        historical_data = weighted_returns[['fund_history','benchamrk_history']].reset_index().to_dict('records')
        fund_std = weighted_returns['sum'].std() * math.sqrt(260)
    
        benchmark_df = self.yf_data[self.benchmark]
        #performance_dict['performance']['historical_data']['benchmark_history'] = ((benchmark_df / benchmark_df.iloc[0]) * 100).to_dict()
        benchmark_std = self.benchmark_return.std() * math.sqrt(260)
        
        pivots = self.calc_period_return()

        performance_dict['performance']['fund_history'] = historical_data 
        performance_dict['performance']['pivots'] = pivots
        return_dict = performance_dict['performance']['pivots']['performance'] 
        return_dict['fund']['std'] = fund_std
        return_dict['benchmark']['std'] = benchmark_std
        return_dict['fund']['sharpe'] = return_dict['fund']['return'] / fund_std
        return_dict['benchmark']['sharpe'] = return_dict['benchmark']['return'] / benchmark_std

        return performance_dict

    def calc_weighted_returns(self):

        weighted_return_df = pd.DataFrame()
        self.positions[self.benchmark] = [1, 1]
        
        for ticker in self.positions:
            percent_aum = self.positions[ticker][1]
            weighted_return_df[ticker] = self.percent_return_df[ticker] * percent_aum 
         
        weighted_return_df['sum'] = weighted_return_df[list(weighted_return_df.columns)].sum(axis=1)
        weighted_return_df['fund_history'], weighted_return_df['benchamrk_history'] = 100, 100

        for index in range(1, len(weighted_return_df)):
            for item in [['fund_history','sum'],['benchamrk_history', self.benchmark]]:
                previous_value = weighted_return_df.loc[weighted_return_df.index[index - 1],item[0]]
                daily_return = weighted_return_df.loc[weighted_return_df.index[index ],item[1]]
                weighted_return_df.loc[weighted_return_df.index[index],item[0]] = round(previous_value * (1 + daily_return),2)
        
        self.positions.pop('key', None)
        return weighted_return_df

    def calc_period_return(self):

        percent_change_df = self.yf_data.iloc[[0, -1]].pct_change()
        percent_change_df = percent_change_df.iloc[-1].to_frame()
        percent_change_df.rename(columns = {list(percent_change_df)[0]: 'perc_return'}, inplace = True)
        position_info_df = pd.DataFrame.from_dict(self.positions, orient='index',columns=['quantity', 'perc_aum', 'sector', 'currency'])
        combined_df = position_info_df.merge(percent_change_df, left_index=True, right_index=True)
        combined_df['perc_contrib'] = combined_df['perc_return'] * combined_df['perc_aum']
        sector_pivot = pd.pivot_table(combined_df, values='perc_contrib', index=['sector'], aggfunc=np.sum)
        currency_pivot = pd.pivot_table(combined_df, values='perc_contrib', index=['currency'], aggfunc=np.sum)
        pivot_dict = {
            'performance': {'fund':{'return': combined_df.sum().to_dict()['perc_contrib']},
            'benchmark' :{'return': percent_change_df.to_dict()['perc_return'][self.benchmark]}} ,
            'pivots': {
                'currency':currency_pivot.reset_index().to_dict('records'),
                'sector': sector_pivot.reset_index().to_dict('records')
                }
            }
        return pivot_dict

def get_yf_data(tickers):
    data = yf.download(  # or pdr.get_data_yahoo(...
        # tickers list or string as well
        tickers=tickers,

        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period="ytd",

        # fetch data by interval (including intraday if period < 60 days)
        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval="1d",

        # group by ticker (to access via data['SPY'])
        # (optional, default is 'column')
        group_by='column',

        # adjust all OHLC automatically
        # (optional, default is False)
        auto_adjust=True,

        # download pre/post regular market hours data
        # (optional, default is False)
        prepost=False,

        # use threads for mass downloading? (True/False/Integer)
        # (optional, default is True)
        threads=True,

        # proxy URL scheme use use when downloading?
        # (optional, default is None)
        proxy=None

    )
    return data

def calc_liquidity(quantity,adv):
    # calcualtes the number of days to liquidate position at 10% of ADV per day 
    max_liquid_per_day = adv * .1
    days_to_liquidate = math.ceil(quantity / max_liquid_per_day)
    amount_final_day = quantity % max_liquid_per_day 

    bucket_dict = {'1':0,'7':0,'30':0,'90':0,'180':0,'365':0,'365+':0}

    # create list of lists with day and amount elements
    liquidity_days_list = [[day,max_liquid_per_day] if day < days_to_liquidate 
               else [day,amount_final_day] 
               for day in range(1,days_to_liquidate +1)]

    for day in liquidity_days_list:
        if day[0] ==1:
            bucket_dict['1'] = bucket_dict['1'] + day[1] 
        elif day[0] <= 7:
            bucket_dict['7']= bucket_dict['7'] + day[1]
        elif day[0] <= 30:
            bucket_dict['30']= bucket_dict['30'] + day[1]
        elif day[0] <= 90:
            bucket_dict['90']= bucket_dict['90'] + day[1]
        elif day[0] <= 180:
            bucket_dict['180']= bucket_dict['180'] + day[1]
        elif day[0] <= 365:
            bucket_dict['365']= bucket_dict['365'] + day[1]
        else:
            bucket_dict['365+']= day[1]

    return bucket_dict

def calc_performance(yf_df,):
    #for tickier  
    return True