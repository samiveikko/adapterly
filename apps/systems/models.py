from django.contrib.auth import get_user_model
from django.db import models

from apps.accounts.models import Account
from apps.core.fields import EncryptedCharField, EncryptedTextField

User = get_user_model()


# Interface and HTTP method choices for the new System → Interface → Resource → Action model
INTERFACE_TYPES = [
    ("API", "API"),  # direct HTTP API (REST)
    ("GRAPHQL", "GraphQL"),  # GraphQL API
    ("XHR", "XHR"),  # Web-app internal JSON endpoints with browser session
]

HTTP_METHODS = [
    ("GET", "GET"),
    ("POST", "POST"),
    ("PUT", "PUT"),
    ("PATCH", "PATCH"),
    ("DELETE", "DELETE"),
]


class System(models.Model):
    """
    Malli eri systeemeille (esim. Jira, Slack, GitHub, jne.)
    """

    SYSTEM_TYPES = [
        ("project_management", "Project Management"),
        ("communication", "Communication"),
        ("version_control", "Version Control"),
        ("ci_cd", "CI/CD"),
        ("monitoring", "Monitoring"),
        ("storage", "Storage"),
        ("quality_management", "Quality Management"),
        ("erp", "ERP / Finance"),
        ("bim", "BIM / Design"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100, unique=True)
    alias = models.CharField(
        max_length=50, unique=True, help_text="Unique alias used in tool names (e.g., 'jira', 'slack')"
    )
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # New generic per-system configuration and metadata
    variables = models.JSONField(default=dict, blank=True)  # e.g. base_url, api_version
    meta = models.JSONField(default=dict, blank=True)  # version, last_verified, etc.
    schema_digest = models.CharField(max_length=64, blank=True, default="")
    system_type = models.CharField(max_length=50, choices=SYSTEM_TYPES)
    icon = models.CharField(max_length=50, blank=True)  # Bootstrap icon name
    website_url = models.URLField(blank=True)
    # Industry category - links to IndustryTemplate
    industry = models.ForeignKey(
        "IndustryTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="systems",
        help_text="Industry category this system belongs to (e.g., construction, energy)",
    )
    is_active = models.BooleanField(default=True)
    # Confirmation status - unconfirmed until first successful integration test
    is_confirmed = models.BooleanField(
        default=False, help_text="True when system has been tested with a working integration"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When the system was first confirmed working")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

    def confirm(self):
        """Mark system as confirmed after successful integration test."""
        if not self.is_confirmed:
            from django.utils import timezone

            self.is_confirmed = True
            self.confirmed_at = timezone.now()
            self.save(update_fields=["is_confirmed", "confirmed_at"])


# New Interface → Resource → Action models
class Interface(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="interfaces")
    alias = models.SlugField(max_length=120, blank=True, default="")
    name = models.SlugField(max_length=120)
    type = models.CharField(max_length=8, choices=INTERFACE_TYPES)
    base_url = models.CharField(max_length=300, blank=True, default="")
    auth = models.JSONField(default=dict, blank=True)
    requires_browser = models.BooleanField(default=False)
    browser = models.JSONField(default=dict, blank=True)  # login_flow, ua, wait_ms (XHR)
    rate_limits = models.JSONField(default=dict, blank=True)
    # GraphQL-specific: cached introspection schema
    graphql_schema = models.JSONField(
        default=dict, blank=True, help_text="Cached GraphQL introspection schema (for GRAPHQL type interfaces)"
    )

    class Meta:
        unique_together = [("system", "alias")]

    def __str__(self):
        return f"{self.system.alias}:{(self.alias or self.name)}({self.type})"


class Resource(models.Model):
    interface = models.ForeignKey(Interface, on_delete=models.PROTECT, related_name="resources")
    alias = models.SlugField(max_length=120, blank=True, default="")
    name = models.SlugField(max_length=120)
    description = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("interface", "alias")]

    def __str__(self):
        return f"{self.system.alias}:{(self.alias or self.name)}"


class Action(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="actions")
    alias = models.SlugField(max_length=120, blank=True, default="")
    name = models.SlugField(max_length=120)  # list, get, search, ...
    description = models.TextField(blank=True, default="")

    # HTTP-like invocation (works for API and XHR channels)
    method = models.CharField(max_length=8, choices=HTTP_METHODS)
    path = models.CharField(max_length=400)
    headers = models.JSONField(default=dict, blank=True)

    # JSON Schemas
    parameters_schema = models.JSONField(default=dict, blank=True)
    output_schema = models.JSONField(default=dict, blank=True)

    # Pagination and errors (simple MVP)
    pagination = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=dict, blank=True)

    examples = models.JSONField(default=list, blank=True)

    # MCP visibility - controls whether this action is exposed as an MCP tool
    is_mcp_enabled = models.BooleanField(
        default=True, help_text="If enabled, this action will be available as an MCP tool for AI agents"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("resource", "alias")]

    def __str__(self):
        return f"{self.resource.interface.system.alias}:{(self.resource.alias or self.resource.name)}_{(self.alias or self.name)}"


