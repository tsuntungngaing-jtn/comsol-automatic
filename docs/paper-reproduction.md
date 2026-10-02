# 论文复现：证据、范围与修正

用于从论文、补充材料、代码或已有模型恢复仿真方法。本文定义 Agent 的工作协议，不新增自动审计引擎或 MCP 工具。只读模型整理继续使用 [Inspector](inspector.md)，不自动转入求解。

## 从目标到证据

先确定论文版本、用户要验证的图表/结论和工况，给每个目标稳定的 `claim_id`。不默认要求复现整篇论文，也不以跑通官方示例替代论文目标。

记录 `evidence/parameters.json`（需表格时另导出 CSV）与 `evidence/sources.json`：

| 记录 | 必需字段与含义 |
| --- | --- |
| 参数 | `parameter_id`, `meaning`, `original_value`, `original_unit`, `value`, `unit`, `source_type`, `source_ids`, `evidence_status`, `conditions`, `critical`, `affected_claim_ids` |
| 来源 | `source_id`, `kind`, `locator`, `version`, `retrieved_at`, `artifact_path`, `sha256`；未取得本地文件时最后两项为 null，记录访问限制 |
| 缺失 | 值为 null，`source_type=missing`, `evidence_status=missing`, `source_ids=[]`，列入规格的 `unresolved` |
| 推导 | 增加 `derivation`：公式、输入参数 ID、单位换算及适用条件；输入仍需溯源 |
| 假设 | 增加 `assumption`：原因、范围、敏感性检查计划；不能标为论文原值 |
| 冲突 | 增加 `candidates`：各候选值、单位、source_ids；另记 `resolution` 的选择与理由，未解决时 value 为 null |

`source_type` 为 `paper / supplement / code / cited_work / manual / derived / assumed / missing`；`evidence_status` 为 `verified / unverified / conflicting / missing`。前者表示来处，后者表示已核查程度。`verified` 只说明该记录的来源/适用性已检查，不证明物理模型正确；假设即使评估过仍保持 `assumed`。

`locator` 必须可定位：页码与公式/图表号，或仓库 URL、提交、文件与行，或手册版本和章节。`conditions` 包含会改变参数意义的温度、频率、材料牌号或实验工况。保留原始单位；温度绝对值与温差、表压与绝压、幅值与 RMS 不能只改单位标签。

按缺口查论文附件、对应提交的官方代码、被引原文和同版本软件资料。搜索摘要只能作线索；未读到来源标 `unverified`。来源冲突按版本、工况及明确的方法描述判断，不能按“哪个结果更接近图”挑值。记录已查范围和访问限制，关键缺失集中询问；继续整理不依赖缺失值的部分。

## 三个独立状态轴

下面的英文标签是本 Skill 的项目约定，不是学界统一分级。每次报告同时给出范围、执行状态和 claim 结果。

| `reproduction_level` | 范围含义 |
| --- | --- |
| `Exact` | 原代码/模型、原数据及关键条件已具备，可按原工作流复跑。不是已经成功，也不默认跨硬件逐位一致 |
| `Reference` | 验证对象是官方示例/参考输出，结果仅覆盖该对象 |
| `Partial` | 独立重建、关键条件采用假设、或仅部分工况/结论；必须写明 `scope` 与偏差 |
| `Non-executable` | 当前目标缺少不可替代条件，无法形成有定义的可执行问题；交付资源和阻塞清单 |

没有原代码不自动判 Non-executable：论文条件足够时可以独立重建，用 Partial 和明确 scope 描述。缺本构不能只填 E、nu 就声称任意超弹性模型完整；若提出替代模型，作为假设分支，不冒充原目标。

`execution_state`：`not_run / blocked / prepared / submission_unknown / submitted / running / failed / completed / artifacts_verified`。`completed` 表示后端报告执行结束；其科学有效性与产物身份仍待核验。失败/未知须附 `reason`，不凭超时推断失败。各 claim 的 `status` 为 `PASS / FAIL / INCONCLUSIVE / NOT_RUN`，判定见 [逐项验收](claim-validation.md)。

