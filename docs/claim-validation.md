# 逐项验收与证据审查

本协议把“结果数值相近”和“本次仿真验证充分”分开，接续 [物理验证](validation.md) 与 [复现范围](paper-reproduction.md)。阈值是本任务的验收约定，不沿用其他论文/教学案例的固定百分比。

## 计算前确定比较契约

每个 claim 保存 `claim_id`, `description`, `reference_source_ids`, `reference_locator`, `output_id`, `condition`, `selection`, `unit`, `metric`, `acceptance`, `required_coverage`, `physical_gates`, `discretization_gates`。reference 数据绑定来源与哈希；`acceptance` 包含非负有限阈值、依据和冻结的版本/时间。

明确总体目标集合与必需/可选目标。不能看到结果后删掉难以匹配的目标而保持原来的“全通过”名称。阈值缺乏依据时报告数值偏差与 INCONCLUSIVE；探索性计算可以继续，但不能自行造一个普适 3% 标准。

结果记录包含 `run_id`, `spec_revision`, `reference`, `simulation`, `absolute_error`, `relative_error`, `coverage`, `status`, `reason`, `evidence_paths`, `review_mode`。缺值为 null；`relative_error` 为比例，展示百分数另乘 100。物理/离散/重开证据可通过 run manifest 引用，避免复制后出现不一致。

## 状态判定顺序

1. 已有可信证据证明本目标对应执行的求解失败或明确的必需物理/离散门槛失败：`FAIL` 并标 `failure_kind`（例如 solver/physical/discretization），即使没有可比较数值也能报告该执行失败；不要编造数值误差。未知字段仍保留。其他 run 的失败不能直接移植到当前 run。
2. 已确认从未对该目标执行：`NOT_RUN`。有输入资料不能改变此状态；执行历史不明不适用本项。
3. 是否执行不明，或数据身份、工况/单位、参考来源或比较规则无法确认，目标数据缺失、NaN/无穷或覆盖不足：`INCONCLUSIVE`，列出原因。旧 CSV 与新模型未建立身份关联按此处理，不能称其证明新模型失败或成功。
4. 证据与覆盖齐全但指标超出冻结阈值：`FAIL`（numerical）。阈值内且所有适用门槛有通过证据：`PASS`。

若同时有未知项与已证明失败，保留所有原因，总状态 FAIL；未知不能冲淡已证实失败。物理/离散门槛应按任务列出，不适用必须有理由；没有检查证据不等于自动通过。记录 `numerical_comparison` 可说明局部数值合格，但总体 status 仍可能 INCONCLUSIVE/FAIL。

## 标量

先转换到同一单位与定义，计算 `absolute_error = abs(simulation-reference)`。常用联合判据：

```text
absolute_error <= atol + rtol * abs(reference)
```

`atol` 使用输出单位，`rtol` 为无量纲比例，二者都要计算前确定。参考为零时 relative_error=null，仍可用绝对判据；接近零时采用有物理依据的 atol，不用极大百分数替代解释。

下面是合成比较记录，不是 COMSOL 测量，前提是场景明确给定身份、物理与离散检查全部通过。actual evidence 路径在真实运行中必须指向存在的证据，不能照抄此示例 null。

```json
{
  "example_only": true,
  "claim_id": "zero-reference-demo",
  "unit": "mm",
  "reference": 0,
  "simulation": 0.002,
  "metric": "absolute_plus_relative",
  "acceptance": {"atol": 0.005, "rtol": 0.01, "basis": "synthetic predeclared criterion"},
  "absolute_error": 0.002,
  "relative_error": null,
  "allowed_error": 0.005,
  "coverage": 1.0,
  "status": "PASS",
  "reason": "synthetic case stipulates all identity, physical and discretization gates passed",
  "evidence_paths": null,
  "review_mode": "synthetic_test"
}
```

## 曲线、场与图像

- 对齐横纵坐标、单位、归一化、参数/时间/频率、采样位置；记录插值策略、重复 x 的处理与有效共同区间。除非预先定义且有依据，不外推补齐未计算区间。
- 预先选择点误差、RMSE、峰位/峰值等指标及归一化尺度。不能在计算后挑误差最小的指标；RMSE 小也不自动证明关键峰值正确。
- `coverage` 定义随目标记录：连续区间用有效区间并集长度/所需区间长度；离散点用已覆盖所需点数/所需点数，不能把两种定义混用。零长度区间改用点比较。间断缺段按并集计算，不用首尾跨度伪装全覆盖。
- 目标 x∈[0,10]，仅 x∈[4,6] 有结果：连续区间覆盖 0.2。局部误差 1% 满足 3% 也只能局部比较合格，全域 claim 为 INCONCLUSIVE。
- 论文图数字化记录坐标标定、线性/对数轴、曲线辨识方法、提取点和不确定度；无法可靠提取时报告限制。可用文档工具看论文图，不以截图/OCR 操作 COMSOL。
- 图像视觉相似、感知哈希或相同配色只能支持展示检查；不能代替数值、守恒和网格证据。场比较需同坐标/区域、分量、尺度和插值；不同显示变形倍率不能当位移一致。

## 汇总与审查

输出 claim 全表：来源定位、工况、参考、模拟、误差、阈值、覆盖、状态、证据。另列 `n_total`, `n_pass`, `n_fail`, `n_inconclusive`, `n_not_run`；总数须一致，PASS 比例分母用原目标集合，不只用已比较项。

目标集全 PASS 才能说“所声明范围通过”。存在 FAIL 时总体 FAIL；无 FAIL 但存在 INCONCLUSIVE 时总体 INCONCLUSIVE；部分 PASS 但仍有 NOT_RUN 时总体 INCONCLUSIVE；全部 NOT_RUN 时总体 NOT_RUN。Reference 全通过仍不代表整篇论文通过。复现级别与总判定分列。

验证者接收冻结的规格/阈值、原始来源和数据、run manifest、原始导出及日志，不仅接收 Builder 的成功摘要。先核验身份与定义，再独立算指标；发现问题输出对应 claim、证据、最小复核动作，不能私自改 Builder 模型或阈值。

记录 `review_mode=independent_agent / self_review` 及可识别的审查记录。无独立代理时明示自检。模型调参或阈值修订遵循 [校准与修正规则](paper-reproduction.md)：保留原判定，拟合目标不作为独立验证数据。
