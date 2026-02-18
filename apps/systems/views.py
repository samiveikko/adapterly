from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.utils import get_active_account, get_active_account_user

from .forms import AccountSystemForm, InterfaceForm, ResourceForm
from .models import AccountSystem, Action, IndustryTemplate, Interface, Resource, System


def _require_admin_with_system(request, system):
    """Check that the user is an admin and their account has this system configured.

    Returns (active_account, active_account_user) on success, or raises PermissionDenied.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        return None, None, "You do not have an active account."

    if not active_account_user.is_admin:
        return None, None, "You do not have permission to modify shared system definitions."

    if not AccountSystem.objects.filter(account=active_account, system=system).exists():
        return None, None, "Your account does not have this system configured."

    return active_account, active_account_user, None


# System type display names and icons
SYSTEM_TYPE_META = {
    "project_management": {"name": "Project Management", "icon": "kanban"},
    "communication": {"name": "Communication", "icon": "chat-dots"},
    "version_control": {"name": "Version Control", "icon": "git"},
    "ci_cd": {"name": "CI/CD", "icon": "gear-wide-connected"},
    "monitoring": {"name": "Monitoring", "icon": "graph-up"},
    "storage": {"name": "Storage", "icon": "cloud"},
    "quality_management": {"name": "Quality Management", "icon": "clipboard-check"},
    "erp": {"name": "ERP / Finance", "icon": "cash-stack"},
    "bim": {"name": "BIM / Design", "icon": "box"},
    "other": {"name": "Other", "icon": "grid"},
}


@login_required
def systems_dashboard(request):
    """
    Systems page showing:
    - Available systems grouped by category
    - Account's configured systems
    - Option to configure new systems
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "You do not have an active account.")
        return redirect("account_dashboard")

    if not active_account_user.is_admin:
        messages.error(request, "You do not have permission to view the systems page.")
        return redirect("index")

    available_systems = System.objects.filter(is_active=True).select_related("industry").order_by("display_name")

    # Get account's configured systems
    configured_systems = (
        AccountSystem.objects.filter(account=active_account)
        .select_related("system", "system__industry")
        .order_by("system__display_name")
    )

    # Build list of unconfigured systems
    configured_system_ids = set(configured_systems.values_list("system_id", flat=True))
    unconfigured_systems = available_systems.exclude(id__in=configured_system_ids)

    # Group ALL systems by category (mark configured ones)
    # Priority: 1) industry (if set), 2) system_type
    categories = defaultdict(lambda: {"systems": [], "icon": "grid", "priority": 99})

    # Get active industry templates
    industries = {t.id: t for t in IndustryTemplate.objects.filter(is_active=True)}

    for system in available_systems:
        system.is_configured = system.id in configured_system_ids
        if system.industry_id and system.industry_id in industries:
            # Use industry category
            industry = industries[system.industry_id]
            cat_key = f"industry_{industry.id}"
            categories[cat_key]["name"] = industry.display_name
            categories[cat_key]["icon"] = industry.icon or "building"
            categories[cat_key]["priority"] = 1  # Industry categories first
            categories[cat_key]["systems"].append(system)
        else:
            # Use system_type category
            cat_key = f"type_{system.system_type}"
            meta = SYSTEM_TYPE_META.get(system.system_type, {"name": system.system_type, "icon": "grid"})
            categories[cat_key]["name"] = meta["name"]
            categories[cat_key]["icon"] = meta["icon"]
            categories[cat_key]["priority"] = 10  # Type categories after industries
            categories[cat_key]["systems"].append(system)

    # Convert dict to list and sort by priority and name
    sorted_categories = sorted(
        [{"key": k, **v} for k, v in categories.items()], key=lambda x: (x["priority"], x["name"])
    )

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "available_systems": available_systems,
        "configured_systems": configured_systems,
        "unconfigured_systems": unconfigured_systems,
        "system_categories": sorted_categories,
        "total_unconfigured": unconfigured_systems.count(),
    }

    return render(request, "systems/dashboard.html", context)


