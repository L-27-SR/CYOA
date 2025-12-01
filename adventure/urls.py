from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("choose_character/", views.choose_character, name="choose_character"),
    path("option/<int:option_id>/", views.follow_option, name="follow_option"),
    path("auth/signup/", views.signup, name="signup"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/token/", views.token_obtain_pair, name="token_obtain_pair"),
    path("api/profile/", views.profile_api, name="profile_api"),
]
