"""Configuration management using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # BYOC OAuth settings
    client_id: str
    client_secret: str
    jwt_secret: str
    port: int = 3000
    
    # WeChat Service Account settings
    wechat_appid: str
    wechat_appsecret: str
    wechat_token: str
    wechat_encoding_aes_key: str = ""  # Optional, for encrypted messages
    
    # CXone Digital Engagement settings
    cxone_base_url: str
    cxone_bearer_token: str
    cxone_channel_id: str
    
    # Mock mode settings (for testing without real APIs)
    mock_mode: bool = False  # Set to True to use mock implementations
    mock_cxone_port: int = 8001  # Port for mock CXone server
    mock_wechat_port: int = 8002  # Port for mock WeChat server
    
    # Logging settings
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    json_logs: bool = False  # Set to True for JSON log output
    
    # HTTP client settings
    http_timeout: int = 30  # HTTP request timeout in seconds
    http_max_retries: int = 3  # Maximum retry attempts
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