@login_required
def configure_system(request, system_id):
    """
    System configuration page.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        messages.error(request, "You do not have permission to configure systems.")
        return redirect("systems_dashboard")

    try:
        system = System.objects.get(id=system_id, is_active=True)
    except System.DoesNotExist:
        messages.error(request, "System not found.")
        return redirect("systems_dashboard")

    # Get or create AccountSystem
    account_system, created = AccountSystem.objects.get_or_create(account=active_account, system=system)

    if request.method == "POST":
        form = AccountSystemForm(request.POST, instance=account_system)
        if form.is_valid():
            form.save()
            messages.success(request, f"System {system.display_name} configured successfully.")
            return redirect("systems_dashboard")
        else:
            # Show validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AccountSystemForm(instance=account_system)

    # Determine required auth fields based on interface configuration
    auth_fields = _get_auth_fields_for_system(system)

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "system": system,
        "account_system": account_system,
        "form": form,
        "auth_fields": auth_fields,
    }

    return render(request, "systems/configure.html", context)


def _get_auth_fields_for_system(system):
    """
    Determine which authentication fields are needed based on interface auth config.
    """
    from apps.systems.models import Interface

    interfaces = Interface.objects.filter(system=system)

    if not interfaces.exists():
        # No interfaces - show generic fields
        return {
            "username": {"label": "Username", "help": "System username (if required)", "type": "text"},
            "password": {"label": "Password", "help": "System password (if required)", "type": "password"},
            "api_key": {"label": "API Key", "help": "System API key (if required)", "type": "text"},
            "token": {"label": "Bearer Token", "help": "System Bearer token (if required)", "type": "text"},
        }

    # Check auth types across all interfaces
    auth_types = set()
    requires_browser = False

    for interface in interfaces:
        auth = interface.auth or {}
        auth_type = auth.get("type", "")
        if auth_type:
            auth_types.add(auth_type)
        if interface.requires_browser:
            requires_browser = True

    # Simplify based on auth type
    fields = {}

    if "oauth2_password" in auth_types:
        fields["username"] = {
            "label": "Email / Username",
            "help": "Your login email or username",
            "type": "text",
            "required": True,
        }
        fields["password"] = {"label": "Password", "help": "Your login password", "type": "password", "required": True}

    elif "oauth2_client" in auth_types or "oauth2" in auth_types:
        fields["client_id"] = {"label": "Client ID", "help": "OAuth Client ID", "type": "text", "required": True}
        fields["client_secret"] = {
            "label": "Client Secret",
            "help": "OAuth Client Secret",
            "type": "password",
            "required": True,
        }

    elif "api_key" in auth_types:
        fields["api_key"] = {"label": "API Key", "help": "Your API key", "type": "text", "required": True}

    elif "bearer" in auth_types or "token" in auth_types:
        fields["token"] = {
            "label": "Bearer Token",
            "help": "Your authentication token",
            "type": "text",
            "required": True,
        }

    elif "basic" in auth_types:
        fields["username"] = {"label": "Username", "help": "Your username", "type": "text", "required": True}
        fields["password"] = {"label": "Password", "help": "Your password", "type": "password", "required": True}

    if requires_browser:
        fields["session_cookie"] = {
            "label": "Session Cookie",
            "help": "Browser session cookie (copy from DevTools)",
            "type": "textarea",
        }
        fields["csrf_token"] = {"label": "CSRF Token", "help": "CSRF token from browser", "type": "text"}

    # If no specific auth type found, show common fields
    if not fields:
        fields = {
            "username": {"label": "Username", "help": "System username", "type": "text"},
            "password": {"label": "Password", "help": "System password", "type": "password"},
            "api_key": {"label": "API Key", "help": "System API key", "type": "text"},
        }

    return fields


@login_required
@require_POST
def test_system_connection(request, system_id):
    """
    Test system connection.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "You do not have permission to test systems."}, status=403)

    try:
        account_system = AccountSystem.objects.select_related("system").get(account=active_account, system_id=system_id)
    except AccountSystem.DoesNotExist:
        return JsonResponse({"error": "System configuration not found."}, status=404)

    # Test the actual connection
    from .services import test_system_connection as do_test_connection

    success, message = do_test_connection(account_system)

    if success:
        account_system.mark_verified()
        return JsonResponse(
            {"success": True, "message": f"Connection to {account_system.system.display_name} successful! {message}"}
        )
    else:
        account_system.mark_error(message)
        return JsonResponse({"success": False, "message": message})


@login_required
@require_POST
def toggle_system_status(request, system_id):
    """
    Toggle system enabled/disabled status.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "You do not have permission to change system status."}, status=403)

    try:
        account_system = AccountSystem.objects.get(account=active_account, system_id=system_id)

        account_system.is_enabled = not account_system.is_enabled
        account_system.save()

        status_text = "enabled" if account_system.is_enabled else "disabled"

        return JsonResponse(
            {
                "success": True,
                "message": f"System {account_system.system.display_name} is now {status_text}.",
                "is_enabled": account_system.is_enabled,
            }
        )

    except AccountSystem.DoesNotExist:
        return JsonResponse({"error": "System configuration not found."}, status=404)


@login_required
@require_POST
def delete_system_config(request, system_id):
    """
    Delete system configuration entirely.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "You do not have permission to delete system configurations."}, status=403)

    try:
        account_system = AccountSystem.objects.get(account=active_account, system_id=system_id)

        system_name = account_system.system.display_name
        account_system.delete()

        return JsonResponse({"success": True, "message": f"System configuration {system_name} deleted successfully."})

    except AccountSystem.DoesNotExist:
        return JsonResponse({"error": "System configuration not found."}, status=404)


