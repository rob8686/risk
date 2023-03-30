from django.urls import path
from .views import index

urlpatterns = [
    path('', index),
    path('positions/<int:fund_id>', index),
    path('liquidity/<int:fund_id>', index),
    path('performance/<int:fund_id>', index),
    path('login/', index),
    path('create_fund/', index),
    path('create_position/<int:fund_id>', index)
]