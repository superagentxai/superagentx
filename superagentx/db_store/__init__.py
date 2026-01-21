from dotenv import load_dotenv
from superagentx.db_store.db_interface import StorageAdapter
from superagentx.db_store.db_storage import SQLiteStorage, PostgresStorage, SQLBaseStorage
import os
import logging

logger = logging.getLogger(__name__)


class StorageFactory:
    @staticmethod
    async def get_storage(provider: str, config: dict) -> StorageAdapter:
        providers = {
            "sqlite": SQLiteStorage,
            "postgres": PostgresStorage
            # "mongodb": MongoStorage
        }
        if provider not in providers:
            raise ValueError(f"Provider {provider} not supported.")

        # Unpack the config dictionary directly into the class constructor
        return providers[provider](**config)


class ConfigLoader:
    @staticmethod
    async def load_db_config() -> StorageAdapter:
        # 1. Load the .env file into os.environ
        load_dotenv()

        # 2. Determine Provider (Default to sqlite if not set)
        provider = os.getenv("DB_PROVIDER", "sqlite").lower()

        # 3. Build configuration dictionary based on provider
        provider_config = {}

        if provider == "sqlite":
            provider_config["db_path"] = os.getenv("SQLITE_DB_PATH", "agents.db")

        elif provider == "postgres":
            provider_config["host"] = os.getenv("POSTGRES_HOST", "localhost")
            provider_config["user"] = os.getenv("POSTGRES_USER")
            provider_config["password"] = os.getenv("POSTGRES_PASSWORD")
            provider_config["db"] = os.getenv("POSTGRES_DB")
            provider_config["port"] = int(os.getenv("POSTGRES_PORT", 5432))

            # Basic Validation for Postgres
            if not all([provider_config["user"], provider_config["password"], provider_config["db"]]):
                raise ValueError("Postgres requires POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB in .env")

        elif provider == "mongodb":
            provider_config["uri"] = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            provider_config["db_name"] = os.getenv("MONGO_DB_NAME", "agent_db")

        else:
            raise ValueError(f"Unsupported database provider: {provider}")

        logger.info(f"🔧 Initializing storage: {provider}")
        return await StorageFactory.get_storage(provider, provider_config)
