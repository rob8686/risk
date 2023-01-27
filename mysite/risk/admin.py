from django.contrib import admin

# Register your models here.

from .models import Security, Position,Fund

admin.site.register(Security)
admin.site.register(Position)
admin.site.register(Fund)