import yfinance as yf
import math
import requests
import pandas as pd
import numpy as np
import time


class GetFx:
    """
    Class for retrieving FX data using the Alpha Vantage API
    ...

    Methods:
    - _init__: Constructor for a get FX object.
    - fx_from_api: Calls API for requested currency and returns the FX data. 
    - get_fx: Retrieve FX data for each currency in the inputed set of currency codes.

    """

    def __init__(self, currency_set,to_currency, FxData):
        """
        Constructor for a get FX object.

        Parameters
        ----------
            currency_set (set) : A set of strings which contains currency codes  
            to_currency (str): A currency code 
        """

        self.currency_set = currency_set
        self.to_currency = to_currency
        self.FxData = FxData

    def fx_from_api(self, from_currency):
        """
        Calls API for requested currency and returns the FX data.

        Parameters
        ---------- 
            from_currency (str): A currency code

        Returns:
        dict: dict containing FX data. 
        """

        apikey='2M3IEELDCP3HPW2F'
        url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_currency}&to_symbol={self.to_currency}&outputsize=full&apikey={apikey}'
        r = requests.get(url)
        data = r.json()
        return data

    def get_fx(self, date=None):
        """
        Retrieve FX data for each currency in the inputed set of currency codes.

        Parameters
        ---------- 
            date (str, optional): A string representing a date. If not provided, the default value is None.

        Returns:
        - pandas.DataFrame: If no date parameter is entered, returns a df containing historical FX date.
        - float: If a date parameter is entered, returns the FX rate on that date.

        """

        df = pd.DataFrame() 
        count = 1
        for currency in self.currency_set:
            
            # Don't need to get data for the fund currency
            if currency != self.to_currency:

                fx_query = self.FxData.objects.filter(as_of_date='2023-12-08').filter(to_currency=self.to_currency).filter(from_currency=currency)

                #if the currecny is already in the DB for the as of date retrieve the FX date from the DB
                if fx_query.count() > 0:
                    fx_df =  pd.DataFrame(fx_query.values('date', 'value')).set_index('date')
                    fx_df = fx_df.rename(columns={"value": currency})

                # Else call the data through trh Alpha Vantange API
                else:
                    # 5 API call per minute limit
                    if count % 5 == 0:
                        time.sleep(60)

                    fx_json = self.fx_from_api(currency)

                    # Check for error messages in the API response 
                    if 'Note' in fx_json:
                        return 'API Limit Reached'
                    if 'Error Message' in fx_json:
                        return 'Invalid Currency Code'
                    
                    # If a date parameter is entered, returns the FX rate on that date.
                    if date != None:
                        return fx_json['Time Series FX (Daily)'][date]['4. close']
                    
                    fx_df =  pd.DataFrame.from_dict(fx_json['Time Series FX (Daily)']).T['4. close']
                    fx_df = fx_df.astype('float')
                    fx_df = fx_df.rename('value')
                    fx_df = fx_df.to_frame()
                    fx_df.index.rename('date',inplace=True)
                    fx_df['as_of_date'] = '2023-12-08'
                    fx_df['to_currency'] = self.to_currency
                    fx_df['from_currency'] = currency

                    # Create the FxData object 
                    fx_data_objs = [self.FxData(**data) for data in fx_df.reset_index().to_dict('records')]
                    self.FxData.objects.filter(to_currency=self.to_currency).filter(from_currency=currency).delete()
                    self.FxData.objects.bulk_create(fx_data_objs)

                    fx_df.rename(columns={"value": currency}, inplace=True)
                    fx_df = fx_df[currency]

                df = pd.concat([df, fx_df],axis=1)
                count = count + 1

            # if both currencies are the same when a specific date is request return a rate of 1  
            #elif date != None:
            #    return 1

        df = df.rename_axis('Date')

        return df

class Liquidity:
    """
    Class calcualtes liquidity statistics for a fund
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
            yf_data (pandas.DataFrame): Historical data containing volume data for each position.  
            position_info (dict): Dict containing info (quantity, percent of AUM, etc.) for each position. 
            fund (Fund): A fund object.
            result_list (list): list of dicts containing data to create Liquidity Result objects.

        """

        self.positions = position_info
        self.average_volumne = yf_data['Volume'].reset_index().mean().to_dict()
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

    """

    def __init__(self, fx_converted_df, position_info_dict, fund, as_of_date, PerformanceHistory, PerformancePivots):
        """
        Constructor for a performance object.

        Parameters
        ----------
            fx_converted_df (pandas.DataFrame): Historical data containing the closing price for each position.  
            position_info_dict (dict): Dict containing info (sector, currency, etc.) for each position. 
            fund (Fund): A fund object.
            PerformanceHistory (PerformanceHistory): A PerformanceHistory object.
            PerformancePivots (PerformancePivots): A PerformancePivots object. 

        """

        self.positions = position_info_dict
        self.yf_data = fx_converted_df
        self.percent_return_df = self.yf_data.pct_change()
        self.fund = fund
        self.as_of_date = as_of_date
        self.benchmark = self.fund.benchmark
        self.benchmark_data = self.yf_data[self.benchmark]
        self.benchmark_return = self.percent_return_df[self.benchmark]
        self.PerformanceHistory = PerformanceHistory
        self.PerformancePivots = PerformancePivots


    def get_performance(self):
        """
        Method runs performance calculations.

        """
        
        self.pivots()
        self.historical_data()

        # update performance status 
        self.PerformanceHistory.objects.performance_stats(self.fund.id)


    def historical_data(self):
        """
        Calcualtes fund and benchmark history and creates PerformanceHistory objects. 

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
        weighted_return_df['as_of_date'] = '2023-12-08'
        weighted_return_df['fund'] = self.fund
        weighted_return_dict = weighted_return_df.to_dict('records')
        print('weighted_return_dict weighted_return_dict weighted_return_dict')
        print(weighted_return_dict)
        performance_history_objs = [self.PerformanceHistory(**data) for data in weighted_return_dict]
        self.PerformanceHistory.objects.all().delete()
        self.PerformanceHistory.objects.bulk_create(performance_history_objs)


    def pivots(self):
        """
        Calculates performance contribution by currency and sector. 

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
        test_sector_pivot['as_of_date'] = '2023-12-08'
        test_sector_pivot['type'] = 'sector'

        test_currency_pivot = pd.pivot_table(combined_df, values='perc_contrib', index=['currency'], aggfunc=np.sum).reset_index().rename(columns={"currency": "label"})
        test_currency_pivot['fund'] = self.fund
        test_currency_pivot['as_of_date'] = '2023-12-08'
        test_currency_pivot['type'] = 'currency'

        self.PerformancePivots.objects.all().delete()
        performance_pivot_list = test_sector_pivot.to_dict('records') + (test_currency_pivot.to_dict('records'))
        performance_pivot_objs = [self.PerformancePivots(**data) for data in performance_pivot_list]
        self.PerformancePivots.objects.bulk_create(performance_pivot_objs)
        
