# 可泛化原则（跨战役）

适用：**任意** 微通道 / MMC / CHT 论文复现或盲评，不限于 2026-10 某次 Zhang–H3 trial。

---

## G0. 三层对象永不混用

| 层 | 用途 | 禁入 |
|----|------|------|
| Paper / skill build | 建几何、BC、求解 | Oracle 真值、entity |
| Self-consistency | 同 recipe 的 CAD↔COMSOL | 「实现一致」冒充「论文正确」 |
| Forensic / oracle compare | 事后体积、墙钟、字段类对照 | 写回 builder 参数「凑齐 oracle」 |

**失效模式：** Blind≈Oracle 场图被当成 paper-only 成功；或发现 ΔV 后 peek-fix。

---

## G1. 论文沉默 ≠ 静默猜一个习惯

论文未写清的特征类 / 分区 / 求解细节：

1. 标 `[NOT IN PAPER]` 或开 **decision-gate** 选项卡；或  
2. 标 `[SOFTWARE_DOC_DEFAULT: <安装版文档 locus>]`（CFD/HT/REF/API 页码级）；  
3. **禁止** 用 benchmark MPH 当默认来源。

典型默认（可复用，仍须记 locus）：

- 开放流体入口 + 仅给 Tin → HT **Inflow(Tustr)**，非 Temperature  
- 开放出口 + 仅给压力 → HT **ConvectiveOutflow**  
- 湍流 CHT Stationary → **Segregated** 序列先于长算  
- 壁宽 `ww` 进单元宽度公式 → 侧向占位必须显式 **A/B**，禁止静默默认

---

## G2. 几何：身份闭合，不是答案闭合

建前写清并建后核：

- 侧向占位 A（边壁固体）/ B（流体满宽）+ `claim_id`  
- `V_fluid_analytic` / `V_solid_analytic` / `A_in` 身份  
- 实测相对 analytic 容差（默认 0.1%）

若事后法医显示与 oracle 分区不同：

- 记「几何族不同」；  
- **重开决策读论文**；  
- **禁止**把 oracle `V_fluid` 设为目标。

**鉴别 round-off：** 同一公式测得 vs 解析误差 ~机器精度 → 浮点；  
**离散分区差**（如整 mm³ 布尔对称差、bbox 端点跳到单元边界）→ **语义选择**，不是舍入。

---

## G3. 热液门禁分闸

| 闸 | 绿不代表 |
|----|----------|
| `GATE_DP` / 质量守恒 | 焓或 Tw 通过 |
| `GATE_INLET_BC` Inflow | 已收敛 |
| `GATE_ENTHALPY` | 可关 nitf 冲数 |
| 求解 completed | 已落盘 mph |

液压 MATCH + 焓 FAIL → **PARTIAL**，不单开绿灯。

---

## G4. 求解阶梯：一枪一类 + 诚实证据

Inflow + NITF 难收敛时（纸面 BC 已绿）：

```
S0 probe → S1 Segregated+init → S2 qw continuation ONLY
→ S3 damping/iter ONLY (SegregatedStep: subdtech 非乱写 dtech)
→ S4 freeze flow, nitf ON → S5 BLOCKED_SOLVER + matrix
```

硬规则：

- **一枪只改一类**（勿 S2+S3+网格同开）  
- **禁止**关 nitf / 回 Temperature / 先加密网格 / 抄 oracle solver 节点  
- 遥测：优先读 `~\.comsol\v*\logs\mphserver*.log` 与结束后 `message`；中途 `model_code` 常锁空  
- 区分 **SLOW** / **NONCONV**（达最大牛顿等）/ **STALL_UNKNOWN**；无证据勿只加长 timeout  
- 同机 oracle clear+resolve 很快而 paper 案卡住 → 先查 **BC 类 / 求解类 / 几何族**，不是「机器不行」

---

## G5. 贵时步骤：无文件 = 未发生

长几何 / 长求解：

1. 开算前 `model_save(file_path=…_pre.mph)` 成功，且路径在 `COMSOL_OUTPUT_ROOT` 下  
2. 算完立刻 `_solved.mph`；核对磁盘存在  
3. API 参数名以工具 schema 为准（`file_path` ≠ `path`）  
4. `comsol_model_code` 业务字段在 `result` 内；须解包再判 `ok`  
5. 另一 MCP 会话 **捡不回** 未保存模型

---

## G6. BLOCKED 是合法科学状态

阶梯用尽仍无物理热解：

- 状态：`BLOCKED_SOLVER`（≠ mesh FAIL ≠ coupling 未挂）  
- 交付：矩阵（BC 类、nitf、阶梯各枪结果、几何 A/B、禁项遵守）  
- 升级：重开论文决策卡 / 改研究问题；**不是** Temperature 绿瓦焓门  

---

## 一句话

**Skill 管「不会选 / 选错类 / 算完不存」；Trial 数字只作法医与回归样例，永不升格为全局几何真理。**
