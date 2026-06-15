"""Canal de Email (esqueleto funcional).

Estrategia: sondear una bandeja de entrada por IMAP cada cierto tiempo, pasar el
cuerpo de cada correo nuevo al cerebro y responder por SMTP. No es tiempo real,
pero funciona con cualquier cuenta (Gmail, Outlook, etc.).

Para activarlo, completa los `TODO` y configura en .env:
  EMAIL_IMAP_HOST, EMAIL_SMTP_HOST, EMAIL_USER, EMAIL_PASSWORD, EMAIL_ALLOWED_SENDERS

Dependencias sugeridas: usa la stdlib (imaplib, smtplib, email) en un executor,
o librerías async como aioimaplib + aiosmtplib.
"""

from __future__ import annotations

import asyncio
import logging

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.email")


class EmailChannel(Channel):
    name = "email"

    def __init__(
        self,
        agent: ProjectAgent,
        imap_host: str,
        smtp_host: str,
        user: str,
        password: str,
        allowed_senders: set[str],
        poll_seconds: int = 30,
    ):
        super().__init__(agent)
        self._imap_host = imap_host
        self._smtp_host = smtp_host
        self._user = user
        self._password = password
        self._allowed = allowed_senders
        self._poll_seconds = poll_seconds
        self._running = False

    async def start(self) -> None:
        self._running = True
        log.info("Canal Email en marcha (sondeo cada %ss).", self._poll_seconds)
        while self._running:
            try:
                await self._poll_once()
            except Exception:
                log.exception("Error sondeando el correo")
            await asyncio.sleep(self._poll_seconds)

    async def stop(self) -> None:
        self._running = False

    async def _poll_once(self) -> None:
        """Lee correos no leídos, los procesa y responde.

        TODO: implementar con imaplib/smtplib (en un executor para no bloquear)
        o con aioimaplib/aiosmtplib. Pasos:
          1. Conectar IMAP, seleccionar INBOX, buscar UNSEEN.
          2. Por cada correo: extraer remitente y cuerpo de texto.
          3. Si el remitente está en self._allowed, llamar a:
                 reply = await self.agent.handle(remitente, cuerpo)
          4. Enviar `reply` por SMTP como respuesta (Re:).
          5. Marcar el correo como leído.
        """
        raise NotImplementedError(
            "EmailChannel es un esqueleto. Implementa _poll_once() para activarlo."
        )
