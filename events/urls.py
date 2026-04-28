from django.urls import path
from . import views

urlpatterns = [
     path("edit/<int:rabbit_id>/", views.edit_event, name="edit_event"),
    path("add/", views.add_event, name="add_event"),
    path("group/<int:group_id>/add/", views.create_group_event, name="create_group_event"),
]