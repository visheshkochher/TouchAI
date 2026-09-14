# MCP bridge setup

Source: [johnsabath/touchdesigner-mcp](https://github.com/johnsabath/touchdesigner-mcp) (MIT),
**with local extensions** — `td_mcp_server.py` in this repo is the source of truth, not upstream.

## Local extensions (beyond upstream)

- **`health` tool** — one-call project verification: sweeps every operator for
  errors/warnings, ranks cook-time hotspots (CPU+GPU ms), and measures real fps as
  frame-delta over wall clock between successive `health` calls (first call = baseline).
- **`observe` pixel stats** — every observe response now includes `stats`
  (mean/std/max/alpha_max + a `verdict`: `black` / `flat` / `transparent` / `static` /
  `ok`) computed from the full-res frame, so dead chains are caught objectively even
  when the thumbnail looks plausible. `static` fires when a multi-frame capture shows
  no motion.

**After editing `td_mcp_server.py`:** the running TD project executes the copy stored
in its Web Server DAT, not this file. Deploy in **three separate calls** — never
combine them, see the warning below:

1. Load the source into the handler DAT. Do it from inside TD so the file never has
   to round-trip through the agent's context, and decode explicitly — the source
   contains non-ASCII arrows/quotes, so a bare `open()` dies on TD's ASCII default:
   ```python
   with open('<repo>/mcp/td_mcp_server.py', encoding='utf-8') as f:
       op('/project1/td_mcp_server/mcp_handler').text = f.read()
   ```
2. Restart the Web Server DAT with the **`set` tool** (`{"restart": true}`).
   ⚠️ **Never call `webserver.par.restart.pulse()` from inside a `run`** — `.pulse()`
   fires synchronously and destroys the HTTP worker thread mid-request, which crashes
   TouchDesigner (SIGTRAP in `libPocoNet`). Setting the pulse par instead defers it to
   the next frame, after the response is sent.
3. Re-save the tox so the checked-in file matches the source:
   `op('/project1/td_mcp_server').save('<repo>/mcp/td_mcp_server.tox')`

**Step 3 is not optional.** The `.tox` committed at the repo's initial commit was
stale — it predated the `health` tool and the `observe` pixel-stats extension, so a
fresh clone got a bridge silently missing both while `td_mcp_server.py` showed them
present. Verify after deploying: the tool list should have **14** tools including
`health`, and `observe` responses should carry `stats`.

## Files

- `td_mcp_server.tox` — self-contained MCP server. Drag into any open TD project;
  it serves MCP Streamable HTTP on port **9988**. No configuration needed.
- `td_mcp_server.py` — the server source (canonical — edited locally, see above).
- `UPSTREAM_README.md` — upstream docs and tool list (does not include local extensions).

## Client wiring (already done in this repo)

- `.mcp.json` at the repo root points Claude Code at `http://127.0.0.1:9988/mcp`.
- `.claude/skills/touchdesigner-building/` — bundled skill teaching tool usage,
  GLSL workflow, feedback wiring, and the observe loop.

## Per-session checklist

1. Open TouchDesigner with your working project (work on a copy in `work/` — the
   `run` tool can rewire or delete anything, so never point it at a project you
   can't restore).
2. Drag `mcp/td_mcp_server.tox` into the network (or keep it saved inside the working project).
3. Start Claude Code in this repo — the `touchdesigner` MCP server connects on demand.

## Remote TD machine

Run TD + tox on the remote machine, then change the URL in `.mcp.json` to
`http://<machine-ip>:9988/mcp`. Keep it LAN-only; the server has no auth.

## Updating

Re-download from the upstream repo's `main` branch (no packaged releases as of Jul 2026).
