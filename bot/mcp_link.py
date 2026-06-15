"""Puente con el servidor MCP de MS Project (server.py).

Lanza `server.py` como subproceso por stdio, lista sus herramientas (las 99
herramientas de MS Project) y permite invocarlas. Mantiene la sesión abierta
durante toda la vida del bot.
"""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

log = logging.getLogger("bot.mcp")


class MCPLink:
    """Conexión persistente al servidor MCP de MS Project."""

    def __init__(self, command: list[str]):
        self._command = command
        self._stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []  # esquemas en formato Anthropic

    async def open(self) -> None:
        """Arranca el servidor MCP y descubre sus herramientas."""
        params = StdioServerParameters(
            command=self._command[0],
            args=self._command[1:],
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()

        result = await self.session.list_tools()
        self.tools = [
            {
                "name": t.name,
                "description": (t.description or "").strip(),
                "input_schema": t.inputSchema or {"type": "object", "properties": {}},
            }
            for t in result.tools
        ]
        log.info("Servidor MCP conectado: %d herramientas disponibles", len(self.tools))

    async def call(self, name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
        """Invoca una herramienta MCP. Devuelve (texto_resultado, es_error)."""
        if self.session is None:
            raise RuntimeError("La sesión MCP no está abierta")
        try:
            result = await self.session.call_tool(name, arguments or {})
        except Exception as exc:  # error de transporte / herramienta inexistente
            log.exception("Error llamando a la herramienta MCP %s", name)
            return f"Error al ejecutar '{name}': {exc}", True

        text = _result_to_text(result)
        is_error = bool(getattr(result, "isError", False))
        return text, is_error

    async def close(self) -> None:
        await self._stack.aclose()
        self.session = None


def _result_to_text(result: Any) -> str:
    """Extrae texto plano del CallToolResult del MCP."""
    parts: list[str] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text is not None:
            parts.append(text)
        else:
            parts.append(str(item))
    return "\n".join(parts) if parts else "(sin contenido)"
