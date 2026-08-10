# MS Project MCP — Roadmap de Comercialización

> Objetivo: convertir el fork `alfonsommc311-boop/ms-project-mcp` (rama `feat/hardening`) en un **producto vendible**: confiable, fácil de instalar, documentado, con licencia clara y modelo de precio. Documento vivo; se ejecuta por fases.

---

## 0. Posicionamiento (qué vendemos y a quién)

**Qué es:** un servidor MCP que controla **Microsoft Project Desktop** (Windows, COM en vivo) por lenguaje natural desde cualquier cliente MCP (Claude, etc.). 99 herramientas: WBS, dependencias, recursos, costos, línea base, ruta crítica, valor ganado, calendarios, reportes.

**Comprador objetivo (nicho real, B2B):**
- **PMOs / planificadores** que ya usan MS Project y quieren automatizar con IA.
- **Consultoras de gestión de proyectos** (construcción, ingeniería, EPC, energía).
- **Integradores AEC** — se puede **empaquetar junto al MCP de ArcGIS** como "suite de automatización IA para AEC".

**Realidad comercial honesta (define la estrategia):**
1. La licencia upstream es **MIT** → legalmente se puede revender, **pero** cualquiera puede forkear el mismo código. **El producto NO es el código; es el paquete:** robustez probada, instalador de 1 clic, soporte, garantía, plantillas verticales y "funciona en tu idioma".
2. El comprador **debe poseer MS Project Desktop** (Windows). Reduce el mercado pero lo cualifica (ya pagan licencias).
3. **Windows + COM es frágil** → se vende con matriz de versiones probada y SLA de soporte, no "as-is".

**Propuesta de valor de una línea:** *"Tu planificador de Project, manejado por IA — robusto, en tu idioma, instalado en 1 clic y con soporte."*

---

## Fase 1 — Robustez y corrección (núcleo del valor) 🔴 PRIORIDAD MÁXIMA

El producto debe **funcionar de verdad**. En uso real (sesión obra vial) aparecieron 3 fallos con **causa común**: el servidor manipula **campos de texto localizados** (`Predecessors`, `ResourceNames`) en vez del **modelo de objetos COM**. Migrarlos es EL arreglo vendible.

| # | Bug (vivido) | Ubicación | Arreglo |
|---|---|---|---|
| 1 | **Vínculos fallan** en Project español (`"3FS"` rechazado; hay que usar `FC`) | `server.py` L.1098 / L.1157 (`add_predecessor`, `bulk_add_predecessors`) | `proj.TaskDependencies.Add(pred, succ, pjType)` con constantes `pj…` (0=FF,1=FS,2=SF,3=SS) — **independiente del idioma**; lag vía `dep.Lag` en minutos (`lag_days * HoursPerDay*60`) |
| 2 | **Cantidad de material se pierde** (queda 1 unidad) | L.3066-3073 (`bulk_assign_resources`) ignora `units` | `t.Assignments.Add(ResourceID, Units)` — fija la cantidad real para work y material |
| 3 | **No se puede quitar recurso material** (`"Mezcla (ton)[1]"` no matchea) | L.3107 (`remove_resource_assignment`) compara texto con sufijo `[N]` | Recorrer `t.Assignments` y `.Delete()` por objeto |
| 4 | **Proyecto activo confuso** (`new_project` crea Proyecto2 pero se escribe en el del frente) | `new_project` L.247 / `switch_project` L.1843 | Tras `new_project`, **activar** el proyecto creado y devolver su nombre; que las tools resuelvan el target de forma explícita y consistente |

**Principio rector:** *preferir el modelo de objetos COM sobre campos de texto localizados.* Misma migración para cualquier tool que arme strings de `Predecessors`/`ResourceNames` (revisar `cross_project_link` L.3341, etc.).

**Pendientes "pasada 2" (ya identificados por Codex, en memoria):**
- #2 transaccionalidad de los `bulk_*` (rollback atómico o reporte parcial claro).
- #3 sandbox de rutas en `open_project`/`save_project_as` (evitar escribir fuera de carpetas permitidas).
- #7 calendario / working time correcto.
- #8 consistencia de `save` (no todas las tools guardan igual).
- #9 `except` silenciosos (tragan errores COM).
- #10 `CoInitialize` por hilo.

