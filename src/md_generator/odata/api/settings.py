from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class OdataToMdSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ODATA_TO_MD_",
        env_file=".env",
        extra="ignore",
    )

    cors_origins: str = "*"
    max_sync_zip_mb: int = 80


def cors_list(settings: OdataToMdSettings) -> list[str]:
    raw = (settings.cors_origins or "*").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]
