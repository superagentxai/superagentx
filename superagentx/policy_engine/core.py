import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from cedarpy import is_authorized, Decision
from superagentx.policy_engine.crypto import verify_signature

logger = logging.getLogger("GenericPolicyEngine")


class GenericPolicyEngine:
    def __init__(self, policies_path: str, entities_path: str):
        """
        Initializes the engine by loading external policy and entity files.
        """
        self.policies_path = policies_path
        self.entities_path = entities_path
        self.policy_store: str = ""
        self.entities_store: List[Dict[str, Any]] = []
        self.reload_assets()

    def reload_assets(self) -> None:
        """Loads or refreshes policies and entities from disk into memory."""
        try:
            with open(self.policies_path, "r") as f:
                self.policy_store = f.read()
            with open(self.entities_path, "r") as f:
                self.entities_store = json.load(f)
            logger.info("Successfully loaded external Cedar assets.")
        except Exception as e:
            logger.error(f"Failed to initialize asset stores: {e}")
            raise

    def authorize_request(
            self,
            *,
            principal: Tuple[str, str],  # e.g., ("User", "alice")
            action: Tuple[str, str],  # e.g., ("Action", "ExecuteWorkflow")
            resource: Tuple[str, str],  # e.g., ("Agent", "EmailBot")
            context: Dict[str, Any],  # Extracted key-values
            crypto_packet: Optional[Dict[str, Any]] = None,
            raw_payload_to_verify: Optional[str] = None
    ) -> bool:
        """
        Evaluates an abstract request against loaded policies.
        Optionally runs cryptographic verification before checking policy authorization.
        """
        # Step 1: Optional Cryptographic Pre-flight Authentication Gate
        if crypto_packet:
            if not raw_payload_to_verify:
                logger.error("Crypto packet provided but missing raw payload to verify.")
                return False

            is_valid = verify_signature(
                public_key_bytes=crypto_packet["public_key"],
                payload=raw_payload_to_verify,
                signature_b64=crypto_packet["signature_b64"]
            )
            if not is_valid:
                logger.warning(f"Crypto Auth Fail for Principal {principal[0]}::{principal[1]}")
                return False
            logger.info("Crypto Auth Pass.")

        # Step 2: Format strings directly into Cedar format strings
        cedar_request = {
            "principal": f'{principal[0]}::"{principal[1]}"',
            "action": f'{action[0]}::"{action[1]}"',
            "resource": f'{resource[0]}::"{resource[1]}"',
            "context": context
        }

        # Step 3: Evaluate via Cedar Policy engine bindings
        try:
            result = is_authorized(
                request=cedar_request,
                policies=self.policy_store,
                entities=self.entities_store
            )
            return result.decision == Decision.Allow
        except Exception as e:
            logger.error(f"Cedar Engine evaluation exception encountered: {e}")
            return False