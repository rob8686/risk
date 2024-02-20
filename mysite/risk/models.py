from django.db import models
from django.utils import timezone
from django.db.models import Max, Min, Sum
import pandas as pd
import math
from .run_risk import RunRisk
from django.contrib.auth.models import User
import yfinance as yf
import requests
import time


class Security(models.Model):
    """
    Model representing a security.

    Fields:
    - name (CharField): The name of the security.
    - ticker (CharField): The ticker of the security.
    - sector (CharField): The sector of the security.
    - industry (CharField): The industry of the security.
    - asset_class (CharField): The asset class of the security.
    - currency (CharField): The currency of the security.

    Methods:
    - __str__: Return a string representation of the security.
    """
    
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=200)
    sector = models.CharField(max_length=200)
    industry = models.CharField(max_length=200)
    asset_class = models.CharField(max_length=200)
    currency = models.CharField(max_length=200)

    def __str__(self):
        """
        Get a string representation of the security.

        Returns:
        - String: the name of the security. 
        """
        return self.ticker
    
class Benchmark(models.Model):
    """
    Model representing a benchmark.

    Fields:
    - name (CharField): the name of the benchmark.
    - ticker (CharField): the ticker of the benchmark.
    - currency (CharField): the currency of the benchmark.

    Methods:
    - __str__: Return a string representation of the benchmark.
    """

    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)

    def __str__(self):
        """
        Get a string representation of the benchamrk.

        Returns:
        - String: the name of the benchmark. 
        """

        return self.name


class Fund(models.Model):
    """
    Model representing a fund.

    Fields:
    - name (CharField): The name of the fund.
    - currency (CharField): The currency of the fund.
    - aum (FloatField): The asset under mangement (aum) of the fund.
    - benchmark (CharField): The benchmark of the fund.
    - liquidity_limit (CharField): The timeframe (7 days, 30 days etc.) the funds need to be able to liquidate in.
    - liquidity_status (CharField): The status (pass / warning / fail) of the fund liquidity test.
    - performance_status (CharField): The status (pass / warning / fail) of the fund performance test.


    Methods:
    - __str__: Get a string representation of the fund.
    - last_date: Get the 'price_date' of most recent related position object.
    - run_risk: Run the risk analytics for the fund.
    - refresh_portfolio: Update position objects related to the fund with the most recent data.
    """
    

    class LiquidityBucket(models.TextChoices):
        D1 = '1', 
        D7 = '7', 
        D30 = '30', 
        D90 = '90', 
        D180 = '180', 
        D365 = '365', 
        D365PLUS = '365+',
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)
    aum = models.FloatField(default=0)
    #benchmark = models.CharField(max_length=200, default='SPY')
    benchmark = models.ForeignKey(Benchmark, on_delete=models.CASCADE,default=1)
    liquidity_limit =  models.CharField(
        choices=LiquidityBucket.choices,
        default=LiquidityBucket.D365PLUS,
        max_length=200
    )
    liquidity_status = models.CharField(max_length=200, default='none')
    performance_status = models.CharField(max_length=200, default='none')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of the fund.

        Returns:
        - String: the name of the fund. 
        """
        return self.name
    
    @property
    def last_date(self):
        """
        Get the 'price_date' of most recent related position object

        Returns:
        - Date: The most recent price date. 
        """
        return Position.objects.filter(fund=self.id).latest('price_date').price_date

    def run_risk(self, date):
        """
        Run the risk analytics for the fund.
        """   

        positions = Position.objects.filter(fund=self)

        # retrieve the factor and FX data
        factor_data = FactorData.objects.get_factors(date)

        currencies = set(positions.values_list('security__currency', flat=True))
        fx_data = FxData.objects.get_fx(currencies,self.currency, date)

        risk_result = RunRisk(self, positions, date, factor_data, fx_data).run_risk()
        
        # create the objects for the risk results 
        result_list = [
            [LiquditiyResult,risk_result[0]],[PerformanceHistory,risk_result[1][0]],[PerformancePivots,risk_result[1][1]],[HistogramBins,risk_result[2][0]], 
            [MarketRiskCorrelation, risk_result[2][1][1]], [MarketRiskStatistics,risk_result[2][3]], [HistVarSeries, risk_result[2][2][1]]
            ]
        
        for item in result_list:
            item[0].objects.filter(fund=self).filter(as_of_date=date).delete()        
            objs = [item[0](**data) for data in item[1]]
            item[0].objects.bulk_create(objs)

        MarketRiskStatistics.objects.create(as_of_date=date, catagory='var_result' ,type='parametric_var',value=risk_result[2][1][0], fund=self)
        MarketRiskStatistics.objects.create(as_of_date=date, catagory='var_result' ,type='hist_var_result',value=risk_result[2][2][0], fund=self)

        #update liquidity and performance status
        LiquditiyResult.objects.liquidity_stats(self.id)
        PerformanceHistory.objects.performance_stats(self.id)


    def refresh_portfolio(self, yf_data):
        """
        Update position objects related to the fund with the most recent data.
        """   
        positions = Position.objects.filter(fund__pk=self.id)

        for position in positions:
            filterd_ticker_df = yf_data[str(position)]
            filterd_currency_df = yf_data[position.security.currency]
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


class Position(models.Model):
    """
    Model representing a position.

    Fields:
    - quantity (FloatField): The quantity of the position.
    - last_price (FloatField): The last price of the position.
    - price_date (FloatField): The date of the last price of the position.
    - percent_aum (FloatField): The position weight as a percent of assets under management.
    - mkt_value_local (FloatField): The market value of the posiiton in the security currency.
    - fx_rate (FloatField): The FX rate on the price date.
    - mkt_value_base (FloatField): The market value of the posiiton in the fund currency.
    - security (ForeignKey): The security of the position (related to Security model).
    - fund (ForeignKey): The fund of the position (related to Fund model).

    Methods:
    - __str__: Return a string representation of the posiiton.
    """

    quantity = models.FloatField(default=0)
    last_price = models.FloatField()
    price_date = models.DateField()
    percent_aum = models.FloatField(default=0)
    mkt_value_local = models.FloatField(default=0)
    fx_rate = models.FloatField(default=0)
    mkt_value_base = models.FloatField(default=0)
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of the position.

        Returns:
        - String: the name of the position. 
        """

        return self.security.ticker
    

