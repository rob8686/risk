import yfinance as yf
import math
import requests
import datetime
import pandas as pd
import numpy as np
from collections import Counter
import time

class RefreshPortfolio:
    def __init__(self, yf_data, positions):
        self.positions = positions
        self.closing = yf_data

    def refresh(self):
        # Update each positon for the new closing price and FX rate
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
        apikey='2M3IEELDCP3HPW2F'
        url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_currency}&to_symbol={self.to_currency}&outputsize=full&apikey={apikey}'
        r = requests.get(url)
        data = r.json()
        return data

    def get_fx(self, date=None):
        df = pd.DataFrame()
        
        for index, currency in enumerate(self.currency_set,start=1):

            # 5 API call per minute limit
            if index % 5 == 0:
                time.sleep(60)

            # if each currency in the pair is different get the data from the API
            # if a date has been enterd a rate for 1 currency on that datw will be returned
            # if no date enetered a df with the currencies requested will be returned 
            if currency != self.to_currency:
                fx_json = self.fx_from_api(currency)
                if 'Note' in fx_json:
                    return 'API Limit Reached'
                if 'Error Message' in fx_json:
                    return 'Invalid Currency Code'
                if date != None:
                    return fx_json['Time Series FX (Daily)'][date]['4. close']
                fx_df =  pd.DataFrame.from_dict(fx_json['Time Series FX (Daily)']).T['4. close']
                fx_df = fx_df.astype('float')
                fx_df = fx_df.rename(currency)
                df = pd.concat([df, fx_df],axis=1)
            # if both currencies are the same when a specific date is request return a rate of 1  
            elif date != None:
                return 1

        return df

class Liquidity:
    def __init__(self, yf_data, position_info, liq_limit):
        self.positions = position_info
        self.average_volumne = yf_data['Volume'].reset_index().mean().to_dict()
        self.liq_limit = liq_limit

    def get_liquidity(self):
        
        days_to_liquidate_dict = {}
        cumulative_list, liquidity_result_list = [], []

        # calcualte liquidity metrics under normal market conditions and stressed condiitons (50% and 30% of ADV)
        for liquidity_stress_percent in [['100%',1],['50%',.5],['30%',.3]]:
            result = self.calc_liq_stats(liquidity_stress_percent[1])
            days_to_liquidate_dict[liquidity_stress_percent[0]] = result[0]
            liquidity_result_list.append(result[1])
            cumulative_list.append(result[2])
        
        # convert the cumulative liquidity result into the required format
        cumulative_list_final = []
        for bucket in ['1', '7', '30', '90', '180', '365', '366']:
            bucket_dict = {}
            bucket_dict['name'] = bucket
            for row, perc_adv in enumerate(['100','50','30']):
                bucket_dict[perc_adv] = cumulative_list[row][bucket]
            cumulative_list_final.append(bucket_dict)

        # prepare data to be reuturned
        liquidity_result_dict = {}        
        liquidity_result_dict['cumulative'] = cumulative_list_final 
        liquidity_result_dict['result'] = liquidity_result_list
        liquidity_result_dict['days'] = days_to_liquidate_dict
        liquidity_result_dict['status'] = self.calc_status(days_to_liquidate_dict)

        return liquidity_result_dict
    
    def calc_status(self, liquidity_days_dict):
        # calcualte liquidity status (pass /warning / fail) based on the days to liquidte and the fund day limit
        # if days to liquidte is less than the limit under stress conditions the sttus is a warning
        if self.liq_limit == '365+':
            return 'pass'
        elif liquidity_days_dict['100%'] > int(self.liq_limit):
             return 'fail'
        elif (liquidity_days_dict['50%'] > int(self.liq_limit)) or (liquidity_days_dict['30%'] > int(self.liq_limit)):
            return 'warning'
        else:
            return 'pass' 

    def calc_liq_stats(self,liquidity_stress_percent):
        #Calcualted the amount disposed in each time bucket and the cumulative amount disposed per bucket  
        cumulative_dict = {'1':0, '7':0, '30':0, '90':0, '180':0, '365':0, '366':0}
        combined_bucket_dict = {'1':0, '7':0, '30':0, '90':0, '180':0, '365':0, '366':0}
        rows = []

        # Loop through each position in the fund and add the amount disposed of each day to the correct dict 
        for ticker in self.average_volumne:
            # reduce average volume by the liquidity stress test percent
            average_vol = self.average_volumne[ticker] * liquidity_stress_percent
            quantity = self.positions[ticker][0]
            perc_aum = self.positions[ticker][1]
            # assume 10% of average volumne can be disposed each day without effecting the price
            quantity_disposed_per_day = math.floor(average_vol * .1)
            qunatity_final_day = quantity % quantity_disposed_per_day
            days_to_liquidate = math.ceil(quantity / quantity_disposed_per_day)

            bucket_list = ['1', '7', '30', '90', '180', '365', '366']
            bucket_dict = {'1':0, '7':0, '30':0, '90':0, '180':0, '365':0, '366':0}

            for day in range(1,days_to_liquidate+1):
                for num, days in enumerate(bucket_list,start=1):

                    # a different amonunt can be dispsoed of if it is the last day
                    if day == days_to_liquidate:
                        aum_disposed = qunatity_final_day / quantity * perc_aum
                    else:
                        aum_disposed = quantity_disposed_per_day / quantity * perc_aum

                    # if the day is less than the time bucket add the amount dispiosed to the cumulative dict
                    # only add to the individual bucket dict if the day is less than the current time bucket and greater than the previous time bucket    
                    if day <= int(days):
                        cumulative_dict[days] = cumulative_dict[days] + aum_disposed
                        if day  > int(bucket_list[num - 2]) or days == '1': 
                            bucket_dict[days] = bucket_dict[days] + aum_disposed
                            combined_bucket_dict[days] = combined_bucket_dict[days] + aum_disposed

   
            bucket_dict['type'] = ticker
            rows.append(bucket_dict)

        combined_bucket_dict['subRows'] = rows
        combined_bucket_dict['type'] = str(int(liquidity_stress_percent *100)) + '%'

        return [days_to_liquidate,combined_bucket_dict,cumulative_dict,days_to_liquidate]
     
