from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://horizonai:horizonai_dev@localhost:5432/horizonai"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    golden_dataset_path: str = "golden_dataset.json"

    # LLM mode: mock (CI / no keys) or live (real inference via OpenRouter)
    llm_mode: str = "mock"

    # OpenRouter — all model tiers route through one API key
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "https://github.com/mayukhg/ai-product-horizon"
    openrouter_app_name: str = "HorizonAI CyberRisk Resident"

    smart_intern_model: str = "meta-llama/llama-3.3-70b-instruct"
    guardrail_model: str = "meta-llama/llama-guard-3-8b"
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dimensions: int = 1536
    phd_reasoner_model: str = "anthropic/claude-sonnet-4"
    phd_reasoner_escalation_model: str = "anthropic/claude-opus-4"
    judge_model: str = "anthropic/claude-sonnet-4"

    # Eval release gates
    eval_groundedness_block_threshold: float = 0.90
    eval_groundedness_warn_threshold: float = 0.92
    eval_pass_rate_block_threshold: float = 0.93
    eval_pass_rate_warn_threshold: float = 0.95

    # API auth (separate from OpenRouter)
    auth_required: bool = False
    auth_jwt_secret: str = ""
    auth_jwt_algorithm: str = "HS256"
    auth_jwt_audience: str = "horizonai-api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_live_llm(self) -> bool:
        return self.llm_mode.lower() == "live"

    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key.strip())


settings = Settings()
