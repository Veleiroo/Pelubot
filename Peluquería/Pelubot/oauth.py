# oauth.py
"""
Script para obtener y guardar el token OAuth de Google Calendar.
Utiliza el flujo de autorización local y guarda el token en oauth_tokens.json.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    here = Path(__file__).resolve().parent
    # Cliente OAuth (autorizacion.json) relativo al módulo
    client_secrets = here / "autorizacion.json"
    if not client_secrets.exists():
        raise FileNotFoundError(f"No se encuentra {client_secrets}")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    creds = flow.run_local_server(port=0)  # abrirá el navegador

    # Destino del token: GOOGLE_OAUTH_JSON si está, si no, Pelubot/oauth_tokens.json
    dest_env = os.getenv("GOOGLE_OAUTH_JSON", "").strip()
    if dest_env and not dest_env.startswith("{"):
        dest = Path(dest_env).expanduser().resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
    else:
        dest = here / "oauth_tokens.json"

    dest.write_text(creds.to_json(), encoding="utf-8")
    print(f"Token OAuth guardado en {dest}")


if __name__ == "__main__":
    main()
