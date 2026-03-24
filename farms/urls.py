from django.urls import path
from .views import farm_page

urlpatterns = [
    path('', farm_page, name='farm_page'),
]
