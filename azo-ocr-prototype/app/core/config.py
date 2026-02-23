"""
Configuration de l'application via variables d'environnement.
Utilise Pydantic BaseSettings pour le chargement et la validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application chargés depuis l'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str
    """Clé API OpenAI (obligatoire)."""

    # Modèles utilisés dans le pipeline (cascading)
    llm_model_light: str = "gpt-4o-mini"
    """Modèle rapide/économique pour la première tentative d'extraction."""

    llm_model_heavy: str = "gpt-4o"
    """Modèle plus capable utilisé en fallback en cas d'échec de validation."""


def get_settings() -> Settings:
    """Retourne l'instance des settings (singleton implicite via dépendance FastAPI)."""
    return Settings()