**Criterio de aceptación Fase 1:** los 3 bugs reproducidos en test FALLAN antes y PASAN después, en Project ES e EN; `level_resources`/recálculo intactos.

---

## Fase 2 — Tests y CI

Base existente: `tests/test_phase2..7.py` + `test_new_tools.py`. Falta endurecer.

- **Tests de regresión** para los 4 bugs de Fase 1 (con un .mpp de fixtures).
- **Matriz de idioma**: correr contra Project con UI ES y EN (los códigos de vínculo/orden de campos cambian).
- **Smoke test de arranque** sin Project abierto (el server debe lanzar Project o fallar con mensaje claro).
- **CI**: GitHub Actions self-hosted runner Windows + MS Project (o documentar que los tests COM son "manuales/local" y CI solo corre los unitarios sin COM).
- **Cobertura mínima** por categoría de tool; badge en README.

**Criterio:** `pytest` verde en local con Project abierto; suite de "no-COM" verde en CI.

---

## Fase 3 — Empaquetado e instalación (fricción histórica #1)

**Problema actual:** `pyproject.toml` tiene `packages = []` → el wheel de hatchling no incluye nada; `uv sync`/`pip install .` no instalan el server.

- **Arreglar el build**: convertir `server.py` en paquete (`ms_project_mcp/__init__.py` + `__main__.py`) o configurar `[tool.hatch.build.targets.wheel] force-include`/`packages = ["ms_project_mcp"]`. Entry point: `ms-project-mcp = ms_project_mcp.server:main`.
- **Instalador de 1 clic** (las 3 opciones, de menos a más esfuerzo):
  1. `pipx install ms-project-mcp` (publicar en PyPI) → comando global.
  2. **`.exe` con PyInstaller** (no requiere Python en la máquina del comprador) — quita la mayor fricción.
  3. Script `install.ps1` que crea venv, instala deps y registra el MCP en Claude (`claude mcp add-json`) automáticamente.
- **Asistente de configuración**: detectar MS Project instalado, verificar COM, registrar en el cliente MCP, test de humo. Mensaje de éxito/diagnóstico.
- **Versionado** semántico + `CHANGELOG.md`.

**Criterio:** un comprador sin saber Python deja el MCP andando en < 5 min con 1 comando o 1 instalador.

---

## Fase 4 — Documentación y onboarding

- **README** orientado a venta: qué hace (con GIF/clip), instalación, primeros 5 prompts útiles, troubleshooting (Project no abierto, COM, idioma).
- **Catálogo de tools** auto-generado desde los docstrings (ya hay 99) → tabla navegable.
- **Guía "del Excel/Project manual al MCP"**: recetas verticales (cronograma de obra, EVM, recursos), reusando el caso real de obra vial como demo.
- **Video de 2-3 min**: "construye una obra vial en Project hablando con IA" (tenemos el guion ya hecho).
- **Página de producto** (landing simple) con CTA de compra/contacto.

**Criterio:** un evaluador entiende el valor y lo prueba sin pedirte ayuda.

---

## Fase 5 — Licencia, IP y cumplimiento

- **MIT upstream** (© 2026 Ibrahim Elsahafy): para revender hay que **conservar el aviso de copyright + texto MIT** del núcleo. Cumplir siempre.
- **Modelo legal recomendado — dual:** el mismo código se puede ofrecer **(a)** como Community MIT (gratis, “as-is”) y **(b)** bajo un **EULA comercial** que aporta lo que MIT no da: **garantía, soporte, indemnización, actualizaciones**. Se vende el EULA + servicio, no la exclusividad del código.
- **Atribución**: NOTICE con autor upstream + tus aportes (hardening). Tus commits son tuyos; documenta la cadena.
- **Marca**: nombre comercial propio (no usar marcas de Microsoft salvo "for Microsoft Project®" con disclaimer "no afiliado a Microsoft").
- **Privacidad/seguridad**: declarar que el server actúa **local** por COM, sin enviar datos del proyecto a la nube (gran argumento de venta para PMOs con datos sensibles). Revisión de seguridad ya hecha (limpia).

