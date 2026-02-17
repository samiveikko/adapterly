from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.utils import get_active_account, get_active_account_user
from apps.systems.api.serializers import (
    EntityMappingCreateSerializer,
    EntityMappingLookupSerializer,
    EntityMappingSerializer,
    EntityTypeSerializer,
    SystemEntityIdentifierCreateSerializer,
    SystemEntityIdentifierSerializer,
)
from apps.systems.models import EntityMapping, EntityType, System, SystemEntityIdentifier


class EntityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for EntityType model - read-only since these are system-defined.

    GET /api/systems/entity-types/ - List all active entity types
    GET /api/systems/entity-types/{id}/ - Get a specific entity type
    """

    serializer_class = EntityTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return EntityType.objects.filter(is_active=True).order_by("display_name")


class EntityMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EntityMapping model.

    GET /api/systems/mappings/ - List all mappings for the active account
    POST /api/systems/mappings/ - Create a new mapping
    GET /api/systems/mappings/{id}/ - Get a specific mapping
    PUT /api/systems/mappings/{id}/ - Update a mapping
    DELETE /api/systems/mappings/{id}/ - Delete a mapping
    POST /api/systems/mappings/{id}/add-identifier/ - Add an identifier to a mapping
    POST /api/systems/mappings/{id}/resolve/ - Get resolved identifiers for a mapping
    POST /api/systems/mappings/lookup/ - Lookup a mapping by system identifier
    """

    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return EntityMappingCreateSerializer
        return EntityMappingSerializer

    def get_queryset(self):
        account = get_active_account(self.request)
        if not account:
            return EntityMapping.objects.none()

        queryset = (
            EntityMapping.objects.filter(account=account)
            .select_related("entity_type")
            .prefetch_related("identifiers__system")
            .order_by("-updated_at")
        )

        # Optional filters
        entity_type = self.request.query_params.get("entity_type")
        if entity_type:
            queryset = queryset.filter(entity_type__name=entity_type)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(canonical_name__icontains=search)

        system = self.request.query_params.get("system")
        if system:
            queryset = queryset.filter(identifiers__system__alias=system).distinct()

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["account"] = get_active_account(self.request)
        return context

    def perform_create(self, serializer):
        account = get_active_account(self.request)
        account_user = get_active_account_user(self.request)

        if not account:
            raise PermissionDenied("No active account found.")
        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can create mappings.")

        serializer.save()

    def perform_update(self, serializer):
        account_user = get_active_account_user(self.request)
        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can update mappings.")
        serializer.save()

    def perform_destroy(self, instance):
        account_user = get_active_account_user(self.request)
        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can delete mappings.")
        instance.delete()

    @action(detail=True, methods=["post"], url_path="add-identifier")
    def add_identifier(self, request, pk=None):
        """
        Add an identifier to an existing mapping.

        POST /api/systems/mappings/{id}/add-identifier/
        {
            "system_alias": "jira",
            "identifier_value": "PROJ-123",
            "resource_hint": "projects",
            "is_primary": false
        }
        """
        mapping = self.get_object()
        account_user = get_active_account_user(request)

        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can modify mappings.")

        serializer = SystemEntityIdentifierCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Resolve system
        system = None
        if data.get("system_id"):
            try:
                system = System.objects.get(id=data["system_id"])
            except System.DoesNotExist:
                return Response(
                    {"error": f"System with id {data['system_id']} not found."}, status=status.HTTP_404_NOT_FOUND
                )
        elif data.get("system_alias"):
            try:
                system = System.objects.get(alias=data["system_alias"])
            except System.DoesNotExist:
                return Response(
                    {"error": f"System with alias '{data['system_alias']}' not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Check for duplicate
        if SystemEntityIdentifier.objects.filter(
            mapping=mapping, system=system, identifier_value=data["identifier_value"]
        ).exists():
            return Response(
                {"error": "This identifier already exists for this mapping and system."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        identifier = SystemEntityIdentifier.objects.create(
            mapping=mapping,
            system=system,
            identifier_value=data["identifier_value"],
            resource_hint=data.get("resource_hint", ""),
            is_primary=data.get("is_primary", False),
        )

        response_serializer = SystemEntityIdentifierSerializer(identifier)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        """
        Get resolved identifiers for a mapping in the format used by the DSL step.

        POST /api/systems/mappings/{id}/resolve/
        {
            "target_systems": ["jira", "salesforce"]  // optional
        }
        """
        mapping = self.get_object()
        target_systems = request.data.get("target_systems", [])

        identifiers_dict = {}
        for identifier in mapping.identifiers.select_related("system"):
            if target_systems and identifier.system.alias not in target_systems:
                continue
            identifiers_dict[identifier.system.alias] = {
                "id": identifier.identifier_value,
                "resource_hint": identifier.resource_hint,
            }

        return Response(
            {
                "mapping_id": mapping.id,
                "canonical_name": mapping.canonical_name,
                "canonical_id": mapping.canonical_id,
                "entity_type": mapping.entity_type.name,
                "identifiers": identifiers_dict,
            }
        )

    @action(detail=False, methods=["post"], url_path="lookup")
    def lookup(self, request):
        """
        Lookup a mapping by system identifier.

        POST /api/systems/mappings/lookup/
        {
            "system_alias": "jira",
            "identifier_value": "PROJ",
            "entity_type": "project"  // optional
        }
        """
        serializer = EntityMappingLookupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        account = get_active_account(request)

        if not account:
            raise PermissionDenied("No active account found.")

        try:
            system = System.objects.get(alias=data["system_alias"])
        except System.DoesNotExist:
            return Response(
                {"error": f"System with alias '{data['system_alias']}' not found."}, status=status.HTTP_404_NOT_FOUND
            )

        queryset = SystemEntityIdentifier.objects.filter(
            mapping__account=account, system=system, identifier_value=data["identifier_value"]
        ).select_related("mapping", "mapping__entity_type")

        if data.get("entity_type"):
            queryset = queryset.filter(mapping__entity_type__name=data["entity_type"])

        identifier = queryset.first()
        if not identifier:
            return Response({"error": "No mapping found for the given identifier."}, status=status.HTTP_404_NOT_FOUND)

        mapping = identifier.mapping
        mapping_serializer = EntityMappingSerializer(mapping)
        return Response(mapping_serializer.data)


class SystemEntityIdentifierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SystemEntityIdentifier model.

    Primarily used for managing individual identifiers.
    """

    serializer_class = SystemEntityIdentifierSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        account = get_active_account(self.request)
        if not account:
            return SystemEntityIdentifier.objects.none()

        return (
            SystemEntityIdentifier.objects.filter(mapping__account=account)
            .select_related("mapping", "system")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        account_user = get_active_account_user(self.request)
        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can create identifiers.")
        serializer.save()

    def perform_update(self, serializer):
        account_user = get_active_account_user(self.request)
        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can update identifiers.")
        serializer.save()

    def perform_destroy(self, instance):
        account_user = get_active_account_user(self.request)
        if not account_user or not account_user.is_admin:
            raise PermissionDenied("Only account admins can delete identifiers.")
        instance.delete()