@login_required
def test_action(request, action_id):
    """
    Test an action with sample parameters.
    Allows GET (show form) and POST (execute test).
    Uses direct HTTP calls to test the API action.
    """
    import json

    import requests

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        if request.method == "POST":
            return JsonResponse({"error": "You do not have permission to test actions."}, status=403)
        messages.error(request, "You do not have permission to test actions.")
        return redirect("systems_dashboard")

    try:
        action = Action.objects.select_related("resource__interface__system").get(id=action_id)
    except Action.DoesNotExist:
        if request.method == "POST":
            return JsonResponse({"error": "Action not found."}, status=404)
        messages.error(request, "Action not found.")
        return redirect("systems_dashboard")

    system = action.resource.interface.system
    interface = action.resource.interface
    resource = action.resource

    # Check if system is configured for this account
    try:
        account_system = AccountSystem.objects.get(account=active_account, system=system, is_enabled=True)
    except AccountSystem.DoesNotExist:
        if request.method == "POST":
            return JsonResponse(
                {"error": f"System {system.display_name} is not configured or enabled for this account."}, status=400
            )
        messages.error(request, f"System {system.display_name} must be configured first.")
        return redirect("configure_system", system_id=system.id)

    if request.method == "POST":
        # Execute the test
        try:
            # Get test parameters from POST data
            test_params = {}
            if request.POST.get("params"):
                try:
                    test_params = json.loads(request.POST.get("params", "{}"))
                except json.JSONDecodeError as e:
                    return JsonResponse({"success": False, "error": f"Invalid JSON parameters: {str(e)}"}, status=400)

            # Get test body for write operations (POST, PUT, PATCH)
            test_body = {}
            if request.POST.get("body"):
                try:
                    test_body = json.loads(request.POST.get("body", "{}"))
                except json.JSONDecodeError as e:
                    return JsonResponse({"success": False, "error": f"Invalid JSON body: {str(e)}"}, status=400)

            # Get authentication headers from account_system
            auth_headers = account_system.get_auth_headers()
            if not auth_headers:
                return JsonResponse(
                    {"success": False, "error": "Not authenticated. Please configure credentials."}, status=400
                )

            # Build the request URL
            path = action.path or ""
            # Substitute path parameters
            for key, value in list(test_params.items()):
                placeholder = f"{{{key}}}"
                if placeholder in path:
                    path = path.replace(placeholder, str(value))
                    del test_params[key]

            base_url = interface.base_url.rstrip("/")
            url = f"{base_url}/{path.lstrip('/')}"

            # Determine HTTP method
            method = (action.method or "GET").upper()

            # Merge headers
            headers = {**(action.headers or {}), **auth_headers}
            if method in ("POST", "PUT", "PATCH") and "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"

            # Execute the request
            if method in ("POST", "PUT", "PATCH"):
                response = requests.request(
                    method=method, url=url, json=test_body or test_params, headers=headers, timeout=30
                )
            else:
                response = requests.request(method=method, url=url, params=test_params, headers=headers, timeout=30)

            # Parse response
            try:
                result = response.json()
            except Exception:
                result = {"text": response.text}

            if response.status_code >= 400:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "status_code": response.status_code,
                        "result": result,
                    }
                )

            # Truncate large responses for display
            result_preview = result
            if isinstance(result, list) and len(result) > 5:
                result_preview = result[:5]
                result_preview.append(f"... and {len(result) - 5} more items")

            return JsonResponse(
                {
                    "success": True,
                    "message": "Action executed successfully",
                    "status_code": response.status_code,
                    "result": result_preview,
                    "result_count": len(result) if isinstance(result, list) else None,
                    "result_type": type(result).__name__,
                }
            )

        except requests.exceptions.Timeout:
            return JsonResponse(
                {"success": False, "error": "Request timed out after 30 seconds", "error_type": "Timeout"}, status=504
            )
        except requests.exceptions.RequestException as e:
            return JsonResponse({"success": False, "error": str(e), "error_type": type(e).__name__}, status=500)
        except Exception as e:
            import traceback

            error_details = traceback.format_exc()

            return JsonResponse(
                {"success": False, "error": str(e), "error_type": type(e).__name__, "traceback": error_details},
                status=500,
            )

    # GET request - show test form
    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "action": action,
        "system": system,
        "interface": interface,
        "resource": resource,
        "account_system": account_system,
        "parameters_schema": action.parameters_schema,
        "examples": action.examples or [],
    }

    return render(request, "systems/test_action.html", context)


# Interface CRUD
@login_required
def interfaces_list(request, system_id):
    active_account = get_active_account(request)
    if not active_account:
        messages.error(request, "You do not have an active account.")
        return redirect("account_dashboard")
    system = get_object_or_404(System, id=system_id, is_active=True)
    if not AccountSystem.objects.filter(account=active_account, system=system).exists():
        messages.error(request, "Your account does not have this system configured.")
        return redirect("systems_dashboard")
    items = Interface.objects.filter(system=system).order_by("name")
    return render(
        request,
        "systems/interfaces_list.html",
        {
            "active_account": active_account,
            "system": system,
            "items": items,
        },
    )


