from rest_framework import serializers

from apps.systems.models import EntityMapping, EntityType, System, SystemEntityIdentifier


class EntityTypeSerializer(serializers.ModelSerializer):
    """Serializer for EntityType model."""

    class Meta:
        model = EntityType
        fields = ["id", "name", "display_name", "description", "icon", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class SystemEntityIdentifierSerializer(serializers.ModelSerializer):
    """Serializer for SystemEntityIdentifier model."""

    system_alias = serializers.CharField(source="system.alias", read_only=True)
    system_name = serializers.CharField(source="system.display_name", read_only=True)

    class Meta:
        model = SystemEntityIdentifier
        fields = [
            "id",
            "system",
            "system_alias",
            "system_name",
            "identifier_value",
            "resource_hint",
            "is_primary",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SystemEntityIdentifierCreateSerializer(serializers.Serializer):
    """Serializer for creating/adding identifiers to a mapping."""

    system_id = serializers.IntegerField(required=False)
    system_alias = serializers.CharField(required=False)
    identifier_value = serializers.CharField(max_length=500)
    resource_hint = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    is_primary = serializers.BooleanField(default=False)

    def validate(self, data):
        if not data.get("system_id") and not data.get("system_alias"):
            raise serializers.ValidationError("Either 'system_id' or 'system_alias' is required.")
        return data


class EntityMappingSerializer(serializers.ModelSerializer):
    """Serializer for EntityMapping model."""

    entity_type_name = serializers.CharField(source="entity_type.name", read_only=True)
    entity_type_display = serializers.CharField(source="entity_type.display_name", read_only=True)
    identifiers = SystemEntityIdentifierSerializer(many=True, read_only=True)
    identifiers_dict = serializers.SerializerMethodField()

    class Meta:
        model = EntityMapping
        fields = [
            "id",
            "account",
            "entity_type",
            "entity_type_name",
            "entity_type_display",
            "canonical_name",
            "canonical_id",
            "description",
            "is_active",
            "identifiers",
            "identifiers_dict",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "account", "created_at", "updated_at"]

    def get_identifiers_dict(self, obj):
        """Return identifiers as a dict keyed by system alias."""
        return obj.get_identifiers_dict()


class EntityMappingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EntityMapping with identifiers."""

    identifiers = SystemEntityIdentifierCreateSerializer(many=True, required=False, default=[])
    entity_type_name = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = EntityMapping
        fields = [
            "id",
            "entity_type",
            "entity_type_name",
            "canonical_name",
            "canonical_id",
            "description",
            "is_active",
            "identifiers",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        # Allow entity_type_name as alternative to entity_type
        if not data.get("entity_type") and data.get("entity_type_name"):
            try:
                data["entity_type"] = EntityType.objects.get(name=data["entity_type_name"])
            except EntityType.DoesNotExist:
                raise serializers.ValidationError(
                    {"entity_type_name": f"Entity type '{data['entity_type_name']}' not found."}
                )
        elif not data.get("entity_type"):
            raise serializers.ValidationError({"entity_type": "This field is required."})
        return data

    def create(self, validated_data):
        identifiers_data = validated_data.pop("identifiers", [])
        validated_data.pop("entity_type_name", None)

        # Get account from context
        account = self.context.get("account")
        if not account:
            raise serializers.ValidationError("Account is required.")

        validated_data["account"] = account
        mapping = EntityMapping.objects.create(**validated_data)

        # Create identifiers
        for identifier_data in identifiers_data:
            system = self._resolve_system(identifier_data)
            SystemEntityIdentifier.objects.create(
                mapping=mapping,
                system=system,
                identifier_value=identifier_data["identifier_value"],
                resource_hint=identifier_data.get("resource_hint", ""),
                is_primary=identifier_data.get("is_primary", False),
            )

        return mapping

    def update(self, instance, validated_data):
        identifiers_data = validated_data.pop("identifiers", None)
        validated_data.pop("entity_type_name", None)

        # Update mapping fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update identifiers if provided
        if identifiers_data is not None:
            # Remove existing identifiers and create new ones
            instance.identifiers.all().delete()
            for identifier_data in identifiers_data:
                system = self._resolve_system(identifier_data)
                SystemEntityIdentifier.objects.create(
                    mapping=instance,
                    system=system,
                    identifier_value=identifier_data["identifier_value"],
                    resource_hint=identifier_data.get("resource_hint", ""),
                    is_primary=identifier_data.get("is_primary", False),
                )

        return instance

    def _resolve_system(self, identifier_data):
        """Resolve system from system_id or system_alias."""
        if identifier_data.get("system_id"):
            try:
                return System.objects.get(id=identifier_data["system_id"])
            except System.DoesNotExist:
                raise serializers.ValidationError(f"System with id {identifier_data['system_id']} not found.")
        elif identifier_data.get("system_alias"):
            try:
                return System.objects.get(alias=identifier_data["system_alias"])
            except System.DoesNotExist:
                raise serializers.ValidationError(f"System with alias '{identifier_data['system_alias']}' not found.")
        else:
            raise serializers.ValidationError("Either 'system_id' or 'system_alias' is required for identifier.")


class EntityMappingLookupSerializer(serializers.Serializer):
    """Serializer for looking up a mapping by system identifier."""

    system_alias = serializers.CharField(required=True)
    identifier_value = serializers.CharField(required=True)
    entity_type = serializers.CharField(required=False)


class EntityMappingResolveSerializer(serializers.Serializer):
    """Serializer for resolve_mapping DSL step output."""

    mapping_id = serializers.IntegerField()
    canonical_name = serializers.CharField()
    canonical_id = serializers.CharField(allow_blank=True)
    entity_type = serializers.CharField()
    identifiers = serializers.DictField()
