from django.urls import path
from .. import views

urlpatterns = [
    path("", views.index, name="index"),
    path("choose_character/", views.choose_character, name="choose_character"),
    path("option/<int:option_id>/", views.follow_option, name="follow_option"),
]
