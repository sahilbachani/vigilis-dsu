from dotenv import load_dotenv
import os

load_dotenv()  # load variables from .env

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    JWT_SECRET = os.getenv("JWT_SECRET")

settings = Settings()
