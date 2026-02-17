from django.urls import include, path
from rest_framework import routers

from apps.systems.api.views import (
    EntityMappingViewSet,
    EntityTypeViewSet,
    SystemEntityIdentifierViewSet,
)

router = routers.DefaultRouter()
router.register(r"entity-types", EntityTypeViewSet, basename="entitytype")
router.register(r"mappings", EntityMappingViewSet, basename="entitymapping")
router.register(r"identifiers", SystemEntityIdentifierViewSet, basename="systementityidentifier")

urlpatterns = [
    path("", include(router.urls)),
]
