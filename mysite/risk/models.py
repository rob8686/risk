from django.db import models


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

    def __str__(self):
        return self.name

    @property
    def last_date(self):
        return Position.objects.filter(fund=self.id).latest('price_date').price_date


class Position(models.Model):
    quantity = models.FloatField()
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
