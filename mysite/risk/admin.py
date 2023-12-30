from django.contrib import admin
from .models import Security, Position,Fund, PerformanceHistory, PerformancePivots, LiquditiyResult, HistVarSeries, MarketRiskStatistics, MarketRiskCorrelation, HistogramBins

admin.site.register(Security)
admin.site.register(Position)
admin.site.register(Fund)
admin.site.register(PerformanceHistory)
admin.site.register(PerformancePivots)
admin.site.register(LiquditiyResult)
admin.site.register(HistVarSeries)
admin.site.register(MarketRiskStatistics)
admin.site.register(MarketRiskCorrelation)
admin.site.register(HistogramBins)
