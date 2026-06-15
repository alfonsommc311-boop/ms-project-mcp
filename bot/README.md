# Bot de mensajería para MS Project

Un bot conversacional que te deja consultar y modificar tu proyecto de Microsoft
Project **por chat** (Telegram, Email, Slack y WhatsApp).
Entiende lenguaje natural gracias a **Claude (Anthropic)** y ejecuta las acciones
a través del servidor MCP de este repositorio (`server.py`, 99 herramientas).

```
[Telegram / Email / Slack / WhatsApp]
            │  (texto del usuario)
            ▼
   ProjectAgent  ──►  Claude (claude-opus-4-8)   ← interpreta y decide
            │              │  tool-use
            │              ▼
        MCPLink  ──►  server.py (MCP)  ──►  Microsoft Project (COM, Windows)
```

## ⚠️ Requisito importante

`server.py` controla MS Project por **COM**, así que **debe ejecutarse en Windows
con MS Project abierto**. El bot lanza `server.py` como subproceso, por lo que el
bot corre en la misma máquina Windows donde está MS Project. El "estar en la nube"
aplica a quien te escribe (Telegram, etc.), no a MS Project.

## Instalación

```bash
pip install -r bot/requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env` (en la raíz del repo) y rellena:
   - `ANTHROPIC_API_KEY` — tu clave de https://console.anthropic.com
   - `TELEGRAM_BOT_TOKEN` — habla con **@BotFather**, crea un bot y copia el token.
   - `TELEGRAM_ALLOWED_IDS` — tu(s) chat ID(s) autorizados.

2. **¿Cómo saber tu chat ID?** Arranca el bot, escríbele algo por Telegram y mira
   el log de la consola: imprime el ID del chat. Añádelo a `TELEGRAM_ALLOWED_IDS`
   y reinicia. (También puedes usar **@userinfobot**.)

   > Por seguridad, si la lista blanca está vacía el bot **rechaza a todos**:
   > este bot puede modificar tu proyecto.

## Arrancar

Con MS Project abierto en Windows:

```bash
python -m bot.run
```

El bot lanza el servidor MCP automáticamente y empieza a escuchar Telegram.

## Ejemplos de uso (en el chat)

- *¿Qué tareas van retrasadas?*
- *Dame el resumen de progreso del proyecto*
- *¿Cuáles son los próximos hitos del Q2?*
- *Pon la tarea 12 en rojo (RAG) y avísame del impacto*
- *¿Qué pasa si retraso la tarea 8 cinco días?*

Comandos: `/start` (ayuda), `/reset` (reinicia la conversación).

## Estructura

| Archivo | Qué hace |
|---|---|
| `config.py` | Lee la configuración desde `.env` / entorno. |
| `mcp_link.py` | Lanza `server.py` por stdio y expone sus 99 herramientas. |
| `agent.py` | El cerebro: bucle de tool-use con Claude. |
| `run.py` | Punto de entrada; arranca MCP + canales. |
| `channels/telegram_channel.py` | Canal Telegram. |
| `channels/email_channel.py` | Canal Email (IMAP/SMTP, stdlib). |
| `channels/slack_channel.py` | Canal Slack (Socket Mode). |
| `channels/whatsapp_channel.py` | Canal WhatsApp (Cloud API de Meta). |

## Canales disponibles

Todos los canales funcionan y se activan automáticamente en `run.py` cuando
defines sus variables de entorno. Puedes tener varios a la vez.

| Canal | Cómo funciona | Dependencias |
|---|---|---|
| **Telegram** | Polling; gratis vía @BotFather. | `python-telegram-bot` |
| **Email** | Sondeo IMAP + respuesta SMTP. Usa contraseña de aplicación. | stdlib (ninguna) |
| **Slack** | Socket Mode (sin URL pública). | `slack_bolt` |
| **WhatsApp** | Webhook (Cloud API de Meta). Requiere HTTPS público. | `fastapi`, `uvicorn` |

Para añadir un canal nuevo, hereda de `channels/base.Channel`, llama a
`await self.agent.handle(conversation_id, texto)` y devuelve la respuesta por tu
medio.

## Seguridad

- **Lista blanca obligatoria** por canal (Telegram: `TELEGRAM_ALLOWED_IDS`).
- El sistema instruye a Claude para **pedir confirmación** antes de acciones
  destructivas o masivas (borrados, reprogramaciones completas, updates masivos).
- Nunca subas tu `.env` (ya está en `.gitignore`).

## Modelo

Por defecto usa **`claude-opus-4-8`**. Puedes cambiarlo con `BOT_MODEL` en `.env`
(p. ej. `claude-sonnet-4-6` para menor coste).
