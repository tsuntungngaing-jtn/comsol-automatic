# Offline Mesh-Native Diagnostics — v0.7.1

**Status:** deterministic input checking and offline nodal comparison implemented. Synthetic Python tests only. Real COMSOL validation **NOT_RUN**.

## Purpose and boundaries

This feature draws **inspiration** from *Mesh-Native Tokenisation* (https://arxiv.org/abs/2610.12618): reason about physical locations rather than comparing node numbers across independent meshes. It **does not implement** the paper's MNC encoder/decoder, deep learning, surrogate solver, automatic mesh generation or adaptive refinement. It makes no claim about mesh-independence or mesh convergence.

The inputs are **already exported** JSON datasets with explicit node-coordinate/field alignment. COMSOL `.mph`, `.mphtxt`, arbitrary finite-element DOF layouts, 3D tets, mixed elements, higher-order elements, interface discontinuities, vector/tensor fields and conservative projection are **not parsed in v0.7.1**. Export and verify the nodal dataset separately using the authorized COMSOL/MCP workflow; do not assume COMSOL degree-of-freedom order matches mesh node order.

## Minimal schema

Each source is a JSON object (max 16 MiB) with a supported schema. All coordinates and scalar values must be finite. Triangles use zero-based indices and must have positive **unsigned** area. The input must identify its source, geometry/conditions and units; strings called hashes must be authentic provenance, not invented identifiers.

```json
{
  "schema": "mesh-native/0.7.1",
  "identity": {
    "case_id": "case-001",
    "run_id": "run-coarse",
    "mesh_id": "mesh-coarse",
    "geometry_hash": "verified-geometry-revision-identifier",
    "conditions_hash": "verified-physics-and-BC-revision-identifier",
    "coordinate_frame": "global",
    "coordinate_unit": "m"
  },
  "nodes": [[0,0], [1,0], [0,1]],
  "cells": [[0,1,2]],
  "fields": {
    "T": {"unit": "K", "values": [300,305,303]}
  }
}
```

The `geometry_hash` and `conditions_hash` keys are caller attestations, **not** independently verified by this tool. The original input file SHA-256 is recorded in a report; distinct `mesh_id` values are required for the cross-mesh operation. Stable, independently verified upstream fingerprints should be used.

### Offline command

```sh
python -m server.mesh_native validate --reference /workspace/coarse.json --output-root /workspace
python -m server.mesh_native compare --reference /workspace/coarse.json --candidate /workspace/fine.json --field T --min-coverage 0.98 --output-root /workspace
python -m unittest tests.test_mesh_native
```

An optional `--max-pairs` stops naive O(number of reference triangles × candidate nodes) work that exceeds the budget (default 2,000,000). Commands return nonzero exit status for incomplete/blocked comparison; some diagnostic reports may still be saved. The standalone CLI reads explicit local paths; use trusted local inputs.

### MCP tool

`mesh_native_analyze(operation, reference_path, candidate_path?, field?, min_coverage?, max_pairs?)` performs the same analysis **without touching COMSOL**. Its paths must resolve inside `COMSOL_OUTPUT_ROOT`; the tool is also allowed in read-only reviewer mode. Reports are written to `COMSOL_OUTPUT_ROOT/mesh-native/report-<uuid>.json`. Inputs are not overwritten. Reports include source-file SHA-256 digests.

## Interpretation

The reference's linear triangular nodal field is interpolated at each candidate node by barycentric coordinates. No extrapolation occurs. Returns `coverage` and, for matched points, unweighted nodal `MAE`, `RMSE`, `max_abs` and `relative_l2` (null when the reference norm is zero). A normal diagnostic result is **`DIAGNOSTIC_ONLY`**, even for zero difference. A coverage below the supplied threshold yields `INSUFFICIENT_COVERAGE`. Geometry/BC/physics identity mismatches and incompatible units yield `BLOCKED`. Large comparisons yield `NOT_RUN`.

All scientific status fields remain **`NOT_RUN`**. Diagnostics do not measure mass/energy conservation, the discretization order, a reference-solution error, local truncation error, boundary-layer resolution, physical convergence, mesh quality in COMSOL, or mesh independence. A piecewise-linear nodal interpolation of higher-order FEM output is only a sampled approximation. Nodal weighting is susceptible to nonuniform mesh density, and a better/smaller nodal error does not imply a valid physical solution. Overlapping triangles and global topology are not certified. A small epsilon is used at triangle boundaries; no tolerance has been validated for all mesh scales.

## Recommended gates before using in an agent

1. Confirm original geometry, frame, physical units and conditions independently; do not invent hashes or nodal mappings.
2. Run schema validation on both inputs, then inspect all unmatched nodes.
3. Compare scalar-field differences only as diagnostic evidence.
4. Evaluate actual observables and conservation in COMSOL through the existing scientific gates.
5. For a genuine grid convergence assessment, perform multiple licensed COMSOL solves with controlled geometry/physics, consistent metrics and appropriate refinement/error estimates. Mark unexecuted checks `NOT_RUN`.
6. Do not use these diagnostics alone as a training signal for RSI retention or automatic geometry/mesh repair.

**Research pathway:** future separately scoped work may add COMSOL export connectors, support for 3D/mixed meshes, spatial indexing, area-weighted/conservative transfer, wall and boundary-layer checks, multimesh study contracts, and eventually an evaluated MNC surrogate. None of these is implemented here.
