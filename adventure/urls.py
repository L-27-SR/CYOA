from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("choose_character/", views.choose_character, name="choose_character"),
    path("option/<int:option_id>/", views.follow_option, name="follow_option"),
    # --- New Paths ---
    path("read/", views.read_chapter, name="read_chapter"),
    path("go_back/", views.go_back, name="go_back"),
    path("my_adventures/", views.my_adventures, name="my_adventures"),
    path("resume/<int:session_id>/", views.resume_adventure, name="resume_adventure"),
    # -----------------
    path("auth/signup/", views.signup, name="signup"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/token/", views.token_obtain_pair, name="token_obtain_pair"),
    path("api/profile/", views.profile_api, name="profile_api"),
]
