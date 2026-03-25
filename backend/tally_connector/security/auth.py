import os
from fastapi import Header, HTTPException


class ConnectorSecurity:
    def __init__(self):
        self.backend_api_token = os.getenv("CONNECTOR_API_TOKEN", "")
        self.company_id = os.getenv("CONNECTOR_COMPANY_ID", "")

    def require_backend_access(
        self,
        authorization: str | None,
        x_company_id: str | None,
    ) -> None:
        if not self.backend_api_token:
            raise HTTPException(status_code=500, detail="CONNECTOR_API_TOKEN not configured")

        expected_auth = f"Bearer {self.backend_api_token}"
        if authorization != expected_auth:
            raise HTTPException(status_code=401, detail="Invalid connector token")

        if self.company_id and x_company_id != self.company_id:
            raise HTTPException(status_code=403, detail="Company ID mismatch")


security = ConnectorSecurity()


async def verify_backend_request(
    authorization: str | None = Header(default=None),
    x_company_id: str | None = Header(default=None),
) -> None:
    security.require_backend_access(authorization, x_company_id)