@login_required
def interface_create(request, system_id):
    system = get_object_or_404(System, id=system_id, is_active=True)
    active_account, active_account_user, error = _require_admin_with_system(request, system)
    if error:
        messages.error(request, error)
        return redirect("systems_dashboard")

    if request.method == "POST":
        form = InterfaceForm(request.POST)
        if form.is_valid():
            interface = form.save(commit=False)
            interface.system = system
            interface.save()
            messages.success(request, "Interface created.")
            return redirect("interfaces_list", system_id=system.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InterfaceForm()

    return render(request, "systems/interface_form.html", {"system": system, "form": form})


@login_required
def interface_edit(request, interface_id):
    interface = get_object_or_404(Interface, id=interface_id)
    system = interface.system
    active_account, active_account_user, error = _require_admin_with_system(request, system)
    if error:
        messages.error(request, error)
        return redirect("systems_dashboard")

    if request.method == "POST":
        form = InterfaceForm(request.POST, instance=interface)
        if form.is_valid():
            form.save()
            messages.success(request, "Interface updated.")
            return redirect("interfaces_list", system_id=system.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InterfaceForm(instance=interface)

    return render(request, "systems/interface_form.html", {"system": system, "item": interface, "form": form})


@login_required
@require_POST
def interface_delete(request, interface_id):
    interface = get_object_or_404(Interface, id=interface_id)
    active_account, active_account_user, error = _require_admin_with_system(request, interface.system)
    if error:
        return JsonResponse({"error": error}, status=403)

    system_id = interface.system.id
    interface_name = interface.name
    interface.delete()

    messages.success(request, f'Interface "{interface_name}" deleted successfully.')
    return JsonResponse({"success": True, "redirect": redirect("interfaces_list", system_id=system_id).url})


# Resource CRUD
@login_required
def resources_list(request, system_id):
    active_account = get_active_account(request)
    if not active_account:
        messages.error(request, "You do not have an active account.")
        return redirect("account_dashboard")
    system = get_object_or_404(System, id=system_id, is_active=True)
    if not AccountSystem.objects.filter(account=active_account, system=system).exists():
        messages.error(request, "Your account does not have this system configured.")
        return redirect("systems_dashboard")
    items = Resource.objects.filter(interface__system=system).select_related("interface").order_by("name")
    interfaces = Interface.objects.filter(system=system).order_by("name")
    return render(
        request,
        "systems/resources_list.html",
        {
            "active_account": active_account,
            "system": system,
            "items": items,
            "interfaces": interfaces,
        },
    )


@login_required
def resource_create(request, system_id):
    system = get_object_or_404(System, id=system_id, is_active=True)
    active_account, active_account_user, error = _require_admin_with_system(request, system)
    if error:
        messages.error(request, error)
        return redirect("systems_dashboard")

    if request.method == "POST":
        form = ResourceForm(request.POST, system=system)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource created.")
            return redirect("resources_list", system_id=system.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ResourceForm(system=system)

    return render(request, "systems/resource_form.html", {"system": system, "form": form})


@login_required
def resource_edit(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    system = resource.interface.system
    active_account, active_account_user, error = _require_admin_with_system(request, system)
    if error:
        messages.error(request, error)
        return redirect("systems_dashboard")

    if request.method == "POST":
        form = ResourceForm(request.POST, instance=resource, system=system)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated.")
            return redirect("resources_list", system_id=system.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ResourceForm(instance=resource, system=system)

    return render(request, "systems/resource_form.html", {"system": system, "item": resource, "form": form})


@login_required
@require_POST
def resource_delete(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    active_account, active_account_user, error = _require_admin_with_system(request, resource.interface.system)
    if error:
        return JsonResponse({"error": error}, status=403)

    system_id = resource.interface.system.id
    resource_name = resource.name
    resource.delete()

    messages.success(request, f'Resource "{resource_name}" deleted successfully.')
    return JsonResponse({"success": True, "redirect": redirect("resources_list", system_id=system_id).url})


# Action CRUD
@login_required
def actions_list(request, resource_id):
    active_account = get_active_account(request)
    if not active_account:
        messages.error(request, "You do not have an active account.")
        return redirect("account_dashboard")
    resource = get_object_or_404(Resource, id=resource_id)
    system = resource.interface.system
    if not AccountSystem.objects.filter(account=active_account, system=system).exists():
        messages.error(request, "Your account does not have this system configured.")
        return redirect("systems_dashboard")
    items = Action.objects.filter(resource=resource).order_by("name")
    return render(
        request,
        "systems/actions_list.html",
        {
            "active_account": active_account,
            "resource": resource,
            "system": system,
            "items": items,
        },
    )


@login_required
def action_create(request, resource_id):
    import json
    import re

    resource = get_object_or_404(Resource, id=resource_id)
    active_account, active_account_user, error = _require_admin_with_system(request, resource.interface.system)
    if error:
        messages.error(request, error)
        return redirect("systems_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        alias = request.POST.get("alias", "").strip()
        description = request.POST.get("description", "")
        method = request.POST.get("method", "GET")
        path = request.POST.get("path", "")

        # Validation
        errors_list = []

        # Name validation
        if not name:
            errors_list.append("Name is required")
        elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
            errors_list.append("Name must start with a letter and contain only letters, numbers, underscores, hyphens")

        # Path validation
        if path and not path.startswith("/"):
            errors_list.append("Path must start with /")

        # Method validation
        if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            errors_list.append("Invalid HTTP method")

        # JSON parsing
        try:
            headers = json.loads(request.POST.get("headers") or "{}")
            if not isinstance(headers, dict):
                errors_list.append("Headers must be a JSON object")
        except json.JSONDecodeError as e:
            errors_list.append(f"Headers JSON error: {e}")
            headers = {}

        try:
            parameters_schema = json.loads(request.POST.get("parameters_schema") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Parameters schema JSON error: {e}")
            parameters_schema = {}

        try:
            output_schema = json.loads(request.POST.get("output_schema") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Output schema JSON error: {e}")
            output_schema = {}

        try:
            pagination = json.loads(request.POST.get("pagination") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Pagination JSON error: {e}")
            pagination = {}

        try:
            errors_json = json.loads(request.POST.get("errors") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Errors JSON error: {e}")
            errors_json = {}

        try:
            examples = json.loads(request.POST.get("examples") or "[]")
            if not isinstance(examples, list):
                errors_list.append("Examples must be a JSON array")
        except json.JSONDecodeError as e:
            errors_list.append(f"Examples JSON error: {e}")
            examples = []

        if errors_list:
            for error in errors_list:
                messages.error(request, error)
            context = {
                "resource": resource,
                "name": name,
                "alias": alias,
                "description": description,
                "method": method,
                "path": path,
                "headers_json": request.POST.get("headers", "{}"),
                "parameters_schema_json": request.POST.get("parameters_schema", "{}"),
                "output_schema_json": request.POST.get("output_schema", "{}"),
                "pagination_json": request.POST.get("pagination", "{}"),
                "errors_json": request.POST.get("errors", "{}"),
                "examples_json": request.POST.get("examples", "[]"),
            }
            return render(request, "systems/action_form.html", context)

        Action.objects.create(
            resource=resource,
            name=name,
            alias=alias or name,
            description=description,
            method=method,
            path=path,
            headers=headers,
            parameters_schema=parameters_schema,
            output_schema=output_schema,
            pagination=pagination,
            errors=errors_json,
            examples=examples,
        )
        messages.success(request, "Action created.")
        return redirect("actions_list", resource_id=resource.id)

    context = {
        "resource": resource,
        "headers_json": "{}",
        "parameters_schema_json": "{}",
        "output_schema_json": "{}",
        "pagination_json": "{}",
        "errors_json": "{}",
        "examples_json": "[]",
    }
    return render(request, "systems/action_form.html", context)


@login_required
def action_edit(request, action_id):
    import json
    import re

    action = get_object_or_404(Action, id=action_id)
    resource = action.resource
    active_account, active_account_user, error = _require_admin_with_system(request, resource.interface.system)
    if error:
        messages.error(request, error)
        return redirect("systems_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        alias = request.POST.get("alias", "").strip()
        description = request.POST.get("description", "")
        method = request.POST.get("method", "GET")
        path = request.POST.get("path", "")

        # Validation
        errors_list = []

        # Name validation
        if not name:
            errors_list.append("Name is required")
        elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
            errors_list.append("Name must start with a letter and contain only letters, numbers, underscores, hyphens")

        # Path validation
        if path and not path.startswith("/"):
            errors_list.append("Path must start with /")

        # Method validation
        if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            errors_list.append("Invalid HTTP method")

        # JSON parsing
        try:
            headers = json.loads(request.POST.get("headers") or "{}")
            if not isinstance(headers, dict):
                errors_list.append("Headers must be a JSON object")
        except json.JSONDecodeError as e:
            errors_list.append(f"Headers JSON error: {e}")
            headers = {}

        try:
            parameters_schema = json.loads(request.POST.get("parameters_schema") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Parameters schema JSON error: {e}")
            parameters_schema = {}

        try:
            output_schema = json.loads(request.POST.get("output_schema") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Output schema JSON error: {e}")
            output_schema = {}

        try:
            pagination = json.loads(request.POST.get("pagination") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Pagination JSON error: {e}")
            pagination = {}

        try:
            errors_json = json.loads(request.POST.get("errors") or "{}")
        except json.JSONDecodeError as e:
            errors_list.append(f"Errors JSON error: {e}")
            errors_json = {}

        try:
            examples = json.loads(request.POST.get("examples") or "[]")
            if not isinstance(examples, list):
                errors_list.append("Examples must be a JSON array")
        except json.JSONDecodeError as e:
            errors_list.append(f"Examples JSON error: {e}")
            examples = []

        if errors_list:
            for error in errors_list:
                messages.error(request, error)
            context = {
                "resource": resource,
                "item": action,
                "headers_json": request.POST.get("headers", "{}"),
                "parameters_schema_json": request.POST.get("parameters_schema", "{}"),
                "output_schema_json": request.POST.get("output_schema", "{}"),
                "pagination_json": request.POST.get("pagination", "{}"),
                "errors_json": request.POST.get("errors", "{}"),
                "examples_json": request.POST.get("examples", "[]"),
            }
            return render(request, "systems/action_form.html", context)

        action.name = name
        action.alias = alias or name
        action.description = description
        action.method = method
        action.path = path
        action.headers = headers
        action.parameters_schema = parameters_schema
        action.output_schema = output_schema
        action.pagination = pagination
        action.errors = errors_json
        action.examples = examples
        action.save()
        messages.success(request, "Action updated.")
        return redirect("actions_list", resource_id=resource.id)

    context = {
        "resource": resource,
        "item": action,
        "headers_json": json.dumps(action.headers, indent=2) if action.headers else "{}",
        "parameters_schema_json": json.dumps(action.parameters_schema, indent=2) if action.parameters_schema else "{}",
        "output_schema_json": json.dumps(action.output_schema, indent=2) if action.output_schema else "{}",
        "pagination_json": json.dumps(action.pagination, indent=2) if action.pagination else "{}",
        "errors_json": json.dumps(action.errors, indent=2) if action.errors else "{}",
        "examples_json": json.dumps(action.examples, indent=2) if action.examples else "[]",
    }
    return render(request, "systems/action_form.html", context)


@login_required
@require_POST
def action_delete(request, action_id):
    action = get_object_or_404(Action, id=action_id)
    active_account, active_account_user, error = _require_admin_with_system(request, action.resource.interface.system)
    if error:
        return JsonResponse({"error": error}, status=403)
    resource_id = action.resource.id
    action_name = action.name
    action.delete()

    messages.success(request, f'Action "{action_name}" deleted successfully.')
    return JsonResponse({"success": True, "redirect": redirect("actions_list", resource_id=resource_id).url})


# =============================================================================
# Adapter Generator Views
# =============================================================================


@login_required
def adapter_generator(request):
    """
    Adapter Generator page - generate System adapters from various sources.
    """
    import json

    from apps.systems.adapter_generator import AdapterGenerator

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "You do not have an active account.")
        return redirect("account_dashboard")

    if not active_account_user.is_admin:
        messages.error(request, "Only admins can use the adapter generator.")
        return redirect("systems_dashboard")

    result = None
    error = None

    if request.method == "POST":
        source_type = request.POST.get("source_type")
        generator = AdapterGenerator(account_id=active_account.id)

        try:
            if source_type == "openapi_url":
                spec_url = request.POST.get("openapi_url", "").strip()
                if not spec_url:
                    raise ValueError("OpenAPI URL is required")
                system = generator.from_openapi(
                    spec_url=spec_url,
                    system_name=request.POST.get("system_name") or None,
                    system_alias=request.POST.get("system_alias") or None,
                )

            elif source_type == "openapi_file":
                if "openapi_file" not in request.FILES:
                    raise ValueError("OpenAPI file is required")
                file = request.FILES["openapi_file"]
                content = file.read().decode("utf-8")
                if file.name.endswith((".yaml", ".yml")):
                    import yaml

                    spec = yaml.safe_load(content)
                else:
                    spec = json.loads(content)
                system = generator.from_openapi(
                    spec=spec,
                    system_name=request.POST.get("system_name") or None,
                    system_alias=request.POST.get("system_alias") or None,
                )

            elif source_type == "documentation":
                docs_url = request.POST.get("docs_url", "").strip()
                system_name = request.POST.get("system_name", "").strip()
                if not docs_url:
                    raise ValueError("Documentation URL is required")
                if not system_name:
                    raise ValueError("System name is required for documentation analysis")
                system = generator.from_documentation(
                    url=docs_url,
                    system_name=system_name,
                    system_alias=request.POST.get("system_alias") or None,
                    base_url=request.POST.get("base_url") or None,
                )

            elif source_type == "har":
                if "har_file" not in request.FILES:
                    raise ValueError("HAR file is required")
                system_name = request.POST.get("system_name", "").strip()
                if not system_name:
                    raise ValueError("System name is required for HAR analysis")
                file = request.FILES["har_file"]
                har_data = json.loads(file.read().decode("utf-8"))
                system = generator.from_har(
                    har_data=har_data,
                    system_name=system_name,
                    system_alias=request.POST.get("system_alias") or None,
                    filter_domain=request.POST.get("filter_domain") or None,
                )
            else:
                raise ValueError("Invalid source type")

            # Check if user wants to save
            if request.POST.get("action") == "save":
                db_system = generator.save_to_database(system, active_account.id)
                messages.success(request, f"System '{db_system.display_name}' created successfully!")
                return redirect("interfaces_list", system_id=db_system.id)

            # Return preview
            result = {"system": generator.to_dict(system), "json": generator.to_json(system)}

        except Exception as e:
            error = str(e)

    context = {
        "active_account": active_account,
        "result": result,
        "error": error,
    }
    return render(request, "systems/adapter_generator.html", context)


@login_required
@require_POST
def adapter_generator_api(request):
    """
    API endpoint for adapter generator.

    POST /systems/api/generate-adapter/

    Body (JSON):
        {
            "source_type": "openapi_url" | "openapi_spec" | "documentation" | "har",
            "openapi_url": "https://...",
            "openapi_spec": {...},
            "docs_url": "https://...",
            "docs_text": "...",
            "har_data": {...},
            "system_name": "Optional name",
            "system_alias": "optional_alias",
            "base_url": "https://...",
            "filter_domain": "api.example.com",
            "save": false
        }

    Returns:
        {
            "success": true,
            "system": {...},
            "system_id": 123  // if saved
        }
    """
    import json

    from apps.systems.adapter_generator import AdapterGenerator

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        return JsonResponse({"error": "No active account"}, status=400)

    if not active_account_user.is_admin:
        return JsonResponse({"error": "Admin access required"}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    source_type = data.get("source_type")
    generator = AdapterGenerator(account_id=active_account.id)

    try:
        if source_type == "openapi_url":
            system = generator.from_openapi(
                spec_url=data.get("openapi_url"),
                system_name=data.get("system_name"),
                system_alias=data.get("system_alias"),
            )
        elif source_type == "openapi_spec":
            system = generator.from_openapi(
                spec=data.get("openapi_spec"),
                system_name=data.get("system_name"),
                system_alias=data.get("system_alias"),
            )
        elif source_type == "documentation":
            system = generator.from_documentation(
                url=data.get("docs_url"),
                text=data.get("docs_text"),
                system_name=data.get("system_name", "Unknown API"),
                system_alias=data.get("system_alias"),
                base_url=data.get("base_url"),
            )
        elif source_type == "har":
            system = generator.from_har(
                har_data=data.get("har_data"),
                system_name=data.get("system_name", "Unknown API"),
                system_alias=data.get("system_alias"),
                filter_domain=data.get("filter_domain"),
            )
        else:
            return JsonResponse({"error": "Invalid source_type"}, status=400)

        result = {"success": True, "system": generator.to_dict(system)}

        # Save if requested
        if data.get("save"):
            db_system = generator.save_to_database(system, active_account.id)
            result["system_id"] = db_system.id
            result["message"] = f"System '{db_system.display_name}' saved"

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =============================================================================
# Entity Mapping Views
# =============================================================================


@login_required
def mappings_list(request):
    """
    Entity mappings list and management page.
    Shows all mappings for the active account with filtering options.
    """
    from .models import EntityMapping, EntityType, System

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "You need an active account to view mappings.")
        return redirect("account_dashboard")

    if not active_account_user.is_admin:
        messages.error(request, "Only admins can manage entity mappings.")
        return redirect("systems_dashboard")

    # Get filter parameters
    entity_type_filter = request.GET.get("entity_type", "")
    system_filter = request.GET.get("system", "")
    search_query = request.GET.get("search", "")

    # Base queryset
    mappings = (
        EntityMapping.objects.filter(account=active_account)
        .select_related("entity_type")
        .prefetch_related("identifiers__system")
        .order_by("-updated_at")
    )

    # Apply filters
    if entity_type_filter:
        mappings = mappings.filter(entity_type__name=entity_type_filter)

    if system_filter:
        mappings = mappings.filter(identifiers__system__alias=system_filter).distinct()

    if search_query:
        mappings = mappings.filter(canonical_name__icontains=search_query)

    # Get entity types and systems for filter dropdowns
    entity_types = EntityType.objects.filter(is_active=True).order_by("display_name")
    configured_systems = (
        System.objects.filter(account_configs__account=active_account, account_configs__is_enabled=True)
        .distinct()
        .order_by("display_name")
    )

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "mappings": mappings,
        "entity_types": entity_types,
        "configured_systems": configured_systems,
        "entity_type_filter": entity_type_filter,
        "system_filter": system_filter,
        "search_query": search_query,
    }

    return render(request, "systems/mappings_list.html", context)


@login_required
def mapping_create(request):
    """
    Create a new entity mapping.
    """
    import json

    from .models import EntityMapping, EntityType, System, SystemEntityIdentifier

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "You need an active account.")
        return redirect("account_dashboard")

    if not active_account_user.is_admin:
        messages.error(request, "Only admins can create entity mappings.")
        return redirect("mappings_list")

    entity_types = EntityType.objects.filter(is_active=True).order_by("display_name")
    configured_systems = (
        System.objects.filter(account_configs__account=active_account, account_configs__is_enabled=True)
        .distinct()
        .order_by("display_name")
    )

    if request.method == "POST":
        entity_type_id = request.POST.get("entity_type")
        canonical_name = request.POST.get("canonical_name", "").strip()
        canonical_id = request.POST.get("canonical_id", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        # Validate
        errors = []
        if not entity_type_id:
            errors.append("Entity type is required.")
        if not canonical_name:
            errors.append("Canonical name is required.")

        # Check for duplicate
        if entity_type_id and canonical_name:
            if EntityMapping.objects.filter(
                account=active_account, entity_type_id=entity_type_id, canonical_name=canonical_name
            ).exists():
                errors.append(f'A mapping with name "{canonical_name}" already exists for this entity type.')

        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                "active_account": active_account,
                "active_account_user": active_account_user,
                "entity_types": entity_types,
                "configured_systems": configured_systems,
                "form_data": request.POST,
            }
            return render(request, "systems/mapping_form.html", context)

        # Create the mapping
        mapping = EntityMapping.objects.create(
            account=active_account,
            entity_type_id=entity_type_id,
            canonical_name=canonical_name,
            canonical_id=canonical_id,
            description=description,
            is_active=is_active,
        )

        # Parse and create identifiers
        identifiers_json = request.POST.get("identifiers", "[]")
        try:
            identifiers_data = json.loads(identifiers_json)
            for ident in identifiers_data:
                if ident.get("system_id") and ident.get("identifier_value"):
                    SystemEntityIdentifier.objects.create(
                        mapping=mapping,
                        system_id=ident["system_id"],
                        identifier_value=ident["identifier_value"].strip(),
                        resource_hint=ident.get("resource_hint", "").strip(),
                        is_primary=ident.get("is_primary", False),
                    )
        except json.JSONDecodeError:
            pass  # Invalid JSON, skip identifiers

        messages.success(request, f'Mapping "{canonical_name}" created successfully.')
        return redirect("mappings_list")

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "entity_types": entity_types,
        "configured_systems": configured_systems,
    }

    return render(request, "systems/mapping_form.html", context)


@login_required
def mapping_edit(request, mapping_id):
    """
    Edit an existing entity mapping.
    """
    import json

    from .models import EntityMapping, EntityType, System, SystemEntityIdentifier

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account:
        messages.error(request, "You need an active account.")
        return redirect("account_dashboard")

    if not active_account_user.is_admin:
        messages.error(request, "Only admins can edit entity mappings.")
        return redirect("mappings_list")

    mapping = get_object_or_404(EntityMapping, id=mapping_id, account=active_account)

    entity_types = EntityType.objects.filter(is_active=True).order_by("display_name")
    configured_systems = (
        System.objects.filter(account_configs__account=active_account, account_configs__is_enabled=True)
        .distinct()
        .order_by("display_name")
    )

    if request.method == "POST":
        entity_type_id = request.POST.get("entity_type")
        canonical_name = request.POST.get("canonical_name", "").strip()
        canonical_id = request.POST.get("canonical_id", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        # Validate
        errors = []
        if not entity_type_id:
            errors.append("Entity type is required.")
        if not canonical_name:
            errors.append("Canonical name is required.")

        # Check for duplicate (excluding current mapping)
        if entity_type_id and canonical_name:
            if (
                EntityMapping.objects.filter(
                    account=active_account, entity_type_id=entity_type_id, canonical_name=canonical_name
                )
                .exclude(id=mapping_id)
                .exists()
            ):
                errors.append(f'A mapping with name "{canonical_name}" already exists for this entity type.')

        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                "active_account": active_account,
                "active_account_user": active_account_user,
                "entity_types": entity_types,
                "configured_systems": configured_systems,
                "mapping": mapping,
                "form_data": request.POST,
            }
            return render(request, "systems/mapping_form.html", context)

        # Update the mapping
        mapping.entity_type_id = entity_type_id
        mapping.canonical_name = canonical_name
        mapping.canonical_id = canonical_id
        mapping.description = description
        mapping.is_active = is_active
        mapping.save()

        # Update identifiers - delete old ones and create new
        identifiers_json = request.POST.get("identifiers", "[]")
        try:
            identifiers_data = json.loads(identifiers_json)
            mapping.identifiers.all().delete()
            for ident in identifiers_data:
                if ident.get("system_id") and ident.get("identifier_value"):
                    SystemEntityIdentifier.objects.create(
                        mapping=mapping,
                        system_id=ident["system_id"],
                        identifier_value=ident["identifier_value"].strip(),
                        resource_hint=ident.get("resource_hint", "").strip(),
                        is_primary=ident.get("is_primary", False),
                    )
        except json.JSONDecodeError:
            pass  # Invalid JSON, keep existing identifiers

        messages.success(request, f'Mapping "{canonical_name}" updated successfully.')
        return redirect("mappings_list")

    # Prepare existing identifiers as JSON for the form
    existing_identifiers = []
    for ident in mapping.identifiers.select_related("system"):
        existing_identifiers.append(
            {
                "system_id": ident.system.id,
                "system_name": ident.system.display_name,
                "identifier_value": ident.identifier_value,
                "resource_hint": ident.resource_hint,
                "is_primary": ident.is_primary,
            }
        )

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "entity_types": entity_types,
        "configured_systems": configured_systems,
        "mapping": mapping,
        "existing_identifiers_json": json.dumps(existing_identifiers),
    }

    return render(request, "systems/mapping_form.html", context)


@login_required
@require_POST
def mapping_delete(request, mapping_id):
    """
    Delete an entity mapping.
    """
    from .models import EntityMapping

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "You do not have permission to delete mappings."}, status=403)

    mapping = get_object_or_404(EntityMapping, id=mapping_id, account=active_account)
    mapping_name = mapping.canonical_name
    mapping.delete()

    messages.success(request, f'Mapping "{mapping_name}" deleted successfully.')
    return JsonResponse({"success": True, "redirect": redirect("mappings_list").url})


@login_required
def mcp_tools_config(request, system_id):
    """
    Configure which actions from a system are exposed as MCP tools.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        messages.error(request, "You do not have permission to configure MCP tools.")
        return redirect("systems_dashboard")

    try:
        system = System.objects.get(id=system_id, is_active=True)
    except System.DoesNotExist:
        messages.error(request, "System not found.")
        return redirect("systems_dashboard")

    # Check if system is configured for this account
    try:
        account_system = AccountSystem.objects.get(account=active_account, system=system)
    except AccountSystem.DoesNotExist:
        messages.error(request, "Please configure the system first.")
        return redirect("configure_system", system_id=system_id)

    # Get all actions for this system, grouped by resource
    actions_by_resource = {}
    actions = (
        Action.objects.filter(resource__interface__system=system)
        .select_related("resource__interface")
        .order_by("resource__name", "name")
    )

    for action in actions:
        resource_key = f"{action.resource.interface.alias}/{action.resource.alias or action.resource.name}"
        if resource_key not in actions_by_resource:
            actions_by_resource[resource_key] = {
                "interface": action.resource.interface,
                "resource": action.resource,
                "actions": [],
            }
        actions_by_resource[resource_key]["actions"].append(action)

    # Calculate stats
    total_actions = actions.count()
    enabled_actions = actions.filter(is_mcp_enabled=True).count()

    context = {
        "active_account": active_account,
        "active_account_user": active_account_user,
        "system": system,
        "account_system": account_system,
        "actions_by_resource": actions_by_resource,
        "total_actions": total_actions,
        "enabled_actions": enabled_actions,
    }

    return render(request, "systems/mcp_tools_config.html", context)


@login_required
@require_POST
def toggle_action_mcp(request, action_id):
    """
    Toggle whether an action is exposed as an MCP tool.
    """
    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "No permission"}, status=403)

    try:
        action = Action.objects.select_related("resource__interface__system").get(id=action_id)
    except Action.DoesNotExist:
        return JsonResponse({"error": "Action not found"}, status=404)

    # Verify account has this system configured
    system = action.resource.interface.system
    if not AccountSystem.objects.filter(account=active_account, system=system).exists():
        return JsonResponse({"error": "System not configured for this account"}, status=403)

    # Toggle
    action.is_mcp_enabled = not action.is_mcp_enabled
    action.save()

    return JsonResponse(
        {
            "success": True,
            "is_mcp_enabled": action.is_mcp_enabled,
            "message": f"Action '{action.name}' is now {'enabled' if action.is_mcp_enabled else 'disabled'} for MCP",
        }
    )


@login_required
@require_POST
def bulk_toggle_actions_mcp(request, system_id):
    """
    Enable or disable all actions for a system as MCP tools.
    """
    import json

    active_account = get_active_account(request)
    active_account_user = get_active_account_user(request)

    if not active_account or not active_account_user.is_admin:
        return JsonResponse({"error": "No permission"}, status=403)

    try:
        system = System.objects.get(id=system_id, is_active=True)
    except System.DoesNotExist:
        return JsonResponse({"error": "System not found"}, status=404)

    # Verify account has this system configured
    if not AccountSystem.objects.filter(account=active_account, system=system).exists():
        return JsonResponse({"error": "System not configured for this account"}, status=403)

    # Get action from request
    try:
        data = json.loads(request.body)
        enable = data.get("enable", True)
    except (json.JSONDecodeError, KeyError):
        enable = True

    # Update all actions
    updated = Action.objects.filter(resource__interface__system=system).update(is_mcp_enabled=enable)

    return JsonResponse(
        {
            "success": True,
            "updated": updated,
            "message": f"{'Enabled' if enable else 'Disabled'} {updated} actions for MCP",
        }
    )