接手已有模型而执行历史不明时，`execution_state=null` 并写明 `reason` 和最近可证实的事件；null 表示未能确定，不是 not_run。资料不足以判级时 `reproduction_level=null` 并列待查证据，不能猜 Exact/Partial；null 不是新增复现级别。明确从未执行才用 NOT_RUN；是否执行也未知而无已证实失败时，claim 为 INCONCLUSIVE。

原始资料齐全但未运行：Exact + not_run + NOT_RUN。官方例子成功仍是 Reference；原论文未运行的目标保留 NOT_RUN，不能被例子结果覆盖。一个研究中不同目标可有不同级别，汇总列出映射，不以最好的级别覆盖其他目标。

## 执行流程

1. 保存目标、来源、参数与未决问题，先明确可复现范围。冻结输入前执行 [物性与模型一致性门槛](model-consistency.md)：追查论文指向的材料库/函数来源，核验完整精度、工作区间与参考工况；不能把印刷舍入造成的异常当作已验证输入。
2. 按 [仿真规格](simulation-specification.md) 写 `simulation/specification.json`。关键缺失阻塞相关求解，不妨碍其他已定义工作。
3. 在计算前确定目标量、数值容差及物理/离散验证门槛并留存版本。没有合理阈值可做探索性计算，比较只给误差与 INCONCLUSIVE。
4. 经 MCP 在独立模型副本建模/执行，沿用 [设置、几何、保存重开核验](research-workflow.md)。远程计算另外读 [HPC 交接](hpc-execution.md)。
5. 将本次输入、解、数据集和导出结果绑定到 run_id，再做逐项验收；文件存在不是解正确的证据。
6. 失败时按下节处理，最终交付所有目标状态、证据与限制。

这些是职责阶段，不必创建固定数量的 Agent。独立验证仅在当前会话允许使用子代理时分派；否则按同一契约自检并注明 `review_mode=self_review`，不能声称独立审查。

## 有界诊断与修正

按输入身份/单位 → 几何与选择 → 材料与耦合 → 研究与解 → 网格/时间步 → 输出定义的顺序缩小原因。每个候选记录 `hypothesis`, `supporting_evidence`, `counter_evidence`, `minimal_check`, `expected_effect`；证据不足时保留为假设，不直接改全部参数。

开始修正前在 `repair_budget` 记录最大追加轮次、总墙钟/资源上限和停止条件。沿用用户已给范围，不重复审批；用户未给数值时，按现有授权范围提出具体预算，缺少授权的高成本远程计算不开始。每轮只改可检验的一组因素，保存 `parent_run_id`、新 spec revision、改动与依据、成本及前后结果。

达到预算、同一错误没有新证据、缺关键物理条件或许可证/后端不可用时，停止相关运行，保留现状与最小下一步。不要为完成报告无限重算。

用论文目标反推 E 等参数属于 `calibration`。同一数据可作为拟合质量报告，但不能作为独立验证；另选未用于拟合的工况/数据并说明来源。看结果后改变阈值必须生成新验收版本、记录理由、保留原 verdict；不得覆盖原失败再称原标准已通过。

## 交付复现包

建议布局（只生成实际有内容的产物，不创建空 MPH 或伪日志）：

```text
reproduction/
  paper/                 # 已取得且可保留的来源文件
  evidence/              # parameters.json, sources.json, assumptions.md
  simulation/            # specification.json, model.mph, 可重放源码
  runs/<run_id>/         # manifest.json, 输入/日志/版本证据
  results/<run_id>/      # 实际导出数值与图
  validation/            # claims.json, errors.csv, 比较图
  report/                # reproduction_report.md（需要时再生成 PDF）
```

报告依次给范围和结论、claim 全表及覆盖率、参数/假设、运行与模型身份、物理及离散检查、修正历史、限制和可复跑步骤。标明源码是否重放、模型是否重开、哪些目标尚未验证。源论文/模型不覆盖；用户数据与报告留在工作区，不纳入 Skill 发布目录。
