from superagentx.db_store.db_interface import StorageAdapter
from superagentx.db_store.db_storage import SQLiteStorage, PostgresStorage, SQLBaseStorage
import yaml
import os


class StorageFactory:
    @staticmethod
    def get_storage(provider: str, config: dict) -> StorageAdapter:
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
    def load_db_config(file_path: str = "config.yaml") -> StorageAdapter:
        # 1. Load YAML as the base configuration
        full_config = {}
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                full_config = yaml.safe_load(f) or {}

        db_settings = full_config.get("database", {})

        # 2. Determine Provider (Env Var takes priority)
        # Env Var: DB_PROVIDER="postgres"
        provider = os.getenv("DB_PROVIDER", db_settings.get("active_provider"))

        if not provider:
            raise ValueError("No database provider specified in YAML or Environment Variables.")

        # 3. Get Provider-specific config from YAML
        provider_config = db_settings.get(provider, {})

        # 4. Overwrite YAML settings with Environment Variables if they exist
        # Mapping standard env naming to your provider keys
        if provider == "sqlite":
            provider_config["db_path"] = os.getenv("SQLITE_DB_PATH", provider_config.get("db_path", "agents.db"))

        elif provider == "postgres":
            provider_config["host"] = os.getenv("POSTGRES_HOST", provider_config.get("host"))
            provider_config["user"] = os.getenv("POSTGRES_USER", provider_config.get("user"))
            provider_config["password"] = os.getenv("POSTGRES_PASSWORD", provider_config.get("password"))
            provider_config["db"] = os.getenv("POSTGRES_DB", provider_config.get("db"))
            provider_config["port"] = int(os.getenv("POSTGRES_PORT", provider_config.get("port", 5432)))

        elif provider == "mongodb":
            provider_config["uri"] = os.getenv("MONGO_URI", provider_config.get("uri"))
            provider_config["db_name"] = os.getenv("MONGO_DB_NAME", provider_config.get("db_name"))

        print(f" Initializing storage provider: {provider} (via {'Env' if os.getenv('DB_PROVIDER') else 'YAML'})")
        return StorageFactory.get_storage(provider, provider_config)
