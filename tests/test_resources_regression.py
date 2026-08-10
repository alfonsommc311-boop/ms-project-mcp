"""Regression test — resource assignment via the COM Assignments object model.

Covers two production bugs:
  #2  Material quantities were dropped: bulk/single assign wrote the localized
      `ResourceNames` text and ignored `units`, so a material resource always
      landed at quantity 1 instead of (e.g.) 500. Fixed with
      `task.Assignments.Add(task.ID, res.ID)` + `assignment.Units = units`.
  #3  Removing a material resource failed: `ResourceNames` returns "Sand m3[1]"
      (with a [N] quantity suffix) so a plain name comparison never matched.
      Fixed by matching the assignment's clean `.ResourceName` and `.Delete()`.

Run with MS Project open (creates and discards its own scratch project):
    .venv\\Scripts\\python.exe tests\\test_resources_regression.py
"""
import asyncio
import json
import importlib.util
import os
import sys

_server_path = os.path.join(os.path.dirname(__file__), "..", "ms_project_mcp", "server.py")
spec = importlib.util.spec_from_file_location("server", _server_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


async def call(name, args=None):
    r = await mod.mcp.call_tool(name, args or {})
    if isinstance(r, tuple):
        r = r[0]
    if isinstance(r, list):
        item = r[0]
        text = item.text if hasattr(item, "text") else str(item)
    elif hasattr(r, "text"):
        text = r.text
    else:
        text = str(r)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


async def run():
    failures = []

    def check(cond, msg):
        print(("  PASS " if cond else "  FAIL ") + msg)
        if not cond:
            failures.append(msg)

    await call("new_project", {"title": "MCP Resource Regression", "start": "2026-04-01"})
    try:
        r = await call("add_task", {"name": "Concrete pour", "duration_days": 5})
        uid = r.get("unique_id") if isinstance(r, dict) else None
        check(bool(uid), f"created task uid={uid}")

        # Material resource with a real per-unit rate.
        await call("add_resource", {"name": "Mortero (m3)", "type": 1, "standard_rate": "130"})

        # #2 — bulk assign material with quantity 500 (was silently dropped to 1).
        print("=== bug #2: material quantity via bulk_assign_resources ===")
        assigns = [{"task_unique_id": uid, "resource_name": "Mortero (m3)", "units": 500}]
        r = await call("bulk_assign_resources", {"assignments_json": json.dumps(assigns)})
        check(isinstance(r, dict) and r.get("assigned") == 1 and not r.get("errors"),
              f"bulk assign reported success: {r}")

        task = await call("get_task", {"unique_id": uid})
        rnames = task.get("resource_names", "") if isinstance(task, dict) else ""
        check("[500]" in rnames, f"material quantity 500 applied (resource_names={rnames!r})")

        # #3 — remove the material resource (old code choked on the [N] suffix).
        print("=== bug #3: remove material resource (clean-name match) ===")
        r = await call("remove_resource_assignment",
                       {"task_unique_id": uid, "resource_name": "Mortero (m3)"})
        check(isinstance(r, dict) and r.get("status") == "removed",
              f"remove reported success: {r}")

        task = await call("get_task", {"unique_id": uid})
        rnames2 = task.get("resource_names", "") if isinstance(task, dict) else ""
        check("Mortero" not in rnames2, f"material no longer assigned (resource_names={rnames2!r})")
    finally:
        await call("close_project", {"save": False, "confirm": True})

    print("\n=== SUMMARY ===")
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED")
        for f in failures:
            print("  -", f)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
