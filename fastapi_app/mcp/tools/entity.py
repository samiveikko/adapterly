"""
MCP Entity Tools - Entity mapping and resolution via MCP.

These tools provide entity mapping capabilities:
- resolve_entity: Resolve canonical entity name to system-specific identifiers
- list_entity_types: List available entity types
- list_entity_mappings: List entity mappings for the account
- suggest_entity_mappings: Analyze fetched data and suggest entity mappings
"""

import logging
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.systems import (
    EntityMapping,
    EntityType,
    IndustryTemplate,
    System,
    SystemEntityIdentifier,
)

logger = logging.getLogger(__name__)


def get_entity_tools() -> list[dict[str, Any]]:
    """Get all entity mapping tools."""
    return [
        # resolve_entity
        {
            "name": "resolve_entity",
            "description": (
                "Resolve a canonical entity name to system-specific identifiers. "
                "For example, resolve 'E18 Turku-Helsinki' (type: project) to get "
                "Infrakit UUID 'abc123', Congrid ID '456', etc. "
                "Use this to find the correct ID for a system before calling its API."
            ),
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "canonical_name": {
                        "type": "string",
                        "description": "The canonical/common name of the entity (e.g., 'E18 Turku-Helsinki', 'ACME Corp')",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": (
                            "Optional entity type to narrow search. "
                            "Values: project, site, user, company, equipment, drawing, material, inspection, "
                            "observation, schedule, contractor, worker, model, ticket, deal, contact, repository"
                        ),
                    },
                    "system": {
                        "type": "string",
                        "description": "Optional system alias to get identifier for (e.g., 'infrakit', 'congrid')",
                    },
                },
                "required": ["canonical_name"],
            },
            "handler": resolve_entity_handler,
        },
        # list_entity_types
        {
            "name": "list_entity_types",
            "description": "List all available entity types (project, site, equipment, etc.).",
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Include inactive entity types (default: false)",
                    },
                },
            },
            "handler": list_entity_types_handler,
        },
        # list_entity_mappings
        {
            "name": "list_entity_mappings",
            "description": (
                "List entity mappings for the account. "
                "Optionally filter by entity type (e.g., 'project', 'site', 'equipment')."
            ),
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "description": "Filter by entity type (e.g., 'project', 'site')"},
                    "search": {"type": "string", "description": "Search term to filter canonical names"},
                    "limit": {"type": "integer", "description": "Maximum number of results (default: 50, max: 200)"},
                },
            },
            "handler": list_entity_mappings_handler,
        },
        # create_entity_mapping
        {
            "name": "create_entity_mapping",
            "description": (
                "Create a new entity mapping to link an entity across systems. "
                "For example, link project 'E18' to Infrakit UUID 'abc123' and Congrid ID '456'."
            ),
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "canonical_name": {
                        "type": "string",
                        "description": "Human-readable name for the entity (e.g., 'E18 Turku-Helsinki')",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Entity type (e.g., 'project', 'site', 'equipment')",
                    },
                    "description": {"type": "string", "description": "Optional description of this entity"},
                    "identifiers": {
                        "type": "object",
                        "description": (
                            "System identifiers as key-value pairs. "
                            "Keys are system aliases, values are identifier objects with 'id' and optional 'resource_hint'. "
                            'Example: {"infrakit": {"id": "abc123"}, "congrid": {"id": "456"}}'
                        ),
                    },
                },
                "required": ["canonical_name", "entity_type", "identifiers"],
            },
            "handler": create_entity_mapping_handler,
        },
        # add_entity_identifier
        {
            "name": "add_entity_identifier",
            "description": (
                "Add a system-specific identifier to an existing entity mapping. "
                "Use this to link an additional system to an existing entity. "
                "For example, add an Infrakit UUID to a project that already has a Congrid ID."
            ),
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "mapping_id": {"type": "integer", "description": "The entity mapping ID to add the identifier to"},
                    "system_alias": {"type": "string", "description": "System alias (e.g., 'infrakit', 'congrid')"},
                    "identifier": {"type": "string", "description": "The system-specific identifier value"},
                    "resource_hint": {
                        "type": "string",
                        "description": "Optional resource type hint for disambiguation",
                    },
                },
                "required": ["mapping_id", "system_alias", "identifier"],
            },
            "handler": add_entity_identifier_handler,
        },
        # list_industries
        {
            "name": "list_industries",
            "description": "List available industry categories (e.g., construction, energy).",
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Include inactive industries (default: false)",
                    },
                },
            },
            "handler": list_industries_handler,
        },
        # list_adapters
        {
            "name": "list_adapters",
            "description": (
                "List available system adapters/integrations. Optionally filter by industry (e.g., 'construction')."
            ),
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Filter by industry name (e.g., 'construction')"},
                    "system_type": {
                        "type": "string",
                        "description": "Filter by system type (e.g., 'project_management', 'quality_management', 'erp')",
                    },
                    "include_inactive": {"type": "boolean", "description": "Include inactive systems (default: false)"},
                },
            },
            "handler": list_adapters_handler,
        },
        # suggest_entity_mappings
        {
            "name": "suggest_entity_mappings",
            "description": (
                "Analyze fetched data from a system and suggest entity mappings. "
                "Use this after fetching a list of items (e.g., projects, sites) from a system "
                "to find matches with existing mappings or suggest new ones. "
                "Returns existing matches where identifiers should be added, and new suggestions "
                "for creating mappings."
            ),
            "tool_type": "entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "system_alias": {
                        "type": "string",
                        "description": "The system alias the data was fetched from (e.g., 'infrakit', 'congrid')",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Entity type (e.g., 'project', 'site', 'equipment')",
                    },
                    "items": {
                        "type": "array",
                        "description": "Array of items fetched from the system",
                        "items": {"type": "object"},
                    },
                    "name_field": {
                        "type": "string",
                        "description": "Field name containing the item name (default: 'name')",
                    },
                    "id_field": {"type": "string", "description": "Field name containing the item ID (default: 'id')"},
                    "confidence_threshold": {
                        "type": "number",
                        "description": "Minimum confidence for fuzzy matches (0.0-1.0, default: 0.7)",
                    },
                },
                "required": ["system_alias", "entity_type", "items"],
            },
            "handler": suggest_entity_mappings_handler,
        },
    ]


