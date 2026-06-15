"""Canal de Telegram (funcional).

Usa python-telegram-bot (v21+, asíncrono). Sólo responde a los chat IDs que
estén en la lista blanca (TELEGRAM_ALLOWED_IDS), porque el bot puede modificar
tu proyecto.

Cómo obtener un token: habla con @BotFather en Telegram, crea un bot y copia el
token. Para saber tu chat ID, escribe a tu bot y mira el log (lo imprime), o
usa @userinfobot.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..agent import ProjectAgent
from .base import Channel

log = logging.getLogger("bot.telegram")

WELCOME = (
    "👋 Hola, soy tu asistente de MS Project.\n\n"
    "Escríbeme en lenguaje natural, por ejemplo:\n"
    "• ¿Qué tareas van retrasadas?\n"
    "• Dame el resumen de progreso del proyecto\n"
    "• ¿Cuáles son los próximos hitos?\n"
    "• Pon la tarea 12 en rojo (RAG)\n\n"
    "Comandos: /start /reset /ayuda"
)


class TelegramChannel(Channel):
    name = "telegram"

    def __init__(self, agent: ProjectAgent, token: str, allowed_ids: set[str]):
        super().__init__(agent)
        self._token = token
        self._allowed = allowed_ids
        self._app: Application | None = None

    def _authorized(self, update: Update) -> bool:
        chat = update.effective_chat
        if chat is None:
            return False
        cid = str(chat.id)
        if not self._allowed:
            log.warning(
                "Chat %s bloqueado: TELEGRAM_ALLOWED_IDS está vacío. "
                "Añade %s a la lista blanca para autorizarlo.",
                cid,
                cid,
            )
            return False
        return cid in self._allowed

    async def _on_start(self, update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        log.info("Mensaje /start del chat %s", update.effective_chat.id)
        if not self._authorized(update):
            await update.message.reply_text(
                f"⛔ No estás autorizado. Tu chat ID es {update.effective_chat.id}. "
                "Pídele al administrador que lo añada a la lista blanca."
            )
            return
        await update.message.reply_text(WELCOME)

    async def _on_reset(self, update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        self.agent.reset(str(update.effective_chat.id))
        await update.message.reply_text("🧹 Conversación reiniciada.")

    async def _on_message(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            await update.message.reply_text(
                f"⛔ No estás autorizado. Tu chat ID es {update.effective_chat.id}."
            )
            return

        text = update.message.text or ""
        cid = str(update.effective_chat.id)
        # Indicador "escribiendo…" mientras el cerebro trabaja.
        await ctx.bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)

        reply = await self.agent.handle(cid, text)
        # Telegram limita a 4096 caracteres por mensaje.
        for chunk in _split(reply, 4000):
            await update.message.reply_text(chunk)

    async def start(self) -> None:
        app = Application.builder().token(self._token).build()
        app.add_handler(CommandHandler(["start", "ayuda", "help"], self._on_start))
        app.add_handler(CommandHandler("reset", self._on_reset))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        self._app = app

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        log.info("Canal Telegram en marcha (escuchando mensajes).")

    async def stop(self) -> None:
        if self._app is None:
            return
        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()


def _split(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    return [text[i : i + size] for i in range(0, len(text), size)]
