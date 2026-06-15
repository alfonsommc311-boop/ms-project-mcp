"""Canal de Email (funcional).

Sondea una bandeja de entrada por IMAP cada cierto tiempo, pasa el cuerpo de
cada correo nuevo al cerebro y responde por SMTP. No es tiempo real, pero
funciona con cualquier cuenta (Gmail, Outlook, etc.) usando sólo la stdlib.

Configura en .env:
  EMAIL_IMAP_HOST, EMAIL_IMAP_PORT (993), EMAIL_SMTP_HOST, EMAIL_SMTP_PORT (465),
  EMAIL_USER, EMAIL_PASSWORD, EMAIL_ALLOWED_SENDERS, EMAIL_POLL_SECONDS

Notas:
- Gmail/Outlook requieren una "contraseña de aplicación" (no tu contraseña normal).
- IMAP/SMTP son bloqueantes: se ejecutan en un hilo (asyncio.to_thread). El
  cerebro (que usa la sesión MCP del loop principal) se llama en el loop principal.
"""

from __future__ import annotations

import asyncio
import email
import imaplib
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.email")


@dataclass
class _Incoming:
    sender: str
    subject: str
    body: str
    message_id: str | None


class EmailChannel(Channel):
    name = "email"

    def __init__(
        self,
        agent: ProjectAgent,
        imap_host: str,
        imap_port: int,
        smtp_host: str,
        smtp_port: int,
        user: str,
        password: str,
        allowed_senders: set[str],
        poll_seconds: int = 30,
    ):
        super().__init__(agent)
        self._imap_host = imap_host
        self._imap_port = imap_port
        self._smtp_host = smtp_host or imap_host.replace("imap", "smtp")
        self._smtp_port = smtp_port
        self._user = user
        self._password = password
        self._allowed = {a.lower() for a in allowed_senders}
        self._poll_seconds = poll_seconds
        self._running = False

    async def start(self) -> None:
        self._running = True
        log.info("Canal Email en marcha (sondeo cada %ss).", self._poll_seconds)
        while self._running:
            try:
                incoming = await asyncio.to_thread(self._fetch_unseen)
                for item in incoming:
                    if not self._allowed or item.sender not in self._allowed:
                        log.warning("Correo de %s ignorado (no autorizado).", item.sender)
                        continue
                    log.info("Email de %s | asunto: %s", item.sender, item.subject)
                    reply = await self.agent.handle(item.sender, item.body)
                    await asyncio.to_thread(
                        self._send_reply, item.sender, item.subject, reply, item.message_id
                    )
            except Exception:
                log.exception("Error sondeando el correo")
            for _ in range(self._poll_seconds):
                if not self._running:
                    break
                await asyncio.sleep(1)

    async def stop(self) -> None:
        self._running = False

    # ----- Trabajo bloqueante (corre en un hilo) -----

    def _fetch_unseen(self) -> list[_Incoming]:
        """Lee los correos no leídos, los marca como leídos y los devuelve."""
        out: list[_Incoming] = []
        ctx = ssl.create_default_context()
        with imaplib.IMAP4_SSL(self._imap_host, self._imap_port, ssl_context=ctx) as imap:
            imap.login(self._user, self._password)
            imap.select("INBOX")
            typ, data = imap.search(None, "UNSEEN")
            if typ != "OK":
                return out
            for num in data[0].split():
                typ, msg_data = imap.fetch(num, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                imap.store(num, "+FLAGS", "\\Seen")  # no reprocesar
                sender = parseaddr(msg.get("From", ""))[1].lower()
                body = _extract_text(msg)
                if not sender or not body.strip():
                    continue
                subject = str(make_header(decode_header(msg.get("Subject", "")))) or "(sin asunto)"
                out.append(_Incoming(sender, subject, body, msg.get("Message-ID")))
        return out

    def _send_reply(self, to_addr: str, subject: str, body: str, in_reply_to: str | None) -> None:
        out = EmailMessage()
        out["From"] = self._user
        out["To"] = to_addr
        out["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        if in_reply_to:
            out["In-Reply-To"] = in_reply_to
            out["References"] = in_reply_to
        out.set_content(body)

        ctx = ssl.create_default_context()
        if self._smtp_port == 465:
            with smtplib.SMTP_SSL(self._smtp_host, self._smtp_port, context=ctx) as smtp:
                smtp.login(self._user, self._password)
                smtp.send_message(out)
        else:  # 587 / STARTTLS
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as smtp:
                smtp.starttls(context=ctx)
                smtp.login(self._user, self._password)
                smtp.send_message(out)
        log.info("Respondido a %s", to_addr)


def _extract_text(msg: email.message.Message) -> str:
    """Extrae el cuerpo en texto plano de un correo (multipart o simple)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition", "")
            ):
                return _decode_part(part)
        return ""
    return _decode_part(msg)


def _decode_part(part: email.message.Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, ValueError):
        return payload.decode("utf-8", errors="replace")
