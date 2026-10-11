# COMSOL Automatic 6.4 English — 0.1.1

Independent English repair release based on commit ef476da8c14cc73662b7c8aad7d091e9d641ba9c of tsuntungngaing-jtn/comsol-automatic. Not an official COMSOL product. Original provenance and licenses are in NOTICE.md and vendor/installed-mcp/LICENSE.

This package contains the skill, MCP adapter, vendored tools, catalog metadata, original teaching source, tests and installation scripts. It contains no commercial COMSOL models, manuals, research results, credentials or Python environment.

On Windows, extract the full folder to a new directory, then run `powershell -ExecutionPolicy Bypass -File scripts/install.ps1`. Register the MCP command using the new folder's `.venv/Scripts/python.exe -m server.main serve --transport stdio` and its working directory. Set COMSOL_OUTPUT_ROOT to your research workspace, not this folder. See docs/connectors.md for details. Existing skills/connectors are not replaced automatically.

Repaired: convective heat-flux API; 6.4 inlet U0in and explicit k-epsilon turbulence inputs; real basic-library material insertion with repeat binding; output containment for version saves; unique version reservation; wheel resources. The executable and package remain named comsol-automatic for compatibility; install them in a dedicated environment. The discoverable skill name is comsol-automatic-6-4-en.

Run `python -m unittest discover -s tests` for Python/protocol checks. Real COMSOL validation must run through MCP. Read docs/validation.md before using results in research. This release is not blanket validation of every upstream physics shortcut.
