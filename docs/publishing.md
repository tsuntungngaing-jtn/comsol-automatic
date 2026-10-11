# Source-only release
Use scripts/release.py to build a ZIP outside the source tree. It uses an explicit folder/type allowlist and rejects model files, images, CSV research outputs, logs, credentials and personal paths. Review the actual manifest and checksums before delivery. This script builds a local artifact; it does not authorize uploading or publishing.

Retain upstream licenses and distinguish the historical upstream snapshot from current modified vendored files. Do not label a modified snapshot unchanged. Commercial COMSOL models/manuals and experiment evidence remain outside the skill archive. Verify a wheel in an isolated environment outside the source directory as well as the source ZIP.
