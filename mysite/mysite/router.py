from django.db import router
from risk.views import FundViewSet, PositionViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('fund',FundViewSet)
router.register('position', PositionViewSet)


print(router.urls)