class PerformanceManager(models.Manager):
    """
    Custom manager for the PerformanceHistory model.

    Methods:
    - performance_stats: Calculate performance statistics using PerformanceHistory objects related to a fund.
    - calc_status: Calculate the performance status of the related fund.
    """

    def performance_stats(self,fund_id):
        """
        Calculate performance statistics using PerformanceHistory objects related to a fund.

        Parameters:
        - fund_id (str): the pk of a related fund.

        Returns:
        - dict: the return, volatility and sharpe ratio of the related fund.
        """

        data = list(self.filter(fund__pk=fund_id).values())
        fund = Fund.objects.filter(id=fund_id).first()

        data_df = pd.DataFrame(data)
        percent_change_df = data_df[['fund_history','benchamrk_history']].iloc[[0, -1]].pct_change()
        fund_return = percent_change_df.iloc[-1,0]
        benchmark_return = percent_change_df.iloc[-1,1]  
        fund_std = data_df['fund_history'].pct_change().std() * math.sqrt(260)
        benchmark_std = data_df['benchamrk_history'].pct_change().std() * math.sqrt(260)
        fund_sharpe = fund_return / fund_std 
        benchmark_sharpe = benchmark_return / benchmark_std
        performance_dict = {'fund':{'return':fund_return,'std':fund_std,'sharpe':fund_sharpe},'benchmark':{'return':benchmark_return,'std':benchmark_std,'sharpe':benchmark_sharpe}} 
        status = self.calc_status(performance_dict)
        performance_dict['status'] = status
        fund.performance_status =  status 
        fund.save()
        return performance_dict
    
    def calc_status(self, return_dict):
        """
        Calculate the performance status of the related fund.

        Parameters:
        - return_dict (dict): the return, volatility and sharpe ratio of the related fund.

        Returns:
        - str: the performance status (pass/warning/fail) of the fund 
        """

        if return_dict['fund']['return'] > 0:
            if return_dict['fund']['sharpe'] >= return_dict['benchmark']['sharpe']:
                return 'pass'
            elif (return_dict['fund']['sharpe'] / return_dict['benchmark']['sharpe']) > .9:
                return 'warning'
            else:
                return 'fail'
        else:
            if return_dict['fund']['return'] >= return_dict['benchmark']['return']:
                return 'pass'
            elif (return_dict['fund']['return'] / return_dict['benchmark']['return']) > .9:
                return 'warning'
            else:
                return 'fail' 
      