class AuthenticationStep(models.Model):
    """
    Malli monivaiheiselle autentikoinnille.
    Mahdollistaa step-by-step autentikoinnin (login → password → 2FA → IAM).
    """

    STEP_TYPES = [
        ("login", "Login"),
        ("password", "Password"),
        ("two_factor", "Two-Factor Authentication"),
        ("iam", "Identity and Access Management"),
        ("oauth", "OAuth"),
        ("saml", "SAML"),
        ("ldap", "LDAP"),
        ("api_key", "API Key"),
        ("custom", "Custom"),
    ]

    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="auth_steps")
    step_order = models.PositiveIntegerField(default=1)
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    step_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    base_url = models.URLField(blank=True)

    # Step configuration
    is_required = models.BooleanField(default=True)
    is_optional = models.BooleanField(default=False)
    timeout_seconds = models.IntegerField(default=300)  # 5 minutes default

    # Input fields for this step
    input_fields = models.JSONField(default=dict)  # Field definitions

    # Validation rules
    validation_rules = models.JSONField(default=dict)

    # Success/failure handling
    success_message = models.CharField(max_length=200, blank=True)
    failure_message = models.CharField(max_length=200, blank=True)

    # Next step configuration
    next_step_on_success = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="success_next"
    )
    next_step_on_failure = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="failure_next"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["system", "step_order"]
        unique_together = ("system", "step_order")

    def __str__(self):
        return f"{self.system.display_name} - Step {self.step_order}: {self.step_name}"

    def get_input_fields(self):
        """Get input field definitions."""
        return self.input_fields or {}

    def get_validation_rules(self):
        """Get validation rules."""
        return self.validation_rules or {}

    def validate_input(self, input_data):
        """Validate input data against this step's rules."""
        rules = self.get_validation_rules()
        errors = []

        for field, rule in rules.items():
            if field not in input_data:
                if rule.get("required", False):
                    errors.append(f"Field '{field}' is required")
                continue

            value = input_data[field]

            # Type validation
            if "type" in rule:
                if rule["type"] == "email" and "@" not in str(value):
                    errors.append(f"Field '{field}' must be a valid email")
                elif rule["type"] == "url" and not str(value).startswith(("http://", "https://")):
                    errors.append(f"Field '{field}' must be a valid URL")
                elif rule["type"] == "number" and not str(value).isdigit():
                    errors.append(f"Field '{field}' must be a number")

            # Length validation
            if "min_length" in rule and len(str(value)) < rule["min_length"]:
                errors.append(f"Field '{field}' must be at least {rule['min_length']} characters")
            if "max_length" in rule and len(str(value)) > rule["max_length"]:
                errors.append(f"Field '{field}' must be at most {rule['max_length']} characters")

        return errors


