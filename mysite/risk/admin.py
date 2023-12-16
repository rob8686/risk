from django.contrib import admin

# Register your models here.

from .models import Security, Position,Fund, PerformanceHistory, PerformancePivots

admin.site.register(Security)
admin.site.register(Position)
admin.site.register(Fund)
admin.site.register(PerformanceHistory)
admin.site.register(PerformancePivots)