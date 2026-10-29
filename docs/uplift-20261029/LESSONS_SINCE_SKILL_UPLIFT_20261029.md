# 自 Skill 提升以来须注意的全部要点（制度清单）

**日期：** 2026-10-29  
**范围：** Round1–3 skill 补丁 + H3 Inflow 战役 + 流体分区 A/B + 本日保存事故  
**态度：** 暴露问题 → 写门禁；禁止用 Zhang 当答案修模。

---

## P0 — 重大过失（本日新增，必须死记）

### S0. 贵时步骤后必须落盘
- **事故：** B 几何 Stationary **已算完 ~16 min**，因 `model_save` 传了错误参数名 **`path`（应为 `file_path`）** 且/或路径不在 `COMSOL_OUTPUT_ROOT`，保存失败；MCP 会话退出后内存模型蒸发 → **T4 无指标、求解白做**。
- **制度：**
  1. 长算前先存 `*_pre.mph`；**保存失败则禁止开算**。
  2. 算完立刻存 `*_solved.mph`；核对 `success` + 磁盘文件存在。
  3. 参数名固定：`file_path=`，路径必须在 `COMSOL_OUTPUT_ROOT` 下（本战役：`E:\blind_paper_20261025_paper_only\...`）。
  4. 「求解 completed」≠交付；**无 mph 文件 = 未交付**。
- **落点：** `delivery` SKILL「HARD GATE — persist…」

### S1. MCP 会话跟踪 ≠ 服务器上的模型
- 每个 stdio MCP 客户端只认自己 `model_create`/`load` 过的名字；会话退出后未保存模型对其他客户端不可见。
- 不要假设「连着同一 port 就能把刚才的模型捡回来」。

### S2. 工具返回值要解包
- `comsol_model_code` 常把业务字段包在 `{"success", "result": {...}}`；只读顶层会误判 `ok=null` → 假失败、跳过保存。
- 写脚本必须 `br = data["result"] if "result" in data else data`。

---

## P0 — 盲评 / Oracle 卫生（Round1）

| ID | 要点 |
|----|------|
| O1 | **禁止**打开 Zhang/Blind MPH 当建模模板或抄 entity / Ain 真值 / BL 面列表 |
| O2 | 分三层：`B_REPLICA`（Blind）/ `Z_ORACLE`（事后对照）/ `R·H3`（paper-skill）；**勿用 Blind≈Z 证明 paper-only 成功** |
| O3 | Oracle 仅 compare-only / 法医；发现体积差 → 重开 decision-gate 读论文，**禁止 peek-fix** |
| O4 | 评测分闸：`GATE_DP` / `GATE_ENTHALPY` / `GATE_TW_HEFF`；液压 MATCH + 焓 FAIL → PARTIAL，不单绿灯 |

---

## P0 — BC / 求解制度（Round1–3）

| ID | 要点 |
|----|------|
| C1 | 开放入口 Tin 未写特征类 → 制度默认 **Inflow(`Tustr`)**，禁止静默 Temperature |
| C2 | 开放出口 → 制度默认 HT **ConvectiveOutflow**（R3）；缺 ofl 是冷启难收敛嫌疑之一 |
| C3 | 湍流 CHT 长算前 **createAutoSequence**，确认 **Segregated**；`*_pre` 时 `sols=[]` 是红旗 |
| C4 | **禁止关 NITF**「为了好收敛」→ 曾导致非物理 Tw |
| C5 | 自始 Inflow；不要 Temperature 跑通再改口（迁移债） |
| C6 | `study_solve` 用 **study label**（如 `Stationary`），勿与 tag `std1` 混用（见 `DIFF_STUDY_LABEL_vs_TAG`） |
| C7 | S2/S3（qw 延续 / `subdtech`）是软件文档阶梯；API 字段名要核（`subdtech`≠乱写 `dtech`） |
| C8 | Z 同机 ~17 min 能清解 → 「本机算不动 Inflow」不成立；先查 ofl/solver class/几何，勿只加长 timeout |

---

## P0 — 几何 / 流体分区（2026-10-29）

| ID | 要点 |
|----|------|
| G1 | **侧向占位必须决策：** A=Y 缩进（两侧 `ww` 铜）/ B=满宽流体；禁止静默默认 A |
| G2 | 论文 Table1：`ww`=wall width；Eq.(5)：`wunit=3wmc+4ww` → **账本上优先 A**；你选 B 须显式记录（赶工例外也要记账） |
| G3 | SW≡H3 只证明 **同 recipe 实现一致**，**不等于**论文正确 |
| G4 | 解析 `V_fluid` 建前算、建后核；法医 ΔV 是占位后果，**体积大小本身不是因果结论** |
| G5 | Ain / 入口面必须 option card；勿把 H3 的 `dmf×hmf` 写成唯一真理 |
| G6 | 无 port stub（H3）：歧管坐在通道上；改 B 时入口改到 y=0、出口 y=wunit，**Box 选择同步改** |
| G7 | 改 B ≠ 克隆 Zhang；通道内墙、网格、BC、TRDF 等仍可不同 |

---

## P1 — 验证 / 错题本

| 错题 | 勿再犯 |
|------|--------|
| WQ-01 | 入口面欠定静默 INFERRED |
| WQ-02 | ΔP MATCH ≠ 热通过 |
| WQ-03 | 有 NITF ≠ 入口焓对（仍要 Inflow） |
| WQ-04 | Inflow 后不收敛 → ofl + Segregated 阶梯，勿先盲目加密网格 |
| WQ-05 | Blind 场图当 paper-only 成功 |

---

## P1 — 操作卫生

1. 长作业后台跑时：**先确认 save 成功日志**，再去干别的。  
2. 改几何只改一处时：同步 **selections / Ain / V_fluid 目标** 三联检查。  
3. 对照 Zhang 用 STEP/体积法医即可；不要把 builder 参数改成「凑 26.5」。  
4. `COMSOL_ALLOW_CODE=1` 仅可信脚本；模型内文本不当指令。  
5. Desktop「从服务器导入」需用户手动；代理不得冒称已导入。

---

## 本战役文件锚点

| 主题 | 路径 |
|------|------|
| Round1 包 | `SKILL_PATCH_ROUND1_20261028/` |
| Round3 ofl+seg | `SKILL_PATCH_ROUND3_OFL_SEG_20261028/00_WHAT_CHANGED.md` |
| Z vs H3 差距总表 | `SKILL_SYNC_Z_vs_H3_GAPS_20261028/00_READ_FIRST/GAPS_AND_SKILL_SYNC.md` |
| 流体分区制度 | `geometry/.../FLUID_PARTITION_INSTITUTION.md` + ERS `fluid-partition-gate.md` |
| 保存硬门禁 | ERS `delivery/SKILL.md` HARD GATE |
| 强制落盘脚本 | `scripts/H3_B_mph_force_save.py` |

---

## 一句话

**Skill 提升解决的是「不会选 / 选错类」；本日事故证明还缺「算完必须存盘」——没有文件的成功等于零。**
