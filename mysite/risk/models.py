from django.db import models
from django.utils import timezone
from django.db.models import Max, Min, Sum
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
    def performance_stats(self,fund_id):
        data = list(self.filter(fund__pk=fund_id).values())
        data_df = pd.DataFrame(data)
        print(data_df)
        percent_change_df = data_df[['fund_history','benchamrk_history']].iloc[[0, -1]].pct_change()
        fund_return = percent_change_df.iloc[-1,0]
        benchmark_return = percent_change_df.iloc[-1,1]  
        fund_std = data_df['fund_history'].pct_change().std() * math.sqrt(260)
        benchmark_std = data_df['benchamrk_history'].pct_change().std() * math.sqrt(260)
        fund_sharpe = fund_return / fund_std 
        benchmark_sharpe = benchmark_return / benchmark_std
        performance_dict = {'fund_return': fund_return ,'benchmark_return': benchmark_return,'fund_std': fund_std, 'benchmark_std': benchmark_std,'fund_sharpe': fund_sharpe, 'benchmark_sharpe': benchmark_sharpe}
        status = self.calc_status(performance_dict)
        performance_dict['status'] = status
        fund = Fund.objects.filter(id=fund_id)[0].performance_status = status 
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

class LiquidityManager(models.Manager):

    def liquidity_stats(self,fund_id):
        result_list, result_dict = [], {}
        for stress_percent in ['30%','50%','100%']:
            data = self.filter(fund__pk=fund_id).filter(stress=stress_percent)
            aggregate_data = data.aggregate(day_1=Sum('day_1'), day_7=Sum('day_7'), day_30=Sum('day_30'),day_90=Sum('day_90'), day_180=Sum('day_180'), day_365=Sum('day_365'),day_366=Sum('day_366'))
            aggregate_data['stress'] = stress_percent
            aggregate_data['subRows'] = list(data.values('day_1', 'day_7', 'day_30', 'day_90', 'day_180', 'day_365', 'day_366','type'))
            result_list.append(aggregate_data)
        
        result_dict['result'] = result_list
        result_dict['cumulative'] = self.cumulative_liquidity(result_list)
        result_dict['status'] = self.calc_status(result_list,fund_id)
        print('Calc Liquidity')
        print(self.calc_status(result_list,fund_id))

        return result_dict
    
    def cumulative_liquidity(self,result_list):
        cumulative_result_list = []
        cumulative_30 = 0
        cumulative_50 = 0
        cumulative_100 = 0

        for day in ['day_1', 'day_7', 'day_30', 'day_90', 'day_180', 'day_365', 'day_366']:
            print(result_list)
            cumulative_30 = cumulative_30 + result_list[0][day]
            cumulative_50 = cumulative_50 + result_list[1][day]
            cumulative_100 = cumulative_100 + result_list[2][day]
            formatted_day = day.split('_')[1]
            cumulative_result_list.append({'30':cumulative_30,'50':cumulative_50,'100':cumulative_100,'name':formatted_day})

        return cumulative_result_list
    
    def calc_status(self,result_list, fund_id):
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
    objects = LiquidityManager()

class CumulativeLiquditiyResult(models.Model):
    as_of_date = models.DateField()
    stress_100 = models.FloatField(default=0)
    stress_50 = models.FloatField(default=0)
    stress_30 = models.FloatField(default=0)
    day = models.CharField(max_length=200)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

class HistVarSeries(models.Model):
    date = models.DateField()
    as_of_date = models.DateField()
    pl = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

class MarketRiskStatistics(models.Model):
    as_of_date = models.DateField()
    catagory = models.CharField(max_length=200) 
    type = models.CharField(max_length=200)
    value = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

class MarketRiskCorrelation(models.Model):
    as_of_date = models.DateField()
    ticker = models.CharField(max_length=200) 
    to = models.CharField(max_length=200)
    value = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)

class HistogramBins(models.Model):
    as_of_date = models.DateField()
    bin = models.FloatField(default=0) 
    count = models.FloatField(default=0)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)