class AccountSystem(models.Model):
    """
    Model for account-specific system settings and credentials.

    Supports two credential scopes:
    - Account-level (project=NULL): shared credentials, visible to all projects
    - Project-level (project=X): dedicated credentials, visible only to that project

    When both exist for the same system, project-level takes precedence.
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="systems")
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="account_configs")
    project = models.ForeignKey(
        "mcp.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="account_systems",
        help_text="Project-scoped credential. NULL = account-level (shared).",
    )

    # Credentials
    username = models.CharField(max_length=200, blank=True, null=True)
    password = EncryptedCharField(max_length=500, blank=True, null=True)
    api_key = EncryptedCharField(max_length=500, blank=True, null=True)
    token = EncryptedCharField(max_length=1000, blank=True, null=True)
    client_id = models.CharField(max_length=200, blank=True, null=True)
    client_secret = EncryptedCharField(max_length=500, blank=True, null=True)

    # OAuth-tiedot
    oauth_token = EncryptedTextField(blank=True, null=True)
    oauth_refresh_token = EncryptedTextField(blank=True, null=True)
    oauth_expires_at = models.DateTimeField(null=True, blank=True)

    # XHR/Session Authentication (for browser-based APIs)
    session_cookie = EncryptedTextField(
        blank=True, null=True, help_text="Session cookie (e.g., JSESSIONID) for XHR authentication"
    )
    csrf_token = EncryptedCharField(max_length=500, blank=True, null=True, help_text="CSRF token for XHR requests")
    session_expires_at = models.DateTimeField(blank=True, null=True, help_text="When the session expires")

    # Muut asetukset
    custom_settings = models.JSONField(default=dict)
    is_enabled = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["system__display_name"]
        constraints = [
            # Project-level: one credential per (account, system, project)
            models.UniqueConstraint(
                fields=["account", "system", "project"],
                name="uix_accountsystem_account_system_project",
            ),
            # Account-level: one shared credential per (account, system) where project IS NULL
            models.UniqueConstraint(
                fields=["account", "system"],
                condition=models.Q(project__isnull=True),
                name="uix_accountsystem_account_system_shared",
            ),
        ]

    def __str__(self):
        scope = f" [{self.project.slug}]" if self.project_id else " [shared]"
        return f"{self.account.name} - {self.system.display_name}{scope}"

    def get_auth_headers(self):
        """Get authentication headers."""
        headers = {}

        # Try OAuth token first
        if self.oauth_token:
            headers["Authorization"] = f"Bearer {self.oauth_token}"
            return headers

        # Then try regular token
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            return headers

        # Then try API key
        if self.api_key:
            # Default to X-API-Key, can be customized via custom_settings
            api_key_name = self.custom_settings.get("api_key_header", "X-API-Key")
            headers[api_key_name] = self.api_key
            return headers

        # Finally try basic auth
        if self.username and self.password:
            import base64

            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"

        return headers

    def is_session_expired(self):
        """Check if the XHR session has expired."""
        if not self.session_expires_at:
            return False
        from django.utils import timezone

        return timezone.now() > self.session_expires_at

    def is_oauth_expired(self):
        """Check if the OAuth token has expired."""
        if not self.oauth_expires_at:
            return False
        from django.utils import timezone

        return timezone.now() > self.oauth_expires_at

    def mark_verified(self):
        """Mark system as verified."""
        from django.utils import timezone

        self.is_verified = True
        self.last_verified_at = timezone.now()
        self.last_error = ""
        self.save()

    def mark_error(self, error_message):
        """Mark an error."""
        self.is_verified = False
        self.last_error = error_message
        self.save()


class EntityType(models.Model):
    """
    Entiteettityypit: project, user, company, repository, ticket, contact, deal
    Määrittelee millaisia entiteettejä voidaan mapata järjestelmien välillä.
    """

    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Bootstrap icon name
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class EntityMapping(models.Model):
    """
    Looginen entiteetti joka yhdistää tunnisteet eri järjestelmissä.
    Esim. "ACME Corporation" on sama yritys Jirassa (ACME), Salesforcessa (001ABC) ja GitHubissa (acme-corp).
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="entity_mappings")
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT, related_name="mappings")
    canonical_name = models.CharField(max_length=255, help_text="Human-readable name, e.g. 'ACME Corporation'")
    canonical_id = models.CharField(max_length=100, blank=True, help_text="Optional internal ID")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["canonical_name"]
        unique_together = [("account", "entity_type", "canonical_name")]

    def __str__(self):
        return f"{self.canonical_name} ({self.entity_type.name})"

    def get_identifier_for_system(self, system_alias):
        """Get the identifier value for a specific system."""
        try:
            identifier = self.identifiers.select_related("system").get(system__alias=system_alias)
            return identifier.identifier_value
        except SystemEntityIdentifier.DoesNotExist:
            return None

    def get_identifiers_dict(self):
        """Return identifiers as a dict keyed by system alias."""
        result = {}
        for identifier in self.identifiers.select_related("system"):
            result[identifier.system.alias] = {
                "id": identifier.identifier_value,
                "resource_hint": identifier.resource_hint,
                "is_primary": identifier.is_primary,
            }
        return result


