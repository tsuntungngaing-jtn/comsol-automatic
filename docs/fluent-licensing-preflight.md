# Fluent licensing and connection preflight

Operational guidance for LAB Fluent hosts (for example LAB7/LAB8) when using the official PyFluent MCP. This document does not install a Fluent connector and does not change paper-reproduction acceptance. Connection PASS/FAIL is separate from scientific PASS.

## Confirmed failure mode (handoff evidence, 2026-11-14)

Observed on `DESKTOP-PG1GAIT`, Fluent 2024 R2 / 24.2, licensing client under the local Ansys `v242\licensingclient\winx64` tree, config `Shared Files\Licensing\ansyslmd.ini`, historical `ANSYSCL_FNP_PATH=1055@localhost`.

1. CodexSandboxOnline started `ansyscl` (example PID 19044). Listen socket came up (example dynamic port 51690).
2. Write failed: `Unable to write port to %APPDATA%\Ansys\ansyscl.<HOST>.<acl-id>. Make sure you have write permissions.` Then `Unable to write server port`.
3. Clients could not read the dynamic port file, so license/connect failed even though a local listen port existed.
4. That dynamic port is not a value to freeze into long-lived license-server configuration.
5. After `%APPDATA%\Ansys` granted `CodexSandboxUsers` Modify (inherit to files/containers), later checkouts of `acfd_fluent_solver` / Fluent features succeeded for multiple new PIDs.
6. Missing Chinese `ansysli_msgs.xml` warnings still appeared on successful checkouts; they do not explain this write failure. Do not copy another language file to fake a Chinese catalog.
7. Unknown: exact historical ACL edit command and pre-fix ACL. Persistence across new Codex sessions, reboot, Codex updates, or SID rebuilds remains NOT_RUN unless re-tested. Do not promise permanent immunity.

Source material: operator handoff archive `Fluent_permission_handoff_20261114_194808` (logs, ACL snapshot, inventory hashes). Re-read live ACL and identity on the target host; the archive is a point-in-time snapshot.

## Preflight checklist

Run before launching or repeatedly retrying Fluent/MCP connect. Prefer serial work when another authorized job owns the machine.

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Ownership | Existing Fluent, `ansyscl`, Python jobs, task lease | No conflicting takeover; do not kill foreign jobs |
| Identity | `whoami /user`, groups; Online vs Offline vs interactive | Launch identity recorded; Offline read access does not prove Online write |
| Environment | `APPDATA`, `LOCALAPPDATA`, `TEMP`, `TMP`, `USERPROFILE` | Paths match the identity that will start Fluent |
| Write ACL | Effective rights on `%APPDATA%\Ansys` (and session-log dir if overridden) | Create/read/delete a unique self-owned test file only; never edit live port files |
| Temp logs | `%TEMP%\.ansys` writable when logging is enabled | Failure to create logs is evidence, not automatic root cause |
| License config | `ansyslmd.ini` / Client Licensing Settings; server such as `1055@localhost` when local | Config readable; do not replace server with ephemeral ACL ports |
| MCP | Official `ansys-fluent-mcp` registered; schemas listed | Provider identity matches inventory; no third-party substitute |
| Checkout (optional) | Authorized `ansysli_util -checkout ...` or Fluent start | Read stdout and `licdebug`/`ansyscl` logs; confirm release; exit code 0 alone is insufficient |

On failure: archive failing logs and ACL, mark BLOCKED, stop retry storms. Minimal ACL repair only with backup of current ACL, operator authorization, and no Everyone FullControl / recursive home unlock / default sandbox disable. Existing adequate Modify rights: do not stack duplicate ACEs.

## Persistence matrix (report explicitly)

| Case | Status vocabulary |
| --- | --- |
| Same-identity file create/read/delete in `%APPDATA%\Ansys` | PASS / FAIL / NOT_RUN |
| New license-client / Fluent process checkout | PASS / FAIL / NOT_RUN |
| New Codex / agent session | PASS / FAIL / NOT_RUN |
| After host reboot (only if user schedules it) | PASS / FAIL / NOT_RUN |
| After Codex update or sandbox SID change | PASS / FAIL / NOT_RUN |

## Official references

- PyFluent-MCP: https://github.com/ansys/pyfluent-mcp
- Quick start / install: https://fluent-mcp.docs.pyansys.com/version/stable/getting_started/quick_start.html
- Session logging defaults to `%APPDATA%\Ansys\...` on Windows; override `FLUIDS_MCP_SESSION_LOG_DIR`, disable `FLUIDS_MCP_DISABLE_SESSION_LOGS`
- Ansys Client Licensing Settings / user vs installation write locations: Ansys licensing help (Client Licensing Settings); user-level settings avoid requiring admin write into Program Files when that path is locked
- Platform/AppData write behavior under restricted tokens: Ansys Windows platform installation notes

Use the help pages that match the installed release. Official docs do not redefine this project's paper-metric thresholds.

## Related research (method principles only)

These works motivate MCP wrappers and Fluent/Python automation discipline; they are not Ansys ACL recipes and do not certify a LAB host.

- LLM agent + MCP tool wrapping of a commercial simulator Python API (AVEVA APS case): arXiv:2601.11650
- Foam-Agent: LLM CFD agents with MCP as a deployment surface: arXiv:2505.04997 / 2509.18178
- CFDTwin: reusable Python automation around ANSYS Fluent batch workflows: arXiv:2605.27725

Prefer curated official MCP tools over inventing an unofficial Fluent executor. Connection recovery must not rewrite scientific acceptance conclusions.
