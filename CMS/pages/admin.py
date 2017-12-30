from django.contrib import admin
from .models import CustomPage


@admin.register(CustomPage)
class CustomPageAdmin(admin.ModelAdmin):
    pass