class PerformanceHistory(models.Model):
    """
    Model representing an entry in a performance history timeseries.

    Fields:
    - date (DateField): The date of the performance history entry.
    - as_of_date (DateField): The date of the performance result the performance history was used tom calculate.
    - fund_history (FloatField): The price of the fund.
    - benchamrk_history (FloatField): The price of the benchmark.
    - fund (ForeignKey): The fund object the PerformanceHistory is related to.

    Methods:
    - __str__: Return a string representation of the performance history.
    """

    date = models.DateField()
    as_of_date = models.DateField()
    fund_history = models.FloatField(default=0)
    benchamrk_history = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    
    # Use the custom manager
    objects = PerformanceManager()


    def __str__(self):
        """
        Get a string representation of the performance history.

        Returns:
        - String: the name of the performance history. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.date.strftime('%Y-%m-%d')


class PerformancePivotManager(models.Manager):
    """
    Custom manager for the PerformancePivot model.

    Methods:
    - performance_stats: format the values of the PerformancePivot objects
      as a dict with the type (currency / sector) as the key and the rest of the data as values.
    """

    def performance_stats(self,fund_id):
        """
        format the values of the PerformancePivot objects
        as a dict with the type (currency / sector) as the key and the rest of the data as values.

        Parameters:
            - fund_id (str): the pk of a related fund.

        Returns:
            - dict: the formated performance pivot data.
        """
        data = self.filter(fund__pk=fund_id).values('type', 'label', 'perc_contrib')
        return_dict = {'currency':[],'sector':[]}
        for row in data:
            return_dict[row['type']].append({'label':row['label'],'perc_contrib': row['perc_contrib']}) 

        return return_dict
    

class PerformancePivots(models.Model):
    """
    Model representing a performance pivot.

    Fields:
    - as_of_date (DateField): The date of the performance result the performance pivots were used tom calculate.
    - fund_history (FloatField): The price of the fund.
    - perc_contrib (FloatField): The price of the benchmark.
    - fund (ForeignKey): The fund object the PerformancePivots is related to.

    Methods:
    - __str__: Return a string representation of the performance pivots.
    """

    as_of_date = models.DateField()
    type = models.CharField(max_length=200)
    label = models.CharField(max_length=200)
    perc_contrib = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    # Use the custom manager
    objects = PerformancePivotManager()


    def __str__(self):
        """
        Get a string representation of the performance pivot.

        Returns:
        - String: the name of the performance pivot. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.type


