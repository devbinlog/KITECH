from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # VM 관련
    vm_api_url: str
    vm_username: str
    vm_password: str

    # DP 관련
    dp_base_url: str
    dp_api_key: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
