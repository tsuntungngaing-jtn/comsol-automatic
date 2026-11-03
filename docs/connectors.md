# Installation and connectors
Install into a new directory and dedicated Python 3.10+ environment. `scripts/install.ps1` creates .venv and installs the complete source editable. A licensed COMSOL installation must already exist. The source directory must remain available after editable installation.

For stdio, configure the client with the absolute `.venv/Scripts/python.exe` path, arguments `-m server.main serve --transport stdio`, and the extracted skill folder as cwd. Set `COMSOL_OUTPUT_ROOT` to a writable research directory. Optional `COMSOL_VERSION=6.4` selects a discovered installation. `COMSOL_ROOT` must match that installation, not merely point to another directory. `COMSOL_ALLOW_CODE=1` enables trusted operator code through MCP; it is not required for Inspector and is not a sandbox.

## Client–server and licensing

Interactive agent work should use a **COMSOL Multiphysics Server** session (`comsolmphserver` / Launchers), not **COMSOL Server™** (app deployment). Read `comsol_status` for `standalone`, `host`, and `port`. Same-machine Desktop client + Multiphysics server is allowed on any license type; client and server on **different** computers require a Floating Network License (FNL). See COMSOL KB 1299 and the 6.4 client–server documentation linked from [agentic official alignment](agentic-official-alignment.md).

After connect, resolve tracked model identity before edits. Connectivity smoke: `param_set` / `param_get` round-trip. Prefer MCP over bare `comsolcompile` Java clients; if MCP is down, restore it rather than automating the Desktop UI.

To install only skill discovery files, run `python scripts/install_skill.py --skills-dir <client-skills-directory>`. It refuses an existing destination. This does not install dependencies or configure a connector. Clients with an Upload Skill feature require that separate action; local copying does not prove visibility.

For HTTP/SSE, use scripts/start-mcp.ps1 with the desired transport. Bind localhost unless external access is explicitly needed. The launcher preserves its local token and refuses conflicting credentials. Use an Authorization: Bearer header and an HTTPS reverse proxy for external transport. Never send tokens in chat. Skill upload, dependency installation, MCP connection, tool discovery and license availability are separate checks.