class Performance:
    def __init__(self, fx_converted_df, position_info_dict, benchmark):
        self.positions = position_info_dict
        self.yf_data = fx_converted_df
        self.percent_return_df = self.yf_data.pct_change()
        self.benchmark = benchmark
        self.benchmark_data = self.yf_data[benchmark]
        self.benchmark_return = self.percent_return_df[benchmark]


    def get_performance(self):

        performance_dict = {'performance':{}}
        weighted_returns = self.calc_weighted_returns()
        historical_data = weighted_returns[['fund_history','benchamrk_history']].reset_index().to_dict('records')
        fund_std = weighted_returns['fund_history'].pct_change().std() * math.sqrt(260)
        benchmark_std = self.benchmark_return.std() * math.sqrt(260)
        pivots = self.calc_period_return()

        performance_dict['performance']['fund_history'] = historical_data 
        performance_dict['performance']['pivots'] = pivots
        
        return_dict = performance_dict['performance']['pivots']['performance'] 
        return_dict['fund']['std'] = fund_std
        return_dict['benchmark']['std'] = benchmark_std
        return_dict['fund']['sharpe'] = return_dict['fund']['return'] / fund_std
        return_dict['benchmark']['sharpe'] = return_dict['benchmark']['return'] / benchmark_std
        return_dict['status'] = self.calc_status(return_dict)
        print('performance_dict2222222222!!!!!!!!')
        print(performance_dict)
        print()
        return performance_dict

    def calc_status(self, return_dict):
        if return_dict['fund']['return'] > 0:
            if return_dict['fund']['sharpe'] > return_dict['benchmark']['sharpe']:
                return 'pass'
            elif (return_dict['fund']['sharpe'] / return_dict['benchmark']['sharpe']) > .9:
                return 'warning'
            else:
                return 'fail'
        else:
            if return_dict['fund']['return'] > return_dict['benchmark']['return']:
                return 'pass'
            elif (return_dict['fund']['return'] / return_dict['benchmark']['return']) > .9:
                return 'warning'
            else:
                return 'fail'
    

    def calc_weighted_returns(self):
        # Calcualte the fund and benchmark time series with a base value of 100

        weighted_return_df = pd.DataFrame()
        remaining_percent = 100 # as funds can have less than 100% invested
        result_list = []

        # Calcualte weighted return for each position in the fund
        for ticker in self.positions:
            percent_aum = self.positions[ticker][1]
            weighted_return_df[ticker] = self.percent_return_df[ticker] * percent_aum 
            #weighted_return_df.reset_index(inplace=True)
            #weighted_return_df = weighted_return_df.reset_index(drop=True)
            #weighted_return_df['fund_return2'] = weighted_return_df.sum(axis=1,numeric_only=True) 
            #weighted_return_df.to_csv('HIST_TEST.csv')
            print()
            print('weighted_return_df')
            print(weighted_return_df)
            #print(weighted_return_df.reset_index())
            #print(weighted_return_df[['MSFT','fund_return']])
            print(weighted_return_df.columns)
            print()
            print(weighted_return_df.sum(axis=0))
            print()
            print(weighted_return_df.sum(axis=1))
            #data.iloc[1: , :]
            print() 
            value = 100 * percent_aum
            remaining_percent = remaining_percent - value
            #print()
            #print('remaining_percent')
            #print(remaining_percent)
            ticker_result_list = [value]
            for percent_return in self.percent_return_df[ticker][1:]:
                value = value * (1 + percent_return)
                ticker_result_list.append(value)
                #print('ticker_result_list')
                #print(ticker_result_list)
            result_list.append(ticker_result_list)
        
        weighted_return_df['fund_return3'] = weighted_return_df.sum(axis=1,numeric_only=True) 
        weighted_return_df['fund_history'] = 100
        hist_col_index = weighted_return_df.columns.get_loc('fund_history')
        return_col_index = weighted_return_df.columns.get_loc('fund_return3')
 
        for index in range(1, len(weighted_return_df)):
        #for index in weighted_return_df.index:
            print('index')
            print(index)
            #weighted_return_df.iloc[index, 'fund_history'] = weighted_return_df.iloc[i-1, 'fund_history'] * (1 + weighted_return_df.iloc[i, 'fund_return3'])
        #weighted_return_df['fund_history'] = weighted_return_df['fund_history'].shift(1) * weighted_return_df['fund_return3'] 
            weighted_return_df.iloc[index, hist_col_index] = weighted_return_df.iloc[index-1, hist_col_index] * (1 + weighted_return_df.iloc[index, return_col_index]) 

        weighted_return_df.to_csv('HIST_TEST.csv')

        if remaining_percent < 0:
            pass
        
        # Sum the weighted return for each position to set the fund time series  
        sum_list = [sum(row) + remaining_percent for row in zip(*result_list)]
        sum_list_2 = [sum(row) for row in zip(*result_list)]
        #print('sum_list')
        #print(sum_list)
        #print()
        # Rebased the benchmark series starting at 100
        benchmark_base = self.benchmark_data[0]
        rebased_benchmark = self.benchmark_data / benchmark_base * 100
        weighted_return_df['fund_history'] = sum_list
        weighted_return_df['TEST2'] = sum_list_2
        weighted_return_df['benchamrk_history'] = rebased_benchmark
        #weighted_return_df.to_csv('HIST_TEST.csv')
        performance_dict = {'performance':{}}
        performance_dict['performance']['fund_history'] = weighted_return_df[['fund_history','benchamrk_history']].reset_index().to_dict('records')

        return weighted_return_df

    def calc_period_return(self):

        # Get first and last price for positions and benchmark and calculate return
        percent_change_df = self.yf_data.iloc[[0, -1]].pct_change()
        # Keep only the row with the most recent date
        percent_change_df = percent_change_df.iloc[-1].to_frame()
        percent_change_df.rename(columns = {percent_change_df.columns[0]: 'perc_return'}, inplace = True)

        # Merge the return df with the position info 
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