class LiquidityManager(models.Manager):
    """
    Custom manager for the LiquditiyResult model.

    Methods:
    - liquidity_stats: aggregate the LiquditiyResult objects related to a specific Fund object by
      summing the time to liquidate for each position and return this with the individual results 
    - cumulative_liquidity: as a dict with the type (currency / sector) as the key and the rest of the data as values.
    - calc_status:

    """

    def liquidity_stats(self,fund_id):
        """
        Aggregate the LiquditiyResult objects related to a specific Fund object by
        summing the time to liquidate for each position and return this with the individual results 

        Parameters:
            - fund_id (str): the pk of a related fund.

        Returns:
            - dict: the formated liquditiy result data.
        """

        result_list, result_dict = [], {}

        # iterate through each average volumne stress testing percent
        for stress_percent in ['30%','50%','100%']:

            data = self.filter(fund__pk=fund_id).filter(stress=stress_percent)

            # sum the selected LiquditiyResult objects to get the total amount liquidated per days bucket 
            aggregate_data = data.aggregate(day_1=Sum('day_1'), day_7=Sum('day_7'), day_30=Sum('day_30'),day_90=Sum('day_90'), day_180=Sum('day_180'), day_365=Sum('day_365'),day_366=Sum('day_366'))
            aggregate_data['type'] = stress_percent
            aggregate_data['subRows'] = list(data.values('day_1', 'day_7', 'day_30', 'day_90', 'day_180', 'day_365', 'day_366','type'))
            result_list.append(aggregate_data)
        
        result_dict['result'] = result_list
        result_dict['cumulative'] = self.cumulative_liquidity(result_list)
        status = self.calc_status(result_list,fund_id)
        result_dict['status'] = status

        fund = Fund.objects.filter(id=fund_id)[0]
        fund.liquidity_status = status
        fund.save()

        return result_dict
    
    def cumulative_liquidity(self,result_list):
        """
        Calcualte the cumulative percent liquidated at each liquidity bicket 

        Parameters:
            - result_list (list): list of dicts containing the time to liquidate for each bucket.

        Returns:
            - list: list of dicts containing the cumulative liquidity results.
        """

        cumulative_result_list = []
        cumulative_30 = 0
        cumulative_50 = 0
        cumulative_100 = 0

        for day in ['day_1', 'day_7', 'day_30', 'day_90', 'day_180', 'day_365', 'day_366']:
            cumulative_30 = cumulative_30 + result_list[0][day]
            cumulative_50 = cumulative_50 + result_list[1][day]
            cumulative_100 = cumulative_100 + result_list[2][day]
            formatted_day = day.split('_')[1]
            cumulative_result_list.append({'30':cumulative_30,'50':cumulative_50,'100':cumulative_100,'name':formatted_day})

        return cumulative_result_list
    
    def calc_status(self,result_list, fund_id):
        """
        Calculate the liquidity status of the related fund object.

        Parameters:
        - return_dict (dict): the return, volatility and sharpe ratio of the related fund.

        Returns:
        - str: the liquidity status (pass/warning/fail) of the fund 
        """

        liquidity_limit = Fund.objects.filter(id=fund_id)[0].liquidity_limit

        for day in ['day_1', 'day_7', 'day_30', 'day_90', 'day_180', 'day_365', 'day_366']:
            formatted_day = day.split('_')[1]
            if result_list[0][day] != 0:
                max_30 = formatted_day 
            if result_list[1][day] != 0:
                max_50 = formatted_day
            if result_list[2][day] != 0:
                max_100 = formatted_day
        
        if liquidity_limit == '365+':
            return 'pass'
        elif int(max_100) > int(liquidity_limit):
             return 'fail'
        elif (int(max_50) > int(liquidity_limit)) or (int(max_30) > int(liquidity_limit)):
            return 'warning'
        else:
            return 'pass' 
    

class LiquditiyResult(models.Model):
    """
    Model representing a liquditiy result.

    Fields:
    - as_of_date (DateField):  The date of the risk statistics the liquditiy result was used tom calculate.
    - day_1 (FloatField): The amount that can be liquidated in the 1 day liquidity bucket
    - day_7 (FloatField): The amount that can be liquidated in the 7 day liquidity bucket
    - day_30 (FloatField): The amount that can be liquidated in the 30 day liquidity bucket
    - day_90 (FloatField): The amount that can be liquidated in the 90 day liquidity bucket
    - day_180 (FloatField): The amount that can be liquidated in the 180 day liquidity bucket
    - day_365 (FloatField): The amount that can be liquidated in the 365 day liquidity bucket
    - day_366 (FloatField): The amount that can be liquidated in the 365+ day liquidity bucket 
    - fund (ForeignKey): The fund object the LiquditiyResult is related to.

    Methods:
    - __str__: Return a string representation of the liquditiy result.
    """

    as_of_date = models.DateField()
    day_1 = models.FloatField(default=0)
    day_7 = models.FloatField(default=0)
    day_30 = models.FloatField(default=0)
    day_90 = models.FloatField(default=0)
    day_180 = models.FloatField(default=0)
    day_365 = models.FloatField(default=0)
    day_366 = models.FloatField(default=0)
    type = models.CharField(max_length=200)
    stress = models.CharField(max_length=200)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    # Use the custom manager
    objects = LiquidityManager()


    def __str__(self):
        """
        Get a string representation of the liquditiy result.

        Returns:
        - String: the name of the liquditiy result. 
        """

        return str(self.fund) + ' ' + self.as_of_date + ' ' + self.stress
    

