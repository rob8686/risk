from django.db import router
from risk.views import FundViewSet, PositionViewSet, PerformanceHistoryViewSet, PerformancePivotViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('fund',FundViewSet)
router.register('position', PositionViewSet)
router.register('performance_history', PerformanceHistoryViewSet)
router.register('performance_pivotViewSet', PerformancePivotViewSet)


print(router.urls)