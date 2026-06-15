"""El cerebro del bot: traduce lenguaje natural a acciones sobre MS Project.

Usa la API de Claude (Anthropic) con tool-use. Recibe un mensaje del usuario,
deja que Claude razone y llame a las herramientas del servidor MCP, y devuelve
la respuesta final en lenguaje natural.
"""

from __future__ import annotations

import asyncio
import logging

from anthropic import AsyncAnthropic

from .mcp_link import MCPLink

log = logging.getLogger("bot.agent")

SYSTEM_PROMPT = """\
Eres un asistente de gestión de proyectos que opera sobre Microsoft Project a \
través de una serie de herramientas. El usuario te escribe por mensajería \
(Telegram, email, etc.) en lenguaje natural, normalmente en español.

Tu trabajo:
- Interpretar lo que pide el usuario y usar las herramientas disponibles para \
consultar o modificar el proyecto.
- Responder de forma breve y clara, lista para leerse en un chat de móvil. Evita \
tablas enormes; resume y destaca lo importante (tareas retrasadas, hitos, RAG, etc.).
- Usa el formato de fechas DD/MM/AAAA.

Reglas de seguridad importantes:
- Antes de hacer cambios DESTRUCTIVOS o de gran alcance (borrar tareas/recursos, \
actualizaciones masivas, reprogramar todo el proyecto), confirma con el usuario \
qué vas a hacer y espera su "sí" antes de ejecutarlo.
- Para consultas de solo lectura, actúa directamente sin pedir confirmación.
- Si una herramienta devuelve un error, explícalo en lenguaje sencillo y propón \
una alternativa.
- Si el usuario pide algo ambiguo, pregunta lo justo para aclararlo.

No inventes datos del proyecto: si no lo sabes, consúltalo con una herramienta.\
"""

MAX_TOOL_ITERATIONS = 12


class ProjectAgent:
    def __init__(self, mcp: MCPLink, api_key: str, model: str, history_limit: int = 40):
        self._mcp = mcp
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._history_limit = history_limit
        self._histories: dict[str, list[dict]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def reset(self, conversation_id: str) -> None:
        self._histories.pop(conversation_id, None)

    def _lock(self, conversation_id: str) -> asyncio.Lock:
        return self._locks.setdefault(conversation_id, asyncio.Lock())

    async def handle(self, conversation_id: str, user_text: str) -> str:
        """Procesa un mensaje del usuario y devuelve la respuesta del bot."""
        # Un lock por conversación: evita carreras si llegan mensajes seguidos.
        async with self._lock(conversation_id):
            history = self._histories.setdefault(conversation_id, [])
            history.append({"role": "user", "content": user_text})

            try:
                reply = await self._run_loop(history)
            except Exception as exc:
                log.exception("Fallo procesando el mensaje")
                # No dejamos el historial en estado inconsistente.
                self._trim(history)
                return f"⚠️ Ups, hubo un problema procesando tu petición: {exc}"

            self._trim(history)
            return reply

    async def _run_loop(self, history: list[dict]) -> str:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=self._mcp.tools,
                messages=history,
            )
            history.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return _text_of(response.content) or "(sin respuesta)"

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                log.info("Herramienta: %s args=%s", block.name, block.input)
                text, is_error = await self._mcp.call(block.name, block.input or {})
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": text,
                        "is_error": is_error,
                    }
                )
            history.append({"role": "user", "content": tool_results})

        return (
            "He hecho varias consultas pero no logré cerrar la tarea. "
            "¿Puedes reformular o dividir la petición en pasos más pequeños?"
        )

    def _trim(self, history: list[dict]) -> None:
        """Recorta el historial conservando la coherencia user/assistant.

        No se puede cortar dejando un tool_result huérfano (sin su tool_use), así
        que recortamos hasta el siguiente mensaje 'user' con texto plano.
        """
        if len(history) <= self._history_limit:
            return
        # Buscamos un punto de corte seguro: un mensaje de usuario con string.
        start = len(history) - self._history_limit
        while start < len(history):
            msg = history[start]
            if msg["role"] == "user" and isinstance(msg["content"], str):
                break
            start += 1
        if start < len(history):
            del history[:start]


def _text_of(content) -> str:
    return "\n".join(b.text for b in content if getattr(b, "type", None) == "text").strip()
