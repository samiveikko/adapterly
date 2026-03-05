from django.urls import path

from . import views

app_name = "oauth"

urlpatterns = [
    path("authorize/", views.authorize, name="authorize"),
    path("token/", views.token, name="token"),
]
