# 落到哪些 skill 文件

合并时：**保留已有条文，补洞与改错名**；勿整文件覆盖丢失旧战役条款。

| 原则 | Live 落点 | 本包补丁 |
|------|-----------|----------|
| G0 三层 / 法医 | `paper-analysis`, `geometry-reconstruction`, `decision-gate`, comsol `paper-only-vs-oracle-compare.md` | `01_PATCHES/P01_forensic_vs_builder.md` |
| G1 SOFTWARE_DOC_DEFAULT | `paper-analysis`, `decision-gate`, comsol `cht-coupling-energy-gates.md` | `P02_software_doc_solver_ladder.md`（已有则对齐 API 名） |
| G2 流体分区 A/B | `checklists/fluid-partition-gate.md`, `paper-analysis`, `geometry-reconstruction`, `decision-gate` | `02_CHECKLISTS/fluid-partition-gate.md` + `P03_partition_roundoff_vs_semantics.md` |
| G3 热液分闸 | `validation` | `P04_gates_partial_not_single_green.md` |
| G4 求解阶梯 | `comsol-debug`, `cht-coupling-energy-gates.md` | `P02` + `P05_telemetry_and_one_class.md` |
| G5 落盘 | `delivery` | `P06_persist_hard_gate.md`（对齐已有 HARD GATE） |
| G6 BLOCKED | `comsol-debug`, `validation`, `cht-coupling` | `P07_blocked_solver_matrix.md` |

## 推荐粘贴顺序

1. Checklists（整文件）  
2. `delivery` persist  
3. `cht-coupling-energy-gates` S2–S5 + subdtech  
4. `comsol-debug` 阶梯指针  
5. `paper-analysis` / `geometry-reconstruction` / `decision-gate` 分区与法医  
6. `validation` 分闸 + BLOCKED 矩阵  

## 验收（泛化）

对 **另一篇** 微通道论文（非 Zhang）口述能否回答：

- [ ] 侧向 A/B 未决策时会不会停？  
- [ ] 论文沉默入口热类型时默认写什么标签？  
- [ ] SegregatedStep 阻尼属性真名是什么？  
- [ ] 算完没 mph 算不算交付？  
- [ ] oracle 体积差能否直接改 builder？  
