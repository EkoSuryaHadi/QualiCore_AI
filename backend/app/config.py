from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./qualicore.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:3000"
    auto_bootstrap: bool = False
    seed_demo: bool = False
    frontend_url: str = "http://localhost:3000"
    # Enable only in controlled test environments. Production should deliver
    # reset/verification links through an email provider instead of API responses.
    auth_link_preview: bool = False
    # Vercel Functions expose a read-only application filesystem.
    # /tmp is the writable ephemeral location supported at runtime.
    upload_dir: str = "/tmp/qualicore_uploads"
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def cors_list(self):
        values = [x.strip() for x in self.cors_origins.split(",") if x.strip()]
        return values or ["http://localhost:3000"]


settings = Settings()