**Criterio:** EULA + NOTICE + disclaimer de marca listos; checklist MIT cumplido.

---

## Fase 6 — Precio y go-to-market

**Modelos de precio (elige 1-2):**
| Modelo | Cómo | Encaje |
|---|---|---|
| Licencia única por máquina | p.ej. US$149-399 one-time + updates 1 año | Simple; bueno para consultores individuales |
| Suscripción por usuario | p.ej. US$15-40/usuario/mes (updates + soporte) | Ingreso recurrente; PMOs/empresas |
| Tiers | Community (MIT, gratis) / Pro (installer+soporte) / Enterprise (recetas a medida + SLA) | Embudo natural; Community alimenta Pro |
| Servicios | Integración + plantillas verticales + capacitación | **Donde suele estar el dinero real en B2B nicho** |

**Canales:**
- Comunidades **PMI / MS Project / construcción**, LinkedIn, foros AEC.
- **Servicio productizado** (Upwork/Fiverr/propio): "instalo y configuro tu PMO con IA".
- **Bundle AEC**: vender junto al **MCP de ArcGIS** (ver `[[arcgis-mcp-product]]`) como suite.
- Marketplace MCP / directorios de servidores MCP (visibilidad gratis).

**Criterio:** 1 modelo de precio elegido, página de pago/contacto, 3 canales activos.

---

## Fase 7 — Diferenciación (foso) y roadmap de features

Como el código es forkeable, el foso se construye con:
- **"Funciona en tu idioma"** (la migración a object-model) — diferenciador real vs. el upstream que se rompe en ES.
- **Recetas verticales** listas (obra vial, EVM, nivelación) — valor que el código pelado no tiene.
- **Soporte + garantía + actualizaciones** con cada release de MS Project.
- **Empaquetado pro** (instalador/.exe) que el upstream no ofrece.

**Features futuras vendibles:** export a Power BI (¡ya tenemos el pipeline obra vial!), generación de informes Word/PDF ejecutivos, sincronización con Excel, plantillas por industria, modo "auditoría de cronograma".

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| COM/Windows frágil entre versiones de Project | Matriz de versiones probada + SLA + telemetría de errores opt-in |
| Upstream forkeable (MIT) | Vender paquete+soporte+recetas, no exclusividad; marca propia |
| Mercado nicho (requiere Project Desktop) | Cualifica al comprador; bundle AEC amplía alcance |
| Dependencia de Microsoft (cambios de API/COM) | Capa de abstracción + tests de regresión por versión |
| Soporte consume tiempo | Docs/onboarding sólidos (Fase 4) reducen tickets; tier Enterprise paga el soporte |

---

## Secuencia recomendada (sprints)

1. **Sprint 1 (núcleo):** Fase 1 bugs #1-#3 + tests de regresión (Fase 2 parcial). → *El producto funciona.*
2. **Sprint 2 (instalable):** Fase 3 (build + installer 1 clic) + Fase 1 #4 y pendientes pasada 2. → *Cualquiera lo instala.*
3. **Sprint 3 (vendible):** Fase 4 (docs/demo) + Fase 5 (EULA/licencia). → *Listo para mostrar y cobrar.*
4. **Sprint 4 (mercado):** Fase 6 (precio/canales) + Fase 7 (1 receta vertical estrella). → *Primeras ventas.*

**Definición de "vendible" (barra de calidad):** instala en <5 min sin saber Python · los 4 bugs no existen · funciona en ES y EN · README+demo claros · EULA y precio publicados · 1 receta vertical de extremo a extremo (obra vial).

---

*Núcleo MIT © 2026 Ibrahim Elsahafy. Hardening y empaquetado: este fork. "For Microsoft Project®" — no afiliado a Microsoft.*
