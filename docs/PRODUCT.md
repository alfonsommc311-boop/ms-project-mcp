# MS Project MCP — Product Overview

**Your Microsoft Project planner, driven by AI — robust, in your language,
installed in one click, and supported.**

MS Project MCP lets any MCP-compatible AI assistant (Claude and others) read and
build real Microsoft Project schedules through natural language: WBS, task
dependencies, resources, costs, baselines, critical path, earned value, calendars
and reports — **99 tools** over a live COM connection to Project Desktop.

## The problem
Planners live in Microsoft Project but do the tedious parts by hand: building the
WBS, wiring dependencies, loading resources and costs, tracking the baseline. AI
assistants can help — but only if they can actually *drive* Project. Generic
scripts break (wrong language, lost material quantities, the wrong project gets
edited) and are painful to install.

## What it does
- **Build & edit schedules** by talking: phases, tasks, milestones, durations.
- **Dependencies** (FS/SS/FF/SF + lag) that work in **any UI language**.
- **Resources & costs**: work, material (with real quantities) and cost resources;
  rates, assignments, leveling, workload, rate tables.
- **Analysis**: critical path, earned value (SPI/CPI), variance, S-curves,
  timephased data, milestone and progress reports.
- **Export** to XML / CSV and (with our Power BI recipe) interactive dashboards.

## Who it's for
PMOs, schedulers and **project-management consultancies** — especially in
**construction, engineering and EPC** — who already run Microsoft Project Desktop
and want AI automation without leaving their tool of record.

## Why this, not a DIY script or the raw open-source core
The code is MIT and forkable — so we don't sell the bytes, we sell the **product**:
- ✅ **Works in your language.** Links and resource assignments use the COM object
  model, not localized text fields. (A raw text approach fails on Spanish/French
  Project and silently drops material quantities — we fixed exactly that.)
- ✅ **Deterministic.** Operates on the intended project even with several open
  (no "edits landed in the wrong file").
- ✅ **One-click install** (`install.ps1`) + auto-registration in your AI client.
- ✅ **Hardened**: safe-mode confirmation gates on destructive operations.
- ✅ **Vertical recipes** (road construction, EVM) and **support + updates** with
  each Microsoft Project release.

## Security & privacy (a real selling point for PMOs)
The server runs **locally** and talks to **your** Microsoft Project over COM. Your
project data is **not sent to any cloud** by this software. Nothing to host, no
data leaves the machine.

## Editions & pricing (illustrative)
| Edition | What you get | Indicative price |
|---|---|---|
| **Community** | MIT core, "AS IS", no support | Free |
| **Pro** | 1-click installer, hardened build, email support, updates | one-time **$149–399/seat** or **$15–40/user/mo** |
| **Enterprise** | SLA, custom vertical recipes, onboarding, priority support | Custom |
| **Services** | Install + configure your PMO with AI, bespoke recipes, training | Quote |

> Bundle option: pair with our ArcGIS MCP as an **AEC AI-automation suite**.

## Requirements
- Windows with **Microsoft Project Desktop** (tested on Project 16.0), separately
  licensed by you.
- Python 3.10+ (handled by the installer).

## FAQ
- **Does it need internet / send my data anywhere?** No — local COM automation.
- **Will it work with Project in Spanish/French?** Yes — that's a core fix.
- **Does it include Microsoft Project?** No; you provide your own licensed copy.
- **Can I try it free?** Yes — the Community (MIT) build.

---
*Legal: the commercial editions are governed by `EULA.md` (template — have counsel
review). "Microsoft Project®" is a trademark of Microsoft Corporation; this product
is independent and not affiliated with Microsoft (see `NOTICE`).*
