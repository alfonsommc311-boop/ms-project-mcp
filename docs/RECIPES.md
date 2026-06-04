# Vertical Recipes

Ready-to-run, natural-language workflows that show the product's value end to end.
Each recipe is a sequence of prompts you give your AI assistant; the assistant
calls the MS Project MCP tools to do the work in live Microsoft Project.

> Prerequisite for every recipe: **Microsoft Project Desktop is open**, and the
> `ms-project` MCP server is registered (run `install.ps1`).

---

## Recipe 1 — Road construction schedule (flagship demo)

Builds a complete civil-works programme: 7-phase WBS, milestones, the full
dependency network, resources with rates, baseline, and the critical path.

**1. Create the project**
> "Create a new MS Project for a 12 km road construction project starting next
> July. Set the manager and company."

**2. Build the WBS (phases → tasks → milestones)**
> "Add these phases with their tasks and durations: Engineering & permits;
> Earthworks (clearing, cut, fill, subgrade); Drainage (culverts, box culvert,
> ditches); Pavement (subbase, base, prime coat, hot-mix asphalt); Road safety
> (markings, signs, guardrail, lighting); Closeout. Add 'Project start' and
> 'Final handover' milestones."
*(Tools: `new_project`, `bulk_add_tasks`.)*

**3. Wire the dependencies**
> "Link the tasks in construction sequence: clearing → cut → fill (SS+15d) →
> subgrade → drainage → pavement → safety works → closeout. Use finish-to-start
> unless I said otherwise."
*(Tool: `bulk_add_predecessors` — works regardless of Project's UI language.)*

**4. Load resources and costs**
> "Add crews (earthworks, drainage, paving, signage), heavy machinery, engineers
> and materials (granular m³, asphalt ton, concrete m³) with daily/unit rates, and
> assign them to the right tasks. Use 5,000 m³ of granular on the fill."
*(Tools: `add_resource`, `bulk_assign_resources` — material **quantities** are
applied correctly.)*

**5. Baseline and analyse**
> "Save a baseline, then show me the critical path, the milestone report and the
> total cost by phase."
*(Tools: `save_baseline`, `get_critical_path`, `get_milestone_report`,
`get_cost_summary`.)*

**6. (Optional) Take it to Power BI**
> "Export the tasks and an S-curve to CSV so I can build an interactive dashboard."
*(See the Power BI dashboard recipe in the suite.)*

**Result:** a ~18-month programme with a real critical path and costed resources —
built by conversation in minutes.

---

## Recipe 2 — Earned Value (EVM) check

> "Save a baseline, mark progress complete through last Friday, then give me SPI,
> CPI, schedule variance and cost variance, and flag any task that's behind."

*(Tools: `save_baseline`, `update_project`, `get_earned_value`,
`get_variance_report`, `get_overdue_tasks`.)*

---

## Recipe 3 — Weekly PMO status

> "Update progress through today, list red/amber tasks, what's critical in the next
> 30 days, and any overdue milestones."

*(Tools: `update_project`, `get_tasks_by_rag`, `get_critical_tasks_for_period`,
`get_milestone_report`.)*

---

*Tip: destructive operations (delete, overwrite, discard) are gated by safe-mode
and ask for confirmation. Always keep a saved copy of important project files.*