class CumulativeLiquditiyResult(models.Model):
    """
    Model representing a cumulative liquditiy result.

    Fields:
    - as_of_date (DateField): The date of the risk statistics the cumulative liquditiy result was used tom calculate.
    - stress_100 (FloatField): the cumulative amount disposed at the 100% average volumne stress.
    - stress_50 (FloatField): the cumulative amount disposed at the 50% average volumne stress.
    - stress_30 (FloatField): the cumulative amount disposed at the 30% average volumne stress.
    - day (CharField): The liquidity bucket
    - fund (ForeignKey): The fund object the CumulativeLiquditiyResult is related to.

    Methods:
    - __str__: Return a string representation of the liquditiy result.
    """

    as_of_date = models.DateField()
    stress_100 = models.FloatField(default=0)
    stress_50 = models.FloatField(default=0)
    stress_30 = models.FloatField(default=0)
    day = models.CharField(max_length=200)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of the cumulative liquditiy result.

        Returns:
        - String: the name of the cumulative liquditiy result. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.day
    

class HistVarSeries(models.Model):
    """
    Model representing a entey in a historical VaR timerseries entry.

    Fields:
    - as_of_date (DateField): The as of date of the risk metrics the historical VaR series entry was used tom calculate.
    - data (DateField): the date of the historical VaR series entry 
    - pl (FloatField): the profit and loss (p&l) on the day
    - fund (ForeignKey): The fund object the HistVarSeries is related to.

    Methods:
    - __str__: Return a string representation of the historical VaR series result.
    """

    as_of_date = models.DateField()
    date = models.DateField()
    pl = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of the historical VaR timerserie.

        Returns:
        - String: the name of the historical VaR timerseries entry. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.date.strftime('%Y-%m-%d')
    

class MarketRiskStatistics(models.Model):
    """
    Model representing a market risk statistic such as a VaR or stress test result.

    Fields:
    - as_of_date (DateField): The as of date of the risk metrics the historical VaR series entry was used tom calculate.
    - catagory (CharField): the catagory (VaR result, Stress Tests etc.) of market risk statistic
    - type (CharField): the type (equity up 10%, Historic VaR etc.) of the catagory of market risk statistic
    - value (FloatField): the value of the market risk statistic. 
    - fund (ForeignKey): The fund object the HistVarSeries is related to.

    Methods:
    - __str__: Return a string representation of the market risk statistic.
    """

    as_of_date = models.DateField()
    catagory = models.CharField(max_length=200) 
    type = models.CharField(max_length=200)
    value = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of the market risk statistic.

        Returns:
        - String: the name of the market risk statistic. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.catagory + ' ' + self.type


class HistogramBins(models.Model):
    """
    Model representing a bin of a histogram.

    Fields:
    - as_of_date (DateField): The as of date of the histogram.
    - bin (FloatField): the value of the bin.
    - count (FloatField): the number of items in the bin.
    - fund (ForeignKey): The fund object the bin is related to.

    Methods:
    - __str__: Return a string representation of the histogram bin.
    """

    as_of_date = models.DateField()
    bin = models.FloatField(default=0) 
    count = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of the histogram bin.

        Returns:
        - String: the name of the histogram bin. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.bin 
    

class CorrelationManager(models.Manager):
    """
    Custom manager for the MarketRiskCorrelation model.

    Methods:
    - get_correlation: combine the MarketRiskCorrelation object into a correlation matrix
    """

    def get_correlation(self,fund_id):
        """
        - get_correlation: combine the MarketRiskCorrelation objects into a correlation matrix

        Parameters:
        - fund_id (str): the pk of a related fund.

        Returns:
        - list: list of list containing the tickers and correlation matrix.
        """
        data = self.filter(fund__pk=fund_id).values('ticker','to','value')
        data_df = pd.DataFrame(data)
        table = pd.pivot_table(data_df, values='value', index=['ticker'], columns=['to'], aggfunc="sum")
        correl_matrix = [table[col].tolist() for col in table.columns]
        tickers = list(table.columns)
        return [tickers,correl_matrix]
    

