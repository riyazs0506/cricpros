import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Base configuration.

    Secrets and database URLs must be provided via environment variables. Do NOT
    commit secrets to source control. For local development you can create a
    `.env` file (already gitignored) and set values there.

    Example (in `.env` - do NOT commit):
    SECRET_KEY=replace-with-a-random-secret
    DATABASE_URL=mysql+pymysql://user:password@host:port/dbname
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")

    # Use DATABASE_URL from the environment; fall back to a local sqlite DB for
    # safe development if not set.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///cricpros_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    PAYMENT_SIMULATE = False