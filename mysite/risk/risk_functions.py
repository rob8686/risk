import yfinance as yf
import math
import pandas as pd
import numpy as np
import time

class Liquidity:
    """
    Class calcualtes liquidity statistics for a fund.
    ...

    Methods:
    - _init__: Constructor for a liquidity object.
    - get_liquidity: Calculates liquidity statistics under normal and stressed liquidity conditions (100%, 50% and 30% of ADV).
    - calc_liq_stats: Calcualte the amount disposed in each time bucket and creates LiquditiyResult objects with the result. 
    """

    def __init__(self, yf_data, position_info, fund, as_of_date):
        """
        Constructor for a liquidity object.

        Parameters
        ----------
            - yf_data (pandas.DataFrame): Historical data containing volume data for each position.  
            - position_info (dict): Dict containing info (quantity, percent of AUM, etc.) for each position. 
            - fund (Fund): A fund object.
            - result_list (list): list of dicts containing data to create Liquidity Result objects.
            - as_of_date (str): the date the risk results will be generated for.

        """

        self.positions = position_info
        self.average_volumne = yf_data['Volume'].mean().to_dict()
        self.liq_limit = fund.liquidity_limit
        self.fund = fund
        self.as_of_date = as_of_date
        self.result_list = []


    def get_liquidity(self):
        """
        Calculates liquidity statistics under normal and stressed liquidity conditions (100%, 50% and 30% of ADV). 

        Returns:
        - list: list of dicts containing data to create Liquidity Result objects.

        """
        
        for liquidity_stress_percent in [['100%',1],['50%',.5],['30%',.3]]:
            self.calc_liq_stats(liquidity_stress_percent[1])

        return self.result_list

    def calc_liq_stats(self,liquidity_stress_percent):
        """
        Calcualte the amount disposed in each time bucket which is used to creates LiquditiyResult objects. 

        """

        # Loop through each position in the fund and add the amount disposed of each day to the correct bucket 
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
            bucket_dict = {'day_1':0, 'day_7':0, 'day_30':0, 'day_90':0, 'day_180':0, 'day_365':0, 'day_366':0,'as_of_date':self.as_of_date,'type':ticker, 'stress':str(int(liquidity_stress_percent*100))+'%','fund':self.fund}

            # for the amount disposed each day determine which liquidity bucket the amount should go in  
            for day in range(1,days_to_liquidate+1):
                for num, days in enumerate(list(bucket_dict.keys())[:-4],start=1):
                    int_days = days.split('_')[1]

                    # Only the remainder is disposed on the final day
                    if day == days_to_liquidate:
                        aum_disposed = qunatity_final_day / quantity * perc_aum
                    else:
                        aum_disposed = quantity_disposed_per_day / quantity * perc_aum

                    # if the day is less than the current liquidity bucket but greater than the previous bucket add to the current bucket
                    if day <= int(int_days):
                        if day  > int(bucket_list[num - 2]) or int_days == '1': 
                            bucket_dict[days] = bucket_dict[days] + aum_disposed

            self.result_list.append(bucket_dict)
            
  
     
