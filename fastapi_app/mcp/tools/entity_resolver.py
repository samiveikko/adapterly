"""
Entity Resolver - Resolves project/entity IDs from EntityMapping.

This module provides functions to resolve canonical entity names
to system-specific identifiers using the EntityMapping model.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.systems import (
    EntityMapping,
    EntityType,
    SystemEntityIdentifier,
)

logger = logging.getLogger(__name__)


async def resolve_project_external_id(
    db: AsyncSession,
    account_id: int,
    project_name: str,
    system_alias: str,
) -> str | None:
    """
    Resolve project external ID from EntityMapping.

    Looks up the EntityMapping table to find the system-specific
    identifier for a project based on its canonical name.

    Args:
        db: Database session
        account_id: Account ID to scope the lookup
        project_name: Canonical project name to resolve
        system_alias: System alias to get the identifier for

    Returns:
        The system-specific identifier value, or None if not found
    """
    if not project_name or not system_alias:
        return None

    try:
        # Get entity type for "project"
        entity_type_stmt = select(EntityType).where(EntityType.name == "project")
        entity_type_result = await db.execute(entity_type_stmt)
        entity_type = entity_type_result.scalar_one_or_none()

        if not entity_type:
            logger.debug("No 'project' entity type found")
            return None

        # Look up EntityMapping by canonical name
        # Try exact match first, then case-insensitive
        stmt = (
            select(EntityMapping)
            .options(selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system))
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.entity_type_id == entity_type.id)
            .where(EntityMapping.is_active == True)  # noqa: E712
        )

        # Try exact match first
        exact_stmt = stmt.where(EntityMapping.canonical_name == project_name)
        result = await db.execute(exact_stmt)
        mapping = result.scalar_one_or_none()

        # Fall back to case-insensitive match
        if not mapping:
            ilike_stmt = stmt.where(EntityMapping.canonical_name.ilike(project_name))
            result = await db.execute(ilike_stmt)
            mapping = result.scalar_one_or_none()

        if not mapping:
            logger.debug(f"No EntityMapping found for project '{project_name}'")
            return None

        # Find the identifier for the specified system
        for identifier in mapping.identifiers:
            if identifier.system and identifier.system.alias == system_alias:
                logger.debug(f"Resolved project '{project_name}' -> {system_alias}:{identifier.identifier_value}")
                return identifier.identifier_value

        logger.debug(f"No identifier for system '{system_alias}' in mapping '{project_name}'")
        return None

    except Exception as e:
        logger.error(f"Error resolving project external ID: {e}")
        return None


async def resolve_entity_external_id(
    db: AsyncSession,
    account_id: int,
    canonical_name: str,
    entity_type_name: str,
    system_alias: str,
) -> str | None:
    """
    Resolve any entity type's external ID from EntityMapping.

    Generic version of resolve_project_external_id that works with
    any entity type (project, site, equipment, etc.).

    Args:
        db: Database session
        account_id: Account ID to scope the lookup
        canonical_name: Canonical entity name to resolve
        entity_type_name: Entity type (e.g., "project", "site")
        system_alias: System alias to get the identifier for

    Returns:
        The system-specific identifier value, or None if not found
    """
    if not canonical_name or not entity_type_name or not system_alias:
        return None

    try:
        # Get entity type
        entity_type_stmt = select(EntityType).where(EntityType.name == entity_type_name)
        entity_type_result = await db.execute(entity_type_stmt)
        entity_type = entity_type_result.scalar_one_or_none()

        if not entity_type:
            logger.debug(f"No '{entity_type_name}' entity type found")
            return None

        # Look up EntityMapping by canonical name
        stmt = (
            select(EntityMapping)
            .options(selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system))
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.entity_type_id == entity_type.id)
            .where(EntityMapping.is_active == True)  # noqa: E712
            .where(EntityMapping.canonical_name.ilike(canonical_name))
        )

        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if not mapping:
            logger.debug(f"No EntityMapping found for {entity_type_name} '{canonical_name}'")
            return None

        # Find the identifier for the specified system
        for identifier in mapping.identifiers:
            if identifier.system and identifier.system.alias == system_alias:
                return identifier.identifier_value

        return None

    except Exception as e:
        logger.error(f"Error resolving entity external ID: {e}")
        return None


async def get_project_context(
    db: AsyncSession,
    account_id: int,
    project_name: str,
) -> dict[str, Any] | None:
    """
    Get full project context with all system identifiers.

    Returns a dict with the project's canonical info and all
    system-specific identifiers for auto-injection.

    Args:
        db: Database session
        account_id: Account ID to scope the lookup
        project_name: Canonical project name to resolve

    Returns:
        Dict with project info and identifiers, or None if not found
    """
    if not project_name:
        return None

    try:
        # Get entity type for "project"
        entity_type_stmt = select(EntityType).where(EntityType.name == "project")
        entity_type_result = await db.execute(entity_type_stmt)
        entity_type = entity_type_result.scalar_one_or_none()

        if not entity_type:
            return None

        # Look up EntityMapping
        stmt = (
            select(EntityMapping)
            .options(selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system))
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.entity_type_id == entity_type.id)
            .where(EntityMapping.is_active == True)  # noqa: E712
            .where(EntityMapping.canonical_name.ilike(project_name))
        )

        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if not mapping:
            return None

        # Build identifiers dict keyed by system alias
        identifiers = {}
        for identifier in mapping.identifiers:
            if identifier.system:
                identifiers[identifier.system.alias] = {
                    "id": identifier.identifier_value,
                    "resource_hint": identifier.resource_hint or "",
                    "is_primary": identifier.is_primary,
                }

        return {
            "name": mapping.canonical_name,
            "canonical_id": mapping.canonical_id or "",
            "description": mapping.description or "",
            "mapping_id": mapping.id,
            "identifiers": identifiers,
        }

    except Exception as e:
        logger.error(f"Error getting project context: {e}")
        return None


async def get_project_context_unified(
    db: AsyncSession,
    account_id: int,
    project_name: str | None = None,
    project_external_mappings: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """
    Get unified project context from EntityMapping with fallback to external_mappings.

    This function:
    1. First tries EntityMapping table for rich entity data
    2. Falls back to project.external_mappings JSON if no EntityMapping found
    3. Merges both sources (EntityMapping takes precedence)

    Args:
        db: Database session
        account_id: Account ID to scope the lookup
        project_name: Canonical project name to resolve
        project_external_mappings: Fallback external_mappings dict from Project model

    Returns:
        Dict with project info and identifiers, or None if nothing found
    """
    context = None

    # Try EntityMapping first (rich source)
    if project_name:
        context = await get_project_context(db, account_id, project_name)

    # If EntityMapping found, optionally merge with external_mappings
    if context and project_external_mappings:
        # Add any external_mappings not already in EntityMapping
        for system_alias, external_id in project_external_mappings.items():
            if system_alias not in context["identifiers"]:
                context["identifiers"][system_alias] = {
                    "id": external_id,
                    "resource_hint": "",
                    "is_primary": False,
                    "source": "external_mappings",  # Mark source for debugging
                }
        return context

    # If no EntityMapping but we have external_mappings, build context from it
    if not context and project_external_mappings:
        identifiers = {}
        for system_alias, external_id in project_external_mappings.items():
            identifiers[system_alias] = {
                "id": external_id,
                "resource_hint": "",
                "is_primary": False,
                "source": "external_mappings",
            }

        return {
            "name": project_name or "",
            "canonical_id": "",
            "description": "",
            "mapping_id": None,
            "identifiers": identifiers,
            "source": "external_mappings",
        }

    return context


async def detect_entities_in_data(
    db: AsyncSession,
    account_id: int,
    data: Any,
    system_alias: str,
    entity_type_hint: str | None = None,
) -> dict[str, Any]:
    """
    Detect potential entities in API response data for auto-suggest mappings.

    Analyzes list data from system tool responses to find items that could
    be mapped to EntityMappings. Returns suggestions for:
    - Exact matches with existing mappings
    - Fuzzy matches that need review
    - New items that could be mapped

    Args:
        db: Database session
        account_id: Account ID
        data: Response data (typically a list of items)
        system_alias: The system the data came from
        entity_type_hint: Optional hint for entity type (e.g., "project", "site")

    Returns:
        Dict with detected entities and mapping suggestions
    """
    from difflib import SequenceMatcher

    result = {
        "has_suggestions": False,
        "entity_type": entity_type_hint,
        "suggestions": [],
        "summary": {
            "items_analyzed": 0,
            "potential_mappings": 0,
            "existing_matches": 0,
        },
    }

    # Only analyze if data is a list of dicts
    items = []
    if isinstance(data, list):
        items = [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        # Check common response patterns
        for key in ["data", "items", "results", "content", "records", "projects", "sites"]:
            if key in data and isinstance(data[key], list):
                items = [item for item in data[key] if isinstance(item, dict)]
                # Infer entity type from key
                if not entity_type_hint:
                    if key in ("projects",):
                        entity_type_hint = "project"
                    elif key in ("sites",):
                        entity_type_hint = "site"
                break

    if not items or len(items) == 0:
        return result

    result["summary"]["items_analyzed"] = len(items)

    # Try to detect name and ID fields
    name_fields = ["name", "title", "displayName", "display_name", "projectName", "project_name"]
    id_fields = ["id", "uuid", "guid", "key", "projectId", "project_id"]

    detected_items = []
    for item in items:
        item_name = None
        item_id = None

        for nf in name_fields:
            if nf in item and item[nf]:
                item_name = str(item[nf])
                break

        for idf in id_fields:
            if idf in item and item[idf]:
                item_id = str(item[idf])
                break

        if item_name and item_id:
            detected_items.append({"name": item_name, "id": item_id, "original_item": item})

    if not detected_items:
        return result

    # Get existing mappings for comparison
    try:
        entity_type = None
        if entity_type_hint:
            from ...models.systems import EntityType as ET

            stmt = select(ET).where(ET.name == entity_type_hint)
            et_result = await db.execute(stmt)
            entity_type = et_result.scalar_one_or_none()

        mappings_stmt = (
            select(EntityMapping)
            .options(selectinload(EntityMapping.identifiers).selectinload(SystemEntityIdentifier.system))
            .where(EntityMapping.account_id == account_id)
            .where(EntityMapping.is_active == True)  # noqa: E712
        )
        if entity_type:
            mappings_stmt = mappings_stmt.where(EntityMapping.entity_type_id == entity_type.id)

        mappings_result = await db.execute(mappings_stmt)
        existing_mappings = mappings_result.scalars().all()

        # Build lookup
        mapping_by_name = {m.canonical_name.lower(): m for m in existing_mappings}

        # Analyze detected items
        for item in detected_items[:50]:  # Limit to first 50 items
            item_name_lower = item["name"].lower()

            # Check exact match
            if item_name_lower in mapping_by_name:
                mapping = mapping_by_name[item_name_lower]
                # Check if this system's ID already exists
                has_id = any(i.system and i.system.alias == system_alias for i in mapping.identifiers)
                if has_id:
                    result["summary"]["existing_matches"] += 1
                else:
                    result["suggestions"].append(
                        {
                            "action": "add_identifier",
                            "item_name": item["name"],
                            "item_id": item["id"],
                            "mapping_id": mapping.id,
                            "canonical_name": mapping.canonical_name,
                            "confidence": 1.0,
                        }
                    )
                    result["summary"]["potential_mappings"] += 1
            else:
                # Check fuzzy match
                best_match = None
                best_score = 0.0
                for mapping in existing_mappings:
                    score = SequenceMatcher(None, item_name_lower, mapping.canonical_name.lower()).ratio()
                    if score > best_score and score >= 0.7:
                        best_score = score
                        best_match = mapping

                if best_match:
                    result["suggestions"].append(
                        {
                            "action": "review",
                            "item_name": item["name"],
                            "item_id": item["id"],
                            "similar_to": best_match.canonical_name,
                            "mapping_id": best_match.id,
                            "confidence": round(best_score, 3),
                        }
                    )
                    result["summary"]["potential_mappings"] += 1
                else:
                    # New item - suggest creating mapping
                    result["suggestions"].append(
                        {
                            "action": "create_mapping",
                            "item_name": item["name"],
                            "item_id": item["id"],
                            "entity_type": entity_type_hint or "unknown",
                            "system_alias": system_alias,
                            "confidence": 1.0,
                        }
                    )
                    result["summary"]["potential_mappings"] += 1

        result["has_suggestions"] = len(result["suggestions"]) > 0
        result["entity_type"] = entity_type_hint

    except Exception as e:
        logger.error(f"Error detecting entities in data: {e}")

    return result