# Tool Handlers


async def resolve_entity_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Resolve canonical entity name to system-specific identifiers."""
    db: AsyncSession = ctx.get("db")
    account_id = ctx.get("account_id")

    canonical_name = kwargs.get("canonical_name")
    entity_type = kwargs.get("entity_type")
    target_system = kwargs.get("system")

    if not canonical_name:
        return {"error": "canonical_name is required"}

    try:
        # Build query
        stmt = (
            select(EntityMapping)
            .options(
                selectinload(EntityMapping.entity_type),
                selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system),
            )
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.is_active == True)  # noqa: E712
        )

        # Filter by canonical_name (case-insensitive partial match)
        stmt = stmt.where(
            or_(
                EntityMapping.canonical_name.ilike(canonical_name),
                EntityMapping.canonical_name.ilike(f"%{canonical_name}%"),
            )
        )

        # Filter by entity type if specified
        if entity_type:
            stmt = stmt.join(EntityType).where(EntityType.name == entity_type)

        result = await db.execute(stmt)
        mappings = result.scalars().all()

        if not mappings:
            return {
                "found": False,
                "message": f"No entity mapping found for '{canonical_name}'",
                "suggestion": "Use list_entity_mappings to see available mappings, or create_entity_mapping to create a new one.",
            }

        # Exact match first, then partial matches
        exact_match = None
        for m in mappings:
            if m.canonical_name.lower() == canonical_name.lower():
                exact_match = m
                break

        # Use exact match if found, otherwise first partial match
        primary_mapping = exact_match or mappings[0]

        # Build identifiers dict
        identifiers = {}
        for identifier in primary_mapping.identifiers:
            if identifier.system:
                identifiers[identifier.system.alias] = {
                    "id": identifier.identifier_value,
                    "resource_hint": identifier.resource_hint or "",
                    "is_primary": identifier.is_primary,
                    "system_name": identifier.system.display_name,
                }

        result_data = {
            "found": True,
            "mapping_id": primary_mapping.id,
            "canonical_name": primary_mapping.canonical_name,
            "canonical_id": primary_mapping.canonical_id or "",
            "entity_type": primary_mapping.entity_type.name if primary_mapping.entity_type else "",
            "entity_type_display": primary_mapping.entity_type.display_name if primary_mapping.entity_type else "",
            "description": primary_mapping.description or "",
            "identifiers": identifiers,
        }

        # If specific system requested, also include direct access
        if target_system and target_system in identifiers:
            result_data["requested_system"] = {
                "system": target_system,
                "identifier": identifiers[target_system]["id"],
            }

        # If multiple mappings found, include count
        if len(mappings) > 1 and not exact_match:
            result_data["multiple_matches"] = len(mappings)
            result_data["other_matches"] = [
                {"canonical_name": m.canonical_name, "entity_type": m.entity_type.name if m.entity_type else ""}
                for m in mappings[1:5]  # Include up to 4 other matches
            ]

        return result_data

    except Exception as e:
        logger.error(f"Failed to resolve entity: {e}")
        return {"error": str(e)}


async def list_entity_types_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """List all available entity types."""
    db: AsyncSession = ctx.get("db")
    include_inactive = kwargs.get("include_inactive", False)

    try:
        stmt = select(EntityType)
        if not include_inactive:
            stmt = stmt.where(EntityType.is_active == True)  # noqa: E712
        stmt = stmt.order_by(EntityType.display_name)

        result = await db.execute(stmt)
        entity_types = result.scalars().all()

        types_list = []
        for et in entity_types:
            types_list.append(
                {
                    "name": et.name,
                    "display_name": et.display_name,
                    "description": et.description or "",
                    "icon": et.icon or "",
                    "is_active": et.is_active,
                }
            )

        return {"entity_types": types_list, "count": len(types_list)}

    except Exception as e:
        logger.error(f"Failed to list entity types: {e}")
        return {"error": str(e)}


async def list_entity_mappings_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """List entity mappings for the account."""
    db: AsyncSession = ctx.get("db")
    account_id = ctx.get("account_id")

    entity_type = kwargs.get("entity_type")
    search = kwargs.get("search")
    limit = min(kwargs.get("limit", 50), 200)

    try:
        stmt = (
            select(EntityMapping)
            .options(
                selectinload(EntityMapping.entity_type),
                selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system),
            )
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.is_active == True)  # noqa: E712
        )

        # Filter by entity type
        if entity_type:
            stmt = stmt.join(EntityType).where(EntityType.name == entity_type)

        # Filter by search term
        if search:
            stmt = stmt.where(
                or_(EntityMapping.canonical_name.ilike(f"%{search}%"), EntityMapping.description.ilike(f"%{search}%"))
            )

        stmt = stmt.order_by(EntityMapping.canonical_name).limit(limit)

        result = await db.execute(stmt)
        mappings = result.scalars().all()

        mappings_list = []
        for m in mappings:
            identifiers = {}
            for identifier in m.identifiers:
                if identifier.system:
                    identifiers[identifier.system.alias] = identifier.identifier_value

            mappings_list.append(
                {
                    "mapping_id": m.id,
                    "canonical_name": m.canonical_name,
                    "canonical_id": m.canonical_id or "",
                    "entity_type": m.entity_type.name if m.entity_type else "",
                    "entity_type_display": m.entity_type.display_name if m.entity_type else "",
                    "description": m.description or "",
                    "identifiers": identifiers,
                    "identifier_count": len(identifiers),
                }
            )

        return {"mappings": mappings_list, "count": len(mappings_list)}

    except Exception as e:
        logger.error(f"Failed to list entity mappings: {e}")
        return {"error": str(e)}


async def create_entity_mapping_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Create a new entity mapping."""
    db: AsyncSession = ctx.get("db")
    account_id = ctx.get("account_id")

    canonical_name = kwargs.get("canonical_name")
    entity_type_name = kwargs.get("entity_type")
    description = kwargs.get("description", "")
    identifiers = kwargs.get("identifiers", {})

    if not canonical_name or not entity_type_name:
        return {"error": "canonical_name and entity_type are required"}

    if not identifiers:
        return {"error": "At least one identifier is required"}

    try:
        # Get entity type
        entity_type_stmt = select(EntityType).where(EntityType.name == entity_type_name)
        entity_type_result = await db.execute(entity_type_stmt)
        entity_type = entity_type_result.scalar_one_or_none()

        if not entity_type:
            return {"error": f"Unknown entity type: {entity_type_name}"}

        # Check if mapping already exists
        existing_stmt = (
            select(EntityMapping)
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.entity_type_id == entity_type.id)
            .where(EntityMapping.canonical_name == canonical_name)
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            return {
                "error": f"Entity mapping '{canonical_name}' ({entity_type_name}) already exists",
                "existing_mapping_id": existing.id,
            }

        # Create the mapping
        mapping = EntityMapping(
            account_id=account_id,
            entity_type_id=entity_type.id,
            canonical_name=canonical_name,
            description=description,
        )
        db.add(mapping)
        await db.flush()  # Get the ID

        # Add identifiers
        created_identifiers = {}
        for system_alias, id_data in identifiers.items():
            # Get system
            system_stmt = select(System).where(System.alias == system_alias)
            system_result = await db.execute(system_stmt)
            system = system_result.scalar_one_or_none()

            if not system:
                logger.warning(f"Unknown system alias: {system_alias}")
                continue

            # Handle both dict and string formats
            if isinstance(id_data, dict):
                identifier_value = id_data.get("id", "")
                resource_hint = id_data.get("resource_hint", "")
            else:
                identifier_value = str(id_data)
                resource_hint = ""

            if not identifier_value:
                continue

            identifier = SystemEntityIdentifier(
                mapping_id=mapping.id,
                system_id=system.id,
                identifier_value=identifier_value,
                resource_hint=resource_hint,
            )
            db.add(identifier)
            created_identifiers[system_alias] = identifier_value

        await db.commit()

        return {
            "created": True,
            "mapping_id": mapping.id,
            "canonical_name": canonical_name,
            "entity_type": entity_type_name,
            "description": description,
            "identifiers": created_identifiers,
            "identifier_count": len(created_identifiers),
        }

    except Exception as e:
        logger.error(f"Failed to create entity mapping: {e}")
        await db.rollback()
        return {"error": str(e)}


