"""Configuración del bot — se lee desde variables de entorno.

Carga un archivo `.env` si existe (usando python-dotenv) para facilitar el
desarrollo local. En producción, define las variables en el entorno del proceso.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv es opcional
    pass


def _split_ids(raw: str | None) -> set[str]:
    """Convierte "111,222 333" en {"111", "222", "333"}."""
    if not raw:
        return set()
    return {p for p in raw.replace(",", " ").split() if p}


@dataclass
class Config:
    # --- Cerebro (Claude / Anthropic) ---
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.environ.get("BOT_MODEL", "claude-opus-4-8"))
    # Cuántos mensajes de historial conservar por conversación (pares user/assistant).
    history_limit: int = field(default_factory=lambda: int(os.environ.get("BOT_HISTORY_LIMIT", "40")))

    # --- Servidor MCP de MS Project ---
    # Comando que lanza el servidor MCP (server.py) por stdio.
    # Por defecto: "python <ruta>/server.py" en la raíz del repo.
    mcp_server_cmd: str = field(default_factory=lambda: os.environ.get("MSPROJECT_SERVER_CMD", ""))

    # --- Canal: Telegram ---
    telegram_token: str = field(default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN", ""))
    # Lista blanca de chat IDs autorizados. Si está vacía, el bot RECHAZA a todos
    # (medida de seguridad: este bot puede modificar tu proyecto).
    telegram_allowed_ids: set[str] = field(
        default_factory=lambda: _split_ids(os.environ.get("TELEGRAM_ALLOWED_IDS"))
    )

    # --- Canal: Email (esqueleto) ---
    email_imap_host: str = field(default_factory=lambda: os.environ.get("EMAIL_IMAP_HOST", ""))
    email_smtp_host: str = field(default_factory=lambda: os.environ.get("EMAIL_SMTP_HOST", ""))
    email_user: str = field(default_factory=lambda: os.environ.get("EMAIL_USER", ""))
    email_password: str = field(default_factory=lambda: os.environ.get("EMAIL_PASSWORD", ""))
    email_allowed: set[str] = field(
        default_factory=lambda: _split_ids(os.environ.get("EMAIL_ALLOWED_SENDERS"))
    )

    # --- Canal: Slack (esqueleto) ---
    slack_bot_token: str = field(default_factory=lambda: os.environ.get("SLACK_BOT_TOKEN", ""))
    slack_app_token: str = field(default_factory=lambda: os.environ.get("SLACK_APP_TOKEN", ""))

    # --- Canal: WhatsApp (esqueleto) ---
    whatsapp_token: str = field(default_factory=lambda: os.environ.get("WHATSAPP_TOKEN", ""))
    whatsapp_phone_id: str = field(default_factory=lambda: os.environ.get("WHATSAPP_PHONE_ID", ""))

    def mcp_command(self) -> list[str]:
        """Devuelve el comando + args para lanzar el servidor MCP por stdio."""
        if self.mcp_server_cmd:
            return shlex.split(self.mcp_server_cmd)
        # Por defecto: server.py en la raíz del repo (un nivel por encima de bot/).
        here = os.path.dirname(os.path.abspath(__file__))
        server_py = os.path.normpath(os.path.join(here, "..", "server.py"))
        import sys

        return [sys.executable, server_py]

    def validate(self) -> None:
        if not self.anthropic_api_key:
            raise SystemExit(
                "Falta ANTHROPIC_API_KEY. Consíguela en https://console.anthropic.com "
                "y ponla en tu archivo .env o variable de entorno."
            )


def load_config() -> Config:
    cfg = Config()
    cfg.validate()
    return cfg
