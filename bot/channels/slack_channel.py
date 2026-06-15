"""Canal de Slack (esqueleto funcional).

Estrategia recomendada: Socket Mode con slack_bolt (no requiere URL pública).
Crea una app en https://api.slack.com/apps, activa Socket Mode y los eventos de
mensaje, y obtén:
  SLACK_BOT_TOKEN  (xoxb-...)  -> permisos del bot
  SLACK_APP_TOKEN  (xapp-...)  -> Socket Mode

Dependencia sugerida: `pip install slack_bolt`
"""

from __future__ import annotations

import logging

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.slack")


class SlackChannel(Channel):
    name = "slack"

    def __init__(self, agent: ProjectAgent, bot_token: str, app_token: str):
        super().__init__(agent)
        self._bot_token = bot_token
        self._app_token = app_token

    async def start(self) -> None:
        """Arranca Slack en Socket Mode.

        TODO: implementar con slack_bolt.async_app. Boceto:

            from slack_bolt.async_app import AsyncApp
            from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

            app = AsyncApp(token=self._bot_token)

            @app.event("message")
            async def on_message(event, say):
                if event.get("bot_id"):
                    return  # ignora mensajes de bots
                cid = event["channel"]
                reply = await self.agent.handle(cid, event.get("text", ""))
                await say(reply)

            handler = AsyncSocketModeHandler(app, self._app_token)
            await handler.start_async()
        """
        raise NotImplementedError(
            "SlackChannel es un esqueleto. Implementa start() con slack_bolt para activarlo."
        )
