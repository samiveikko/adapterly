from django.urls import include, path
from rest_framework import routers

from apps.accounts.api.views import AccountUserViewSet, AccountViewSet

router = routers.DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"account-users", AccountUserViewSet, basename="accountuser")

urlpatterns = [
    path("", include(router.urls)),
]
