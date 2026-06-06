import asyncio
from superagentx.policy_engine.core import GenericPolicyEngine
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64


async def main():
    # 1. Spin up the engine pointing to assets
    engine = GenericPolicyEngine(
        policies_path="policies.cedar",
        entities_path="entities.json"
    )

    # 2. Simulate User Client Cryptographic Signing setup
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key_bytes = private_key.public_key().public_bytes_raw()


    instruction_payload = "Process transaction dataset alpha"
    sig_bytes = private_key.sign(instruction_payload.encode('utf-8'))
    sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')

    crypto_packet = {
        "public_key": public_key_bytes,
        "signature_b64": sig_b64
    }

    # 3. Evaluate Authorizations Abstractly
    is_allowed = engine.authorize_request(
        principal=("User", "user_ram"),
        action=("Action", "RunTask"),
        resource=("Service", "SuperAgentX_Worker"),
        context={"depth": 3},
        crypto_packet=crypto_packet,
        raw_payload_to_verify=instruction_payload
    )

    print(f"🔒 Final Policy Decision Outcome: {is_allowed}")


if __name__ == "__main__":
    asyncio.run(main())