"""
System models - mirrors Django systems_* tables.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..crypto import decrypt_value
from .base import Base


class System(Base):
    """System model - mirrors systems_system table."""

    __tablename__ = "systems_system"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    alias = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    variables = Column(JSON, default=dict)
    meta = Column(JSON, default=dict)
    schema_digest = Column(String(64), default="")
    system_type = Column(String(50), nullable=False)
    icon = Column(String(50), default="")
    website_url = Column(String(500), default="")
    industry_id = Column(Integer, ForeignKey("systems_industrytemplate.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_confirmed = Column(Boolean, default=False)  # True when tested with working integration
    confirmed_at = Column(DateTime, nullable=True)  # When first confirmed working
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interfaces = relationship("Interface", back_populates="system")
    account_systems = relationship("AccountSystem", back_populates="system")
    industry = relationship("IndustryTemplate", back_populates="systems")

    def __repr__(self):
        return f"<System(alias='{self.alias}', name='{self.display_name}')>"


class Interface(Base):
    """Interface model - mirrors systems_interface table."""

    __tablename__ = "systems_interface"

    id = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey("systems_system.id"), nullable=False)
    alias = Column(String(120), default="")
    name = Column(String(120), nullable=False)
    type = Column(String(8), nullable=False)  # API, GRAPHQL, XHR
    base_url = Column(String(300), default="")
    auth = Column(JSON, default=dict)
    requires_browser = Column(Boolean, default=False)
    browser = Column(JSON, default=dict)
    rate_limits = Column(JSON, default=dict)
    graphql_schema = Column(JSON, default=dict)  # Cached GraphQL introspection schema

    # Relationships
    system = relationship("System", back_populates="interfaces")
    resources = relationship("Resource", back_populates="interface")

    def __repr__(self):
        return f"<Interface(system='{self.system.alias if self.system else '?'}', alias='{self.alias}')>"


class Resource(Base):
    """Resource model - mirrors systems_resource table."""

    __tablename__ = "systems_resource"

    id = Column(Integer, primary_key=True)
    interface_id = Column(Integer, ForeignKey("systems_interface.id"), nullable=False)
    alias = Column(String(120), default="")
    name = Column(String(120), nullable=False)
    description = Column(Text, default="")

    # Relationships
    interface = relationship("Interface", back_populates="resources")
    actions = relationship("Action", back_populates="resource")

    def __repr__(self):
        return f"<Resource(alias='{self.alias}', name='{self.name}')>"


class Action(Base):
    """Action model - mirrors systems_action table."""

    __tablename__ = "systems_action"

    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey("systems_resource.id"), nullable=False)
    alias = Column(String(120), default="")
    name = Column(String(120), nullable=False)
    description = Column(Text, default="")
    method = Column(String(8), nullable=False)  # GET, POST, PUT, PATCH, DELETE
    path = Column(String(400), nullable=False)
    headers = Column(JSON, default=dict)
    parameters_schema = Column(JSON, default=dict)
    output_schema = Column(JSON, default=dict)
    pagination = Column(JSON, default=dict)
    errors = Column(JSON, default=dict)
    examples = Column(JSON, default=list)
    is_mcp_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resource = relationship("Resource", back_populates="actions")

    def __repr__(self):
        return f"<Action(name='{self.name}', method='{self.method}')>"


class AccountSystem(Base):
    """Account-System connection - mirrors systems_accountsystem table."""

    __tablename__ = "systems_accountsystem"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts_account.id"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems_system.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("mcp_project.id"), nullable=True)

    # Credentials (encrypted in Django, stored as-is here for read-only)
    username = Column(String(200), nullable=True)
    password = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    token = Column(String(1000), nullable=True)
    client_id = Column(String(200), nullable=True)
    client_secret = Column(String(500), nullable=True)

    # OAuth
    oauth_token = Column(Text, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)
    oauth_expires_at = Column(DateTime, nullable=True)

    # Session/XHR auth
    session_cookie = Column(Text, nullable=True)
    csrf_token = Column(String(500), nullable=True)
    session_expires_at = Column(DateTime, nullable=True)

    # Settings
    custom_settings = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account", backref="account_systems")
    system = relationship("System", back_populates="account_systems")
    project = relationship("Project", back_populates="account_systems")

    def __repr__(self):
        return f"<AccountSystem(account_id={self.account_id}, system='{self.system.alias if self.system else '?'}')>"

    def _decrypt(self, value: str | None) -> str | None:
        """Decrypt a Fernet-encrypted field value."""
        return decrypt_value(value)

    def get_auth_headers(self) -> dict:
        """Get authentication headers for this system."""
        headers = {}

        # Try OAuth token first
        oauth_tok = self._decrypt(self.oauth_token)
        if oauth_tok:
            headers["Authorization"] = f"Bearer {oauth_tok}"
            return headers

        # Then try regular token
        tok = self._decrypt(self.token)
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
            return headers

        # Then try API key
        key = self._decrypt(self.api_key)
        if key:
            api_key_name = (self.custom_settings or {}).get("api_key_header", "X-API-Key")
            headers[api_key_name] = key
            return headers

        # Finally try basic auth
        uname = self.username
        pwd = self._decrypt(self.password)
        if uname and pwd:
            import base64

            credentials = f"{uname}:{pwd}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    def is_oauth_expired(self) -> bool:
        """Check if OAuth token is expired."""
        if not self.oauth_expires_at:
            return False
        expires = self.oauth_expires_at
        now = datetime.now(timezone.utc)
        # Handle both naive and aware datetimes from DB
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires


class EntityType(Base):
    """Entity type model - mirrors systems_entitytype table."""

    __tablename__ = "systems_entitytype"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(50), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mappings = relationship("EntityMapping", back_populates="entity_type")

    def __repr__(self):
        return f"<EntityType(name='{self.name}', display_name='{self.display_name}')>"


class EntityMapping(Base):
    """Entity mapping model - mirrors systems_entitymapping table."""

    __tablename__ = "systems_entitymapping"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts_account.id"), nullable=False, index=True)
    entity_type_id = Column(Integer, ForeignKey("systems_entitytype.id"), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    canonical_id = Column(String(100), default="")
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entity_type = relationship("EntityType", back_populates="mappings")
    identifiers = relationship("SystemEntityIdentifier", back_populates="mapping", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EntityMapping(canonical_name='{self.canonical_name}')>"

    def get_identifier_for_system(self, system_alias: str) -> str | None:
        """Get the identifier value for a specific system."""
        for identifier in self.identifiers:
            if identifier.system and identifier.system.alias == system_alias:
                return identifier.identifier_value
        return None

    def get_identifiers_dict(self) -> dict:
        """Return identifiers as a dict keyed by system alias."""
        result = {}
        for identifier in self.identifiers:
            if identifier.system:
                result[identifier.system.alias] = {
                    "id": identifier.identifier_value,
                    "resource_hint": identifier.resource_hint or "",
                    "is_primary": identifier.is_primary,
                }
        return result


class SystemEntityIdentifier(Base):
    """System entity identifier - mirrors systems_systementityidentifier table."""

    __tablename__ = "systems_systementityidentifier"

    id = Column(Integer, primary_key=True)
    mapping_id = Column(Integer, ForeignKey("systems_entitymapping.id"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems_system.id"), nullable=False)
    identifier_value = Column(String(500), nullable=False)
    resource_hint = Column(String(100), default="")
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mapping = relationship("EntityMapping", back_populates="identifiers")
    system = relationship("System")

    def __repr__(self):
        return f"<SystemEntityIdentifier(system='{self.system.alias if self.system else '?'}', value='{self.identifier_value}')>"


class IndustryTemplate(Base):
    """Industry template model - mirrors systems_industrytemplate table."""

    __tablename__ = "systems_industrytemplate"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(50), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    systems = relationship("System", back_populates="industry")
    term_mappings = relationship("TermMapping", back_populates="template", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IndustryTemplate(name='{self.name}')>"


class TermMapping(Base):
    """Term mapping model - mirrors systems_termmapping table."""

    __tablename__ = "systems_termmapping"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("systems_industrytemplate.id"), nullable=False)
    canonical_term = Column(String(100), nullable=False)
    system_id = Column(Integer, ForeignKey("systems_system.id"), nullable=False)
    system_term = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    template = relationship("IndustryTemplate", back_populates="term_mappings")
    system = relationship("System")

    def __repr__(self):
        return f"<TermMapping(canonical='{self.canonical_term}', system_term='{self.system_term}')>"


class FieldMapping(Base):
    """Field mapping model - mirrors systems_fieldmapping table."""

    __tablename__ = "systems_fieldmapping"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("systems_industrytemplate.id"), nullable=False)
    entity_type_id = Column(Integer, ForeignKey("systems_entitytype.id"), nullable=False)
    canonical_field = Column(String(100), nullable=False)
    system_id = Column(Integer, ForeignKey("systems_system.id"), nullable=False)
    system_field = Column(String(100), nullable=False)
    transform = Column(String(50), default="")
    is_required = Column(Boolean, default=False)
    description = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    template = relationship("IndustryTemplate", back_populates="field_mappings")
    entity_type = relationship("EntityType")
    system = relationship("System")

    def __repr__(self):
        return f"<FieldMapping(canonical='{self.canonical_field}', system_field='{self.system_field}')>"
