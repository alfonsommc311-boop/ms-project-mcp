"""Canal de WhatsApp (funcional, vía WhatsApp Cloud API de Meta).

Levanta un servidor web (FastAPI + uvicorn) que recibe los webhooks de Meta y
responde por la Graph API. Necesitas:
  - Una app de Meta con un número de WhatsApp Business (Cloud API).
  - Exponer este endpoint con HTTPS público (un servidor o un túnel tipo ngrok).

Variables en .env:
  WHATSAPP_TOKEN          -> token de acceso de la app de Meta
  WHATSAPP_PHONE_ID       -> ID del número emisor
  WHATSAPP_VERIFY_TOKEN   -> token que tú eliges y pones en el panel de Meta
  WHATSAPP_HOST/PORT      -> dónde escucha el servidor (por defecto 0.0.0.0:8080)
  WHATSAPP_ALLOWED_NUMBERS-> lista blanca de números (intl. sin '+'); vacío = rechaza

Dependencias:  pip install fastapi uvicorn   (httpx ya viene con anthropic)

En el panel de Meta configura el webhook apuntando a  https://TU_DOMINIO/webhook
con el mismo Verify Token.
"""

from __future__ import annotations

import logging

import httpx

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.whatsapp")


class WhatsAppChannel(Channel):
    name = "whatsapp"

    def __init__(
        self,
        agent: ProjectAgent,
        token: str,
        phone_id: str,
        verify_token: str,
        host: str = "0.0.0.0",
        port: int = 8080,
        graph_version: str = "v20.0",
        allowed_numbers: set[str] | None = None,
    ):
        super().__init__(agent)
        self._token = token
        self._phone_id = phone_id
        self._verify_token = verify_token
        self._host = host
        self._port = port
        self._graph_version = graph_version
        self._allowed = allowed_numbers or set()
        self._server = None

    async def start(self) -> None:
        try:
            import uvicorn
            from fastapi import FastAPI, Request, Response
        except ImportError as exc:  # pragma: no cover - depende de instalación
            raise RuntimeError(
                "Faltan dependencias. Instala con: pip install fastapi uvicorn"
            ) from exc

        app = FastAPI()

        @app.get("/webhook")
        async def verify(request: Request):  # noqa: ANN001
            params = request.query_params
            if (
                params.get("hub.mode") == "subscribe"
                and params.get("hub.verify_token") == self._verify_token
            ):
                return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
            return Response(status_code=403)

        @app.post("/webhook")
        async def incoming(request: Request):  # noqa: ANN001
            data = await request.json()
            for from_number, text in _iter_messages(data):
                if self._allowed and from_number not in self._allowed:
                    log.warning("Número de WhatsApp %s no autorizado.", from_number)
                    continue
                log.info("Mensaje de WhatsApp de %s", from_number)
                reply = await self.agent.handle(from_number, text)
                await self._send(from_number, reply)
            return Response(status_code=200)

        config = uvicorn.Config(
            app, host=self._host, port=self._port, log_level="info", loop="asyncio"
        )
        self._server = uvicorn.Server(config)
        log.info("Canal WhatsApp en marcha (webhook en %s:%s/webhook).", self._host, self._port)
        await self._server.serve()  # bloquea hasta should_exit

    async def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True

    async def _send(self, to_number: str, body: str) -> None:
        url = f"https://graph.facebook.com/{self._graph_version}/{self._phone_id}/messages"
        headers = {"Authorization": f"Bearer {self._token}"}
        # WhatsApp limita a 4096 caracteres por mensaje de texto.
        async with httpx.AsyncClient(timeout=30) as client:
            for chunk in _split(body, 4000):
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to_number,
                    "type": "text",
                    "text": {"body": chunk},
                }
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    log.error("Graph API devolvió %s: %s", resp.status_code, resp.text)


def _iter_messages(data: dict):
    """Recorre el payload de Meta y produce (numero_remitente, texto)."""
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                yield msg.get("from", ""), msg.get("text", {}).get("body", "")


def _split(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    return [text[i : i + size] for i in range(0, len(text), size)]
