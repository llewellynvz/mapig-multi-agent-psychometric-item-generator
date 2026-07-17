# TEMPORARY: Azure test override (remove after evaluation)
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any

from backend.settings import settings

_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"

_credential: Any = None
_credential_lock = threading.Lock()


def get_azure_credential() -> Any:
    """Return the cached Azure CertificateCredential, building it on first use."""
    global _credential
    if _credential is not None:
        return _credential

    with _credential_lock:
        if _credential is not None:
            return _credential

        try:
            from azure.identity import CertificateCredential
        except ImportError as exc:
            raise RuntimeError(
                "azure-identity is not installed — pip install azure-identity>=1.19 "
                "to use AZURE_TEST_OVERRIDE"
            ) from exc

        missing = [
            name
            for name, value in (
                ("AZURE_TENANT_ID", settings.AZURE_TENANT_ID),
                ("AZURE_CLIENT_ID", settings.AZURE_CLIENT_ID),
                ("AZURE_CLIENT_CERT_PATH", settings.AZURE_CLIENT_CERT_PATH),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "AZURE_TEST_OVERRIDE requires certificate auth settings; missing: "
                + ", ".join(missing)
                + ". Set them in .env, then restart the backend."
            )

        cert_path = Path(settings.AZURE_CLIENT_CERT_PATH)
        if not cert_path.exists():
            raise RuntimeError(
                f"Azure client certificate not found at {str(cert_path)!r}. "
                "Point AZURE_CLIENT_CERT_PATH at the client certificate file "
                "(.pem or .pfx), then restart the backend."
            )

        _credential = CertificateCredential(
            tenant_id=settings.AZURE_TENANT_ID,
            client_id=settings.AZURE_CLIENT_ID,
            certificate_path=str(cert_path),
            password=settings.AZURE_CLIENT_CERT_PASSWORD or None,
        )
        return _credential


def azure_token_provider() -> str:
    """Sync azure_ad_token_provider for AzureChatOpenAI."""
    return get_azure_credential().get_token(_TOKEN_SCOPE).token


async def azure_token_provider_async() -> str:
    """Async azure_ad_async_token_provider for AzureChatOpenAI."""
    return await asyncio.to_thread(azure_token_provider)
