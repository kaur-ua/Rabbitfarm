from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_farm, name="create_farm"),
]