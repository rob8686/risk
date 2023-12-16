from django.db import models
from django.utils import timezone
from django.db.models import Max, Min
import pandas as pd
import math

class Security(models.Model):
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=200)
    sector = models.CharField(max_length=200)
    industry = models.CharField(max_length=200)
    asset_class = models.CharField(max_length=200)
    currency = models.CharField(max_length=200)

    def __str__(self):
        return self.ticker


class Fund(models.Model):

    class LiquidityBucket(models.TextChoices):
        D1 = '1', 
        D7 = '7', 
        D30 = '30', 
        D90 = '90', 
        D180 = '180', 
        D365 = '365', 
        D365PLUS = '365+',

    name = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)
    aum = models.FloatField(default=0)
    benchmark = models.CharField(max_length=200, default='SPY')
    liquidity_limit =  models.CharField(
        choices=LiquidityBucket.choices,
        default=LiquidityBucket.D365PLUS,
        max_length=200
    )
    liquidity_status = models.CharField(max_length=200, default='none')
    performance_status = models.CharField(max_length=200, default='none')   


    def __str__(self):
        return self.name

    #def performance_history(self,date):
    #    performance_history = PerformanceHistory.objects.filter(as_of_date=date).filter(fund=self)
    #    print(performance_history)
    #    return performance_history

    #def performance_stats(self,date):
    #    data = list(self.performance_history(date).values())
    #    data_df = pd.DataFrame(data)
    #    percent_change_df = data_df.iloc[[0, -1]].pct_change()
    #    fund_return = percent_change_df.iloc[-1,0]
    #    benchmark_return = percent_change_df.iloc[-1,1]  
    #    fund_std = data_df['fund_history'].pct_change().std() * math.sqrt(260)
    #    benchmark_std = data_df['benchamrk_history'].pct_change().std() * math.sqrt(260)
    #    fund_sharpe = fund_return / fund_std 
    #    benchmark_sharpe = benchmark_return / benchmark_std
    #    performance_dict = {'fund_return': fund_return ,'benchmark_return': benchmark_return,'fund_std': fund_std, 'benchmark_std': benchmark_std,'fund_sharpe': fund_sharpe, 'benchmark_sharpe': benchmark_sharpe}
    #    print(performance_dict)
    #    return data_df


class Position(models.Model):
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
        return self.security.ticker
    

class PerformanceManager(models.Manager):
    def performance_stats(self):
        print('TYPEEEEEEEEEEEEEEEEEEEE')
        data = list(self.values())
        data_df = pd.DataFrame(data)
        print(self)
        print(type(self))
        print(data_df)
        print('FILTER!!!')
        print(self.filter(fund__pk=1))
        print()
        percent_change_df = data_df[['fund_history','benchamrk_history']].iloc[[0, -1]].pct_change()
        fund_return = percent_change_df.iloc[-1,0]
        benchmark_return = percent_change_df.iloc[-1,1]  
        fund_std = data_df['fund_history'].pct_change().std() * math.sqrt(260)
        benchmark_std = data_df['benchamrk_history'].pct_change().std() * math.sqrt(260)
        fund_sharpe = fund_return / fund_std 
        benchmark_sharpe = benchmark_return / benchmark_std
        performance_dict = {'fund_return': fund_return ,'benchmark_return': benchmark_return,'fund_std': fund_std, 'benchmark_std': benchmark_std,'fund_sharpe': fund_sharpe, 'benchmark_sharpe': benchmark_sharpe}
        performance_dict['status'] = self.calc_status(performance_dict)
        print(performance_dict)
        return performance_dict
    
    def performance_stats2(self):
        print('TYPEEEEEEEEEEEEEEEEEEEE')
        data = list(self.values())
        data_df = pd.DataFrame(data)
        print(self)
        print(type(self))
        print(data_df)
        print('FILTER!!!')
        print(self.filter(fund__pk=1))
        print()
        percent_change_df = data_df[['fund_history','benchamrk_history']].iloc[[0, -1]].pct_change()
        fund_return = percent_change_df.iloc[-1,0]
        benchmark_return = percent_change_df.iloc[-1,1]  
        fund_std = data_df['fund_history'].pct_change().std() * math.sqrt(260)
        benchmark_std = data_df['benchamrk_history'].pct_change().std() * math.sqrt(260)
        fund_sharpe = fund_return / fund_std 
        benchmark_sharpe = benchmark_return / benchmark_std
        performance_dict = {'fund_return': fund_return ,'benchmark_return': benchmark_return,'fund_std': fund_std, 'benchmark_std': benchmark_std,'fund_sharpe': fund_sharpe, 'benchmark_sharpe': benchmark_sharpe}
        performance_dict['status'] = self.calc_status(performance_dict)
        print(performance_dict)
        return performance_dict

    def calc_status(self, return_dict):
        if return_dict['fund_return'] > 0:
            if return_dict['fund_sharpe'] > return_dict['benchmark_sharpe']:
                return 'pass'
            elif (return_dict['fund_sharpe'] / return_dict['benchmark_sharpe']) > .9:
                return 'warning'
            else:
                return 'fail'
        else:
            if return_dict['fund_return'] > return_dict['benchmark']['return']:
                return 'pass'
            elif (return_dict['fund_return'] / return_dict['benchmark_return']) > .9:
                return 'warning'
            else:
                return 'fail'    


class PerformanceHistory(models.Model):
    date = models.DateField()
    as_of_date = models.DateField()
    fund_history = models.FloatField(default=0)
    benchamrk_history = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    objects = PerformanceManager()

class PerformancePivots(models.Model):
    as_of_date = models.DateField()
    type = models.CharField(max_length=200)
    label = models.CharField(max_length=200)
    perc_contrib = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)



