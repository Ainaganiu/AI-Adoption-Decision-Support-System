from __future__ import annotations

"""Application configuration helpers."""

import os
from urllib.parse import quote_plus
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

_DEFAULT_MODEL = os.getenv("DSS_HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct:fastest")
_DEFAULT_API_URL = os.getenv(
    "DSS_HF_API_URL",
    "https://router.huggingface.co/v1/chat/completions",
)


class Settings(BaseModel):
    """Typed view over environment-driven configuration."""

    mysql_host: str = Field(
        default_factory=lambda: os.getenv("DSS_MYSQL_HOST", "localhost").strip()
    )
    mysql_port: int = Field(
        default_factory=lambda: int(os.getenv("DSS_MYSQL_PORT", "3306"))
    )
    mysql_user: str = Field(
        default_factory=lambda: os.getenv("DSS_MYSQL_USER", "root").strip()
    )
    mysql_password: str | None = Field(
        default_factory=lambda: os.getenv("DSS_MYSQL_PASSWORD")
    )
    mysql_db: str = Field(
        default_factory=lambda: os.getenv("DSS_MYSQL_DB", "aiadoption").strip()
    )
    mysql_uri: str | None = Field(
        default_factory=lambda: (os.getenv("DSS_MYSQL_URI") or "").strip() or None
    )
    mysql_dsn: str = Field(
        default_factory=lambda: (
            Settings._build_mysql_dsn(
                os.getenv("DSS_MYSQL_URI"),
                os.getenv("DSS_MYSQL_USER", "root"),
                os.getenv("DSS_MYSQL_PASSWORD", ""),
                os.getenv("DSS_MYSQL_HOST", "localhost"),
                os.getenv("DSS_MYSQL_PORT", "3306"),
                os.getenv("DSS_MYSQL_DB", "aiadoption"),
            )
        )
    )

    @staticmethod
    def _build_mysql_dsn(
        uri: str | None,
        user: str,
        password: str,
        host: str,
        port: str,
        db: str,
    ) -> str:
        if uri:
            return uri.strip().strip('"').strip("'")
        quoted_pw = quote_plus(password or "")
        return f"mysql+pymysql://{user}:{quoted_pw}@{host}:{port}/{db}"
    huggingface_model: str = _DEFAULT_MODEL
    huggingface_api_url: str = _DEFAULT_API_URL
    llm_provider: str = Field(
        default_factory=lambda: os.getenv("DSS_LLM_PROVIDER", "huggingface").strip()
    )
    huggingface_token: str | None = Field(
        default_factory=lambda: os.getenv("DSS_HF_TOKEN") or os.getenv("HF_API_TOKEN")
    )
    huggingface_max_new_tokens: int = Field(
        default_factory=lambda: int(os.getenv("DSS_HF_MAX_NEW_TOKENS", "450"))
    )
    huggingface_temperature: float = Field(
        default_factory=lambda: float(os.getenv("DSS_HF_TEMPERATURE", "0.2"))
    )
    mistral_api_key: str | None = Field(
        default_factory=lambda: os.getenv("DSS_MISTRAL_API_KEY")
        or os.getenv("MISTRAL_API_KEY")
    )
    mistral_model: str = Field(
        default_factory=lambda: os.getenv("DSS_MISTRAL_MODEL", "mistral-small").strip()
    )
    mistral_api_url: str = Field(
        default_factory=lambda: os.getenv(
            "DSS_MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions"
        ).strip()
    )
    local_model_id: str | None = Field(
        default_factory=lambda: (os.getenv("DSS_LOCAL_MODEL_ID") or "").strip() or None
    )
    local_prompt_template: str = Field(
        default_factory=lambda: os.getenv(
            "DSS_LOCAL_PROMPT_TEMPLATE", "<|prompter|>{prompt}</s><|assistant|>"
        ).strip()
    )
    local_use_chat_template: bool = Field(
        default_factory=lambda: os.getenv("DSS_LOCAL_USE_CHAT_TEMPLATE", "true")
        .strip()
        .lower()
        in {"1", "true", "yes", "on"}
    )
    local_max_new_tokens: int = Field(
        default_factory=lambda: int(os.getenv("DSS_LOCAL_MAX_TOKENS", "400"))
    )
    local_device_map: str = Field(
        default_factory=lambda: os.getenv("DSS_LOCAL_DEVICE_MAP", "auto").strip()
    )
    local_torch_dtype: str | None = Field(
        default_factory=lambda: (os.getenv("DSS_LOCAL_TORCH_DTYPE", "auto").strip() or None)
    )
    local_use_flash_attention: bool = Field(
        default_factory=lambda: os.getenv("DSS_LOCAL_USE_FLASH_ATTN", "false")
        .strip()
        .lower()
        in {"1", "true", "yes", "on"}
    )
    min_confidence: float = Field(
        default_factory=lambda: float(os.getenv("DSS_MIN_CONFIDENCE", "0.35"))
    )
    timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DSS_HF_TIMEOUT", "25"))
    )

    def normalized_llm_provider(self) -> str:
        provider = self.llm_provider.strip().lower()
        aliases = {
            "hf": "huggingface",
            "hugging_face": "huggingface",
            "text-generation": "huggingface",
        }
        return aliases.get(provider, provider or "huggingface")

    def preferred_llm_providers(self) -> tuple[str, ...]:
        provider = self.normalized_llm_provider()
        if provider == "auto":
            return ("huggingface", "mistral", "local")
        return (provider,)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so FastAPI dependency injection stays cheap."""

    return Settings()
