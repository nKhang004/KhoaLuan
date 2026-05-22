from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/ngan_hang_cau_hoi"
    SECRET_KEY: str = "khoaluan2026_secret_key_very_long_random_string_here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()