class Performance:
    """
    Class calcualtes performance statistics for a fund
    ...

    Methods:
    - _init__: Constructor for performance object.
    - get_performance: Method runs performance calculations.
    - historical_data: Calcualtes fund and benchmark history and creates PerformanceHistory objects.
    - pivots: Calculates performance contribution by currency and sector. 
    - as_of_date (str): the date the risk results will be generated for.

    """

    def __init__(self, fx_converted_df, position_info_dict, fund, as_of_date):
        """
        Constructor for a performance object.

        Parameters
        ----------
            fx_converted_df (pandas.DataFrame): Historical data containing the closing price for each position.  
            position_info_dict (dict): Dict containing info (sector, currency, etc.) for each position. 
            fund (Fund): A fund object.

        """

        self.positions = position_info_dict
        self.yf_data = fx_converted_df
        self.percent_return_df = self.yf_data.pct_change()
        self.fund = fund
        self.as_of_date = as_of_date
        self.benchmark = self.fund.benchmark.ticker
        self.benchmark_data = self.yf_data[self.benchmark]
        self.benchmark_return = self.percent_return_df[self.benchmark]


    def get_performance(self):
        """
        Method runs performance calculations.

        Returns:
        - list: list of list of dicts containing data to create performance related objects.

        """
        
        pivot_data = self.pivots()
        hist_data = self.historical_data()

        return [hist_data, pivot_data]


    def historical_data(self):
        """
        Calcualtes fund and benchmark history. 


        Returns:
        - list: list of dicts containing data to create performance history objects.

        """

        weighted_return_df = pd.DataFrame()

        # Calcualte weighted return for each position in the fund
        for ticker in self.positions:
            percent_aum = self.positions[ticker][1]
            weighted_return_df[ticker] = self.percent_return_df[ticker] * percent_aum 

        # Sum the weighted return for each posiiton to get the fund return then calcualte the funds historical time series
        weighted_return_df['fund_return'] = weighted_return_df.sum(axis=1,numeric_only=True) 
        weighted_return_df['fund_history'] = 100
        hist_col_index = weighted_return_df.columns.get_loc('fund_history')
        return_col_index = weighted_return_df.columns.get_loc('fund_return')
 
        for index in range(1, len(weighted_return_df)):
            weighted_return_df.iloc[index, hist_col_index] = weighted_return_df.iloc[index-1, hist_col_index] * (1 + weighted_return_df.iloc[index, return_col_index]) 

        # Calculate the benchamrk history by rebasing the benchmark back to 100
        benchmark_base = self.benchmark_data[0]
        rebased_benchmark = self.benchmark_data / benchmark_base * 100
        weighted_return_df['benchamrk_history'] = rebased_benchmark

        weighted_return_df = weighted_return_df[['fund_history','benchamrk_history']].reset_index()
        weighted_return_df.rename(columns={"Date": "date"}, inplace=True)
        weighted_return_df['as_of_date'] = self.as_of_date
        weighted_return_df['fund'] = self.fund
        weighted_return_dict = weighted_return_df.to_dict('records')

        return weighted_return_dict


    def pivots(self):
        """
        Calculates performance contribution by currency and sector. 

        Returns:
        - list: list of dicts containing data to create performance pivot objects.

        """

        # Get first and last price for positions and benchmark and calculate return
        percent_change_df = self.yf_data.iloc[[0, -1]].pct_change()
        percent_change_df = percent_change_df.iloc[-1].to_frame()
        percent_change_df.rename(columns = {percent_change_df.columns[0]: 'perc_return'}, inplace = True)

        # Merge the return df with the position info 
        position_info_df = pd.DataFrame.from_dict(self.positions, orient='index',columns=['quantity', 'perc_aum', 'sector', 'currency'])
        combined_df = position_info_df.merge(percent_change_df, left_index=True, right_index=True)
        combined_df['perc_contrib'] = combined_df['perc_return'] * combined_df['perc_aum']

        test_sector_pivot = pd.pivot_table(combined_df, values='perc_contrib', index=['sector'], aggfunc=np.sum).reset_index().rename(columns={"sector": "label"})
        test_sector_pivot['fund'] = self.fund
        test_sector_pivot['as_of_date'] = self.as_of_date
        test_sector_pivot['type'] = 'sector'

        test_currency_pivot = pd.pivot_table(combined_df, values='perc_contrib', index=['currency'], aggfunc=np.sum).reset_index().rename(columns={"currency": "label"})
        test_currency_pivot['fund'] = self.fund
        test_currency_pivot['as_of_date'] = self.as_of_date
        test_currency_pivot['type'] = 'currency'

        performance_pivot_list = test_sector_pivot.to_dict('records') + (test_currency_pivot.to_dict('records'))

        return performance_pivot_list
        
