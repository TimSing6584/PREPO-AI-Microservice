# src/config.py
import os
from infisical_sdk import InfisicalSDKClient
from dotenv import load_dotenv

load_dotenv()  # ← load .env into os.environ first

def _load_infisical_secrets():
    client = InfisicalSDKClient(host=os.getenv("INFISICAL_HOST", "https://app.infisical.com"))

    # --- detect which auth method is available ---
    if os.getenv("INFISICAL_SERVICE_TOKEN"):
        client.auth.token_auth.login(
            token=os.environ["INFISICAL_SERVICE_TOKEN"]
        )

    elif os.getenv("INFISICAL_CLIENT_ID") and os.getenv("INFISICAL_CLIENT_SECRET"):
        client.auth.universal_auth.login(
            client_id=os.environ["INFISICAL_CLIENT_ID"],
            client_secret=os.environ["INFISICAL_CLIENT_SECRET"],
        )

    else:
        # no Infisical credentials found — fall back to local .env
        print("[config] No Infisical credentials found, using local .env")
        return

    secrets = client.secrets.list_secrets(
        project_id=os.environ["INFISICAL_PROJECT_ID"],
        environment_slug=os.getenv("INFISICAL_ENV", "dev"),
        secret_path="/",
    )
    for s in secrets.secrets:
        os.environ[s.secretKey] = s.secretValue

    print(f"[config] Loaded {len(secrets.secrets)} secrets from Infisical")

_load_infisical_secrets()