class MarketRiskCorrelation(models.Model):
    """
    Model representing an cell in a correlation matrix.

    Fields:
    - as_of_date (DateField): The as of date of the risk metrics the historical VaR series entry was used tom calculate.
    - ticker (CharField): one of the tickers in the correlation pair.
    - to (CharField): one of the tickers in the correlation pair.
    - value (FloatField): the correlation between 'ticker' and 'to'.  
    - fund (ForeignKey): The fund object the HistVarSeries is related to.

    Methods:
    - __str__: Return a string representation of the market risk statistic.
    """

    as_of_date = models.DateField()
    ticker = models.CharField(max_length=200) 
    to = models.CharField(max_length=200)
    value = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

    # Use the custom manager
    objects = CorrelationManager()

    def __str__(self):
        """
        Get a string representation of the correlation matrix element.

        Returns:
        - String: the name of the correlation matrix element. 
        """

        return str(self.fund) + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.ticker + ' ' + self.to
    

class FactorManager(models.Manager):
    """
    Custom manager for the FactorData model.

    Methods:
    - get_factors: Get the factor timeseries from Yahoo Finance and save and return it.
    """

    def get_factors(self, as_of_date):
        """
        Get the factor timeseries from Yahoo Finance and save and return it.
            
        Parameters:
        - as_of_date (str): the date the factor data will be retrieved for.

        Returns:
        pandas.DataFrame: df containing factor data 

        """

        factor_data = FactorData.objects.filter(as_of_date=as_of_date)

        # if factor data for the as of date is not already in the DB retrieve the data from yfinance 
        if factor_data.count() == 0:
            ticker_string = ''.join([ticker +' ' for ticker in ['SPY','^TNX','BZ=F','^NYICDX','IGLN.L','^VIX']])

            data = yf.download(tickers=ticker_string, period="1y",
                interval="1d", group_by='column',auto_adjust=True, prepost=False,threads=True,proxy=None)

            data = data['Close'].fillna(method="ffill").dropna().reset_index()
            data['as_of_date'] = as_of_date
            data.columns = [col.lower() for col in data.columns]
            data = data.rename(columns={"bz=f": "bz", "igln.l": "igln","^nyicdx": "nyicdx","^tnx": "tnx","^vix": "vix"}).to_dict('records')
            #DELTE THEIS DELTE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #FactorData.objects.all().delete()

            # Create and retrieve factor data objects
            factor_data_objs = [FactorData(**obj) for obj in data]
            FactorData.objects.bulk_create(factor_data_objs)
            factor_data = FactorData.objects.filter(as_of_date=as_of_date)
        
        factor_data_df = pd.DataFrame(factor_data.values('date','spy','tnx','bz','nyicdx','igln','vix'))

        factor_data_df = factor_data_df.set_index('date')
        factor_data_df.index.rename('Date',inplace=True)

        return factor_data_df
    

class FactorData(models.Model):
    """
    Model representing a factor data on a speific date.

    Fields:
    - as_of_date (DateField): The as of date of timeseries.
    - date (DateField): the data of the time series element
    - spy (FloatField): the price of the S&P 500 index
    - tnx (FloatField): 10 year US treasury 
    - bz (FloatField): Brent crude price
    - nyicdx (FloatField): Dollar index
    - igln (FloatField): Gold price  
    - vix (FloatField): Vix index

    Methods:
    - __str__: Return a string representation of the factor data.
    """

    as_of_date = models.DateField()
    date = models.DateField()
    spy = models.FloatField(default=0)
    tnx =  models.FloatField(default=0)
    bz =  models.FloatField(default=0)
    nyicdx = models.FloatField(default=0)
    igln = models.FloatField(default=0)
    vix = models.FloatField(default=0)

    # Use the custom manager
    objects = FactorManager()


    def __str__(self):
        """
        Get a string representation of the factor data.

        Returns:
        - String: the name of the factor data. 
        """

        return self.date.strftime('%Y-%m-%d')

   
