# Paper2Simu Discovery Mode v0.3.0 — cost-aware CFD surrogate screening

**Research-branch prototype only.** No COMSOL / Ansys Fluent connection, no autonomous optimization, no authenticated CFD input/result readback, and no new scientific PASS.

## Two operating modes

| Contract | REPRODUCTION | DISCOVERY |
| --- | --- | --- |
| Goal | reconstruct a particular paper's reported numerical setup and results | explore new, explicitly user-defined designs |
| Authoritative inputs | journal body, author supplements, source-grounded conditional alternatives | declared design bounds, fixed baselines and relevant physical/manufacturing constraints |
| Changing geometry | only a disclosed conditional hypothesis, never silently equated with original author geometry | allowed inside frozen design-space constraints |
| AI surrogate | diagnosis and bounded sensitivity; never a replacement for original CFD evidence | screen candidate conditions, propose costly runs |
| Claim | source-grounded paper comparison, with numerical/physical gates | independently verified new-design findings, not paper reproduction |

Do not call surrogate-interpolated objectives CFD results. Do not reinsert predictions as native training evidence. User authorization to inspect a paper does not imply permission to launch a solver.

## Implemented, purely offline workflow

1. Freeze a DISCOVERY design-space contract (research_design/contracts.py), with continuous/integer/categorical variables, fixed inputs, basic physical constraints, objectives, solver route and budget.
2. Register caller-declared native observations with research_design/observations.py. Records declare dataset/configuration hash, case/result hashes, solver, fidelity group, original source reference, exact metric units, estimated runtime, train/held_out split, and four native/scientific checks.
3. Exclude incomplete/failed checks and different configurations/fidelity; hold-out data is never used for model fitting. A given design may not occur in both train and held_out splits. Mixing COMSOL and Fluent datasets is refused until a separate solver comparability study.
4. Fit a simple inverse-distance-weighted baseline (IDW, k=3) with research_design/surrogate.py. Require >=4 independent designs; aggregate replicates of the same design before grouped leave-one-design-out (LODO) validation.
5. Report objective-specific LODO absolute/normalized MAE. The normalized error divides by maximum absolute observed target, not by each individual target; it is NOT a local percent error and NOT calibrated predictive uncertainty.
6. Predict only within the observed numeric coordinate range and seen categorical choices. This rectangular check does NOT establish dense sampling coverage or guarantee interpolation fidelity. Out-of-range conditions receive no proxy prediction, but could still be proposed as separate authorized real CFD experiments.
7. Use research_design/discovery_loop.py with explicitly declared per-objective maximum LODO normalized MAE. If even one required objective exceeds its threshold, stop surrogate-based ranking without stopping independent source or conditional modeling work.
8. For admitted candidates, calculate heuristic information distance and observed-range desirability proxies; the existing budget selector screens proposed solver, user-estimated time/RAM, and design hash. All selection outputs remain FOR_OPERATOR_REVIEW_NOT_SCHEDULED with scientific status NOT_RUN.
9. Before any real solve, a trusted separately authorized solver adapter must inspect actual effective BC/material/source values, geometry identity, native stop criteria, resource availability, ownership, conservation/mesh and independently save and reopen artifacts. Actual CFD outputs can enter later training only with independently audited provenance.

All record hashes and PASS check flags are **caller-declared** in this prototype, not independently authenticated. The synthetic tests are not real CFD measurements.

## Method limitations and future research

Motivating research: Neural-Network and Reduced-order Modeling Workflows for AI-Driven CFD. A small collection of geometry cases does not automatically justify a high-capacity MLP or confidence about an apparent optimum. Individual output quantities can show very different validation errors.

IDW is only a weighted average: it cannot predict values outside the extrema of observed targets. Therefore the score field named improvement_value in the legacy selector is explicitly interpreted as a **within-observed-range desirability proxy, not actual or expected improvement**. Nearest-distance score is a heuristic, not Bayesian information gain or calibrated uncertainty.

Not implemented in v0.3.0: MLP, PCHIP, Gaussian Process, calibrated uncertainty intervals, Bayesian acquisition, POD/SINDy, verified multi-fidelity physics, self-directed solver execution, real CFD benchmark or measured compute savings. None are implied by the file/module names.

Suggested next independent PRs: trusted solver record adapter, separate held-out evaluation, random/LHS/MLP/GP benchmarking with frozen resource budgets, scientific conservation and mesh gates for candidate outputs, then authorized active solver iteration. Track false scientific PASS and unnecessary blocking under the same held-out cases.

## Run offline

~~~bash
python -m unittest tests.test_research_design tests.test_discovery_surrogate -v
python -m unittest discover -s tests -v
~~~

API sketch (requires the caller's reviewed space, observation data and request; no real jobs are supplied by the repository):

~~~python
from research_design import validate_space, screen_and_rank

space_report = validate_space(space)
decision = screen_and_rank(space, dataset, request)
assert decision["solver_contacted"] is False
assert decision["solver_execution_authorized"] is False
~~~

See tests/test_discovery_surrogate.py for fully synthetic fixtures; examples/microchannel_design.json is a hypothetical design space, not a research paper's data.

## Governance

- [Native solver convergence](native-convergence-policy.md)
- [Conditional paper reconstruction](conditional-reconstruction-and-rsi-evidence-v0.2.1.md)
- [CHT energy policy](cht-coupling-energy-gates.md)
- [Eça–Hoekstra original paper review](eca-hoekstra-2014-original-paper-review.md)
- [Research plan prototype](ai-experiment-design-research.md)

Never upload private COMSOL files, Fluent case/data, confidential paper inputs, personal directories or undisclosed native solver logs to a public GitHub repository.
