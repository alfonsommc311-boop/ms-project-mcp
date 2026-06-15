"""Canal de Slack (funcional).

Usa Socket Mode con slack_bolt (no requiere URL pública). Crea una app en
https://api.slack.com/apps, activa **Socket Mode**, suscríbete a los eventos
`message.im` / `message.channels` y dale los scopes `chat:write`,
`im:history`/`channels:history`. Obtén:
  SLACK_BOT_TOKEN  (xoxb-...)
  SLACK_APP_TOKEN  (xapp-...)
  SLACK_ALLOWED_USERS  (opcional; vacío = todo el workspace)

Dependencia:  pip install slack_bolt
"""

from __future__ import annotations

import logging

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.slack")


class SlackChannel(Channel):
    name = "slack"

    def __init__(
        self,
        agent: ProjectAgent,
        bot_token: str,
        app_token: str,
        allowed_users: set[str] | None = None,
    ):
        super().__init__(agent)
        self._bot_token = bot_token
        self._app_token = app_token
        self._allowed = allowed_users or set()
        self._handler = None

    async def start(self) -> None:
        try:
            from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
            from slack_bolt.async_app import AsyncApp
        except ImportError as exc:  # pragma: no cover - depende de instalación
            raise RuntimeError(
                "Falta slack_bolt. Instálalo con: pip install slack_bolt"
            ) from exc

        app = AsyncApp(token=self._bot_token)

        @app.event("message")
        async def on_message(event, say):  # noqa: ANN001
            # Ignora mensajes de bots y ediciones/borrados (subtype presente).
            if event.get("bot_id") or event.get("subtype"):
                return
            user = event.get("user", "")
            if self._allowed and user not in self._allowed:
                log.warning("Usuario de Slack %s no autorizado.", user)
                await say("⛔ No estás autorizado para usar este bot.")
                return
            text = event.get("text", "")
            # Conversación por canal (DM o canal). El cerebro mantiene el hilo.
            cid = event.get("channel", user)
            log.info("Mensaje de Slack de %s en %s", user, cid)
            reply = await self.agent.handle(cid, text)
            await say(reply)

        self._handler = AsyncSocketModeHandler(app, self._app_token)
        log.info("Canal Slack en marcha (Socket Mode).")
        await self._handler.start_async()  # bloquea hasta cerrar

    async def stop(self) -> None:
        if self._handler is not None:
            try:
                await self._handler.close_async()
            except Exception:
                log.exception("Error cerrando Slack")