class FxDataManager(models.Manager):
    """
    Custom manager for the FactorData model.

    Methods:
    - get_factors: Get the factor timeseries from Yahoo Finance and save and return it.
    """

    def fx_from_api(self, from_currency,to_currency):
        """
        Calls API for requested currency and returns the FX data.

        Parameters
        ---------- 
            from_currency (str): A currency code

        Returns:
        dict: dict containing FX data. 
        """

        apikey='2M3IEELDCP3HPW2F'
        url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_currency}&to_symbol={to_currency}&outputsize=full&apikey={apikey}'
        r = requests.get(url)
        data = r.json()
        return data

    def get_fx(self, currency_set,to_currency, as_of_date, date=None):
        """
        Retrieve FX data for each currency in the inputed set of currency codes.

        Parameters
        ---------- 
            currency_set (set) : A set of strings which contains currency codes  
            to_currency (str): A currency code 
            date (str, optional): A string representing a date. If not provided, the default value is None.

        Returns:
        - pandas.DataFrame: If no date parameter is entered, returns a df containing historical FX date.
        - float: If a date parameter is entered, returns the FX rate on that date.

        """

        df = pd.DataFrame() 
        count = 1
        
        for currency in currency_set:
            
            # Don't need to get data for the fund currency
            if currency != to_currency:

                fx_query = FxData.objects.filter(as_of_date=as_of_date).filter(to_currency=to_currency).filter(from_currency=currency)
                    
                #if the currecny is already in the DB for the as of date retrieve the FX date from the DB
                if fx_query.count() > 0:
                    # If a date parameter is not entered retrieve the FX history, else returns the FX rate on that date 
                    if date == None:
                        fx_df =  pd.DataFrame(fx_query.values('date', 'value')).set_index('date')
                        fx_df = fx_df.rename(columns={"value": currency})
                    else:
                      return fx_query.filter(date=date).values('value')[0]['value']  

                else:
                    # 5 API call per minute limit
                    if count % 5 == 0:
                        time.sleep(60)

                    fx_json = self.fx_from_api(currency,to_currency)

                    # Check for error messages in the API response 
                    if 'Note' in fx_json:
                        return 'API Limit Reached'
                    if 'Error Message' in fx_json:
                        return 'Invalid Currency Code'
                    
                    fx_df =  pd.DataFrame.from_dict(fx_json['Time Series FX (Daily)']).T['4. close']
                    fx_df = fx_df.astype('float')
                    fx_df = fx_df.rename('value')
                    fx_df = fx_df.to_frame()
                    fx_df.index.rename('date',inplace=True)
                    fx_df['as_of_date'] = as_of_date
                    fx_df['to_currency'] = to_currency
                    fx_df['from_currency'] = currency

                    # Create the FxData object 
                    fx_data_objs = [FxData(**data) for data in fx_df.reset_index().to_dict('records')]
                    FxData.objects.filter(to_currency=to_currency).filter(from_currency=currency).delete()
                    FxData.objects.bulk_create(fx_data_objs)

                    # If a date parameter is entered, returns the FX rate on that date.
                    if date != None:
                        return fx_json['Time Series FX (Daily)'][date]['4. close']

                    fx_df.rename(columns={"value": currency}, inplace=True)
                    fx_df = fx_df[currency]

                df = pd.concat([df, fx_df],axis=1)
                count = count + 1

        df = df.rename_axis('Date')

        return df
    

class FxData(models.Model):
    """
    Model representing a the FX rate for a currency pair on a specific date.

    Fields:
    - as_of_date (DateField): The as of date of timeseries.
    - date (DateField): the data of the FX rate
    - to_currency (CharField): a currency in the currency pair
    - from_currency (CharField): a currency in the currency pair 
    - value (FloatField): the FX rate

    Methods:
    - __str__: Return a string representation of the factor data.
    """
        
    as_of_date = models.DateField()
    date = models.DateField()
    to_currency = models.CharField(max_length=3)
    from_currency = models.CharField(max_length=3) 
    value = models.FloatField(default=0)

    # Use the custom manager
    objects = FxDataManager()

    def __str__(self):
        """
        Get a string representation of the fx rate.

        Returns:
        - String: the name of the fx rate. 
        """

        return self.to_currency + self.from_currency + ' ' + self.as_of_date.strftime('%Y-%m-%d') + ' ' + self.date