async def add_entity_identifier_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Add a system-specific identifier to an existing entity mapping."""
    db: AsyncSession = ctx.get("db")
    account_id = ctx.get("account_id")

    mapping_id = kwargs.get("mapping_id")
    system_alias = kwargs.get("system_alias")
    identifier_value = kwargs.get("identifier")
    resource_hint = kwargs.get("resource_hint", "")

    if not mapping_id:
        return {"error": "mapping_id is required"}
    if not system_alias:
        return {"error": "system_alias is required"}
    if not identifier_value:
        return {"error": "identifier is required"}

    try:
        # Get the mapping (ensure it belongs to this account)
        mapping_stmt = (
            select(EntityMapping)
            .options(
                selectinload(EntityMapping.entity_type),
                selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system),
            )
            .where(EntityMapping.id == mapping_id)
            .where(EntityMapping.account_id == account_id)
        )
        result = await db.execute(mapping_stmt)
        mapping = result.scalar_one_or_none()

        if not mapping:
            return {"error": f"Entity mapping {mapping_id} not found or not accessible"}

        # Get the system
        system_stmt = select(System).where(System.alias == system_alias)
        system_result = await db.execute(system_stmt)
        system = system_result.scalar_one_or_none()

        if not system:
            return {"error": f"Unknown system: {system_alias}"}

        # Check if identifier already exists for this system
        for existing in mapping.identifiers:
            if existing.system_id == system.id:
                if existing.identifier_value == identifier_value:
                    return {
                        "added": False,
                        "message": f"Identifier already exists for {system_alias}",
                        "mapping_id": mapping_id,
                        "canonical_name": mapping.canonical_name,
                    }
                else:
                    # Update existing identifier
                    existing.identifier_value = identifier_value
                    if resource_hint:
                        existing.resource_hint = resource_hint
                    await db.commit()
                    return {
                        "updated": True,
                        "mapping_id": mapping_id,
                        "canonical_name": mapping.canonical_name,
                        "system_alias": system_alias,
                        "identifier": identifier_value,
                        "previous_identifier": existing.identifier_value,
                    }

        # Create new identifier
        new_identifier = SystemEntityIdentifier(
            mapping_id=mapping_id,
            system_id=system.id,
            identifier_value=identifier_value,
            resource_hint=resource_hint,
        )
        db.add(new_identifier)
        await db.commit()

        return {
            "added": True,
            "mapping_id": mapping_id,
            "canonical_name": mapping.canonical_name,
            "entity_type": mapping.entity_type.name if mapping.entity_type else "",
            "system_alias": system_alias,
            "identifier": identifier_value,
        }

    except Exception as e:
        logger.error(f"Failed to add entity identifier: {e}")
        await db.rollback()
        return {"error": str(e)}


async def list_industries_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """List available industry categories."""
    db: AsyncSession = ctx.get("db")
    include_inactive = kwargs.get("include_inactive", False)

    try:
        stmt = select(IndustryTemplate).options(selectinload(IndustryTemplate.systems))
        if not include_inactive:
            stmt = stmt.where(IndustryTemplate.is_active == True)  # noqa: E712
        stmt = stmt.order_by(IndustryTemplate.display_name)

        result = await db.execute(stmt)
        industries = result.scalars().all()

        industries_list = []
        for ind in industries:
            active_systems = [s for s in ind.systems if s.is_active]
            industries_list.append(
                {
                    "name": ind.name,
                    "display_name": ind.display_name,
                    "description": ind.description or "",
                    "icon": ind.icon or "",
                    "system_count": len(active_systems),
                    "systems": [{"alias": s.alias, "display_name": s.display_name} for s in active_systems],
                    "is_active": ind.is_active,
                }
            )

        return {"industries": industries_list, "count": len(industries_list)}

    except Exception as e:
        logger.error(f"Failed to list industries: {e}")
        return {"error": str(e)}


async def list_adapters_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """List available system adapters/integrations."""
    db: AsyncSession = ctx.get("db")

    industry = kwargs.get("industry")
    system_type = kwargs.get("system_type")
    include_inactive = kwargs.get("include_inactive", False)

    try:
        stmt = select(System).options(selectinload(System.industry))

        if not include_inactive:
            stmt = stmt.where(System.is_active == True)  # noqa: E712

        # Filter by industry
        if industry:
            stmt = stmt.join(IndustryTemplate).where(IndustryTemplate.name == industry)

        # Filter by system type
        if system_type:
            stmt = stmt.where(System.system_type == system_type)

        stmt = stmt.order_by(System.display_name)

        result = await db.execute(stmt)
        systems = result.scalars().all()

        systems_list = []
        for sys in systems:
            systems_list.append(
                {
                    "alias": sys.alias,
                    "name": sys.name,
                    "display_name": sys.display_name,
                    "description": sys.description or "",
                    "system_type": sys.system_type,
                    "icon": sys.icon or "",
                    "website_url": sys.website_url or "",
                    "industry": sys.industry.name if sys.industry else None,
                    "industry_display": sys.industry.display_name if sys.industry else None,
                    "is_active": sys.is_active,
                }
            )

        return {"adapters": systems_list, "count": len(systems_list)}

    except Exception as e:
        logger.error(f"Failed to list adapters: {e}")
        return {"error": str(e)}


def _fuzzy_match_score(s1: str, s2: str) -> float:
    """
    Calculate fuzzy match score between two strings.

    Uses SequenceMatcher for similarity comparison.
    Returns a score between 0.0 and 1.0.
    """
    if not s1 or not s2:
        return 0.0

    # Normalize strings: lowercase, strip whitespace
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()

    # Exact match
    if s1_norm == s2_norm:
        return 1.0

    # Use SequenceMatcher for fuzzy comparison
    return SequenceMatcher(None, s1_norm, s2_norm).ratio()


def _extract_item_value(item: dict[str, Any], field: str) -> str | None:
    """
    Extract value from item, supporting nested field paths.

    Supports dot notation for nested fields, e.g., "metadata.name".
    """
    if not item or not field:
        return None

    # Handle nested fields with dot notation
    if "." in field:
        parts = field.split(".")
        value = item
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return str(value) if value is not None else None

    value = item.get(field)
    return str(value) if value is not None else None


async def suggest_entity_mappings_handler(ctx: dict[str, Any], **kwargs) -> dict[str, Any]:
    """
    Analyze fetched data and suggest entity mappings.

    Compares items from a system with existing EntityMappings using fuzzy matching.
    Returns:
    - existing_matches: Items that match existing mappings (may need identifier added)
    - new_suggestions: Items that could be new mappings (high confidence matches)
    - no_match: Items with no reasonable match
    """
    db: AsyncSession = ctx.get("db")
    account_id = ctx.get("account_id")

    system_alias = kwargs.get("system_alias")
    entity_type_name = kwargs.get("entity_type")
    items = kwargs.get("items", [])
    name_field = kwargs.get("name_field", "name")
    id_field = kwargs.get("id_field", "id")
    confidence_threshold = kwargs.get("confidence_threshold", 0.7)

    if not system_alias:
        return {"error": "system_alias is required"}
    if not entity_type_name:
        return {"error": "entity_type is required"}
    if not items:
        return {"error": "items array is required and must not be empty"}

    try:
        # Verify system exists
        system_stmt = select(System).where(System.alias == system_alias)
        system_result = await db.execute(system_stmt)
        system = system_result.scalar_one_or_none()

        if not system:
            return {"error": f"Unknown system: {system_alias}"}

        # Get entity type
        entity_type_stmt = select(EntityType).where(EntityType.name == entity_type_name)
        entity_type_result = await db.execute(entity_type_stmt)
        entity_type = entity_type_result.scalar_one_or_none()

        if not entity_type:
            return {"error": f"Unknown entity type: {entity_type_name}"}

        # Get existing mappings for this account and entity type
        mappings_stmt = (
            select(EntityMapping)
            .options(selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system))
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.entity_type_id == entity_type.id)
            .where(EntityMapping.is_active == True)  # noqa: E712
        )
        mappings_result = await db.execute(mappings_stmt)
        existing_mappings = mappings_result.scalars().all()

        # Build lookup for existing mappings
        mapping_lookup: dict[str, EntityMapping] = {}
        for mapping in existing_mappings:
            mapping_lookup[mapping.canonical_name.lower()] = mapping

        existing_matches = []
        new_suggestions = []
        already_mapped = []

        for item in items:
            item_name = _extract_item_value(item, name_field)
            item_id = _extract_item_value(item, id_field)

            if not item_name:
                continue

            # Check for exact match first
            exact_mapping = mapping_lookup.get(item_name.lower())

            if exact_mapping:
                # Check if this system's identifier already exists
                has_identifier = False
                existing_id = None
                for identifier in exact_mapping.identifiers:
                    if identifier.system and identifier.system.alias == system_alias:
                        has_identifier = True
                        existing_id = identifier.identifier_value
                        break

                if has_identifier:
                    # Already fully mapped
                    if existing_id == item_id:
                        already_mapped.append(
                            {
                                "item_name": item_name,
                                "item_id": item_id,
                                "canonical_name": exact_mapping.canonical_name,
                                "mapping_id": exact_mapping.id,
                                "status": "already_mapped",
                            }
                        )
                    else:
                        # ID mismatch - potential conflict
                        already_mapped.append(
                            {
                                "item_name": item_name,
                                "item_id": item_id,
                                "canonical_name": exact_mapping.canonical_name,
                                "mapping_id": exact_mapping.id,
                                "existing_id": existing_id,
                                "status": "id_mismatch",
                                "warning": f"Existing ID '{existing_id}' differs from fetched ID '{item_id}'",
                            }
                        )
                else:
                    # Mapping exists but needs this system's identifier
                    existing_matches.append(
                        {
                            "item_name": item_name,
                            "item_id": item_id,
                            "canonical_name": exact_mapping.canonical_name,
                            "mapping_id": exact_mapping.id,
                            "confidence": 1.0,
                            "match_type": "exact",
                            "action": "add_identifier",
                            "suggested_call": {
                                "tool": "add_entity_identifier",
                                "args": {
                                    "mapping_id": exact_mapping.id,
                                    "system_alias": system_alias,
                                    "identifier": item_id,
                                },
                            },
                        }
                    )
                continue

            # Try fuzzy matching against all existing mappings
            best_match: tuple[EntityMapping, float] | None = None
            for mapping in existing_mappings:
                score = _fuzzy_match_score(item_name, mapping.canonical_name)
                if score >= confidence_threshold:
                    if not best_match or score > best_match[1]:
                        best_match = (mapping, score)

            if best_match:
                mapping, score = best_match

                # Check if this system's identifier already exists
                has_identifier = False
                for identifier in mapping.identifiers:
                    if identifier.system and identifier.system.alias == system_alias:
                        has_identifier = True
                        break

                if has_identifier:
                    # Fuzzy match but already has identifier - possible duplicate
                    new_suggestions.append(
                        {
                            "item_name": item_name,
                            "item_id": item_id,
                            "similar_to": mapping.canonical_name,
                            "mapping_id": mapping.id,
                            "confidence": round(score, 3),
                            "match_type": "fuzzy",
                            "action": "review",
                            "note": f"Similar to existing mapping '{mapping.canonical_name}' which already has a {system_alias} identifier",
                        }
                    )
                else:
                    # Fuzzy match, needs identifier
                    existing_matches.append(
                        {
                            "item_name": item_name,
                            "item_id": item_id,
                            "canonical_name": mapping.canonical_name,
                            "mapping_id": mapping.id,
                            "confidence": round(score, 3),
                            "match_type": "fuzzy",
                            "action": "add_identifier",
                            "note": f"Fuzzy match with '{mapping.canonical_name}'",
                        }
                    )
            else:
                # No match - suggest creating new mapping
                new_suggestions.append(
                    {
                        "item_name": item_name,
                        "item_id": item_id,
                        "confidence": 1.0,  # Confidence in creating new
                        "action": "create_mapping",
                        "suggested_call": {
                            "tool": "create_entity_mapping",
                            "args": {
                                "canonical_name": item_name,
                                "entity_type": entity_type_name,
                                "identifiers": {system_alias: {"id": item_id}},
                            },
                        },
                    }
                )

        return {
            "system_alias": system_alias,
            "entity_type": entity_type_name,
            "items_analyzed": len(items),
            "existing_matches": existing_matches,
            "existing_matches_count": len(existing_matches),
            "new_suggestions": new_suggestions,
            "new_suggestions_count": len(new_suggestions),
            "already_mapped": already_mapped,
            "already_mapped_count": len(already_mapped),
            "summary": {
                "total": len(items),
                "to_add_identifier": len(existing_matches),
                "to_create": len([s for s in new_suggestions if s.get("action") == "create_mapping"]),
                "to_review": len([s for s in new_suggestions if s.get("action") == "review"]),
                "already_complete": len(already_mapped),
            },
        }

    except Exception as e:
        logger.error(f"Failed to suggest entity mappings: {e}")
        return {"error": str(e)}
