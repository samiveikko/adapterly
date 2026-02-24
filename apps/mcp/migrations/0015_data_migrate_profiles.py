"""
Data migration: Move AgentProfiles to project scope.

For each AgentProfile:
- Find projects via its API keys
- If 1 project → assign profile.project = that project
- If multiple projects → clone profile per project, reassign API keys
- If no project → assign to first project in the account (or skip if none)

For each MCPApiKey without a profile:
- Create an auto-profile under the key's project
- Assign the key to that profile
"""

from django.db import migrations


def migrate_profiles_to_projects(apps, schema_editor):
    AgentProfile = apps.get_model("mcp", "AgentProfile")
    MCPApiKey = apps.get_model("mcp", "MCPApiKey")
    Project = apps.get_model("mcp", "Project")

    # Step 1: Assign profiles to projects based on their API keys
    for profile in AgentProfile.objects.filter(project__isnull=True):
        # Find distinct projects from API keys using this profile
        project_ids = list(
            MCPApiKey.objects.filter(profile=profile, project__isnull=False)
            .values_list("project_id", flat=True)
            .distinct()
        )

        if len(project_ids) == 1:
            # Simple case: one project
            profile.project_id = project_ids[0]
            profile.save(update_fields=["project_id"])

        elif len(project_ids) > 1:
            # Multiple projects: assign first, clone for the rest
            profile.project_id = project_ids[0]
            profile.save(update_fields=["project_id"])

            for pid in project_ids[1:]:
                # Clone the profile
                old_id = profile.id
                new_profile = AgentProfile(
                    account_id=profile.account_id,
                    project_id=pid,
                    name=profile.name,
                    description=profile.description,
                    mode=profile.mode,
                    is_active=profile.is_active,
                    include_tools=profile.include_tools or [],
                    exclude_tools=profile.exclude_tools or [],
                )
                new_profile.save()

                # Copy M2M categories
                for cat in profile.allowed_categories.all():
                    new_profile.allowed_categories.add(cat)

                # Reassign API keys in this project to the new profile
                MCPApiKey.objects.filter(
                    profile_id=old_id, project_id=pid
                ).update(profile=new_profile)

        else:
            # No API keys with projects — assign to first project in account
            first_project = Project.objects.filter(
                account_id=profile.account_id
            ).first()
            if first_project:
                profile.project_id = first_project.id
                profile.save(update_fields=["project_id"])
            # If no projects exist at all, leave null (will be caught by finalize)

    # Step 2: Create auto-profiles for API keys without a profile
    for key in MCPApiKey.objects.filter(profile__isnull=True, project__isnull=False):
        auto_name = f"Auto: {key.name}"[:100]

        # Ensure unique name per project
        base_name = auto_name
        counter = 1
        while AgentProfile.objects.filter(
            project_id=key.project_id, name=auto_name
        ).exists():
            auto_name = f"{base_name} ({counter})"[:100]
            counter += 1

        new_profile = AgentProfile(
            account_id=key.account_id,
            project_id=key.project_id,
            name=auto_name,
            description=f"Auto-created from API key '{key.name}'",
            mode=key.mode or "safe",
            is_active=True,
            include_tools=key.allowed_tools or [],
            exclude_tools=key.blocked_tools or [],
        )
        new_profile.save()
        key.profile = new_profile
        key.save(update_fields=["profile_id"])


def reverse_migrate(apps, schema_editor):
    """Remove project assignments from profiles (reverse is lossy for clones)."""
    AgentProfile = apps.get_model("mcp", "AgentProfile")
    AgentProfile.objects.filter(name__startswith="Auto: ").delete()
    AgentProfile.objects.all().update(project=None)


class Migration(migrations.Migration):

    dependencies = [
        ("mcp", "0014_profile_project_fk"),
    ]

    operations = [
        migrations.RunPython(migrate_profiles_to_projects, reverse_migrate),
    ]
