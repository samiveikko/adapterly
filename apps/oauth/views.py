import logging
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.mcp.models import MCPApiKey

from .models import AuthorizationCode, OAuthApplication

logger = logging.getLogger(__name__)


def _error_redirect(redirect_uri, error, description, state=None):
    """Build OAuth2 error redirect."""
    params = {"error": error, "error_description": description}
    if state:
        params["state"] = state
    return redirect(f"{redirect_uri}?{urlencode(params)}")


def _error_json(error, description, status=400):
    """Return OAuth2 error JSON response."""
    return JsonResponse({"error": error, "error_description": description}, status=status)


@login_required
@require_http_methods(["GET", "POST"])
def authorize(request):
    """OAuth2 authorization endpoint."""
    client_id = request.GET.get("client_id") or request.POST.get("client_id")
    redirect_uri = request.GET.get("redirect_uri") or request.POST.get("redirect_uri")
    response_type = request.GET.get("response_type") or request.POST.get("response_type")
    state = request.GET.get("state") or request.POST.get("state", "")

    # Validate required params
    if not client_id or not redirect_uri:
        return render(request, "oauth/authorize.html", {
            "error": "Missing client_id or redirect_uri.",
        }, status=400)

    if response_type != "code":
        return render(request, "oauth/authorize.html", {
            "error": "Unsupported response_type. Only 'code' is supported.",
        }, status=400)

    # Look up application
    try:
        app = OAuthApplication.objects.get(client_id=client_id, is_active=True)
    except OAuthApplication.DoesNotExist:
        return render(request, "oauth/authorize.html", {
            "error": "Unknown application.",
        }, status=400)

    # Validate redirect_uri
    if redirect_uri != app.redirect_uri:
        return render(request, "oauth/authorize.html", {
            "error": "redirect_uri does not match registered URI.",
        }, status=400)

    # Check user has an active account
    account = getattr(request, "account", None)
    if not account:
        return render(request, "oauth/authorize.html", {
            "error": "No active account. Please set up your account first.",
        }, status=400)

    if request.method == "GET":
        return render(request, "oauth/authorize.html", {
            "app": app,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "state": state,
            "account": account,
        })

    # POST — user clicked Authorize
    code = AuthorizationCode.objects.create(
        application=app,
        user=request.user,
        account=account,
        code=AuthorizationCode.generate_code(),
        redirect_uri=redirect_uri,
        state=state,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    params = {"code": code.code}
    if state:
        params["state"] = state

    logger.info("OAuth code issued for app=%s user=%s account=%s", app.name, request.user, account)
    return redirect(f"{redirect_uri}?{urlencode(params)}")


@csrf_exempt
@require_POST
def token(request):
    """OAuth2 token endpoint (server-to-server)."""
    # Rate limiting: 20 req/min per client_id
    client_id = request.POST.get("client_id", "")
    rate_key = f"oauth_token_rate:{client_id}"
    count = cache.get(rate_key, 0)
    if count >= 20:
        return _error_json("rate_limit_exceeded", "Too many requests. Try again later.", status=429)
    cache.set(rate_key, count + 1, timeout=60)

    grant_type = request.POST.get("grant_type")
    client_secret = request.POST.get("client_secret", "")
    code_value = request.POST.get("code", "")
    redirect_uri = request.POST.get("redirect_uri", "")

    if grant_type != "authorization_code":
        return _error_json("unsupported_grant_type", "Only authorization_code is supported.")

    if not client_id or not client_secret or not code_value:
        return _error_json("invalid_request", "Missing client_id, client_secret, or code.")

    # Validate client
    try:
        app = OAuthApplication.objects.get(client_id=client_id, is_active=True)
    except OAuthApplication.DoesNotExist:
        return _error_json("invalid_client", "Unknown client.", status=401)

    if not app.verify_secret(client_secret):
        return _error_json("invalid_client", "Bad client_secret.", status=401)

    # Validate code
    try:
        auth_code = AuthorizationCode.objects.select_related("account", "user", "application").get(code=code_value)
    except AuthorizationCode.DoesNotExist:
        return _error_json("invalid_grant", "Unknown authorization code.")

    if auth_code.application_id != app.id:
        return _error_json("invalid_grant", "Code does not belong to this client.")

    if not auth_code.is_valid:
        return _error_json("invalid_grant", "Code is expired or already used.")

    if redirect_uri and redirect_uri != auth_code.redirect_uri:
        return _error_json("invalid_grant", "redirect_uri mismatch.")

    # Mark code as used
    auth_code.is_used = True
    auth_code.save(update_fields=["is_used"])

    # Create MCPApiKey as the access token
    key, prefix, key_hash = MCPApiKey.generate_key()
    MCPApiKey.objects.create(
        account=auth_code.account,
        created_by=auth_code.user,
        name=f"OAuth: {app.name} ({auth_code.user.username})",
        key_prefix=prefix,
        key_hash=key_hash,
        mode=app.mode,
        is_active=True,
    )

    logger.info(
        "OAuth token issued for app=%s user=%s account=%s",
        app.name, auth_code.user, auth_code.account,
    )

    return JsonResponse({
        "access_token": key,
        "token_type": "Bearer",
    })
