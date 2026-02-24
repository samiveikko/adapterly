"""
Salesforce API Executor

Handles OAuth 2.0 authentication and API calls to Salesforce REST API.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class SalesforceExecutor:
    """Execute Salesforce API calls with OAuth 2.0 authentication."""

    API_VERSION = "v59.0"

    def __init__(self, account_system):
        """
        Initialize with AccountSystem credentials.

        Args:
            account_system: AccountSystem instance with Salesforce credentials
        """
        self.account_system = account_system
        self.instance_url = account_system.custom_settings.get("instance_url", "")
        self.access_token = account_system.oauth_token
        self.refresh_token = account_system.oauth_refresh_token
        self.client_id = account_system.client_id
        self.client_secret = account_system.client_secret

    @property
    def base_url(self) -> str:
        """Get the base API URL."""
        return f"{self.instance_url}/services/data/{self.API_VERSION}"

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authorization."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def refresh_access_token(self) -> bool:
        """
        Refresh the OAuth access token.

        Returns:
            True if successful, False otherwise
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        token_url = "https://login.salesforce.com/services/oauth2/token"

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]

            # Update stored token
            self.account_system.oauth_token = self.access_token
            if "instance_url" in token_data:
                self.instance_url = token_data["instance_url"]
                self.account_system.custom_settings["instance_url"] = self.instance_url
            self.account_system.save()

            logger.info("Successfully refreshed Salesforce access token")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            return False

    @classmethod
    def authenticate_password_flow(
        cls, instance_url: str, client_id: str, client_secret: str, username: str, password_with_token: str
    ) -> dict[str, Any]:
        """
        Authenticate using OAuth 2.0 password flow.

        Args:
            instance_url: Salesforce instance URL
            client_id: Connected App Consumer Key
            client_secret: Connected App Consumer Secret
            username: Salesforce username
            password_with_token: Password + Security Token

        Returns:
            Dict with access_token, refresh_token, instance_url
        """
        token_url = "https://login.salesforce.com/services/oauth2/token"

        data = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password_with_token,
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            error_data = response.json()
            raise AuthenticationError(error_data.get("error_description", "Authentication failed"))

        return response.json()

    def _make_request(
        self, method: str, path: str, params: dict | None = None, data: dict | None = None, retry_on_401: bool = True
    ) -> dict[str, Any]:
        """
        Make an API request with automatic token refresh.

        Args:
            method: HTTP method
            path: API path (relative to base_url)
            params: Query parameters
            data: Request body (for POST/PATCH)
            retry_on_401: Whether to retry after refreshing token on 401

        Returns:
            Response data as dict
        """
        url = f"{self.base_url}{path}"

        try:
            response = requests.request(
                method=method, url=url, headers=self._get_headers(), params=params, json=data, timeout=30
            )

            # Handle token expiration
            if response.status_code == 401 and retry_on_401:
                logger.info("Access token expired, attempting refresh")
                if self.refresh_access_token():
                    return self._make_request(method, path, params, data, retry_on_401=False)
                else:
                    raise AuthenticationError("Token refresh failed")

            response.raise_for_status()

            # Handle empty responses (e.g., DELETE, PATCH success)
            if response.status_code == 204 or not response.content:
                return {"success": True}

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Salesforce API request failed: {e}")
            raise APIError(str(e))

    # ==================== Query Operations ====================

    def query(self, soql: str) -> dict[str, Any]:
        """
        Execute a SOQL query.

        Args:
            soql: SOQL query string

        Returns:
            Query results with records
        """
        return self._make_request("GET", "/query", params={"q": soql})

    def query_all(self, soql: str) -> dict[str, Any]:
        """
        Execute a SOQL query including deleted/archived records.
        """
        return self._make_request("GET", "/queryAll", params={"q": soql})

    def search(self, sosl: str) -> dict[str, Any]:
        """
        Execute a SOSL search.

        Args:
            sosl: SOSL search string
        """
        return self._make_request("GET", "/search", params={"q": sosl})

    # ==================== CRUD Operations ====================

    def get_record(self, sobject: str, record_id: str, fields: list | None = None) -> dict[str, Any]:
        """
        Get a single record by ID.

        Args:
            sobject: Salesforce object type (e.g., 'Account')
            record_id: Record ID
            fields: Optional list of fields to retrieve
        """
        path = f"/sobjects/{sobject}/{record_id}"
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self._make_request("GET", path, params=params if params else None)

    def create_record(self, sobject: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new record.

        Args:
            sobject: Salesforce object type
            data: Record data

        Returns:
            Created record info with id
        """
        path = f"/sobjects/{sobject}"
        return self._make_request("POST", path, data=data)

    def update_record(self, sobject: str, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing record.

        Args:
            sobject: Salesforce object type
            record_id: Record ID
            data: Fields to update
        """
        path = f"/sobjects/{sobject}/{record_id}"
        return self._make_request("PATCH", path, data=data)

    def delete_record(self, sobject: str, record_id: str) -> dict[str, Any]:
        """
        Delete a record.

        Args:
            sobject: Salesforce object type
            record_id: Record ID
        """
        path = f"/sobjects/{sobject}/{record_id}"
        return self._make_request("DELETE", path)

    # ==================== Describe Operations ====================

    def describe_global(self) -> dict[str, Any]:
        """Get metadata about all available objects."""
        return self._make_request("GET", "/sobjects")

    def describe_object(self, sobject: str) -> dict[str, Any]:
        """
        Get metadata about a specific object.

        Args:
            sobject: Object name (e.g., 'Account')
        """
        path = f"/sobjects/{sobject}/describe"
        return self._make_request("GET", path)

    # ==================== Convenience Methods ====================

    def list_accounts(self, limit: int = 100) -> dict[str, Any]:
        """List Account records."""
        soql = f"SELECT Id, Name, Industry, Website, Phone, BillingCity, BillingCountry FROM Account LIMIT {limit}"
        return self.query(soql)

    def list_contacts(self, limit: int = 100) -> dict[str, Any]:
        """List Contact records."""
        soql = (
            f"SELECT Id, FirstName, LastName, Email, Phone, Title, AccountId, Account.Name FROM Contact LIMIT {limit}"
        )
        return self.query(soql)

    def list_leads(self, limit: int = 100) -> dict[str, Any]:
        """List Lead records."""
        soql = f"SELECT Id, FirstName, LastName, Company, Email, Phone, Status, LeadSource FROM Lead LIMIT {limit}"
        return self.query(soql)

    def list_opportunities(self, limit: int = 100) -> dict[str, Any]:
        """List Opportunity records."""
        soql = f"SELECT Id, Name, Amount, StageName, CloseDate, Probability, AccountId, Account.Name FROM Opportunity LIMIT {limit}"
        return self.query(soql)

    def test_connection(self) -> dict[str, Any]:
        """Test the connection by fetching user info."""
        try:
            url = f"{self.instance_url}/services/oauth2/userinfo"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return {"success": True, "user_info": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class APIError(Exception):
    """Raised when an API call fails."""

    pass


def execute_salesforce_action(account_system, action, parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a Salesforce action.

    Args:
        account_system: AccountSystem with Salesforce credentials
        action: Action model instance
        parameters: Action parameters

    Returns:
        Action result
    """
    executor = SalesforceExecutor(account_system)

    resource_alias = action.resource.alias
    action_alias = action.alias

    # Map action to executor method
    if action_alias == "list":
        soql = parameters.get("soql_query")
        if soql:
            return executor.query(soql)
        # Default queries per resource
        if resource_alias == "account":
            return executor.list_accounts(parameters.get("limit", 100))
        elif resource_alias == "contact":
            return executor.list_contacts(parameters.get("limit", 100))
        elif resource_alias == "lead":
            return executor.list_leads(parameters.get("limit", 100))
        elif resource_alias == "opportunity":
            return executor.list_opportunities(parameters.get("limit", 100))
        else:
            # Generic query
            sobject = resource_alias.title()
            soql = f"SELECT Id, Name FROM {sobject} LIMIT {parameters.get('limit', 100)}"
            return executor.query(soql)

    elif action_alias == "get":
        sobject = resource_alias.title()
        record_id = parameters.get("id")
        fields = parameters.get("fields")
        return executor.get_record(sobject, record_id, fields)

    elif action_alias == "create":
        sobject = resource_alias.title()
        # Remove 'id' if present (not needed for create)
        data = {k: v for k, v in parameters.items() if k != "id" and v is not None}
        return executor.create_record(sobject, data)

    elif action_alias == "update":
        sobject = resource_alias.title()
        record_id = parameters.pop("id")
        data = {k: v for k, v in parameters.items() if v is not None}
        return executor.update_record(sobject, record_id, data)

    elif action_alias == "delete":
        sobject = resource_alias.title()
        record_id = parameters.get("id")
        return executor.delete_record(sobject, record_id)

    elif action_alias == "query":
        soql = parameters.get("soql")
        return executor.query(soql)

    else:
        raise ValueError(f"Unknown action: {action_alias}")
