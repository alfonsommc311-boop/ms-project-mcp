"""Punto de entrada del bot.

Levanta el servidor MCP de MS Project, crea el cerebro (Claude) y arranca todos
los canales para los que haya credenciales configuradas.

Uso:
    python -m bot.run
"""

from __future__ import annotations

import asyncio
import logging
import signal

from .agent import ProjectAgent
from .channels.base import Channel
from .config import Config, load_config
from .mcp_link import MCPLink

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bot")


def build_channels(cfg: Config, agent: ProjectAgent) -> list[Channel]:
    """Crea los canales según las credenciales presentes en la configuración."""
    channels: list[Channel] = []

    if cfg.telegram_token:
        from .channels.telegram_channel import TelegramChannel

        channels.append(TelegramChannel(agent, cfg.telegram_token, cfg.telegram_allowed_ids))

    if cfg.email_imap_host and cfg.email_user:
        from .channels.email_channel import EmailChannel

        channels.append(
            EmailChannel(
                agent,
                cfg.email_imap_host,
                cfg.email_smtp_host,
                cfg.email_user,
                cfg.email_password,
                cfg.email_allowed,
            )
        )

    if cfg.slack_bot_token and cfg.slack_app_token:
        from .channels.slack_channel import SlackChannel

        channels.append(SlackChannel(agent, cfg.slack_bot_token, cfg.slack_app_token))

    if cfg.whatsapp_token and cfg.whatsapp_phone_id:
        from .channels.whatsapp_channel import WhatsAppChannel

        channels.append(WhatsAppChannel(agent, cfg.whatsapp_token, cfg.whatsapp_phone_id))

    return channels


async def main() -> None:
    cfg = load_config()

    mcp = MCPLink(cfg.mcp_command())
    log.info("Arrancando servidor MCP: %s", " ".join(cfg.mcp_command()))
    await mcp.open()

    agent = ProjectAgent(
        mcp,
        api_key=cfg.anthropic_api_key,
        model=cfg.model,
        history_limit=cfg.history_limit,
    )

    channels = build_channels(cfg, agent)
    if not channels:
        await mcp.close()
        raise SystemExit(
            "No hay ningún canal configurado. Define al menos TELEGRAM_BOT_TOKEN "
            "(y TELEGRAM_ALLOWED_IDS) en tu .env. Ver bot/README.md."
        )

    log.info("Canales activos: %s", ", ".join(c.name for c in channels))

    # Señal de parada (Ctrl+C / SIGTERM).
    stop = asyncio.Event()

    def _request_stop(*_a):
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            pass  # Windows no soporta add_signal_handler para SIGTERM

    # Cada canal corre como tarea: Telegram arranca el polling y retorna; otros
    # (Email) se quedan en bucle. Si una tarea falla, lo registramos.
    def _log_task_error(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            log.error("El canal terminó con error: %r", exc)

    tasks: list[asyncio.Task] = []
    for ch in channels:
        t = asyncio.create_task(ch.start(), name=ch.name)
        t.add_done_callback(_log_task_error)
        tasks.append(t)

    try:
        log.info("Bot en marcha. Pulsa Ctrl+C para salir.")
        await stop.wait()
    finally:
        log.info("Apagando…")
        for ch in channels:
            try:
                await ch.stop()
            except Exception:
                log.exception("Error parando el canal %s", ch.name)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await mcp.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
