"""Interfaz común de los canales de mensajería.

Un canal es una "puerta" (Telegram, Email, Slack, WhatsApp). Todos comparten el
mismo cerebro (ProjectAgent): reciben texto del usuario, llaman a
`agent.handle(conversation_id, texto)` y devuelven la respuesta por su medio.
"""

from __future__ import annotations

import abc

from ..agent import ProjectAgent


class Channel(abc.ABC):
    name: str = "canal"

    def __init__(self, agent: ProjectAgent):
        self.agent = agent

    @abc.abstractmethod
    async def start(self) -> None:
        """Arranca el canal y se queda escuchando mensajes."""

    async def stop(self) -> None:
        """Detiene el canal de forma ordenada (opcional)."""
