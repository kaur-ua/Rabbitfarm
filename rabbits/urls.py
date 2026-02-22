from django.urls import path
from . import views

urlpatterns = [
    path("", views.rabbit_list, name="rabbit_list"),
]


