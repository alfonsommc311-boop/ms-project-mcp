"""Regression test — task links via the COM object model (locale-independent).

Reproduces the production bug where `add_predecessor` / `bulk_add_predecessors`
built the *localized* `Predecessors` text string (e.g. "3FS"), which non-English
MS Project (Spanish, French, ...) rejects with a COM error
("Hay un problema con la informacion de la tarea predecesora").

The fix routes links through `TaskDependencies.Add(pred, succ, pjType)` using the
locale-independent pj* constants, so English codes (FS/SS/FF/SF) work in ANY UI
language. With the OLD code this test FAILS on a Spanish Project; with the fix it
PASSES on any language.

Run with MS Project open (creates and discards its own scratch project):
    .venv\\Scripts\\python.exe tests\\test_links_regression.py
"""
import asyncio
import json
import importlib.util
import os
import sys

_server_path = os.path.join(os.path.dirname(__file__), "..", "server.py")
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

    # Scratch project so we never touch the user's files.
    await call("new_project", {"title": "MCP Link Regression", "start": "2026-04-01"})
    try:
        uids = []
        for i in range(1, 4):
            r = await call("add_task", {"name": f"Task {i}", "duration_days": 5})
            uids.append(r.get("unique_id") if isinstance(r, dict) else None)
        check(all(uids) and len(uids) == 3, f"created 3 tasks: {uids}")

        # 1) Single add_predecessor with English "FS" must succeed.
        print("=== add_predecessor FS (English code, must work in any language) ===")
        r = await call("add_predecessor", {
            "successor_unique_id": uids[1],
            "predecessor_unique_id": uids[0],
            "link_type": "FS",
        })
        check(isinstance(r, dict) and r.get("status") == "linked" and "error" not in r,
              f"FS link created without COM error: {r}")

        deps = await call("get_task_dependencies", {"unique_id": uids[1]})
        n_pred = len(deps.get("predecessors", [])) if isinstance(deps, dict) else 0
        check(n_pred >= 1, f"successor now has a predecessor (n={n_pred})")

        # 2) bulk_add_predecessors with SS + lag: linked, no errors.
        print("=== bulk_add_predecessors SS + lag (English code) ===")
        links = [{"successor_unique_id": uids[2], "predecessor_unique_id": uids[1],
                  "link_type": "SS", "lag_days": 3}]
        r = await call("bulk_add_predecessors", {"links_json": json.dumps(links)})
        check(isinstance(r, dict) and r.get("linked") == 1 and not r.get("errors"),
              f"bulk SS+3d linked, no errors: {r}")

        # 3) Invalid link_type must be rejected cleanly (not a COM crash).
        print("=== invalid link_type rejected cleanly ===")
        r = await call("add_predecessor", {
            "successor_unique_id": uids[2],
            "predecessor_unique_id": uids[0],
            "link_type": "ZZ",
        })
        check(isinstance(r, dict) and "error" in r, f"invalid link_type rejected: {r}")
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
