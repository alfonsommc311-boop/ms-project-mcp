"""Canal de WhatsApp (esqueleto).

WhatsApp es el canal más complejo: requiere la WhatsApp Business Platform (Cloud
API de Meta) o un proveedor como Twilio, con cuenta de pago y verificación de
negocio. Funciona por WEBHOOK, así que necesitas exponer un endpoint HTTPS
público (FastAPI/Flask + un túnel o un servidor).

Variables sugeridas en .env:
  WHATSAPP_TOKEN     -> token de acceso de la app de Meta
  WHATSAPP_PHONE_ID  -> ID del número de teléfono emisor

A diferencia de los demás canales, este NO hace polling: el servidor web recibe
los mensajes entrantes y este "canal" es realmente el manejador del webhook.
"""

from __future__ import annotations

import logging

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.whatsapp")


class WhatsAppChannel(Channel):
    name = "whatsapp"

    def __init__(self, agent: ProjectAgent, token: str, phone_id: str):
        super().__init__(agent)
        self._token = token
        self._phone_id = phone_id

    async def start(self) -> None:
        """Arranca el receptor de webhooks de WhatsApp.

        TODO: levantar un servidor web (FastAPI) con dos rutas:
          - GET  /webhook  -> verificación (responde hub.challenge)
          - POST /webhook  -> mensajes entrantes; por cada uno:
                from_ = msg["from"]
                text  = msg["text"]["body"]
                reply = await self.agent.handle(from_, text)
                # enviar `reply` con POST a la Graph API:
                #   https://graph.facebook.com/v20.0/{phone_id}/messages
                #   Authorization: Bearer {token}

        Recuerda configurar este endpoint público en el panel de Meta y verificar
        la firma (X-Hub-Signature-256) de las peticiones entrantes.
        """
        raise NotImplementedError(
            "WhatsAppChannel es un esqueleto. Implementa el webhook (FastAPI + Graph API)."
        )
