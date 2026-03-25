from django.urls import path
from . import views

urlpatterns = [
    path("", views.rabbit_list, name="rabbit_list"),
    path("add/", views.rabbit_create, name="rabbit_create"),
    path("<int:pk>/", views.rabbit_detail, name="rabbit_detail"),
    path("groups/create/", views.create_group, name="create_group"),
]
    



