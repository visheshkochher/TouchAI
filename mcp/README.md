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
in its Web Server DAT, not this file. To deploy changes, paste the new source into the
server's text DAT inside TD (or use the still-running old bridge's `write` tool on that
DAT), restart the Web Server DAT, and re-save `td_mcp_server.tox` so the tox stays in
sync with the repo source.

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