class SystemEntityIdentifier(models.Model):
    """
    Järjestelmäkohtainen tunniste mappaukselle.
    Esim. Jira-projekti "PROJ" = Salesforce Account "001ABC" = GitHub repo "my-repo".
    """

    mapping = models.ForeignKey(EntityMapping, on_delete=models.CASCADE, related_name="identifiers")
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="entity_identifiers")
    identifier_value = models.CharField(
        max_length=500, help_text="The identifier in this system, e.g. 'PROJ', '001ABC'"
    )
    resource_hint = models.CharField(
        max_length=100, blank=True, help_text="Resource type hint, e.g. 'projects', 'accounts'"
    )
    is_primary = models.BooleanField(default=False, help_text="Whether this is the primary identifier for this mapping")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["system__display_name"]
        unique_together = [("mapping", "system", "identifier_value")]

    def __str__(self):
        return f"{self.system.alias}:{self.identifier_value}"


class IndustryTemplate(models.Model):
    """
    Alakohtainen mapping-template.
    Sisältää valmiit termimappaukset ja kenttämappaukset per toimiala.
    Esim. "construction" (Rakennusala), "energy" (Energia), "real_estate" (Kiinteistöt).
    """

    name = models.CharField(max_length=100, unique=True, help_text="Internal name, e.g. 'construction'")
    display_name = models.CharField(max_length=200, help_text="Display name, e.g. 'Rakennusala'")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class TermMapping(models.Model):
    """
    Termimappaus templatessa.
    Mappaa canonical termi (esim. "project") järjestelmäkohtaiseen termiin (esim. "Project", "Projekti").
    """

    template = models.ForeignKey(IndustryTemplate, on_delete=models.CASCADE, related_name="term_mappings")
    canonical_term = models.CharField(max_length=100, help_text="Canonical term, e.g. 'project', 'site'")
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="term_mappings")
    system_term = models.CharField(max_length=100, help_text="Term in this system, e.g. 'Project', 'Projekti'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["canonical_term", "system__display_name"]
        unique_together = [("template", "canonical_term", "system")]

    def __str__(self):
        return f"{self.template.name}: {self.canonical_term} → {self.system.alias}:{self.system_term}"


class FieldMapping(models.Model):
    """
    Kenttämappaus templatessa.
    Mappaa canonical kenttä (esim. "project_id") järjestelmäkohtaiseen kenttään (esim. "uuid", "project_id").
    Sisältää myös transformaatiot (esim. päivämääräformaatit).
    """

    TRANSFORM_CHOICES = [
        ("", "None"),
        ("uppercase", "Uppercase"),
        ("lowercase", "Lowercase"),
        ("date_iso", "Date ISO format (YYYY-MM-DD)"),
        ("date_fi", "Date Finnish format (DD.MM.YYYY)"),
        ("date_us", "Date US format (MM/DD/YYYY)"),
        ("datetime_iso", "Datetime ISO format"),
        ("boolean_01", "Boolean as 0/1"),
        ("boolean_yn", "Boolean as Y/N"),
        ("trim", "Trim whitespace"),
    ]

    template = models.ForeignKey(IndustryTemplate, on_delete=models.CASCADE, related_name="field_mappings")
    entity_type = models.ForeignKey(EntityType, on_delete=models.CASCADE, related_name="field_mappings")
    canonical_field = models.CharField(
        max_length=100, help_text="Canonical field name, e.g. 'project_id', 'start_date'"
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="field_mappings")
    system_field = models.CharField(max_length=100, help_text="Field name in this system, e.g. 'uuid', 'startDate'")
    transform = models.CharField(
        max_length=50, choices=TRANSFORM_CHOICES, blank=True, help_text="Optional transformation"
    )
    is_required = models.BooleanField(default=False, help_text="Whether this field is required")
    description = models.CharField(max_length=255, blank=True, help_text="Description of this field mapping")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["entity_type__name", "canonical_field", "system__display_name"]
        unique_together = [("template", "entity_type", "canonical_field", "system")]

    def __str__(self):
        return f"{self.template.name}/{self.entity_type.name}: {self.canonical_field} → {self.system.alias}:{self.system_field}"
