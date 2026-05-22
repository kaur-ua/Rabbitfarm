from django.urls import path
from .views import farm_page, edit_farm, create_farm, feedback

urlpatterns = [
    path('create/', create_farm, name='create_farm'),
    path('', farm_page, name='farm_page'),
    path('edit/', edit_farm, name='edit_farm'),
    path("feedback/", feedback, name="feedback"),
]
