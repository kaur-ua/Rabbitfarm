from django.urls import path
from .views import farm_page, edit_farm

urlpatterns = [
    path('', farm_page, name='farm_page'),
    path('edit/', edit_farm, name='edit_farm'),
]
